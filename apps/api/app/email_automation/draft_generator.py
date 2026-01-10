"""Email draft generation service orchestrating the full pipeline.

Coordinates: Email extraction → PII redaction → RAG retrieval → LLM generation → HITL queue.
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.email_processing_queue import EmailProcessingQueue
from app.models.email_draft import EmailDraft
from app.models.email_monitoring_rule import EmailMonitoringRule
from app.models.bot import Bot
from app.models.user_writing_style import UserWritingStyle
from app.services.pii_service import PIIRedactionService
from app.services.vector_search_service import VectorSearchService
from app.services.llm_service import LLMService
from app.services.citation_service import CitationService
from app.email_automation.email_extractor import EmailExtractor
from app.email_automation.style_analyzer import create_style_guidelines_prompt

logger = logging.getLogger(__name__)

# Thresholds and timeouts
CONTEXT_RELEVANCE_THRESHOLD = 0.5
LLM_GENERATION_TIMEOUT_S = 30
DEFAULT_LOW_CONTEXT_DRAFT = "Thank you for your email. I need to review this and will get back to you shortly."
DEFAULT_LOW_CONTEXT_CONFIDENCE = 0


class DraftGenerationError(Exception):
    """Error during draft generation."""
    pass


class EmailDraftGenerationService:
    """Service for generating email drafts from queued emails."""
    
    def __init__(
        self,
        pii_service: PIIRedactionService,
        vector_search_service: VectorSearchService,
        llm_service: LLMService,
        citation_service: CitationService,
    ):
        self.pii_service = pii_service
        self.vector_search_service = vector_search_service
        self.llm_service = llm_service
        self.citation_service = citation_service
    
    async def process_queued_email(
        self,
        db: AsyncSession,
        queue_item: EmailProcessingQueue,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        provider: str,
    ) -> Optional[EmailDraft]:
        """Process a queued email and generate a draft.
        
        Args:
            db: Database session
            queue_item: EmailProcessingQueue item to process
            client_id: OAuth client ID
            client_secret: OAuth client secret
            refresh_token: OAuth refresh token
            provider: Email provider (gmail, outlook)
        
        Returns:
            Generated EmailDraft if successful, None on failure
        """
        start_time = time.time()
        
        try:
            # Get monitoring rule to find bot_id
            rule = await db.scalar(
                select(EmailMonitoringRule).where(
                    EmailMonitoringRule.id == queue_item.rule_id
                )
            )
            
            if not rule:
                raise DraftGenerationError(f"Monitoring rule {queue_item.rule_id} not found")
            
            bot_id = rule.bot_id
            queue_item.bot_id = bot_id
            
            # Step 1: Extract email content
            logger.info(f"Extracting email {queue_item.provider_message_id}")
            email_data = await self._extract_email(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                provider=provider,
                provider_message_id=queue_item.provider_message_id,
                thread_id=queue_item.thread_id,
            )
            
            if not email_data:
                raise DraftGenerationError("Failed to extract email content")
            
            # Update queue item with extracted data
            queue_item.email_subject = email_data['subject']
            queue_item.email_body = email_data['body']
            queue_item.sender_email = email_data['sender_email']
            queue_item.thread_id = email_data.get('thread_id')
            queue_item.status = "processing"
            await db.flush()
            
            # Step 2: Redact PII
            logger.info(f"Redacting PII from email body")
            redacted = await self.pii_service.redact_query(email_data['body'])
            redacted_body = redacted.redacted_query
            
            # Step 3: Retrieve relevant context via RAG
            logger.info(f"Retrieving context for bot {bot_id}")
            search_results, search_latency_ms = await self.vector_search_service.search(
                db=db,
                bot_id=bot_id,
                tenant_id=queue_item.tenant_id,
                query=redacted_body,  # Use redacted body for search
                k=5,
                similarity_threshold=CONTEXT_RELEVANCE_THRESHOLD,
            )
            
            logger.debug(f"Found {len(search_results)} relevant chunks (latency: {search_latency_ms}ms)")
            
            # Step 4: Generate draft via LLM
            logger.info(f"Generating draft for email")
            
            # Load user's writing style profile
            style_profile = await self._get_user_writing_style(
                db=db,
                user_id=queue_item.user_id,
                integration_id=queue_item.integration_id
            )
            
            draft_body, citations, confidence_score = await self._generate_draft(
                original_email=email_data,
                context_results=search_results,
                bot_id=bot_id,
                has_context=len(search_results) > 0,
                style_profile=style_profile,
            )
            
            # Step 5: Create draft record
            generation_time_ms = int((time.time() - start_time) * 1000)
            draft = EmailDraft(
                id=uuid4(),
                tenant_id=queue_item.tenant_id,
                queue_id=queue_item.id,
                bot_id=bot_id,
                integration_id=queue_item.integration_id,
                original_email_id=queue_item.provider_message_id,
                thread_id=queue_item.thread_id,
                sender_email=queue_item.sender_email,
                original_subject=email_data['subject'],
                subject=f"Re: {email_data['subject']}",
                body=draft_body,
                citations=citations,
                confidence_score=confidence_score,
                generation_time_ms=generation_time_ms,
                status="pending_review",
            )
            
            db.add(draft)
            
            # Step 6: Mark queue item as completed
            queue_item.status = "completed"
            queue_item.processed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(
                f"Draft generated successfully: {draft.id} "
                f"(confidence: {confidence_score}%, time: {generation_time_ms}ms)"
            )
            
            return draft
            
        except DraftGenerationError as e:
            logger.error(f"Draft generation failed: {e}")
            queue_item.status = "failed"
            queue_item.error_message = str(e)
            queue_item.retry_count += 1
            await db.commit()
            return None
        except Exception as e:
            logger.exception(f"Unexpected error during draft generation: {e}")
            queue_item.status = "failed"
            queue_item.error_message = str(e)[:500]
            queue_item.retry_count += 1
            try:
                await db.commit()
            except:
                pass
            return None
    
    async def _extract_email(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        provider: str,
        provider_message_id: str,
        thread_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Extract email from provider."""
        extractor = EmailExtractor(client_id, client_secret)
        
        try:
            if provider == "gmail":
                return await extractor.extract_gmail_email(
                    refresh_token=refresh_token,
                    message_id=provider_message_id,
                    thread_id=thread_id or provider_message_id,
                )
            elif provider == "outlook":
                return await extractor.extract_outlook_email(
                    refresh_token=refresh_token,
                    message_id=provider_message_id,
                    conversation_id=thread_id or provider_message_id,
                )
            else:
                raise DraftGenerationError(f"Unsupported provider: {provider}")
        except Exception as e:
            logger.exception(f"Failed to extract email: {e}")
            return None
    
    async def _get_user_writing_style(
        self,
        db: AsyncSession,
        user_id: UUID,
        integration_id: UUID,
    ) -> Optional['UserWritingStyle']:
        """Get user's writing style profile for an integration.
        
        Returns:
            UserWritingStyle if exists, None otherwise
        """
        try:
            stmt = select(UserWritingStyle).where(
                and_(
                    UserWritingStyle.user_id == user_id,
                    UserWritingStyle.integration_id == integration_id
                )
            )
            result = await db.execute(stmt)
            return result.scalar()
        except Exception as e:
            logger.warning(f"Failed to load writing style profile: {e}")
            return None
    
    async def _generate_draft(
        self,
        original_email: Dict[str, str],
        context_results: List,
        bot_id: UUID,
        has_context: bool,
        style_profile: Optional['UserWritingStyle'] = None,
    ) -> tuple[str, Optional[Dict], int]:
        """Generate draft using LLM with optional style matching.
        
        Returns:
            Tuple of (draft_body, citations, confidence_score)
        """
        # Handle low/no context scenario
        if not has_context:
            return (
                DEFAULT_LOW_CONTEXT_DRAFT,
                None,
                DEFAULT_LOW_CONTEXT_CONFIDENCE,
            )
        
        # Build prompt with optional style guidelines
        prompt = self._build_draft_prompt(original_email, context_results, style_profile)
        
        try:
            # Generate using LLM with 20-second timeout (AC#3: <20s LLM generation)
            response_tokens = []
            try:
                async with asyncio.timeout(20):  # Python 3.11+
                    async for token in self.llm_service.generate_answer(
                        query=original_email['body'],
                        context_chunks=context_results,
                    ):
                        response_tokens.append(token)
            except asyncio.TimeoutError:
                logger.error(f"LLM generation timeout (20s limit) for bot {bot_id}")
                raise DraftGenerationError("LLM generation timeout (20s limit)")
            
            draft_body = ''.join(response_tokens)
            
            # Extract citations from context
            citations_data = None
            if context_results:
                citations_data = await self.citation_service.extract_citations(
                    answer=draft_body,
                    context_chunks=context_results,
                )
            
            # Calculate confidence based on context relevance
            avg_similarity = sum(r.similarity for r in context_results) / len(context_results) if context_results else 0
            confidence_score = int(min(100, avg_similarity * 100))
            
            return draft_body, citations_data, confidence_score
            
        except asyncio.TimeoutError:
            logger.error(f"LLM generation timeout for bot {bot_id}")
            raise DraftGenerationError("LLM generation timeout")
        except Exception as e:
            logger.exception(f"LLM generation failed: {e}")
            raise DraftGenerationError(f"LLM generation failed: {e}")
    
    def _build_draft_prompt(
        self,
        original_email: Dict[str, str],
        context_results: List,
        style_profile: Optional['UserWritingStyle'] = None,
    ) -> str:
        """Build structured prompt for draft generation with optional style guidelines."""
        
        context_text = "\n\n".join([
            f"Source: {r.document_name} (Section: {r.section})\n{r.text}"
            for r in context_results
        ])
        
        # Build base prompt
        prompt = f"""You are a helpful email assistant. Generate a professional reply to the email below using ONLY the provided context.

Context from knowledge base:
{context_text}

"""
        
        # Inject style guidelines if profile exists and has sufficient data
        if style_profile and style_profile.sample_count >= 10:
            style_dict = {
                "tone": style_profile.tone,
                "greeting_pattern": style_profile.greeting_pattern,
                "closing_pattern": style_profile.closing_pattern,
                "avg_email_length": style_profile.avg_email_length,
                "avg_sentence_length": style_profile.avg_sentence_length,
                "uses_emojis": style_profile.uses_emojis,
                "formality_score": style_profile.formality_score,
            }
            # Add any custom preferences (overrides)
            if style_profile.custom_preferences:
                style_dict.update(style_profile.custom_preferences)
            
            style_guidelines = create_style_guidelines_prompt(style_dict)
            prompt += style_guidelines + "\n\n"
        elif style_profile and style_profile.sample_count > 0 and style_profile.sample_count < 10:
            # Show learning banner
            prompt += f"""**Note**: We're learning your writing style ({style_profile.sample_count}/10 emails analyzed). Send more emails to improve personalization.

"""
        
        # Add original email
        prompt += f"""Original Email:
From: {original_email.get('sender_email', 'Unknown')}
Subject: {original_email.get('subject', '(No Subject)')}

{original_email.get('body', '')}

Generate a reply that:
- Addresses the sender's question/request
- Uses information from the context only
- Is professional and courteous
- Maintains company tone"""
        
        if style_profile and style_profile.sample_count >= 10:
            prompt += """
- Matches the user's detected writing style"""
        
        prompt += """
- If context insufficient: politely say you need to review and will respond soon

Reply:"""
        
        return prompt

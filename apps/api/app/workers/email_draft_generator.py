"""Background worker for email draft generation.

Polls the email_processing_queue for pending items and processes them through
the draft generation pipeline.
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select, and_
from sqlalchemy.orm import sessionmaker

from app.models.email_processing_queue import EmailProcessingQueue
from app.models.email_integration import EmailIntegration
from app.models.integration_credentials import IntegrationCredentials
from app.email_automation.draft_generator import EmailDraftGenerationService
from app.services.pii_service import PIIRedactionService
from app.services.vector_search_service import VectorSearchService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.citation_service import CitationService
from app.utils.encryption import decrypt_token

logger = logging.getLogger(__name__)

# Configuration
POLL_INTERVAL_SECONDS = 10
PROCESSING_TIMEOUT_SECONDS = 30
MAX_CONCURRENT_DRAFTS = 2
MAX_RETRIES = 3


class EmailDraftGeneratorWorker:
    """Worker for processing email drafts from the queue."""
    
    def __init__(
        self,
        db_url: str,
        tenant_id: Optional[UUID] = None,
        poll_interval: int = POLL_INTERVAL_SECONDS,
    ):
        self.db_url = db_url
        self.tenant_id = tenant_id
        self.poll_interval = poll_interval
        self.is_running = False
        self.engine = None
        self.session_factory = None
        
        # Initialize services
        self.pii_service = PIIRedactionService(presidio_enabled=True)
        self.embedding_service = EmbeddingService()
        self.vector_search_service = VectorSearchService(self.embedding_service)
        self.llm_service = LLMService()
        self.citation_service = CitationService()
        self.draft_generator = EmailDraftGenerationService(
            pii_service=self.pii_service,
            vector_search_service=self.vector_search_service,
            llm_service=self.llm_service,
            citation_service=self.citation_service,
        )
    
    async def start(self):
        """Start the worker."""
        logger.info(f"Starting EmailDraftGeneratorWorker (poll_interval={self.poll_interval}s)")
        
        # Initialize database
        self.engine = create_async_engine(self.db_url, echo=False)
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        self.is_running = True
        try:
            await self._polling_loop()
        except Exception as e:
            logger.exception(f"Worker error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the worker and clean up."""
        logger.info("Stopping EmailDraftGeneratorWorker")
        self.is_running = False
        
        if self.llm_service:
            await self.llm_service.close()
        
        if self.engine:
            await self.engine.dispose()
    
    async def _polling_loop(self):
        """Main polling loop."""
        while self.is_running:
            try:
                async with self.session_factory() as db:
                    # Get pending items from queue
                    pending_items = await self._get_pending_items(db)
                    
                    if pending_items:
                        logger.info(f"Found {len(pending_items)} pending email(s)")
                        
                        # Process in batches respecting concurrency limit
                        for i in range(0, len(pending_items), MAX_CONCURRENT_DRAFTS):
                            batch = pending_items[i:i + MAX_CONCURRENT_DRAFTS]
                            await asyncio.gather(*[
                                self._process_item(db, item)
                                for item in batch
                            ])
                    else:
                        logger.debug("No pending emails in queue")
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.exception(f"Error in polling loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _get_pending_items(self, db: AsyncSession) -> list:
        """Get pending items from queue, ordered by creation time (FIFO)."""
        query = select(EmailProcessingQueue).where(
            and_(
                EmailProcessingQueue.status == "queued",
                EmailProcessingQueue.retry_count < MAX_RETRIES,
            )
        ).order_by(EmailProcessingQueue.created_at.asc()).limit(MAX_CONCURRENT_DRAFTS)
        
        if self.tenant_id:
            query = query.where(EmailProcessingQueue.tenant_id == self.tenant_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _process_item(self, db: AsyncSession, queue_item: EmailProcessingQueue):
        """Process a single queue item."""
        try:
            logger.info(f"Processing email {queue_item.id} (provider_id: {queue_item.provider_message_id})")
            
            # Get integration details
            integration = await db.scalar(
                select(EmailIntegration).where(
                    EmailIntegration.id == queue_item.integration_id
                )
            )
            
            if not integration:
                logger.error(f"Integration {queue_item.integration_id} not found")
                queue_item.status = "failed"
                queue_item.error_message = "Integration not found"
                await db.commit()
                return
            
            # Get OAuth credentials
            client_id, client_secret = await self._resolve_oauth_credentials(
                db, queue_item.tenant_id, integration.provider
            )
            
            if not client_id or not client_secret:
                logger.error(f"OAuth credentials not found for {integration.provider}")
                queue_item.status = "failed"
                queue_item.error_message = "OAuth credentials not found"
                await db.commit()
                return
            
            # Decrypt refresh token
            try:
                refresh_token = decrypt_token(integration.encrypted_refresh_token)
            except Exception as e:
                logger.error(f"Failed to decrypt refresh token: {e}")
                queue_item.status = "failed"
                queue_item.error_message = "Token decryption failed"
                await db.commit()
                return
            
            # Process with timeout
            try:
                draft = await asyncio.wait_for(
                    self.draft_generator.process_queued_email(
                        db=db,
                        queue_item=queue_item,
                        client_id=client_id,
                        client_secret=client_secret,
                        refresh_token=refresh_token,
                        provider=integration.provider,
                    ),
                    timeout=PROCESSING_TIMEOUT_SECONDS,
                )
                
                if draft:
                    logger.info(f"Draft generated: {draft.id} (confidence: {draft.confidence_score}%)")
                else:
                    logger.warning(f"Draft generation returned None for queue item {queue_item.id}")
                    
            except asyncio.TimeoutError:
                logger.error(f"Processing timeout for queue item {queue_item.id}")
                queue_item.status = "failed"
                queue_item.error_message = "Processing timeout"
                queue_item.retry_count += 1
                await db.commit()
            
        except Exception as e:
            logger.exception(f"Error processing queue item {queue_item.id}: {e}")
            queue_item.status = "failed"
            queue_item.error_message = str(e)[:500]
            queue_item.retry_count += 1
            try:
                await db.commit()
            except:
                pass
    
    async def _resolve_oauth_credentials(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        provider: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Resolve OAuth credentials for a provider."""
        # Try tenant-specific first
        cred = await db.scalar(
            select(IntegrationCredentials).where(
                and_(
                    IntegrationCredentials.provider == provider,
                    IntegrationCredentials.tenant_id == tenant_id,
                )
            ).limit(1)
        )
        
        if cred:
            return cred.client_id, cred.client_secret
        
        # Try global credentials
        cred = await db.scalar(
            select(IntegrationCredentials).where(
                and_(
                    IntegrationCredentials.provider == provider,
                    IntegrationCredentials.tenant_id.is_(None),
                )
            ).limit(1)
        )
        
        if cred:
            return cred.client_id, cred.client_secret
        
        return None, None


async def run_worker(
    db_url: str,
    tenant_id: Optional[UUID] = None,
    poll_interval: int = POLL_INTERVAL_SECONDS,
):
    """Run the email draft generator worker."""
    worker = EmailDraftGeneratorWorker(
        db_url=db_url,
        tenant_id=tenant_id,
        poll_interval=poll_interval,
    )
    await worker.start()

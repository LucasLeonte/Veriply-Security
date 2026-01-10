"""Background worker for analyzing writing style from email history."""

import logging
from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import UserEmailHistory, UserWritingStyle, EmailIntegration
from app.email_automation.email_history import EmailHistoryCollector
from app.email_automation.style_analyzer import StyleAnalyzer

logger = logging.getLogger(__name__)


class StyleAnalysisWorker:
    """Background worker for analyzing user writing styles."""
    
    MINIMUM_EMAIL_SAMPLE = 10  # Minimum emails for reliable analysis
    MAXIMUM_EMAIL_SAMPLE = 100  # Maximum emails to analyze for performance
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.collector = EmailHistoryCollector(client_id, client_secret)
        self.analyzer = StyleAnalyzer()
    
    async def analyze_user_style(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        integration_id: UUID
    ) -> Optional[UserWritingStyle]:
        """Analyze user's writing style based on email history.
        
        Args:
            session: Database session
            tenant_id: Tenant ID
            user_id: User ID
            integration_id: Email integration ID
        
        Returns:
            UserWritingStyle record if successful, None otherwise
        """
        logger.info(f"Starting style analysis for user {user_id}, integration {integration_id}")
        
        # Get or create style profile record
        stmt = select(UserWritingStyle).where(
            and_(
                UserWritingStyle.user_id == user_id,
                UserWritingStyle.integration_id == integration_id,
                UserWritingStyle.tenant_id == tenant_id
            )
        )
        result = await session.execute(stmt)
        style_profile = result.scalar()
        
        if not style_profile:
            # Create new profile
            style_profile = UserWritingStyle(
                tenant_id=tenant_id,
                user_id=user_id,
                integration_id=integration_id,
                tone="semi_formal",
                formality_score=65
            )
            session.add(style_profile)
        
        # Fetch email history (if not already collected)
        emails_exist = await session.execute(
            select(UserEmailHistory).where(
                and_(
                    UserEmailHistory.user_id == user_id,
                    UserEmailHistory.integration_id == integration_id,
                    UserEmailHistory.tenant_id == tenant_id
                )
            ).limit(1)
        )
        
        if not emails_exist.scalar():
            logger.info(f"No email history found, collecting emails...")
            await self.collector.collect_sent_emails_for_user(
                session,
                tenant_id,
                user_id,
                integration_id,
                limit=50
            )
        
        # Get email history from database
        stmt = select(UserEmailHistory).where(
            and_(
                UserEmailHistory.user_id == user_id,
                UserEmailHistory.integration_id == integration_id,
                UserEmailHistory.tenant_id == tenant_id
            )
        ).order_by(UserEmailHistory.sent_at.desc()).limit(self.MAXIMUM_EMAIL_SAMPLE)
        
        result = await session.execute(stmt)
        email_records = result.scalars().all()
        
        if not email_records:
            logger.warning(f"No emails found for analysis user {user_id}")
            await session.commit()
            return style_profile
        
        # Extract email bodies
        emails = [
            record.body for record in email_records
            if record.body and isinstance(record.body, str)
        ]
        
        logger.info(f"Analyzing {len(emails)} emails for user {user_id}")
        
        # Check minimum sample size
        if len(emails) < self.MINIMUM_EMAIL_SAMPLE:
            logger.info(f"Insufficient email history ({len(emails)} < {self.MINIMUM_EMAIL_SAMPLE}). Using default style.")
            # Use default but record the sample count
            analysis_result = self.analyzer.analyze_emails([])
            style_profile.sample_count = len(emails)
            style_profile.tone = "semi_formal"
            style_profile.formality_score = 65
            style_profile.is_manual_override = False
            await session.commit()
            return style_profile
        
        # Analyze style
        analysis_result = self.analyzer.analyze_emails(emails)
        
        # Update profile
        style_profile.tone = analysis_result["tone"]
        style_profile.tone_score = analysis_result.get("tone_score", 0)
        style_profile.formality_score = analysis_result["formality_score"]
        style_profile.greeting_pattern = analysis_result["greeting_pattern"]
        style_profile.closing_pattern = analysis_result["closing_pattern"]
        style_profile.avg_email_length = analysis_result["avg_email_length"]
        style_profile.avg_sentence_length = int(analysis_result["avg_sentence_length"])
        style_profile.uses_emojis = analysis_result["uses_emojis"]
        style_profile.sample_count = len(emails)
        style_profile.last_analyzed_at = datetime.utcnow()
        style_profile.is_manual_override = False
        
        # Mark emails as analyzed
        for record in email_records:
            record.analyzed = True
        
        await session.commit()
        logger.info(f"Style analysis complete for user {user_id}. Detected tone: {style_profile.tone}")
        
        return style_profile
    
    async def refresh_user_style(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        integration_id: UUID,
        fetch_new_emails: bool = True
    ) -> Optional[UserWritingStyle]:
        """Refresh user's writing style (manual trigger).
        
        Args:
            session: Database session
            tenant_id: Tenant ID
            user_id: User ID
            integration_id: Email integration ID
            fetch_new_emails: Whether to fetch new emails before analyzing
        
        Returns:
            Updated UserWritingStyle record
        """
        logger.info(f"Refreshing style for user {user_id}, integration {integration_id}")
        
        if fetch_new_emails:
            # Fetch new sent emails
            await self.collector.collect_sent_emails_for_user(
                session,
                tenant_id,
                user_id,
                integration_id,
                limit=50
            )
        
        # Analyze with new/updated email history
        return await self.analyze_user_style(
            session, tenant_id, user_id, integration_id
        )
    
    async def refresh_all_user_styles(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID
    ) -> dict:
        """Refresh writing styles for all email accounts of a user.
        
        Args:
            session: Database session
            tenant_id: Tenant ID
            user_id: User ID
        
        Returns:
            Dict with results for each integration
        """
        logger.info(f"Refreshing all styles for user {user_id}")
        
        # Get all active integrations for user
        stmt = select(EmailIntegration).where(
            and_(
                EmailIntegration.user_id == user_id,
                EmailIntegration.tenant_id == tenant_id,
                EmailIntegration.is_active.is_(True)
            )
        )
        result = await session.execute(stmt)
        integrations = result.scalars().all()
        
        results = {}
        for integration in integrations:
            try:
                style = await self.analyze_user_style(
                    session, tenant_id, user_id, integration.id
                )
                results[str(integration.id)] = {
                    "success": True,
                    "tone": style.tone if style else None,
                    "sample_count": style.sample_count if style else 0
                }
            except Exception as e:
                logger.error(f"Error analyzing style for integration {integration.id}: {e}")
                results[str(integration.id)] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results

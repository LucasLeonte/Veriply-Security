"""Notification service for moderation alerts."""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ModerationAlert, UserAbuseSuspicion, Bot
from app.core.settings import settings

logger = logging.getLogger(__name__)


class ModerationNotificationService:
    """Send notifications for moderation events."""

    @staticmethod
    async def notify_moderation_alert(
        db: AsyncSession,
        alert: ModerationAlert,
    ) -> None:
        """
        Send notification when moderation alert is created.
        
        Supports:
        - Email notifications to moderation team
        - Webhook to external systems (Slack, PagerDuty, etc.)
        
        Args:
            db: Database session
            alert: The moderation alert that was created
        """
        try:
            # Get bot details for context
            bot = await db.get(Bot, alert.bot_id)
            if not bot:
                logger.error(f"Bot {alert.bot_id} not found for alert {alert.id}")
                return

            # Prepare notification data
            data = {
                "event": "moderation_alert_created",
                "alert_id": str(alert.id),
                "bot_id": str(alert.bot_id),
                "bot_name": bot.name,
                "answer_id": str(alert.answer_id),
                "feedback_count": alert.feedback_count,
                "user_ids": alert.user_ids.split(",") if alert.user_ids else [],
                "created_at": alert.created_at.isoformat(),
                "severity": "high" if alert.feedback_count >= 5 else "medium",
            }

            # Send email notification
            if settings.MODERATION_EMAIL_ENABLED:
                await ModerationNotificationService._send_email(
                    subject=f"[Veriply] Moderation Alert: Bot #{bot.name} Answer Flagged",
                    body=ModerationNotificationService._format_email_body(data),
                    recipients=settings.MODERATION_EMAIL_RECIPIENTS,
                )

            # Send webhook notification
            if settings.MODERATION_WEBHOOK_URL:
                await ModerationNotificationService._send_webhook(
                    url=settings.MODERATION_WEBHOOK_URL,
                    payload=data,
                )

            logger.info(f"Moderation alert notification sent: {alert.id}")

        except Exception as e:
            # Don't fail the main feedback flow if notification fails
            logger.error(f"Failed to send moderation alert notification: {e}", exc_info=True)

    @staticmethod
    async def notify_user_abuse(
        db: AsyncSession,
        suspicion: UserAbuseSuspicion,
    ) -> None:
        """
        Send notification when user abuse suspicion is flagged.
        
        Args:
            db: Database session
            suspicion: The abuse suspicion that was created
        """
        try:
            # Get bot details
            bot = await db.get(Bot, suspicion.bot_id)
            if not bot:
                logger.error(f"Bot {suspicion.bot_id} not found for suspicion {suspicion.id}")
                return

            # Prepare notification data
            data = {
                "event": "user_abuse_suspicion_created",
                "suspicion_id": str(suspicion.id),
                "user_id": str(suspicion.user_id),
                "bot_id": str(suspicion.bot_id),
                "bot_name": bot.name,
                "feedback_ids": suspicion.feedback_ids.split(",") if suspicion.feedback_ids else [],
                "ip_address": suspicion.ip_address,
                "created_at": suspicion.created_at.isoformat(),
                "severity": "critical",
            }

            # Send email notification (admin only)
            if settings.MODERATION_EMAIL_ENABLED:
                await ModerationNotificationService._send_email(
                    subject=f"[Veriply] User Abuse Detected: User #{suspicion.user_id}",
                    body=ModerationNotificationService._format_abuse_email_body(data),
                    recipients=settings.MODERATION_ADMIN_EMAIL_RECIPIENTS,
                )

            # Send webhook notification
            if settings.MODERATION_WEBHOOK_URL:
                await ModerationNotificationService._send_webhook(
                    url=settings.MODERATION_WEBHOOK_URL,
                    payload=data,
                )

            logger.info(f"User abuse notification sent: {suspicion.id}")

        except Exception as e:
            # Don't fail the main feedback flow if notification fails
            logger.error(f"Failed to send user abuse notification: {e}", exc_info=True)

    @staticmethod
    async def _send_email(subject: str, body: str, recipients: list[str]) -> None:
        """
        Send email notification.
        
        TODO: Implement with your email service (SendGrid, AWS SES, etc.)
        For now, this is a placeholder that logs the email.
        """
        logger.info(f"Email notification (placeholder): {subject}")
        logger.debug(f"Recipients: {recipients}")
        logger.debug(f"Body: {body}")
        
        # Example implementation with SendGrid:
        # import sendgrid
        # from sendgrid.helpers.mail import Mail, Email, To, Content
        # 
        # sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        # from_email = Email(settings.MODERATION_FROM_EMAIL)
        # to_emails = [To(email) for email in recipients]
        # content = Content("text/html", body)
        # mail = Mail(from_email, to_emails, subject, content)
        # response = sg.client.mail.send.post(request_body=mail.get())

    @staticmethod
    async def _send_webhook(url: str, payload: dict) -> None:
        """
        Send webhook notification to external system.
        
        TODO: Implement with httpx or aiohttp
        For now, this is a placeholder that logs the webhook.
        """
        logger.info(f"Webhook notification (placeholder): {url}")
        logger.debug(f"Payload: {payload}")
        
        # Example implementation with httpx:
        # import httpx
        # 
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         url,
        #         json=payload,
        #         headers={"Content-Type": "application/json"},
        #         timeout=10.0,
        #     )
        #     response.raise_for_status()

    @staticmethod
    def _format_email_body(data: dict) -> str:
        """Format moderation alert email body."""
        user_ids = ", ".join(data["user_ids"][:5])  # Show first 5
        if len(data["user_ids"]) > 5:
            user_ids += f" (+{len(data['user_ids']) - 5} more)"

        return f"""
        <html>
        <body>
            <h2>Moderation Alert: Harmful Content Detected</h2>
            <p>A bot answer has been flagged as harmful by multiple users and requires review.</p>
            
            <h3>Alert Details</h3>
            <ul>
                <li><strong>Bot:</strong> {data['bot_name']} ({data['bot_id']})</li>
                <li><strong>Answer ID:</strong> {data['answer_id']}</li>
                <li><strong>Feedback Count:</strong> {data['feedback_count']} users</li>
                <li><strong>Severity:</strong> {data['severity'].upper()}</li>
                <li><strong>Timestamp:</strong> {data['created_at']}</li>
            </ul>
            
            <h3>Reporting Users</h3>
            <p>{user_ids}</p>
            
            <h3>Action Required</h3>
            <ol>
                <li>Review the flagged answer in the moderation dashboard</li>
                <li>Determine if content should be removed or updated</li>
                <li>Mark alert as resolved when complete</li>
            </ol>
            
            <p>
                <a href="https://app.veriply.com/moderation/alerts/{data['alert_id']}" 
                   style="background-color: #dc2626; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View Alert in Dashboard
                </a>
            </p>
            
            <hr>
            <p style="color: #6b7280; font-size: 12px;">
                Veriply Moderation System - Automated Alert
            </p>
        </body>
        </html>
        """

    @staticmethod
    def _format_abuse_email_body(data: dict) -> str:
        """Format user abuse suspicion email body."""
        feedback_count = len(data["feedback_ids"])

        return f"""
        <html>
        <body>
            <h2 style="color: #dc2626;">User Abuse Detected</h2>
            <p>A user has been flagged for submitting excessive harmful feedback in a short time period.</p>
            
            <h3>Suspicion Details</h3>
            <ul>
                <li><strong>User ID:</strong> {data['user_id']}</li>
                <li><strong>Bot:</strong> {data['bot_name']} ({data['bot_id']})</li>
                <li><strong>Harmful Feedback Count:</strong> {feedback_count} submissions in 1 hour</li>
                <li><strong>IP Address:</strong> {data['ip_address']}</li>
                <li><strong>Timestamp:</strong> {data['created_at']}</li>
            </ul>
            
            <h3>Action Required</h3>
            <ol>
                <li>Review user's feedback history for patterns</li>
                <li>Determine if abuse is intentional or user frustration</li>
                <li>Consider rate limiting or account suspension if malicious</li>
                <li>Document findings and mark suspicion as resolved</li>
            </ol>
            
            <p>
                <a href="https://app.veriply.com/moderation/abuse-suspicions/{data['suspicion_id']}" 
                   style="background-color: #dc2626; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View Suspicion in Dashboard
                </a>
            </p>
            
            <hr>
            <p style="color: #6b7280; font-size: 12px;">
                Veriply Moderation System - Automated Alert (Admin Only)
            </p>
        </body>
        </html>
        """

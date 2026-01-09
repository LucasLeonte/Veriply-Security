"""Service for collecting and storing email history for writing style analysis."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import UserEmailHistory, EmailIntegration
from app.utils.encryption import decrypt_token
from app.integrations import gmail, outlook

logger = logging.getLogger(__name__)


class EmailHistoryCollector:
    """Collects email history from Gmail and Outlook for style analysis."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def collect_sent_emails_for_user(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        integration_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Collect sent emails from a user's email account.
        
        Args:
            session: Database session
            tenant_id: Tenant ID
            user_id: User ID
            integration_id: Email integration ID
            limit: Maximum number of emails to fetch (default 50)
        
        Returns:
            List of fetched email data
        """
        # Get integration details
        stmt = select(EmailIntegration).where(
            EmailIntegration.id == integration_id,
            EmailIntegration.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        integration = result.scalar()
        
        if not integration:
            logger.error(f"Integration {integration_id} not found")
            return []
        
        try:
            if integration.provider.lower() == "gmail":
                return await self._collect_gmail_sent_emails(
                    session, tenant_id, user_id, integration, limit
                )
            elif integration.provider.lower() == "outlook":
                return await self._collect_outlook_sent_emails(
                    session, tenant_id, user_id, integration, limit
                )
        except Exception as e:
            logger.error(f"Error collecting emails for {integration_id}: {str(e)}")
            return []
    
    async def _collect_gmail_sent_emails(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        integration: EmailIntegration,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Collect sent emails from Gmail."""
        # Decrypt refresh token
        try:
            refresh_token = decrypt_token(integration.refresh_token)
        except Exception as e:
            logger.error(f"Failed to decrypt Gmail refresh token: {e}")
            return []
        
        try:
            # Get access token
            token_data = await gmail.refresh_access_token(
                self.client_id, self.client_secret, refresh_token
            )
            access_token = token_data["access_token"]
        except Exception as e:
            logger.error(f"Failed to refresh Gmail access token: {e}")
            return []
        
        collected_emails = []
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Fetch sent emails (label:SENT)
                params = {
                    "q": "label:SENT",
                    "maxResults": limit,
                    "pageToken": None
                }
                
                response = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                messages = data.get("messages", [])
                logger.info(f"Found {len(messages)} sent emails in Gmail")
                
                for msg_ref in messages:
                    message_id = msg_ref["id"]
                    
                    # Check if already stored
                    stmt = select(UserEmailHistory).where(
                        and_(
                            UserEmailHistory.integration_id == integration.id,
                            UserEmailHistory.email_id == message_id
                        )
                    )
                    existing = await session.execute(stmt)
                    if existing.scalar():
                        logger.debug(f"Email {message_id} already stored, skipping")
                        continue
                    
                    # Fetch full message details
                    msg_response = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                        headers=headers,
                        params={"format": "full"}
                    )
                    msg_response.raise_for_status()
                    msg_data = msg_response.json()
                    
                    # Parse message
                    parsed_msg = self._parse_gmail_message(msg_data)
                    
                    # Store in database
                    email_history = UserEmailHistory(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        integration_id=integration.id,
                        email_id=message_id,
                        subject=parsed_msg["subject"],
                        body=parsed_msg["body"],
                        sent_at=parsed_msg["sent_at"],
                        analyzed=False
                    )
                    session.add(email_history)
                    collected_emails.append(parsed_msg)
                
                await session.commit()
                logger.info(f"Stored {len(collected_emails)} new emails from Gmail")
        
        except Exception as e:
            logger.error(f"Error collecting Gmail sent emails: {e}")
        
        return collected_emails
    
    async def _collect_outlook_sent_emails(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        integration: EmailIntegration,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Collect sent emails from Outlook."""
        # Decrypt refresh token
        try:
            refresh_token = decrypt_token(integration.refresh_token)
        except Exception as e:
            logger.error(f"Failed to decrypt Outlook refresh token: {e}")
            return []
        
        try:
            # Get access token
            token_data = await outlook.refresh_access_token(
                self.client_id, self.client_secret, refresh_token
            )
            access_token = token_data["access_token"]
        except Exception as e:
            logger.error(f"Failed to refresh Outlook access token: {e}")
            return []
        
        collected_emails = []
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                # Fetch sent items
                params = {
                    "$top": limit,
                    "$select": "id,subject,bodyPreview,sentDateTime,from,toRecipients",
                    "$orderby": "sentDateTime desc"
                }
                
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me/mailFolders/sentitems/messages",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                messages = data.get("value", [])
                logger.info(f"Found {len(messages)} sent emails in Outlook")
                
                for msg_data in messages:
                    message_id = msg_data["id"]
                    
                    # Check if already stored
                    stmt = select(UserEmailHistory).where(
                        and_(
                            UserEmailHistory.integration_id == integration.id,
                            UserEmailHistory.email_id == message_id
                        )
                    )
                    existing = await session.execute(stmt)
                    if existing.scalar():
                        logger.debug(f"Email {message_id} already stored, skipping")
                        continue
                    
                    # Parse message
                    parsed_msg = self._parse_outlook_message(msg_data)
                    
                    # Store in database
                    email_history = UserEmailHistory(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        integration_id=integration.id,
                        email_id=message_id,
                        subject=parsed_msg["subject"],
                        body=parsed_msg["body"],
                        sent_at=parsed_msg["sent_at"],
                        analyzed=False
                    )
                    session.add(email_history)
                    collected_emails.append(parsed_msg)
                
                await session.commit()
                logger.info(f"Stored {len(collected_emails)} new emails from Outlook")
        
        except Exception as e:
            logger.error(f"Error collecting Outlook sent emails: {e}")
        
        return collected_emails
    
    @staticmethod
    def _parse_gmail_message(msg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message data."""
        payload = msg_data.get("payload", {})
        headers_list = payload.get("headers", [])
        
        subject = next(
            (h["value"] for h in headers_list if h["name"].lower() == "subject"),
            "(No Subject)"
        )
        date_str = next(
            (h["value"] for h in headers_list if h["name"].lower() == "date"),
            None
        )
        
        # Parse date (RFC 2822 format)
        sent_at = None
        if date_str:
            try:
                from email.utils import parsedate_to_datetime
                sent_at = parsedate_to_datetime(date_str)
            except Exception:
                logger.warning(f"Failed to parse date: {date_str}")
        
        # Extract body
        body = _extract_gmail_body(payload)
        
        return {
            "subject": subject,
            "body": body,
            "sent_at": sent_at
        }
    
    @staticmethod
    def _parse_outlook_message(msg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Outlook message data."""
        subject = msg_data.get("subject", "(No Subject)")
        
        # Get preview (Outlook includes bodyPreview)
        body_preview = msg_data.get("bodyPreview", "")
        
        # Parse sent date (ISO format)
        sent_at = None
        sent_datetime_str = msg_data.get("sentDateTime")
        if sent_datetime_str:
            try:
                sent_at = datetime.fromisoformat(sent_datetime_str.replace("Z", "+00:00"))
            except Exception:
                logger.warning(f"Failed to parse Outlook date: {sent_datetime_str}")
        
        return {
            "subject": subject,
            "body": body_preview,
            "sent_at": sent_at
        }


def _extract_gmail_body(payload: Dict[str, Any]) -> str:
    """Extract body from Gmail message payload."""
    import base64
    
    if not payload:
        return ""
    
    # Check if body is directly in payload
    if "body" in payload and payload["body"].get("data"):
        data = payload["body"]["data"]
        # Fix padding
        padding = len(data) % 4
        if padding:
            data += "=" * (4 - padding)
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8")
        except Exception:
            return ""
    
    # Check parts
    parts = payload.get("parts", [])
    
    # Prioritize text/plain for style analysis
    text_part = next((p for p in parts if p.get("mimeType") == "text/plain"), None)
    if text_part:
        return _extract_gmail_body(text_part)
    
    # Fallback to text/html
    html_part = next((p for p in parts if p.get("mimeType") == "text/html"), None)
    if html_part:
        body = _extract_gmail_body(html_part)
        # Convert HTML to text
        from app.email_automation.email_extractor import html_to_text
        return html_to_text(body)
    
    # Recursive search if nested multipart
    for part in parts:
        if part.get("mimeType", "").startswith("multipart/"):
            result = _extract_gmail_body(part)
            if result:
                return result
    
    return ""

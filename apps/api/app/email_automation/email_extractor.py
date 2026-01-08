"""Email content extraction from Gmail and Outlook providers."""

import logging
from typing import Optional, Dict, Any
import base64
import re
from email import message_from_bytes
from html.parser import HTMLParser

from app.utils.encryption import decrypt_token
from app.integrations import gmail, outlook

logger = logging.getLogger(__name__)


class HTMLToTextParser(HTMLParser):
    """Simple HTML to text converter."""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
    
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip = True
    
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = False
        elif tag == 'br':
            self.text.append('\n')
        elif tag == 'p':
            self.text.append('\n')
    
    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)
    
    def get_text(self) -> str:
        text = ''.join(self.text)
        # Clean up multiple newlines and whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    parser = HTMLToTextParser()
    try:
        parser.feed(html)
        return parser.get_text()
    except Exception as e:
        logger.warning(f"Failed to parse HTML: {e}. Returning original text.")
        return html


class EmailExtractor:
    """Extracts structured email data from Gmail and Outlook."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def extract_gmail_email(
        self,
        refresh_token: str,
        message_id: str,
        thread_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Extract email data from Gmail.
        
        Args:
            refresh_token: Gmail refresh token
            message_id: Gmail message ID
            thread_id: Gmail thread ID
        
        Returns:
            Dict with keys: subject, body, sender_email, thread_id, received_time, labels
        """
        try:
            # Get fresh access token
            token_data = await gmail.refresh_access_token(
                self.client_id,
                self.client_secret,
                refresh_token
            )
            access_token = token_data["access_token"]
            
            # Fetch full message
            message = await gmail.get_message(
                access_token=access_token,
                message_id=message_id,
                format="full"
            )
            
            if not message:
                logger.error(f"Failed to fetch Gmail message {message_id}")
                return None
            
            # Parse message
            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
            
            subject = headers.get('Subject', '')
            sender_email = self._extract_email_address(headers.get('From', ''))
            received_time = headers.get('Date', '')
            
            # Extract body
            body = self._extract_gmail_body(message.get('payload', {}))
            
            # Get labels
            labels = message.get('labelIds', [])
            
            return {
                'subject': subject,
                'body': body,
                'sender_email': sender_email,
                'thread_id': thread_id,
                'received_time': received_time,
                'labels': labels,
                'provider': 'gmail',
            }
        except Exception as e:
            logger.exception(f"Failed to extract Gmail email {message_id}: {e}")
            return None
    
    async def extract_outlook_email(
        self,
        refresh_token: str,
        message_id: str,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Extract email data from Outlook.
        
        Args:
            refresh_token: Outlook refresh token
            message_id: Outlook message ID
            conversation_id: Outlook conversation ID
        
        Returns:
            Dict with keys: subject, body, sender_email, thread_id, received_time
        """
        try:
            # Get fresh access token
            token_data = await outlook.refresh_access_token(
                self.client_id,
                self.client_secret,
                refresh_token
            )
            access_token = token_data["access_token"]
            
            # Fetch message
            message = await outlook.get_message(
                access_token=access_token,
                message_id=message_id
            )
            
            if not message:
                logger.error(f"Failed to fetch Outlook message {message_id}")
                return None
            
            subject = message.get('subject', '')
            body = message.get('bodyPreview', '') or message.get('body', {}).get('content', '')
            sender_email = self._extract_email_address(
                message.get('from', {}).get('emailAddress', {}).get('address', '')
            )
            received_time = message.get('receivedDateTime', '')
            
            return {
                'subject': subject,
                'body': body,
                'sender_email': sender_email,
                'thread_id': conversation_id,
                'received_time': received_time,
                'provider': 'outlook',
            }
        except Exception as e:
            logger.exception(f"Failed to extract Outlook email {message_id}: {e}")
            return None
    
    def _extract_gmail_body(self, payload: Dict[str, Any]) -> str:
        """Extract body from Gmail message payload."""
        body = ""
        
        # Check if multipart
        if 'parts' in payload:
            # Find text or html part
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif mime_type == 'text/html' and not body:
                    data = part.get('body', {}).get('data', '')
                    if data:
                        html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        body = html_to_text(html)
        else:
            # Single part message
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body.strip()
    
    def _extract_email_address(self, from_header: str) -> str:
        """Extract email address from From header.
        
        Handles formats like:
        - "user@example.com"
        - "User Name <user@example.com>"
        """
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', from_header)
        if match:
            return match.group(0)
        return from_header

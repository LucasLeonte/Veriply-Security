import os
import httpx
import base64
from email.mime.text import MIMEText
from urllib.parse import urlencode

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify"
]


def get_authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "state": state,
        "prompt": "consent",  # Force consent to ensure we get a refresh token
        "include_granted_scopes": "true" # Incremental auth
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

async def exchange_code_for_token(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()


async def list_threads(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    query: str = "label:INBOX",
    max_results: int = 20
) -> dict:
    """List email threads matching the query."""
    # First, get a fresh access token
    token_data = await refresh_access_token(client_id, client_secret, refresh_token)
    access_token = token_data["access_token"]

    async with httpx.AsyncClient() as client:
        # List threads
        params = {
            "q": query,
            "maxResults": max_results,
            "includeSpamTrash": "false"
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/threads",
            params=params,
            headers=headers
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Include the response body in the error for debugging
            print(f"Gmail API Error: {e.response.text}")
            raise Exception(f"Gmail API Error: {e.response.text}") from e
            
        data = response.json()
        threads = data.get("threads", [])
        
        results = []
        for thread in threads:
            # Fetch details for each thread (lite version) to get snippet and dates
            thread_detail = await get_thread_details(client, access_token, thread["id"])
            if thread_detail:
                results.append(thread_detail)
                
        return results


async def get_thread_details(client: httpx.AsyncClient, access_token: str, thread_id: str) -> dict:
    """Fetch basic details of a thread (snippet, date, subject)."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}",
            headers=headers
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"Gmail Thread Detail Error: {e.response.text}")
            return None
            
        data = response.json()
        
        # Extract useful info from the last message in thread
        messages = data.get("messages", [])
        if not messages:
            return None
            
        last_msg = messages[-1]
        payload = last_msg.get("payload", {})
        headers_list = payload.get("headers", [])
        
        subject = next((h["value"] for h in headers_list if h["name"].lower() == "subject"), None)
        if not subject:
             print(f"DEBUG: Missing Subject for thread {thread_id}. Available headers: {[h['name'] for h in headers_list]}")
             subject = "(No Subject)"
             
        from_header = next((h["value"] for h in headers_list if h["name"].lower() == "from"), "Unknown")
        to_header = next((h["value"] for h in headers_list if h["name"].lower() == "to"), "")
        date = next((h["value"] for h in headers_list if h["name"].lower() == "date"), "")
        
        return {
            "id": thread_id,
            "thread_id": thread_id,
            "last_message_id": last_msg.get("id", thread_id),
            "snippet": last_msg.get("snippet", ""),
            "subject": subject,
            "from": from_header,
            "to": to_header,
            "date": date,
            "messages": messages # Return all messages for full context if needed later
        }
    except Exception as e:
        print(f"Error fetching thread {thread_id}: {e}")
        return None


async def get_message_details(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    message_id: str
) -> dict:
    """Fetch full content of a specific message and parse it."""
    token_data = await refresh_access_token(client_id, client_secret, refresh_token)
    access_token = token_data["access_token"]
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
            headers=headers
        )
        response.raise_for_status()
        return _parse_message_data(data)

async def get_thread_with_messages(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    thread_id: str
) -> dict:
    """Fetch full thread with all messages parsed."""
    token_data = await refresh_access_token(client_id, client_secret, refresh_token)
    access_token = token_data["access_token"]
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}",
            params={"format": "full"},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        messages = [_parse_message_data(msg) for msg in data.get("messages", [])]
        
        # Determine subject from the first message (or any message)
        subject = "(No Subject)"
        if messages:
            subject = messages[0]["subject"]
            
        return {
            "id": data.get("id"),
            "historyId": data.get("historyId"),
            "messages": messages,
            "subject": subject
        }

def _parse_message_data(data: dict) -> dict:
    """Parse a single Gmail message resource."""
    payload = data.get("payload", {})
    headers_list = payload.get("headers", [])
    
    subject = next((h["value"] for h in headers_list if h["name"].lower() == "subject"), "(No Subject)")
    from_header = next((h["value"] for h in headers_list if h["name"].lower() == "from"), "Unknown")
    to_header = next((h["value"] for h in headers_list if h["name"].lower() == "to"), "")
    date = next((h["value"] for h in headers_list if h["name"].lower() == "date"), "")
    
    # Parse body
    body = _extract_body(payload)
    
    return {
        "id": data.get("id"),
        "threadId": data.get("threadId"),
        "snippet": data.get("snippet", ""),
        "subject": subject,
        "from": from_header,
        "to": to_header,
        "date": date,
        "body": body
    }

def _extract_body(payload: dict) -> str:
    """Recursively extract HTML or plain text body from Gmail payload."""
    if not payload:
        return ""
        
    # Check if body is directly in payload (e.g. non-multipart)
    if "body" in payload and payload["body"].get("data"):
        data = payload["body"]["data"]
        # Fix padding
        padding = len(data) % 4
        if padding:
            data += "=" * (4 - padding)
        return base64.urlsafe_b64decode(data).decode("utf-8")
    
    # Check parts
    parts = payload.get("parts", [])
    
    # Prioritize text/html
    html_part = next((p for p in parts if p.get("mimeType") == "text/html"), None)
    if html_part:
        return _extract_body(html_part)
        
    # Fallback to text/plain
    text_part = next((p for p in parts if p.get("mimeType") == "text/plain"), None)
    if text_part:
        return _extract_body(text_part)

    # Recursive search if nested multipart
    for part in parts:
        if part.get("mimeType", "").startswith("multipart/"):
            return _extract_body(part)
            
    return ""


async def get_message(
    access_token: str,
    message_id: str,
    format: str = "full"
) -> dict:
    """Fetch message using an existing access token.
    
    Args:
        access_token: Gmail API access token
        message_id: Message ID to fetch
        format: Format for the message (minimal, full, raw)
    
    Returns:
        Message dict from Gmail API
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"format": format}
        response = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Refresh the access token using the refresh token."""
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()


async def send_reply(
    access_token: str,
    thread_id: str,
    message_id: str,
    to: str,
    subject: str,
    body: str
) -> dict:
    """Send a reply to an existing email thread.
    
    Args:
        access_token: Gmail API access token
        thread_id: Thread ID to reply to
        message_id: Message ID being replied to
        to: Recipient email address
        subject: Subject line (should start with "Re: ")
        body: Reply body text
    
    Returns:
        Sent message dict from Gmail API
    """
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject if subject.startswith('Re: ') else f'Re: {subject}'
    
    # Add headers to make it a reply
    message['In-Reply-To'] = message_id
    message['References'] = message_id
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "raw": raw_message,
            "threadId": thread_id
        }
        response = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

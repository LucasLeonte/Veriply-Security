import os
import httpx
from urllib.parse import urlencode

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

SCOPES = [
    "Mail.Read",
    "Mail.Send",
    "offline_access",
    "User.Read" # Usually good to have basic profile access
]


def get_authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": " ".join(SCOPES),
        "state": state
    }
    return f"{MICROSOFT_AUTH_URL}?{urlencode(params)}"

async def exchange_code_for_token(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    async with httpx.AsyncClient() as client:
        data = {
            "client_id": client_id,
            "scope": " ".join(SCOPES),
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "client_secret": client_secret,
        }
        response = await client.post(MICROSOFT_TOKEN_URL, data=data)
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
            "scope": " ".join(SCOPES),
        }
        response = await client.post(MICROSOFT_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()

async def get_message(
    access_token: str,
    message_id: str
) -> dict:
    """Fetch message using Microsoft Graph API.
    
    Args:
        access_token: Outlook API access token
        message_id: Message ID to fetch
    
    Returns:
        Message dict from Microsoft Graph API
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/messages/{message_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

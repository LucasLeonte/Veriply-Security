import os
import httpx
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
        "prompt": "consent"  # Force consent to ensure we get a refresh token
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

"""Integration routes (Gmail/Outlook connect flows)."""

import os
import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.database import get_db
from app.models.email_integration import EmailIntegration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/gmail/authorize")
async def gmail_authorize(request: Request):
    """Return a Google OAuth2 authorization URL to redirect the user to."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    redirect_uri = os.environ.get("GOOGLE_OAUTH_REDIRECT", "http://localhost:3000/api/integrations/gmail/callback")
    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    state = str(uuid4())
    # In production store state in user session to validate in callback
    scope = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/gmail.modify"
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code&client_id={client_id}"
        f"&scope={httpx.utils.quote(scope)}&access_type=offline&prompt=consent"
        f"&redirect_uri={httpx.utils.quote(redirect_uri)}&state={state}"
    )

    return RedirectResponse(auth_url)


@router.get("/gmail/callback")
async def gmail_callback(code: Optional[str] = None, state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth2 callback: exchange code for refresh token and store encrypted token."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing code from provider")

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.environ.get("GOOGLE_OAUTH_REDIRECT", "http://localhost:3000/api/integrations/gmail/callback")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured")

    token_endpoint = "https://oauth2.googleapis.com/token"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_endpoint,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )

    if resp.status_code != 200:
        logger.error("Failed to exchange token: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Failed to exchange token with Google")

    token_data = resp.json()
    refresh_token = token_data.get("refresh_token")
    access_token = token_data.get("access_token")

    if not refresh_token:
        # Google may not return a refresh token if consent previously given; handle gracefully
        logger.info("No refresh token returned by Google; storing access token with short TTL")

    # TODO: Encrypt token before storing (use encryption util)
    # For now store raw token (developer to replace with encryption util)
    integration = EmailIntegration(
        id=uuid4(),
        tenant_id="00000000-0000-0000-0000-000000000000",
        user_id="00000000-0000-0000-0000-000000000000",
        provider="gmail",
        encrypted_refresh_token=refresh_token or access_token,
        scope=token_data.get("scope"),
        status="connected",
    )

    try:
        db.add(integration)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to save email integration: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save integration")

    # Redirect to frontend integrations page after successful connect
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend_url}/dashboard/integrations?connected=gmail")

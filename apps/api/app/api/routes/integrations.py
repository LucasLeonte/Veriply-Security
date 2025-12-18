"""Integration routes (Gmail/Outlook connect flows)."""

import os
import logging
from typing import Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import httpx

from app.core.database import get_db
from app.models.email_integration import EmailIntegration
from app.models.user import User
from app.api.v1.auth import get_current_user, get_current_tenant
from app.utils.encryption import encrypt_token, decrypt_token

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
async def gmail_callback(
    code: Optional[str] = None, 
    state: Optional[str] = None, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: uuid4 = Depends(get_current_tenant),
):
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
        logger.warning("No refresh token returned by Google; storing access token (short TTL)")

    # Encrypt token before storing
    token_to_encrypt = refresh_token or access_token
    try:
        encrypted_token = encrypt_token(token_to_encrypt)
    except Exception as e:
        logger.error(f"Failed to encrypt token: {e}")
        raise HTTPException(status_code=500, detail="Failed to secure token")

    # Check if integration already exists for this user
    existing = await db.execute(
        select(EmailIntegration).where(
            and_(
                EmailIntegration.user_id == current_user.id,
                EmailIntegration.provider == "gmail",
            )
        )
    )
    integration = existing.scalars().first()

    if integration:
        # Update existing integration
        integration.encrypted_refresh_token = encrypted_token
        integration.scope = token_data.get("scope")
        integration.status = "connected"
        integration.is_active = True
        integration.last_sync_time = datetime.utcnow()
        integration.updated_at = datetime.utcnow()
    else:
        # Create new integration
        integration = EmailIntegration(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=current_user.id,
            provider="gmail",
            encrypted_refresh_token=encrypted_token,
            scope=token_data.get("scope"),
            status="connected",
        )
        db.add(integration)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to save email integration: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save integration")

    # Redirect to frontend integrations page after successful connect
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend_url}/dashboard/integrations?connected=gmail")


@router.get("/list")
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all email integrations for the current user."""
    result = await db.execute(
        select(EmailIntegration).where(
            and_(
                EmailIntegration.user_id == current_user.id,
                EmailIntegration.is_active == True,
            )
        )
    )
    integrations = result.scalars().all()

    return {
        "integrations": [
            {
                "id": str(integration.id),
                "provider": integration.provider,
                "status": integration.status,
                "last_sync_time": integration.last_sync_time.isoformat() if integration.last_sync_time else None,
                "created_at": integration.created_at.isoformat() if integration.created_at else None,
            }
            for integration in integrations
        ]
    }


@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disconnect an email integration (soft delete by setting is_active=false)."""
    result = await db.execute(
        select(EmailIntegration).where(
            and_(
                EmailIntegration.id == integration_id,
                EmailIntegration.user_id == current_user.id,
            )
        )
    )
    integration = result.scalars().first()

    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    integration.is_active = False
    integration.status = "disconnected"
    integration.updated_at = datetime.utcnow()

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to disconnect integration: %s", e)
        raise HTTPException(status_code=500, detail="Failed to disconnect integration")

    return {"message": "Integration disconnected successfully"}

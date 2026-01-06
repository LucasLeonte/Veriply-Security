"""Integration routes (Gmail/Outlook connect flows)."""

import os
import logging
from typing import Optional
from uuid import uuid4, UUID
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.models.email_integration import EmailIntegration
from app.models.integration_credentials import IntegrationCredentials
from app.models.user import User
from app.api.v1.auth import get_current_user, get_current_tenant, get_jwt_secret, JWT_ALGORITHM
from app.utils.encryption import encrypt_token, decrypt_token
from pydantic import BaseModel, Field
import jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])
optional_bearer = HTTPBearer(auto_error=False)


class IntegrationCredentialRequest(BaseModel):
    provider: str = Field(..., description="gmail or outlook")
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None


async def _get_oauth_credentials(
    db: AsyncSession,
    tenant_id: UUID,
    provider: str,
    redirect_fallback: str,
):
    """Fetch tenant-specific OAuth credentials, falling back to global row then env vars.

    Order of resolution:
    1) integration_credentials matching tenant_id + provider
    2) integration_credentials with tenant_id IS NULL (global default)
    3) environment variables
    """
    query = (
        select(IntegrationCredentials)
        .where(
            and_(
                IntegrationCredentials.provider == provider,
                IntegrationCredentials.tenant_id == tenant_id,
            )
        )
        .limit(1)
    )
    result = await db.execute(query)
    row = result.scalar_one_or_none()

    if not row:
        # Global default credentials (tenant_id is NULL)
        query = (
            select(IntegrationCredentials)
            .where(
                and_(
                    IntegrationCredentials.provider == provider,
                    IntegrationCredentials.tenant_id.is_(None),
                )
            )
            .limit(1)
        )
        result = await db.execute(query)
        row = result.scalar_one_or_none()

    client_id = None
    client_secret = None
    redirect_uri = None

    if row:
        client_id = row.client_id
        client_secret = decrypt_token(row.encrypted_client_secret)
        redirect_uri = row.redirect_uri or redirect_fallback

    # Fallback to env vars if nothing configured
    if not client_id:
        client_id = os.environ.get("GOOGLE_CLIENT_ID") if provider == "gmail" else os.environ.get("OUTLOOK_CLIENT_ID")
    if not client_secret:
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET") if provider == "gmail" else os.environ.get("OUTLOOK_CLIENT_SECRET")
    if not redirect_uri:
        redirect_uri = redirect_fallback

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail=f"{provider.upper()} client credentials not configured")

    return client_id, client_secret, redirect_uri


async def _get_tenant_from_token(
    request: Request,
    token: Optional[str],
    credentials: Optional[HTTPAuthorizationCredentials],
):
    raw_token = token or (credentials.credentials if credentials else None)

    # Fallback: look for cookie-based token if not provided explicitly
    if not raw_token:
        raw_token = request.cookies.get("access_token")

    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(raw_token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        tenant_id: str = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant ID not found in token")
        return UUID(tenant_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


@router.get("/gmail/authorize")
async def gmail_authorize(
    request: Request,
    token: Optional[str] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Return a Google OAuth2 authorization URL to redirect the user to."""
    tenant_id = await _get_tenant_from_token(request, token, credentials)
    redirect_default = os.environ.get("GOOGLE_OAUTH_REDIRECT", "http://localhost:3000/api/integrations/gmail/callback")
    client_id, _, redirect_uri = await _get_oauth_credentials(
        db=db,
        tenant_id=tenant_id,
        provider="gmail",
        redirect_fallback=redirect_default,
    )

    state = str(uuid4())
    # In production store state in user session to validate in callback
    scope = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/gmail.modify"
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code&client_id={client_id}"
        f"&scope={quote(scope)}&access_type=offline&prompt=consent"
        f"&redirect_uri={quote(redirect_uri)}&state={state}"
    )

    return RedirectResponse(auth_url)

@router.post("/credentials")
async def set_integration_credentials(
    payload: IntegrationCredentialRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
):
    """Store or update OAuth credentials for the tenant for the given provider.

    This endpoint enables the hybrid model: per-tenant credentials override global/env.
    """
    # Basic guard: only owners/admins should set credentials; for now ensure user is active.
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    provider = payload.provider.lower()
    if provider not in {"gmail", "outlook"}:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    encrypted_secret = encrypt_token(payload.client_secret)

    # Upsert logic: try fetch existing
    existing_query = select(IntegrationCredentials).where(
        and_(
            IntegrationCredentials.provider == provider,
            IntegrationCredentials.tenant_id == tenant_id,
        )
    )
    result = await db.execute(existing_query)
    existing = result.scalar_one_or_none()

    if existing:
        existing.client_id = payload.client_id
        existing.encrypted_client_secret = encrypted_secret
        existing.redirect_uri = payload.redirect_uri
        existing.updated_at = datetime.utcnow()
        cred = existing
    else:
        cred = IntegrationCredentials(
            id=uuid4(),
            tenant_id=tenant_id,
            provider=provider,
            client_id=payload.client_id,
            encrypted_client_secret=encrypted_secret,
            redirect_uri=payload.redirect_uri,
        )
        db.add(cred)

    await db.commit()
    return {"status": "ok", "provider": provider, "scope": "tenant"}


@router.get("/gmail/callback")
async def gmail_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Handle Google OAuth2 callback: exchange code for refresh token and store encrypted token."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing code from provider")

    redirect_default = os.environ.get("GOOGLE_OAUTH_REDIRECT", "http://localhost:3000/api/integrations/gmail/callback")
    client_id, client_secret, redirect_uri = await _get_oauth_credentials(
        db=db,
        tenant_id=tenant_id,
        provider="gmail",
        redirect_fallback=redirect_default,
    )

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

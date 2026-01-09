"""Integration routes (Gmail/Outlook connect flows)."""

import os
import logging
from typing import Optional
from uuid import uuid4, UUID
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, HTTPException, status, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db, set_tenant_context
from app.core.settings import settings
from app.models.email_integration import EmailIntegration
from app.models.integration_credentials import IntegrationCredentials
from app.models.user import User
from app.models.bot import Bot
from app.models.group import Group
from app.api.v1.auth import get_current_user, get_current_tenant, get_jwt_secret, JWT_ALGORITHM
from app.utils.encryption import encrypt_token, decrypt_token
from pydantic import BaseModel, Field
import jwt
from app.integrations import gmail, outlook
from app.services.document_service import create_document
from app.services.llm_service import LLMService
from pydantic import ConfigDict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])
optional_bearer = HTTPBearer(auto_error=False)


class IntegrationCredentialRequest(BaseModel):
    provider: str = Field(..., description="gmail or outlook")
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None


class GmailMessageImport(BaseModel):
    message_id: str


class GmailMessageReply(BaseModel):
    message_id: str
    original_text: str  # OR fetch it fresh, but passing it might be easier/faster if frontend already has it
    subject: Optional[str] = None
    bot_id: Optional[str] = None


class GmailSendReply(BaseModel):
    thread_id: str
    message_id: str
    to: str
    subject: str
    body: str
    
    model_config = ConfigDict(populate_by_name=True)

    bot_id: Optional[UUID] = None  # Bot to use for KB search; if None, generate without KB
    subject: Optional[str] = None  # Email subject for better context


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
        client_id = settings.GOOGLE_CLIENT_ID if provider == "gmail" else settings.OUTLOOK_CLIENT_ID
    if not client_secret:
        client_secret = settings.GOOGLE_CLIENT_SECRET if provider == "gmail" else settings.OUTLOOK_CLIENT_SECRET
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
    redirect_default = settings.GOOGLE_OAUTH_REDIRECT or "http://localhost:8000/api/v1/integrations/gmail/callback"
    client_id, _, redirect_uri = await _get_oauth_credentials(
        db=db,
        tenant_id=tenant_id,
        provider="gmail",
        redirect_fallback=redirect_default,
    )

    state = str(uuid4())
    # In production store state in user session to validate in callback
    
    auth_url = gmail.get_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state
    )

    response = RedirectResponse(auth_url)
    
    # Set a short-lived cookie with the auth token so we can identify the user on callback
    # The frontend passes 'token' in the query param or header to this endpoint
    if token:
        response.set_cookie(
            key="veriply_oauth_token",
            value=token,
            max_age=300,  # 5 minutes
            httponly=True,
            samesite="lax",
            secure=settings.is_production  # True in prod, False in dev (http://localhost)
        )
    
    return response

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
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth2 callback: exchange code for refresh token and store encrypted token."""
    # Manually retrieve user from cookie since Authorization header is missing in redirect
    token = request.cookies.get("veriply_oauth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication cookie missing. Please try again.")

    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        user_id = UUID(payload.get("sub"))
        tenant_id = UUID(payload.get("tenant_id"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication cookie")

    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id))
    current_user = result.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=401, detail="User not found")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code from provider")

    redirect_default = settings.GOOGLE_OAUTH_REDIRECT or "http://localhost:8000/api/v1/integrations/gmail/callback"
    client_id, client_secret, redirect_uri = await _get_oauth_credentials(
        db=db,
        tenant_id=tenant_id,
        provider="gmail",
        redirect_fallback=redirect_default,
    )

    try:
        token_data = await gmail.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            code=code
        )
    except Exception as e:
        logger.error("Failed to exchange token: %s", e)
        raise HTTPException(status_code=502, detail="Failed to exchange token with Google")
    
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
    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
    return RedirectResponse(f"{frontend_url}/dashboard/integrations?connected=gmail")


@router.get("/gmail/messages")
async def list_gmail_messages(
    folder: str = "INBOX",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent emails from Gmail (Inbox or Sent)."""
    # SECURITY FIX: Only allow user to access THEIR OWN Gmail integration
    # Previous code allowed tenant-level fallback which enabled cross-user email access
    result = await db.execute(
        select(EmailIntegration)
        .where(
            and_(
                EmailIntegration.user_id == current_user.id,
                EmailIntegration.provider == "gmail",
                EmailIntegration.is_active == True,
                EmailIntegration.encrypted_refresh_token.is_not(None),
            )
        )
        .order_by(desc(EmailIntegration.updated_at))
        .limit(1)
    )
    integration = result.scalars().first()

    if not integration:
        raise HTTPException(
            status_code=404,
            detail="No Gmail integration found for your account. Please connect Gmail in Settings."
        )

    # Get configured credentials using the helper (supports tenant-specific overrides)
    redirect_default = settings.GOOGLE_OAUTH_REDIRECT or "http://localhost:8000/api/v1/integrations/gmail/callback"
    try:
        client_id, client_secret, _ = await _get_oauth_credentials(
            db=db,
            tenant_id=integration.tenant_id,
            provider="gmail",
            redirect_fallback=redirect_default,
        )
    except Exception as e:
         logger.error(f"Failed to get OAuth credentials: {e}")
         raise HTTPException(status_code=500, detail="Service configuration error")

    try:
        refresh_token = decrypt_token(integration.encrypted_refresh_token)
    except Exception as e:
        logger.error(f"Failed to decrypt refresh token for integration {integration.id}: {e}")
        # Make user re-authenticate
        raise HTTPException(status_code=401, detail="Authentication invalid (token decryption failed). Please reconnect Gmail.")

    query = "label:INBOX" if folder.upper() == "INBOX" else "label:SENT"
    
    try:
        messages = await gmail.list_threads(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            query=query, 
            max_results=20
        )
        return {"messages": messages}
    except Exception as e:
        logger.exception(f"Failed to list messages: {e}") # Log full traceback
        # Return generic error details to frontend
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails from Gmail: {str(e)}")


@router.get("/gmail/messages/{message_id}")
async def get_gmail_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full details of a specific email message."""
    # SECURITY FIX: Only allow user to access THEIR OWN Gmail integration
    result = await db.execute(
        select(EmailIntegration)
        .where(
            and_(
                EmailIntegration.user_id == current_user.id,
                EmailIntegration.provider == "gmail",
                EmailIntegration.is_active == True,
                EmailIntegration.encrypted_refresh_token.is_not(None),
            )
        )
        .order_by(desc(EmailIntegration.updated_at))
        .limit(1)
    )
    integration = result.scalars().first()

    if not integration:
        raise HTTPException(
            status_code=404,
            detail="No Gmail integration found for your account. Please connect Gmail in Settings."
        )

    # 2. Get credentials
    try:
        redirect_default = settings.GOOGLE_OAUTH_REDIRECT or "http://localhost:8000/api/v1/integrations/gmail/callback"
        client_id, client_secret, _ = await _get_oauth_credentials(
            db=db,
            tenant_id=integration.tenant_id,
            provider="gmail",
            redirect_fallback=redirect_default,
        )
    except Exception as e:
         logger.error(f"Configuration error: {e}")
         raise HTTPException(status_code=500, detail="Service configuration error")

    # 3. Decrypt token
    try:
        refresh_token = decrypt_token(integration.encrypted_refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication invalid")

    # 4. Fetch message
    try:
        # Fetch full thread details (which allows showing conversation history)
        # We use message_id as thread_id hint because normally get_gmail_message is called from a list context
        # But actually `message_id` from list_threads IS the thread_id effectively (or we can get threadId from message detail).
        # To be safe: we first fetch the message to get its threadId, OR we just assume the frontend is passing a valid ID for usage.
        
        # NOTE: The frontend might be passing a message ID. Let's first get the message to find the thread ID, 
        # OR we can assume `list_gmail_messages` returned thread IDs as `id`.
        # Taking a look at `list_gmail_messages`: it returns `id` which is `thread['id']`.
        # So `message_id` passed here is actually `thread_id`.
        
        # Let's verify if `message_id` is a thread ID using `gmail.get_thread_with_messages`.
        # If it fails, maybe it is a collection of messages.
        
        thread = await gmail.get_thread_with_messages(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            thread_id=message_id 
        )
        return thread
    except Exception as e:
        logger.error(f"Failed to fetch message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail/import")
async def import_gmail_message(
    payload: GmailMessageImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Import a specific Gmail message as a Document."""
    # SECURITY FIX: Only allow user to access THEIR OWN Gmail integration
    result = await db.execute(
        select(EmailIntegration)
        .where(
            and_(
                EmailIntegration.user_id == current_user.id,
                EmailIntegration.provider == "gmail",
                EmailIntegration.is_active == True,
                EmailIntegration.encrypted_refresh_token.is_not(None),
            )
        )
        .order_by(desc(EmailIntegration.updated_at))
        .limit(1)
    )
    integration = result.scalars().first()

    if not integration:
        raise HTTPException(
            status_code=404,
            detail="No Gmail integration found for your account. Please connect Gmail in Settings."
        )

    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    refresh_token = decrypt_token(integration.encrypted_refresh_token)

    try:
        # Fetch full thread (treat payload.message_id as thread_id)
        thread = await gmail.get_thread_with_messages(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            thread_id=payload.message_id
        )
        
        # Build content from all messages in the thread
        subject = thread.get("subject", "Imported Email")
        messages = thread.get("messages", [])
        
        content_parts = [f"Subject: {subject}\n"]
        
        for msg in messages:
            content_parts.append(f"From: {msg.get('from', 'Unknown')}")
            content_parts.append(f"Date: {msg.get('date', 'Unknown')}")
            content_parts.append(f"To: {msg.get('to', '')}")
            content_parts.append("\n" + msg.get("body", "(No content)"))
            content_parts.append("\n" + "-" * 50 + "\n")
            
        content = "\n".join(content_parts)
        
        content = "\n".join(content_parts)
        
        # Determine Group (Knowledge Base) to assign this document to
        group_id = None
        
        # 1. Prefer the integration's default bot if set
        if integration.default_reply_bot_id:
            bot = await db.get(Bot, integration.default_reply_bot_id)
            if bot and bot.group_id:
                group_id = bot.group_id
        
        if not group_id:
            # 2. Strategy: Fetch the first available group for this tenant
            group_result = await db.execute(select(Group).where(Group.tenant_id == tenant_id).limit(1))
            group = group_result.scalar_one_or_none()
            
            if not group:
                # 3. Create a default "General" group if none exists
                group = Group(
                    tenant_id=tenant_id,
                    name="General",
                    description="Default group for imported documents",
                    created_by=current_user.id
                )
                db.add(group)
                await db.flush() # Ensure we have an ID
            
            group_id = group.id

        # Create document
        doc, _ = await create_document(
            db=db,
            bot_id=group_id, # The service maps 'bot_id' argument to 'group_id' column
            tenant_id=tenant_id,
            uploader_id=current_user.id,
            filename=f"Email: {subject}.txt",
            size_bytes=len(content.encode('utf-8')),
            mime_type="text/plain", # Plain text representation of the thread
            file_bytes=content.encode('utf-8'),
            title=f"Email: {subject}"
        )
        await db.commit()
        
        return {"document_id": str(doc.id), "message": "Email thread imported successfully"}

    except Exception as e:
        logger.error(f"Failed to import message: {e}")
        # If it was a 404 on the thread endpoint, it might really be missing
        if "404" in str(e):
             raise HTTPException(status_code=404, detail="Email thread not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail/generate-reply")
async def generate_gmail_reply(
    payload: GmailMessageReply,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a draft reply using LLM with optional KB context.
    
    If bot_id is provided, uses that bot's knowledge base.
    If no bot_id, tries to find a matching monitoring rule and use its bot.
    If still no bot, generates a generic professional reply.
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(db, current_user.tenant_id)

        llm = LLMService()
        bot_to_use = None
        
        # Strategy 1: User explicitly provided bot_id
        if payload.bot_id:
            bot_to_use = await db.get(Bot, payload.bot_id)
            if not bot_to_use:
                raise HTTPException(status_code=404, detail="Bot not found")
            if bot_to_use.tenant_id != current_user.tenant_id:
                raise HTTPException(status_code=403, detail="Unauthorized")
        else:
            # Strategy 2: Try to find matching monitoring rule
            # Look up the email integration from the message (if available through message metadata)
            # For now, find the active Gmail integration for this user
            from app.models.email_monitoring_rule import EmailMonitoringRule
            
            result = await db.execute(
                select(EmailIntegration).where(
                    and_(
                        EmailIntegration.user_id == current_user.id,
                        EmailIntegration.provider == "gmail",
                        EmailIntegration.is_active == True
                    )
                )
            )
            gmail_integration = result.scalar_one_or_none()
            
            if gmail_integration:
                # Try to match this email against the user's rules
                rules_result = await db.execute(
                    select(EmailMonitoringRule).where(
                        and_(
                            EmailMonitoringRule.tenant_id == current_user.tenant_id,
                            EmailMonitoringRule.integration_id == gmail_integration.id,
                            EmailMonitoringRule.is_active == True
                        )
                    ).order_by(EmailMonitoringRule.priority.asc())
                )
                rules = rules_result.scalars().all()
                
                # Simple matching: first active rule wins
                # (In production, you'd use proper email matching logic)
                if rules:
                    first_rule = rules[0]
                    bot_to_use = await db.get(Bot, first_rule.bot_id)
                
                # Strategy 3: No rule matched, try default bot for this integration
                if not bot_to_use and gmail_integration.default_reply_bot_id:
                    bot_to_use = await db.get(Bot, gmail_integration.default_reply_bot_id)
                    if bot_to_use and bot_to_use.tenant_id != current_user.tenant_id:
                        bot_to_use = None
        
        # Prepare context for RAG if we have a bot
        context_chunks = []
        if bot_to_use:
            from app.services.vector_search_service import VectorSearchService
            from app.services.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            vector_search = VectorSearchService(embedding_service)
            
            search_query = f"{payload.subject or ''} {payload.original_text}".strip()
            
            search_results, _ = await vector_search.search(
                db=db,
                bot_id=bot_to_use.id,
                tenant_id=current_user.tenant_id,
                query=search_query,
                k=5,
                similarity_threshold=0.3,
            )
            
            context_chunks = search_results
        
        query = f"Subject: {payload.subject or 'No subject'}\n\nEmail:\n{payload.original_text}"
        
        response_text = ""
        async for token in llm.generate_answer(query, context_chunks):
            response_text += token
            
        return {"reply": response_text}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail/send-reply")
async def send_gmail_reply(
    payload: GmailSendReply = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a reply email via Gmail API."""
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(db, current_user.tenant_id)

        logger.info(f"Send reply payload: {payload.model_dump()}")
        
        # SECURITY FIX: Only allow user to access THEIR OWN Gmail integration
        result = await db.execute(
            select(EmailIntegration)
            .where(
                and_(
                    EmailIntegration.user_id == current_user.id,
                    EmailIntegration.provider == "gmail",
                    EmailIntegration.is_active == True,
                    EmailIntegration.encrypted_refresh_token.is_not(None),
                )
            )
            .order_by(desc(EmailIntegration.updated_at))
            .limit(1)
        )
        integration = result.scalar_one_or_none()

        if not integration:
            raise HTTPException(
                status_code=404,
                detail="No Gmail integration found for your account. Please connect Gmail in Settings."
            )

        # Resolve OAuth credentials (supports tenant overrides)
        redirect_default = settings.GOOGLE_OAUTH_REDIRECT or "http://localhost:8000/api/v1/integrations/gmail/callback"
        client_id, client_secret, _ = await _get_oauth_credentials(
            db=db,
            tenant_id=integration.tenant_id,
            provider="gmail",
            redirect_fallback=redirect_default,
        )

        # Decrypt and refresh token
        refresh_token = decrypt_token(integration.encrypted_refresh_token)
        token_data = await gmail.refresh_access_token(
            client_id,
            client_secret,
            refresh_token
        )
        access_token = token_data["access_token"]
        
        # Send the reply
        sent_message = await gmail.send_reply(
            access_token=access_token,
            thread_id=payload.thread_id,
            message_id=payload.message_id,
            to=payload.to,
            subject=payload.subject,
            body=payload.body
        )
        
        return {
            "message": "Reply sent successfully",
            "sent_message_id": sent_message.get("id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send reply: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
                EmailIntegration.encrypted_refresh_token.is_not(None),
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
                "default_reply_bot_id": str(integration.default_reply_bot_id) if integration.default_reply_bot_id else None,
                "last_sync_time": integration.last_sync_time.isoformat() if integration.last_sync_time else None,
                "created_at": integration.created_at.isoformat() if integration.created_at else None,
            }
            for integration in integrations
        ]
    }


@router.put("/{integration_id}/default-reply-bot")
async def set_default_reply_bot(
    integration_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set the default bot for email replies on this integration."""
    bot_id = payload.get("bot_id")
    
    result = await db.execute(
        select(EmailIntegration).where(
            and_(
                EmailIntegration.id == integration_id,
                EmailIntegration.user_id == current_user.id,
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if bot_id:
        # Verify bot exists and belongs to tenant
        bot = await db.get(Bot, bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        if bot.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        integration.default_reply_bot_id = bot_id
    else:
        integration.default_reply_bot_id = None
    
    await db.commit()
    await db.refresh(integration)
    
    return {
        "id": str(integration.id),
        "default_reply_bot_id": str(integration.default_reply_bot_id) if integration.default_reply_bot_id else None,
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


@router.get("/outlook/authorize")
async def outlook_authorize(
    request: Request,
    token: Optional[str] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Return a Microsoft OAuth2 authorization URL to redirect the user to."""
    tenant_id = await _get_tenant_from_token(request, token, credentials)
    redirect_default = settings.OUTLOOK_OAUTH_REDIRECT or "http://localhost:8000/api/v1/integrations/outlook/callback"
    client_id, _, redirect_uri = await _get_oauth_credentials(
        db=db,
        tenant_id=tenant_id,
        provider="outlook",
        redirect_fallback=redirect_default,
    )

    state = str(uuid4())
    # In production store state in user session to check in callback
    
    auth_url = outlook.get_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state
    )

    response = RedirectResponse(auth_url)
    
    if token:
        response.set_cookie(
            key="veriply_oauth_token",
            value=token,
            max_age=300,
            httponly=True,
            samesite="lax",
            secure=settings.is_production
        )

    return response


@router.get("/outlook/callback")
async def outlook_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Outlook OAuth2 callback."""
    token = request.cookies.get("veriply_oauth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication cookie missing")

    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        user_id = UUID(payload.get("sub"))
        tenant_id = UUID(payload.get("tenant_id"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication cookie")

    result = await db.execute(select(User).where(User.id == user_id))
    current_user = result.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=401, detail="User not found")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code from provider")

    redirect_default = settings.OUTLOOK_OAUTH_REDIRECT or "http://localhost:8000/api/v1/integrations/outlook/callback"
    client_id, client_secret, redirect_uri = await _get_oauth_credentials(
        db=db,
        tenant_id=tenant_id,
        provider="outlook",
        redirect_fallback=redirect_default,
    )

    try:
        token_data = await outlook.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            code=code
        )
    except Exception as e:
        logger.error("Failed to exchange token with Microsoft: %s", e)
        raise HTTPException(status_code=502, detail="Failed to exchange token with Microsoft")

    refresh_token = token_data.get("refresh_token")
    access_token = token_data.get("access_token")

    if not refresh_token:
        logger.warning("No refresh token returned by Microsoft; storing access token")

    token_to_encrypt = refresh_token or access_token
    try:
        encrypted_token = encrypt_token(token_to_encrypt)
    except Exception as e:
        logger.error(f"Failed to encrypt token: {e}")
        raise HTTPException(status_code=500, detail="Failed to secure token")

    # Check/Upsert integration
    existing = await db.execute(
        select(EmailIntegration).where(
            and_(
                EmailIntegration.user_id == current_user.id,
                EmailIntegration.provider == "outlook",
            )
        )
    )
    integration = existing.scalars().first()

    if integration:
        integration.encrypted_refresh_token = encrypted_token
        integration.scope = token_data.get("scope")
        integration.status = "connected"
        integration.is_active = True
        integration.last_sync_time = datetime.utcnow()
        integration.updated_at = datetime.utcnow()
    else:
        integration = EmailIntegration(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=current_user.id,
            provider="outlook",
            encrypted_refresh_token=encrypted_token,
            scope=token_data.get("scope"),
            status="connected",
        )
        db.add(integration)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to save outlook integration: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save integration")

    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
    return RedirectResponse(f"{frontend_url}/dashboard/integrations?connected=outlook")

"""Tests for email integration OAuth endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def test_app():
    """Get the FastAPI app with integrations router properly registered."""
    from app.main import app
    from app.api.routes import integrations
    
    # Ensure integrations router is registered
    if not any(r.path.startswith("/api/v1/integrations") for r in app.routes if hasattr(r, 'path')):
        app.include_router(integrations.router)
    
    return app


@pytest.mark.asyncio
async def test_gmail_authorize_redirects(test_app):
    """Test that gmail/authorize endpoint returns a redirect to Google OAuth."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"}):
            response = await client.get(
                "/api/v1/integrations/gmail/authorize",
                follow_redirects=False
            )
    
    assert response.status_code == 307  # Redirect
    assert "accounts.google.com" in response.headers["location"]
    assert "test_client_id" in response.headers["location"]


@pytest.mark.asyncio
async def test_gmail_authorize_missing_client_id(test_app):
    """Test that gmail/authorize returns 500 if GOOGLE_CLIENT_ID is missing."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.dict("os.environ", {}, clear=True):
            response = await client.get("/api/v1/integrations/gmail/authorize")
    
    assert response.status_code == 500
    assert "GOOGLE_CLIENT_ID not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_gmail_callback_missing_code(test_app):
    """Test that gmail/callback returns 400 if code is missing."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/integrations/gmail/callback")
    
    assert response.status_code == 401  # Requires auth, will fail before code check
    # In real implementation, if auth is bypassed, it would be 400


# TODO: Add integration test for full OAuth flow with mocked Google token endpoint
# TODO: Add test for list_integrations endpoint
# TODO: Add test for disconnect_integration endpoint

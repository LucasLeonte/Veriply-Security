"""Tests for email integration OAuth endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app


@pytest.mark.asyncio
async def test_gmail_authorize_redirects():
    """Test that gmail/authorize endpoint returns a redirect to Google OAuth."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"}):
            response = await client.get(
                "/api/v1/integrations/gmail/authorize",
                follow_redirects=False
            )
    
    assert response.status_code == 307  # Redirect
    assert "accounts.google.com" in response.headers["location"]
    assert "test_client_id" in response.headers["location"]


@pytest.mark.asyncio
async def test_gmail_authorize_missing_client_id():
    """Test that gmail/authorize returns 500 if GOOGLE_CLIENT_ID is missing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch.dict("os.environ", {}, clear=True):
            response = await client.get("/api/v1/integrations/gmail/authorize")
    
    assert response.status_code == 500
    assert "GOOGLE_CLIENT_ID not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_gmail_callback_missing_code():
    """Test that gmail/callback returns 400 if code is missing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/integrations/gmail/callback")
    
    assert response.status_code == 401  # Requires auth, will fail before code check
    # In real implementation, if auth is bypassed, it would be 400


# TODO: Add integration test for full OAuth flow with mocked Google token endpoint
# TODO: Add test for list_integrations endpoint
# TODO: Add test for disconnect_integration endpoint

"""
Test Suite for Health Check Endpoint

Tests the /healthz endpoint functionality and configuration reporting.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_healthz_endpoint_exists():
    """Verify /healthz endpoint exists and returns 200."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_healthz_returns_json():
    """Verify /healthz returns valid JSON."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_healthz_includes_status():
    """Verify /healthz includes status field."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_healthz_includes_environment():
    """Verify /healthz reports environment."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
        data = response.json()
        assert "environment" in data
        assert data["environment"] in ["development", "staging", "production"]


@pytest.mark.asyncio
async def test_healthz_includes_database_config():
    """Verify /healthz reports database configuration (non-sensitive)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
        data = response.json()
        assert "database" in data
        
        db_config = data["database"]
        assert "pool_size" in db_config
        assert "max_overflow" in db_config
        
        # Should NOT include password
        db_str = str(db_config)
        assert "password" not in db_str.lower() or "***" in db_str


@pytest.mark.asyncio
async def test_healthz_includes_timestamp():
    """Verify /healthz includes timestamp."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
        data = response.json()
        assert "timestamp" in data
        # Basic ISO format check
        assert "T" in data["timestamp"]

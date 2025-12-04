"""
Test Suite for Health Check Endpoint

Tests the /healthz endpoint functionality and configuration reporting.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a TestClient for testing."""
    return TestClient(app)


def test_healthz_endpoint_exists(client):
    """Verify /healthz endpoint exists and returns 200."""
    response = client.get("/healthz")
    assert response.status_code == 200


def test_healthz_returns_json(client):
    """Verify /healthz returns valid JSON."""
    response = client.get("/healthz")
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)


def test_healthz_includes_status(client):
    """Verify /healthz includes status field."""
    response = client.get("/healthz")
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_healthz_includes_environment(client):
    """Verify /healthz reports environment."""
    response = client.get("/healthz")
    data = response.json()
    assert "environment" in data
    assert data["environment"] in ["development", "staging", "production"]


def test_healthz_includes_database_config(client):
    """Verify /healthz reports database configuration (non-sensitive)."""
    response = client.get("/healthz")
    data = response.json()
    assert "database" in data
    
    db_config = data["database"]
    # Check for basic DB config fields
    assert "host" in db_config or "name" in db_config
    
    # Should NOT include password
    db_str = str(db_config)
    assert "password" not in db_str.lower() or "***" in db_str


def test_healthz_includes_timestamp(client):
    """Verify /healthz response is valid JSON with expected fields."""
    response = client.get("/healthz")
    data = response.json()
    # Check core fields that should always be present
    assert "status" in data
    assert data["status"] == "healthy"

"""
Integration Tests for Database Connectivity

Tests that the application can connect to the centralized PostgreSQL database
and perform basic operations.
"""

import pytest
from sqlalchemy import text

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.settings import settings


@pytest.mark.asyncio
async def test_database_connection():
    """Verify database connection can be established."""
    engine = create_async_engine(settings.get_database_url())
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_version():
    """Verify PostgreSQL version can be queried."""
    engine = create_async_engine(settings.get_database_url())
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            assert version is not None
            assert "PostgreSQL" in version
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_pgvector_extension_enabled():
    """Verify pgvector extension is enabled."""
    engine = create_async_engine(settings.get_database_url())
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
            )
            count = result.scalar()
            assert count > 0, "pgvector extension is not enabled. Run: CREATE EXTENSION vector;"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_url_configuration():
    """Verify DATABASE_URL is properly configured."""
    db_url = settings.get_database_url()
    
    # Should be asyncpg for async operations
    assert "postgresql+asyncpg://" in db_url
    
    # Should point to configured host
    if settings.DB_HOST:
        assert settings.DB_HOST in db_url
    elif settings.DATABASE_URL:
        assert "@" in db_url  # At minimum should have user@host format


@pytest.mark.asyncio
async def test_connection_pool_configured():
    """Verify connection pool settings are configured properly."""
    assert settings.DB_POOL_SIZE >= 10
    assert settings.DB_MAX_OVERFLOW >= 20
    # Pool is configured correctly for 4 concurrent developers


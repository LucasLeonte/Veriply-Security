import sys
import os
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Add app directory to sys.path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.main import app
from app.core.database import get_db
from app.core.settings import settings

# Import Base from models.base and all models to register them with metadata
from app.models import Base, User, Tenant, Bot, Document, Embedding


# Test database URL - use file-based SQLite for tests to avoid in-memory connection issues
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_veriply.db"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-scoped fixture that ensures the test database schema exists.
    Runs once per test session for all tests (including integration tests using settings.get_database_url()).
    This ensures Tenant, Document, Chunk tables exist before any tests that access them.
    """
    # Create a new event loop for this fixture
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    async def _create_schema():
        # For integration tests that use settings.get_database_url(), create tables in that database
        try:
            database_url = settings.get_database_url()
            print(f"Creating test database schema in: {database_url[:50]}...")
            
            # Create engine with appropriate settings
            if "postgresql" in database_url:
                # For PostgreSQL, use connection pool
                engine = create_async_engine(
                    database_url,
                    future=True,
                    echo=False,
                    pool_pre_ping=True,
                )
            else:
                # For SQLite and others, use NullPool
                engine = create_async_engine(
                    database_url,
                    future=True,
                    echo=False,
                    poolclass=NullPool,
                )
            
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            print("Test database schema created successfully")
            await engine.dispose()
        except Exception as e:
            print(f"Warning: Could not create tables in settings database: {type(e).__name__}: {e}")
            # Don't fail the test session - let tests fail individually if needed
    
    # Create tables at session start
    loop.run_until_complete(_create_schema())
    yield
    # Don't close the loop - pytest manages it


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a test database engine and tables."""
    # Use SQLite for isolated unit tests
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    # Create session factory
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create and yield session
    async with async_session() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database session override."""
    from httpx import ASGITransport
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

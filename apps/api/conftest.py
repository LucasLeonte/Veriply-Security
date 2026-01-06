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

# Ensure integrations router is registered (for Story 6.1 tests)
# Note: Integrations router may not auto-register in test environment,
# so we explicitly check and add it here for consistency
from app.api.routes import integrations
if not any(r.path.startswith("/api/v1/integrations") for r in app.routes if hasattr(r, 'path')):
    app.include_router(integrations.router)

# Import Base from models.base and all models to register them with metadata
from app.models import Base  # noqa: F401 - imported for model registration
from app.models.user import User  # noqa: F401
from app.models.tenant import Tenant, SubscriptionTier  # noqa: F401
from app.models.group import Group  # noqa: F401
from app.models.group_member import GroupMember, GroupRole  # noqa: F401
from app.models.bot import Bot, BotStatus  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.chunk import Chunk  # noqa: F401
from app.models.embedding import Embedding  # noqa: F401


# SQLite fallback for JSONB columns used in Postgres
def _install_sqlite_jsonb_compiler():
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    # Treat JSONB as JSON when compiling DDL for SQLite test database
    def visit_JSONB(self, type_, **kw):  # noqa: N802 - external API naming
        return "JSON"

    # Only install once
    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
        SQLiteTypeCompiler.visit_JSONB = visit_JSONB


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

    if engine.dialect.name == "sqlite":
        _install_sqlite_jsonb_compiler()
    
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
    """Create a test HTTP client with database session and auth overrides."""
    from httpx import ASGITransport
    from app.api.v1.auth import get_current_user, get_current_tenant
    from sqlalchemy import select
    import uuid
    
    async def override_get_db():
        yield db_session
    
    async def override_get_current_user(credentials=None, db=None):
        """Bypass JWT auth for tests - use first user from test database."""
        # Import here to avoid circular dependency
        from app.models.user import User
        
        # Use the test database session
        test_db = db if db is not None else db_session
            
        # Get first user from database (created by test fixtures)
        result = await test_db.execute(select(User).limit(1))
        user = result.scalars().first()
        
        if user:
            return user
            
        # Fallback: create a mock user
        mock_user = User()
        mock_user.id = uuid.uuid4()
        mock_user.tenant_id = uuid.uuid4()
        mock_user.email = "test@example.com"
        mock_user.role = "agent"
        return mock_user
    
    async def override_get_current_tenant(credentials=None):
        """Bypass JWT auth for tests - return tenant_id from first user."""
        from app.models.user import User
        
        # Get first user from database
        result = await db_session.execute(select(User).limit(1))
        user = result.scalars().first()
        
        if user:
            return user.tenant_id
            
        # Fallback
        return uuid.uuid4()
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# =============================================================================
# Test User/Bot Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def test_tenant(db_session: AsyncSession):
    """Create a test tenant."""
    from uuid import uuid4
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        plan="pro",
        subscription_tier=SubscriptionTier.PRO
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_tenant: Tenant):
    """Create a test user."""
    from uuid import uuid4
    from app.services.auth_service import hash_password
    
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        tenant_id=test_tenant.id,
        role="admin"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_bot(db_session: AsyncSession, test_tenant: Tenant, test_user: User):
    """Create a test bot."""
    from uuid import uuid4
    from datetime import datetime
    
    bot = Bot(
        id=uuid4(),
        tenant_id=test_tenant.id,
        name="Test Bot",
        description="Test bot for HITL tests",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(bot)
    await db_session.commit()
    await db_session.refresh(bot)
    return bot


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User, test_tenant: Tenant):
    """Create auth headers with valid JWT token."""
    import jwt
    from datetime import datetime, timedelta
    from app.core.settings import settings
    
    JWT_ALGORITHM = "HS256"
    
    token_payload = {
        "sub": str(test_user.id),
        "tenant_id": str(test_tenant.id),
        "email": test_user.email,
        "role": test_user.role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "Authorization": f"Bearer {token}"
    }

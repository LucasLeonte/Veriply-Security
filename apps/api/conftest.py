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
from app.models import Base  # noqa: F401 - imported for model registration
from app.models.user import User  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401
from app.models.group import Group  # noqa: F401
from app.models.group_member import GroupMember, GroupRole  # noqa: F401
from app.models.bot import Bot  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.chunk import Chunk  # noqa: F401
from app.models.embedding import Embedding  # noqa: F401
from app.models.verified_qa import VerifiedQA  # noqa: F401
from app.models.confidence_log import ConfidenceLog, RoutingDecision  # noqa: F401


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


# Test data fixtures

@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession):
    """Create a test tenant."""
    from uuid import uuid4
    from datetime import datetime
    
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        created_at=datetime.utcnow(),
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_tenant):
    """Create a test user."""
    from uuid import uuid4
    from datetime import datetime
    
    user = User(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="test@example.com",
        name="Test User",
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_group(db_session: AsyncSession, test_tenant, test_user):
    """Create a test group."""
    from uuid import uuid4
    from datetime import datetime
    
    group = Group(
        id=uuid4(),
        tenant_id=test_tenant.id,
        name="Test Group",
        created_by=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)
    return group


@pytest_asyncio.fixture
async def test_bot(db_session: AsyncSession, test_tenant, test_group):
    """Create a test bot."""
    from uuid import uuid4
    from datetime import datetime
    
    bot = Bot(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Test Bot",
        created_at=datetime.utcnow(),
    )
    db_session.add(bot)
    await db_session.commit()
    await db_session.refresh(bot)
    return bot


@pytest_asyncio.fixture
async def test_confidence_log_hitl(db_session: AsyncSession, test_tenant, test_group, test_bot):
    """Create a test confidence log routed to HITL."""
    from uuid import uuid4
    from datetime import datetime
    
    confidence_log = ConfidenceLog(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        query_text="What is the refund policy for damaged items?",
        generated_response="We offer full refunds for damaged items within 30 days.",
        overall_confidence=0.35,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.utcnow(),
    )
    db_session.add(confidence_log)
    await db_session.commit()
    await db_session.refresh(confidence_log)
    return confidence_log


# Alias db_session as db for compatibility
@pytest_asyncio.fixture
async def db(db_session: AsyncSession):
    """Alias for db_session to support both naming conventions."""
    return db_session

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.models import Base
from app.core.settings import settings
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# Create async engine with connection pooling configured for multiple developers
engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.DEBUG,  # SQL logging in debug mode
    future=True,
    pool_size=settings.DB_POOL_SIZE,          # Base connection pool size
    max_overflow=settings.DB_MAX_OVERFLOW,    # Additional connections under load
    pool_timeout=settings.DB_POOL_TIMEOUT,    # Wait time for connection
    pool_recycle=settings.DB_POOL_RECYCLE,    # Recycle connections after 1 hour
    pool_pre_ping=True,                       # Test connections before using them
    connect_args={
        "timeout": 10,                        # Connection timeout (10 seconds)
        "command_timeout": 10,                # Command timeout (10 seconds)
        "server_settings": {
            "application_name": "veriply_api"  # Identify connections in pg_stat_activity
        }
    }
)

AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def set_tenant_context(session: AsyncSession, tenant_id: UUID, group_id: UUID | None = None):
    """Set RLS context variables for tenant and optional group isolation.
    
    CRITICAL: This must be called on EVERY database session to enforce Row-Level Security.
    Without this, RLS policies are bypassed and users can access all data.
    """
    try:
        await session.execute(
            text("SET LOCAL app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )
        if group_id:
            await session.execute(
                text("SET LOCAL app.current_group_id = :group_id"),
                {"group_id": str(group_id)}
            )
        logger.debug(f"RLS context set: tenant_id={tenant_id}, group_id={group_id}")
    except Exception as e:
        logger.error(f"Failed to set RLS context: {e}")
        raise

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for getting database sessions.
    
    NOTE: This does NOT set RLS context. Endpoints must call set_tenant_context() explicitly.
    TODO: Consider adding middleware to automatically set context from JWT token.
    """
    async with AsyncSessionLocal() as session:
        yield session

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.core.settings import settings

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

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for getting database sessions."""
    async with AsyncSessionLocal() as session:
        yield session

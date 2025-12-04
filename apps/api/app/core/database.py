from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.core.settings import settings

# Create async engine with connection pooling configured for multiple developers
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # SQL logging in debug mode
    future=True,
    pool_size=settings.DB_POOL_SIZE,          # Base connection pool size
    max_overflow=settings.DB_MAX_OVERFLOW,    # Additional connections under load
    pool_timeout=settings.DB_POOL_TIMEOUT,    # Wait time for connection
    pool_recycle=settings.DB_POOL_RECYCLE,    # Recycle connections after 1 hour
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

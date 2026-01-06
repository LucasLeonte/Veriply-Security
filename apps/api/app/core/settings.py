"""
Application Settings Configuration

This module provides centralized configuration management using Pydantic BaseSettings.
All environment variables are loaded from the root .env file.

Environment variables are loaded in this order (via python-dotenv):
1. ../../.env (project root - SINGLE SOURCE OF TRUTH)
2. System environment variables (Docker, OS)

Usage:
    from app.core.settings import settings
    
    db_url = settings.DATABASE_URL
    jwt_secret = settings.JWT_SECRET
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All values come from the root .env file (../../.env).
    See ../../.env.example for documentation of each variable.
    """
    
    model_config = SettingsConfigDict(
        # Load .env from project root (four levels up from this file)
        # settings.py is at: apps/api/app/core/settings.py
        # parents[4] goes: core -> app -> api -> apps -> PROJECT_ROOT
        env_file=str(Path(__file__).resolve().parents[4] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env
    )
    
    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    
    # Primary: Direct DATABASE_URL (preferred)
    DATABASE_URL: Optional[str] = None
    
    # Alternative: Individual components (for backward compatibility)
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    
    # Legacy variable names for backward compatibility
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    
    def get_database_url(self) -> str:
        """
        Get PostgreSQL connection string.
        
        Priority:
        1. Use DATABASE_URL if set directly (preferred)
        2. Construct from DB_* components
        3. Fall back to POSTGRES_* components (legacy)
        
        Format: postgresql+asyncpg://user:password@host:port/database
        """
        # If DATABASE_URL is set directly, use it
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Otherwise, construct from components
        host = self.DB_HOST or self.POSTGRES_HOST or "localhost"
        port = self.DB_PORT or self.POSTGRES_PORT or 5432
        db = self.DB_NAME or self.POSTGRES_DB or "veriply_dev"
        user = self.DB_USER or self.POSTGRES_USER or "veriply_user"
        password = self.DB_PASSWORD or self.POSTGRES_PASSWORD
        
        if not password:
            raise ValueError(
                "Database credentials required. "
                "Set DATABASE_URL or DB_PASSWORD/POSTGRES_PASSWORD in .env"
            )
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """
        Synchronous PostgreSQL connection string (for migrations, etc.).
        
        Uses psycopg2 driver instead of asyncpg.
        Format: postgresql://user:password@host:port/database
        """
        # Replace asyncpg with standard driver
        return self.get_database_url().replace("postgresql+asyncpg://", "postgresql://")
    
    # Connection pooling configuration

    
    # Database connection pool settings
    # Configured for 4 concurrent developers + production load
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    
    # ========================================================================
    # OLLAMA CONFIGURATION
    # ========================================================================
    
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Public base URL for building absolute links (used for avatar URLs)
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"
    
    # ========================================================================
    # REDIS CONFIGURATION
    # ========================================================================
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    # ========================================================================
    # JWT & AUTHENTICATION
    # ========================================================================
    
    JWT_SECRET: Optional[str] = None  # REQUIRED - validation done on first use
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    
    # ========================================================================
    # EMAIL CONFIGURATION
    # ========================================================================
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # ========================================================================
    # MODERATION NOTIFICATION CONFIGURATION
    # ========================================================================
    
    # Email notifications for moderation alerts
    MODERATION_EMAIL_ENABLED: bool = False  # Set to True to enable email alerts
    MODERATION_EMAIL_RECIPIENTS: list[str] = []  # List of emails to notify for moderation alerts
    MODERATION_ADMIN_EMAIL_RECIPIENTS: list[str] = []  # List of admin emails for abuse alerts
    MODERATION_FROM_EMAIL: str = "moderation@veriply.com"
    
    # Webhook notifications for external integrations (Slack, PagerDuty, etc.)
    MODERATION_WEBHOOK_URL: Optional[str] = None  # Set to webhook URL to enable
    MODERATION_WEBHOOK_SECRET: Optional[str] = None  # Optional secret for webhook auth
    EMAIL_FROM: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"
    
    # ========================================================================
    # API SERVER CONFIGURATION
    # ========================================================================
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = True
    LOG_LEVEL: str = "info"
    
    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        env="ALLOW_ORIGINS"
    )
    
    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ========================================================================
    # VECTOR SEARCH CONFIGURATION
    # ========================================================================
    
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384
    SIMILARITY_THRESHOLD: float = 0.7
    
    # ========================================================================
    # FILE UPLOAD CONFIGURATION
    # ========================================================================
    
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "pdf,docx,txt,md"
    UPLOAD_DIR: str = "./uploads"
    
    @property
    def ALLOWED_FILE_TYPES_LIST(self) -> list[str]:
        """Parse comma-separated file types into a list."""
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]
    
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # ========================================================================
    # ENVIRONMENT & DEPLOYMENT
    # ========================================================================
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT.lower() == "development"
    
    # ========================================================================
    # OBSERVABILITY & MONITORING
    # ========================================================================
    
    SENTRY_DSN: Optional[str] = None
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    
    # ========================================================================
    # NEXTAUTH CONFIGURATION (if needed for server-side validation)
    # ========================================================================
    
    NEXTAUTH_SECRET: Optional[str] = None
    NEXTAUTH_URL: Optional[str] = None
    
    # ========================================================================
    # WEB/FRONTEND CONFIGURATION (if needed for SSR or API communication)
    # ========================================================================
    
    NEXT_PUBLIC_API_URL: Optional[str] = None
    NEXT_PUBLIC_APP_URL: Optional[str] = None
    NEXT_PUBLIC_APP_NAME: Optional[str] = "Veriply"


# ============================================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================================

settings = Settings()

# Validate critical settings on import
if not settings.JWT_SECRET:
    raise ValueError(
        "JWT_SECRET is required but not set. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))' "
        "and add it to your .env file."
    )

# Validate database connection (check if we can construct a URL)
try:
    _ = settings.get_database_url()
except ValueError as e:
    raise ValueError(f"Database configuration error: {e}") from e


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
"""
# Import settings
from app.core.settings import settings

# Access configuration
db_url = settings.DATABASE_URL
jwt_secret = settings.JWT_SECRET
is_prod = settings.is_production

# Use in database connection
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

# Use in FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(debug=settings.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""

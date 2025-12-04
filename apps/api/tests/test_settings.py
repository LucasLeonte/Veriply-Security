"""
Test Suite for Settings Configuration

Tests that settings are properly loaded from root .env file and
that all required configuration is available.
"""

import pytest
from app.core.settings import settings


class TestSettings:
    """Test settings configuration and validation."""

    def test_settings_instance_exists(self):
        """Verify settings singleton is created."""
        assert settings is not None

    def test_jwt_secret_is_set(self):
        """Verify JWT secret is configured."""
        assert settings.JWT_SECRET is not None
        assert len(settings.JWT_SECRET) > 0

    def test_database_url_is_constructed(self):
        """Verify DATABASE_URL is properly constructed or set."""
        db_url = settings.get_database_url()
        assert db_url is not None
        assert db_url.startswith("postgresql+asyncpg://")
        assert "@" in db_url  # Should have user:pass@host format

    def test_database_individual_parameters(self):
        """Verify individual DB parameters are available."""
        # At least one set should be present (new or legacy)
        has_new_config = settings.DB_HOST or settings.DATABASE_URL
        has_legacy_config = settings.POSTGRES_HOST
        
        assert has_new_config or has_legacy_config

    def test_connection_pool_settings(self):
        """Verify connection pool is configured for multi-developer use."""
        assert settings.DB_POOL_SIZE >= 10
        assert settings.DB_MAX_OVERFLOW >= 20
        assert settings.DB_POOL_TIMEOUT > 0

    def test_cors_origins_list(self):
        """Verify CORS origins are parsed correctly."""
        origins = settings.CORS_ORIGINS_LIST
        assert isinstance(origins, list)
        assert len(origins) > 0

    def test_environment_detection(self):
        """Verify environment is properly detected."""
        assert settings.ENVIRONMENT in ["development", "staging", "production"]
        
        # Test environment helpers
        is_dev = settings.is_development
        is_prod = settings.is_production
        assert isinstance(is_dev, bool)
        assert isinstance(is_prod, bool)
        
        # Can't be both dev and prod
        assert not (is_dev and is_prod)

    def test_ollama_configuration(self):
        """Verify Ollama/embedding configuration."""
        assert settings.OLLAMA_HOST is not None
        assert settings.OLLAMA_HOST.startswith("http")

    def test_api_server_configuration(self):
        """Verify API server settings."""
        assert settings.API_PORT > 0
        assert settings.API_HOST is not None

    def test_file_upload_limits(self):
        """Verify file upload configuration."""
        assert settings.MAX_UPLOAD_SIZE_MB > 0
        assert settings.MAX_UPLOAD_SIZE_BYTES == settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        
        allowed_types = settings.ALLOWED_FILE_TYPES_LIST
        assert isinstance(allowed_types, list)
        assert len(allowed_types) > 0

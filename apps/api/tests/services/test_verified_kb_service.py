"""Tests for VerifiedKBService."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.verified_kb_service import VerifiedKBService


@pytest.mark.asyncio
class TestVerifiedKBService:
    """Tests for VerifiedKBService."""

    @pytest.fixture
    def service(self):
        """Provide VerifiedKBService instance."""
        return VerifiedKBService()

    async def test_is_verified_returns_false_placeholder(self, service, db_session: AsyncSession):
        """Test that is_verified returns False (placeholder implementation)."""
        chunk_id = uuid4()
        document_id = uuid4()

        result = await service.is_verified(
            db=db_session,
            chunk_id=chunk_id,
            document_id=document_id,
        )

        assert result is False

    async def test_is_verified_with_bot_id(self, service, db_session: AsyncSession):
        """Test is_verified with bot context."""
        chunk_id = uuid4()
        document_id = uuid4()
        bot_id = uuid4()

        result = await service.is_verified(
            db=db_session,
            chunk_id=chunk_id,
            document_id=document_id,
            bot_id=bot_id,
        )

        assert result is False

    async def test_is_verified_without_chunk_id(self, service, db_session: AsyncSession):
        """Test is_verified with only document_id."""
        document_id = uuid4()

        result = await service.is_verified(
            db=db_session,
            chunk_id=None,
            document_id=document_id,
        )

        assert result is False

    async def test_is_verified_without_document_id(self, service, db_session: AsyncSession):
        """Test is_verified with only chunk_id."""
        chunk_id = uuid4()

        result = await service.is_verified(
            db=db_session,
            chunk_id=chunk_id,
            document_id=None,
        )

        assert result is False

    async def test_get_verified_metadata_returns_none_placeholder(
        self, service, db_session: AsyncSession
    ):
        """Test that get_verified_metadata returns None (placeholder)."""
        document_id = uuid4()

        result = await service.get_verified_metadata(
            db=db_session,
            document_id=document_id,
        )

        assert result is None

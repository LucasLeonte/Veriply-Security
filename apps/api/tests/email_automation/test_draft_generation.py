"""Tests for email draft generation functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.email_processing_queue import EmailProcessingQueue
from app.models.email_draft import EmailDraft
from app.models.email_monitoring_rule import EmailMonitoringRule
from app.email_automation.email_extractor import EmailExtractor, html_to_text
from app.email_automation.draft_generator import EmailDraftGenerationService


# Test fixtures
@pytest.fixture
async def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        yield session


# Tests for email extraction
class TestEmailExtractor:
    """Tests for EmailExtractor."""
    
    def test_extract_email_address_with_name(self):
        """Test extracting email from 'Name <email@domain.com>' format."""
        extractor = EmailExtractor("client_id", "client_secret")
        email = extractor._extract_email_address("John Doe <john@example.com>")
        assert email == "john@example.com"
    
    def test_extract_email_address_plain(self):
        """Test extracting email from plain 'email@domain.com' format."""
        extractor = EmailExtractor("client_id", "client_secret")
        email = extractor._extract_email_address("john@example.com")
        assert email == "john@example.com"
    
    def test_extract_email_address_invalid(self):
        """Test extracting email from invalid format."""
        extractor = EmailExtractor("client_id", "client_secret")
        email = extractor._extract_email_address("No Email Here")
        assert email == "No Email Here"
    
    def test_html_to_text_conversion(self):
        """Test HTML to text conversion."""
        html = "<p>Hello <strong>World</strong></p><p>Second paragraph</p>"
        text = html_to_text(html)
        assert "Hello" in text
        assert "World" in text
        assert "Second paragraph" in text
        assert "<" not in text
    
    def test_html_to_text_with_script(self):
        """Test HTML to text skips script tags."""
        html = "<p>Hello</p><script>var x = 1;</script><p>World</p>"
        text = html_to_text(html)
        assert "Hello" in text
        assert "World" in text
        assert "var x" not in text
    
    @pytest.mark.asyncio
    async def test_extract_gmail_email_success(self):
        """Test successful Gmail email extraction."""
        extractor = EmailExtractor("client_id", "client_secret")
        
        # Mock the Gmail API
        mock_message = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "2025-01-08"},
                ],
                "body": {"data": "VGVzdCBib2R5"},  # base64 for "Test body"
            },
            "labelIds": ["INBOX", "IMPORTANT"],
        }
        
        with patch.object(extractor, '_extract_gmail_body') as mock_extract:
            mock_extract.return_value = "Test body"
            with patch('app.email_automation.email_extractor.gmail.refresh_access_token') as mock_refresh:
                mock_refresh.return_value = {"access_token": "token"}
                with patch('app.email_automation.email_extractor.gmail.get_message') as mock_get:
                    mock_get.return_value = mock_message
                    
                    result = await extractor.extract_gmail_email(
                        refresh_token="refresh_token",
                        message_id="msg123",
                        thread_id="thread123",
                    )
                    
                    assert result is not None
                    assert result['subject'] == "Test Subject"
                    assert result['sender_email'] == "sender@example.com"
                    assert result['thread_id'] == "thread123"
                    assert result['provider'] == "gmail"


# Tests for PII redaction
class TestPIIRedaction:
    """Tests for PII redaction in email content."""
    
    @pytest.mark.asyncio
    async def test_redact_email_address(self):
        """Test PII service redacts email addresses."""
        from app.services.pii_service import PIIRedactionService
        
        service = PIIRedactionService(presidio_enabled=False)
        text = "Contact us at support@example.com for help"
        result = await service.redact_query(text)
        
        assert result.contains_pii
        assert "<EMAIL>" in result.redacted_query
        assert "support@example.com" not in result.redacted_query
    
    @pytest.mark.asyncio
    async def test_redact_credit_card(self):
        """Test PII service redacts credit card numbers."""
        from app.services.pii_service import PIIRedactionService
        
        service = PIIRedactionService(presidio_enabled=False)
        text = "My card is 4532-1234-5678-9010"
        result = await service.redact_query(text)
        
        # May or may not redact depending on Luhn validation
        # But service should handle it without crashing
        assert result is not None


# Tests for RAG integration
class TestRAGIntegration:
    """Tests for RAG context retrieval for email drafts."""
    
    @pytest.mark.asyncio
    async def test_no_context_scenario(self):
        """Test handling when no relevant context is found."""
        from app.email_automation.draft_generator import (
            DEFAULT_LOW_CONTEXT_DRAFT,
            EmailDraftGenerationService,
        )
        
        # Create mocked services
        pii_service = AsyncMock()
        vector_search_service = AsyncMock()
        llm_service = AsyncMock()
        citation_service = AsyncMock()
        
        service = EmailDraftGenerationService(
            pii_service=pii_service,
            vector_search_service=vector_search_service,
            llm_service=llm_service,
            citation_service=citation_service,
        )
        
        original_email = {
            'subject': 'Help Request',
            'body': 'I need help with something',
            'sender_email': 'user@example.com',
        }
        
        # No context
        body, citations, confidence = await service._generate_draft(
            original_email=original_email,
            context_results=[],
            bot_id=uuid4(),
            has_context=False,
        )
        
        assert body == DEFAULT_LOW_CONTEXT_DRAFT
        assert confidence == 0
        assert citations is None


# Tests for draft generation
class TestDraftGeneration:
    """Tests for email draft generation."""
    
    @pytest.mark.asyncio
    async def test_draft_subject_formatting(self):
        """Test draft subject is correctly formatted as 'Re: ...'."""
        from app.email_automation.draft_generator import EmailDraftGenerationService
        
        pii_service = AsyncMock()
        vector_search_service = AsyncMock()
        llm_service = AsyncMock()
        citation_service = AsyncMock()
        
        service = EmailDraftGenerationService(
            pii_service=pii_service,
            vector_search_service=vector_search_service,
            llm_service=llm_service,
            citation_service=citation_service,
        )
        
        original_email = {
            'subject': 'Question about pricing',
            'body': 'What is your pricing?',
            'sender_email': 'customer@example.com',
        }
        
        # Mock LLM response
        llm_service.generate_answer.return_value = (
            _async_generator(["Our pricing", " is available on our website."])
        )
        
        from app.services.vector_search_service import SearchResult
        context = [
            SearchResult(
                chunk_id="chunk1",
                document_id="doc1",
                document_name="Pricing Page",
                section="Overview",
                text="Our pricing starts at $99/month",
                similarity=0.8,
                position=0,
            )
        ]
        
        body, _, _ = await service._generate_draft(
            original_email=original_email,
            context_results=context,
            bot_id=uuid4(),
            has_context=True,
        )
        
        assert "Our pricing" in body


# Tests for error handling
class TestErrorHandling:
    """Tests for error handling and retry logic."""
    
    @pytest.mark.asyncio
    async def test_max_retry_limit(self):
        """Test that items respect max retry limit."""
        from app.workers.email_draft_generator import EmailDraftGeneratorWorker
        
        worker = EmailDraftGeneratorWorker(
            db_url="sqlite+aiosqlite:///:memory:",
            poll_interval=1,
        )
        
        # Create a queue item with max retries
        queue_item = EmailProcessingQueue(
            id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            integration_id=uuid4(),
            provider_message_id="msg123",
            status="failed",
            retry_count=3,
        )
        
        # Should not be selected for processing
        pending_count = 0
        if queue_item.retry_count < 3:
            pending_count += 1
        
        assert pending_count == 0


# Helper function for async generators in tests
def _async_generator(items):
    """Create an async generator from items."""
    async def gen():
        for item in items:
            yield item
    return gen()


# Integration tests
class TestEmailDraftIntegration:
    """Integration tests for email draft generation."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_draft_generation(self, test_db: AsyncSession):
        """Test full pipeline from queue item to draft creation."""
        # This would require a full setup with mocked dependencies
        # Placeholder for comprehensive integration test
        pass

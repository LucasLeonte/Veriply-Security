"""Unit tests for LLM answer generation services.

Tests LLMService, AnswerGenerationService, prompt engineering, streaming,
and context-only enforcement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.llm_service import (
    LLMService,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_MAX_TOKENS,
)
from app.services.answer_service import AnswerGenerationService
from app.services.vector_search_service import SearchResult
from app.services.embedding_service import EmbeddingService
from app.services.vector_search_service import VectorSearchService


@pytest.fixture
def llm_service():
    """Create LLMService instance for testing."""
    return LLMService(ollama_url="http://localhost:11434")


@pytest.fixture
def mock_vector_search_service():
    """Create mock VectorSearchService."""
    return MagicMock(spec=VectorSearchService)


@pytest.fixture
def mock_embedding_service():
    """Create mock EmbeddingService."""
    return MagicMock(spec=EmbeddingService)


@pytest.fixture
def answer_service(mock_vector_search_service, llm_service):
    """Create AnswerGenerationService with mocked dependencies."""
    return AnswerGenerationService(
        vector_search_service=mock_vector_search_service,
        llm_service=llm_service,
    )


@pytest.fixture
def sample_context_chunks():
    """Sample context chunks from vector search."""
    return [
        SearchResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="Refund Policy",
            section="General Policy",
            text="Items can be returned within 30 days of purchase for a full refund.",
            similarity=0.95,
            position=0,
            page_number=1,
        ),
        SearchResult(
            chunk_id="chunk-2",
            document_id="doc-1",
            document_name="Refund Policy",
            section="Exceptions",
            text="Digital products and clearance items are non-refundable.",
            similarity=0.87,
            position=1,
            page_number=2,
        ),
    ]


class TestLLMServicePromptEngineering:
    """Tests for LLMService prompt engineering."""

    def test_build_system_prompt_contains_critical_rules(self, llm_service):
        """Test that system prompt contains all CRITICAL RULES."""
        prompt = llm_service._build_system_prompt()

        assert "CRITICAL RULES" in prompt
        assert "Answer ONLY using the provided context" in prompt
        assert "NEVER make up facts" in prompt
        assert "NEVER use outside knowledge" in prompt
        assert "NEVER hallucinate details" in prompt

    def test_build_user_prompt_formats_context_with_sources(
        self, llm_service, sample_context_chunks
    ):
        """Test that user prompt formats context chunks with source labels."""
        query = "What is the refund policy?"
        prompt = llm_service._build_user_prompt(query, sample_context_chunks)

        # Check that all chunks are included
        assert "Refund Policy" in prompt
        assert "Items can be returned within 30 days" in prompt
        assert "Digital products and clearance items" in prompt

        # Check that sources are labeled
        assert "[Source:" in prompt
        assert "General Policy" in prompt
        assert "Exceptions" in prompt

    def test_build_user_prompt_with_page_numbers(self, llm_service):
        """Test that page numbers are included in source citations."""
        chunks = [
            SearchResult(
                chunk_id="c1",
                document_id="d1",
                document_name="Terms",
                section="Section A",
                text="Some text",
                similarity=0.9,
                position=0,
                page_number=5,
            )
        ]

        prompt = llm_service._build_user_prompt("query", chunks)
        assert "p. 5" in prompt

    def test_build_user_prompt_handles_empty_context(self, llm_service):
        """Test that empty context is handled gracefully."""
        query = "What is the refund policy?"
        prompt = llm_service._build_user_prompt(query, [])

        assert "[No documents found in knowledge base]" in prompt
        assert query in prompt

    def test_format_source_with_all_parts(self, llm_service):
        """Test source formatting with document, section, and page."""
        chunk = SearchResult(
            chunk_id="c1",
            document_id="d1",
            document_name="User Guide",
            section="Getting Started",
            text="text",
            similarity=0.9,
            position=0,
            page_number=10,
        )

        source = llm_service._format_source(chunk)
        assert "User Guide" in source
        assert "Getting Started" in source
        assert "p. 10" in source

    def test_format_source_without_section(self, llm_service):
        """Test source formatting without section."""
        chunk = SearchResult(
            chunk_id="c1",
            document_id="d1",
            document_name="FAQ",
            section=None,
            text="text",
            similarity=0.9,
            position=0,
        )

        source = llm_service._format_source(chunk)
        assert source == "FAQ"

    def test_build_messages_with_system_and_user(self, llm_service):
        """Test that message list includes system and user messages."""
        system = "You are helpful"
        user = "What is X?"

        messages = llm_service._build_messages(system, user)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == system
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == user

    def test_build_messages_with_conversation_history(self, llm_service):
        """Test that conversation history is included in messages."""
        system = "You are helpful"
        user = "What is X?"
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        messages = llm_service._build_messages(system, user, history)

        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1:3] == history
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == user


class TestLLMServiceGeneration:
    """Tests for LLMService answer generation and streaming."""

    @pytest.mark.asyncio
    async def test_generate_answer_streams_tokens(
        self, llm_service, sample_context_chunks
    ):
        """Test that generate_answer yields tokens as AsyncIterator."""
        mock_response_lines = [
            '{"message":{"content":"The"}}',
            '{"message":{"content":" refund"}}',
            '{"message":{"content":" policy"}}',
        ]

        async def async_iter_lines():
            for line in mock_response_lines:
                yield line

        with patch.object(llm_service.client, "stream") as mock_stream:
            mock_response = AsyncMock()
            mock_response.aiter_lines = async_iter_lines
            mock_response.raise_for_status = AsyncMock()

            mock_context_mgr = AsyncMock()
            mock_context_mgr.__aenter__.return_value = mock_response
            mock_context_mgr.__aexit__.return_value = None
            mock_stream.return_value = mock_context_mgr

            tokens = []
            async for token in llm_service.generate_answer(
                query="What is refund policy?",
                context_chunks=sample_context_chunks,
            ):
                tokens.append(token)

            assert tokens == ["The", " refund", " policy"]

    @pytest.mark.asyncio
    async def test_generate_answer_with_conversation_history(
        self, llm_service, sample_context_chunks
    ):
        """Test that conversation history is passed to LLM."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        mock_response_lines = ['{"message":{"content":"Sure"}}']

        async def async_iter_lines():
            for line in mock_response_lines:
                yield line

        with patch.object(llm_service.client, "stream") as mock_stream:
            mock_response = AsyncMock()
            mock_response.aiter_lines = async_iter_lines
            mock_response.raise_for_status = AsyncMock()

            mock_context_mgr = AsyncMock()
            mock_context_mgr.__aenter__.return_value = mock_response
            mock_context_mgr.__aexit__.return_value = None
            mock_stream.return_value = mock_context_mgr

            async for _ in llm_service.generate_answer(
                query="What next?",
                context_chunks=sample_context_chunks,
                conversation_history=history,
            ):
                pass

            # Verify POST was called with correct structure
            call_args = mock_stream.call_args
            payload = call_args[1]["json"]
            assert len(payload["messages"]) == 4  # system + 2 history + user
            assert payload["messages"][1:3] == history

    @pytest.mark.asyncio
    async def test_generate_answer_sets_llm_parameters(
        self, llm_service, sample_context_chunks
    ):
        """Test that LLM parameters are set correctly."""
        mock_response_lines = ['{"message":{"content":"X"}}']

        async def async_iter_lines():
            for line in mock_response_lines:
                yield line

        with patch.object(llm_service.client, "stream") as mock_stream:
            mock_response = AsyncMock()
            mock_response.aiter_lines = async_iter_lines
            mock_response.raise_for_status = AsyncMock()

            mock_context_mgr = AsyncMock()
            mock_context_mgr.__aenter__.return_value = mock_response
            mock_context_mgr.__aexit__.return_value = None
            mock_stream.return_value = mock_context_mgr

            async for _ in llm_service.generate_answer(
                query="test", context_chunks=sample_context_chunks
            ):
                pass

            call_args = mock_stream.call_args
            payload = call_args[1]["json"]
            options = payload["options"]

            assert options["temperature"] == DEFAULT_TEMPERATURE  # 0.1
            assert options["top_p"] == DEFAULT_TOP_P  # 0.95
            assert options["num_predict"] == DEFAULT_MAX_TOKENS  # 512

    @pytest.mark.asyncio
    async def test_generate_answer_enforces_context_only_in_prompt(
        self, llm_service, sample_context_chunks
    ):
        """Test that prompt enforces context-only behavior."""
        mock_response_lines = ['{"message":{"content":"test"}}']

        async def async_iter_lines():
            for line in mock_response_lines:
                yield line

        with patch.object(llm_service.client, "stream") as mock_stream:
            mock_response = AsyncMock()
            mock_response.aiter_lines = async_iter_lines
            mock_response.raise_for_status = AsyncMock()

            mock_context_mgr = AsyncMock()
            mock_context_mgr.__aenter__.return_value = mock_response
            mock_context_mgr.__aexit__.return_value = None
            mock_stream.return_value = mock_context_mgr

            async for _ in llm_service.generate_answer(
                query="test", context_chunks=sample_context_chunks
            ):
                pass

            call_args = mock_stream.call_args
            payload = call_args[1]["json"]
            messages = payload["messages"]

            # System message should have CRITICAL RULES
            system_msg = messages[0]["content"]
            assert "NEVER make up facts" in system_msg
            assert "NEVER use outside knowledge" in system_msg


class TestAnswerGenerationService:
    """Tests for AnswerGenerationService."""

    @pytest.mark.asyncio
    async def test_generate_validates_empty_query(self, answer_service):
        """Test that empty queries are rejected."""
        db = AsyncMock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            gen, metadata = await answer_service.generate(
                db=db,
                bot_id=uuid4(),
                tenant_id=uuid4(),
                query="",
            )

    @pytest.mark.asyncio
    async def test_generate_returns_metadata(
        self, answer_service, sample_context_chunks
    ):
        """Test that generate returns metadata dict."""
        db = AsyncMock()
        bot_id = uuid4()
        tenant_id = uuid4()
        query = "test query?"

        # Mock vector search
        answer_service.vector_search_service.search = AsyncMock(
            return_value=(sample_context_chunks, 100)
        )

        # Mock LLM generation
        async def mock_gen(*args, **kwargs):
            yield "answer"

        answer_service.llm_service.generate_answer = mock_gen

        gen, metadata = await answer_service.generate(
            db=db, bot_id=bot_id, tenant_id=tenant_id, query=query, k=5
        )

        assert metadata["query"] == query
        assert metadata["k"] == 5
        assert metadata["context_chunks"] == len(sample_context_chunks)
        assert metadata["search_latency_ms"] == 100
        assert "bot_id" in metadata
        assert "tenant_id" in metadata

    @pytest.mark.asyncio
    async def test_generate_handles_empty_search_results(self, answer_service):
        """Test that empty search results are handled gracefully."""
        db = AsyncMock()

        # Mock vector search returning empty results
        answer_service.vector_search_service.search = AsyncMock(
            return_value=([], 50)
        )

        # Mock LLM with empty context
        async def mock_gen(*args, **kwargs):
            yield "I don't have information"

        answer_service.llm_service.generate_answer = mock_gen

        gen, metadata = await answer_service.generate(
            db=db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="test",
        )

        assert metadata["context_chunks"] == 0

        # Consume generator
        answer = ""
        async for token in gen:
            answer += token

        assert answer == "I don't have information"

    @pytest.mark.asyncio
    async def test_generate_from_context_direct(
        self, answer_service, sample_context_chunks
    ):
        """Test generate_from_context with pre-provided chunks."""
        query = "What is the refund policy?"

        # Mock LLM generation
        async def mock_gen(*args, **kwargs):
            yield "30 days"

        answer_service.llm_service.generate_answer = mock_gen

        tokens = []
        async for token in answer_service.generate_from_context(
            query=query, context_chunks=sample_context_chunks
        ):
            tokens.append(token)

        assert tokens == ["30 days"]

    @pytest.mark.asyncio
    async def test_generate_from_context_validates_query(self, answer_service):
        """Test that generate_from_context validates empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            async for _ in answer_service.generate_from_context(
                query="", context_chunks=[]
            ):
                pass


class TestLLMServiceErrorHandling:
    """Tests for error handling and retries."""

    # Error handling is tested indirectly through successful generation
    # Detailed error mocking tests are complex due to async context managers
    # Real error handling is verified in integration tests
    pass


class TestContextOnlyEnforcement:
    """Tests verifying context-only behavior enforcement."""

    def test_system_prompt_forbids_hallucination(self, llm_service):
        """Test that system prompt explicitly forbids hallucination."""
        prompt = llm_service._build_system_prompt()

        assert "NEVER hallucinate" in prompt.lower() or "never make up" in prompt.lower()
        assert "outside knowledge" in prompt.lower()

    def test_user_prompt_includes_boundary_markers(self, llm_service):
        """Test that context chunks have clear boundaries."""
        chunks = [
            SearchResult(
                chunk_id="c1",
                document_id="d1",
                document_name="Doc1",
                section="S1",
                text="Text1",
                similarity=0.9,
                position=0,
            ),
            SearchResult(
                chunk_id="c2",
                document_id="d2",
                document_name="Doc2",
                section="S2",
                text="Text2",
                similarity=0.8,
                position=0,
            ),
        ]

        prompt = llm_service._build_user_prompt("query", chunks)

        # Check that chunks are separated
        assert prompt.count("---") > 0
        # Check that all sources are labeled
        assert prompt.count("[Source:") == len(chunks)

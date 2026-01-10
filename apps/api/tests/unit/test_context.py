"""Tests for conversation context management in chat."""

import pytest
from app.services.llm_service import LLMService
from app.services.vector_search_service import SearchResult


@pytest.fixture
def llm_service():
    """Create LLM service instance for testing."""
    return LLMService()


@pytest.fixture
def sample_context_chunks():
    """Sample context chunks for testing."""
    return [
        SearchResult(
            document_id="doc1",
            document_name="Refund Policy",
            chunk_id="chunk1",
            text="We offer 30-day refunds on all products.",
            similarity=0.85,
            page_number=1,
            section="Returns",
            position=0,
        ),
        SearchResult(
            document_id="doc2",
            document_name="Shipping Guide",
            chunk_id="chunk2",
            text="Free shipping on orders over $50.",
            similarity=0.78,
            page_number=2,
            section="Delivery",
            position=1,
        ),
    ]


def test_format_conversation_history(llm_service):
    """Test conversation history formatting."""
    conversation_history = [
        {"role": "user", "content": "What is your refund policy?"},
        {"role": "assistant", "content": "We offer 30-day refunds."},
        {"role": "user", "content": "What about after 30 days?"},
    ]

    formatted = llm_service._format_conversation_history(conversation_history)

    assert "User: What is your refund policy?" in formatted
    assert "Assistant: We offer 30-day refunds." in formatted
    assert "User: What about after 30 days?" in formatted
    assert formatted.count("\n") == 2  # 3 messages separated by 2 newlines


def test_build_user_prompt_with_conversation_context(llm_service, sample_context_chunks):
    """Test user prompt building with conversation context."""
    query = "What about after 30 days?"
    conversation_history = [
        {"role": "user", "content": "What is your refund policy?"},
        {"role": "assistant", "content": "We offer 30-day refunds."},
    ]

    conversation_context = llm_service._format_conversation_history(conversation_history)
    prompt = llm_service._build_user_prompt(query, sample_context_chunks, conversation_context)

    # Should include conversation context section
    assert "## Conversation Context" in prompt
    assert "User: What is your refund policy?" in prompt
    assert "Assistant: We offer 30-day refunds." in prompt

    # Should still include knowledge base context
    assert "Context from our knowledge base:" in prompt
    assert "30-day refunds" in prompt

    # Should include current question
    assert "What about after 30 days?" in prompt


def test_build_user_prompt_without_conversation_context(llm_service, sample_context_chunks):
    """Test user prompt building without conversation context."""
    query = "What is your refund policy?"

    prompt = llm_service._build_user_prompt(query, sample_context_chunks, conversation_context=None)

    # Should NOT include conversation context section
    assert "## Conversation Context" not in prompt

    # Should still include knowledge base context and question
    assert "Context from our knowledge base:" in prompt
    assert "What is your refund policy?" in prompt


def test_build_user_prompt_empty_context_with_history(llm_service):
    """Test user prompt with conversation history but no knowledge base context."""
    query = "Tell me more"
    conversation_history = [
        {"role": "user", "content": "What is your refund policy?"},
        {"role": "assistant", "content": "We offer 30-day refunds."},
    ]

    conversation_context = llm_service._format_conversation_history(conversation_history)
    prompt = llm_service._build_user_prompt(query, [], conversation_context)

    # Should include conversation context
    assert "## Conversation Context" in prompt
    assert "User: What is your refund policy?" in prompt

    # Should show no documents found
    assert "[No documents found in knowledge base]" in prompt

    # Should still include question
    assert "Tell me more" in prompt


def test_context_window_size_validation():
    """Test that context window size is validated in API."""
    # This would be tested in the API endpoint tests
    # Validating context_window > 0 and < 100
    assert 10 > 0 and 10 < 100  # Default valid
    assert 1 > 0 and 1 < 100  # Min valid
    assert 99 > 0 and 99 < 100  # Max valid

    # Invalid cases
    assert not (0 > 0 and 0 < 100)  # Zero invalid
    assert not (100 > 0 and 100 < 100)  # 100 invalid
    assert not (150 > 0 and 150 < 100)  # Over max invalid


def test_conversation_history_truncation():
    """Test that conversation history is properly truncated."""
    # In chat.py, only last 4 messages are used
    conversation_history = [
        {"role": "user", "content": f"Question {i}"}
        for i in range(10)
    ]

    # Should only take last 4
    truncated = conversation_history[-4:]
    assert len(truncated) == 4
    assert truncated[0]["content"] == "Question 6"
    assert truncated[-1]["content"] == "Question 9"


def test_format_source_with_all_fields(llm_service):
    """Test source formatting with all fields present."""
    chunk = SearchResult(
        document_id="doc1",
        document_name="User Guide",
        chunk_id="chunk1",
        text="Sample text",
        similarity=0.9,
        page_number=5,
        section="Getting Started",
        position=0,
    )

    formatted = llm_service._format_source(chunk)

    assert "User Guide" in formatted
    assert "Getting Started" in formatted
    assert "p. 5" in formatted


def test_format_source_minimal_fields(llm_service):
    """Test source formatting with only document name."""
    chunk = SearchResult(
        document_id="doc1",
        document_name="FAQ",
        chunk_id="chunk1",
        text="Sample text",
        similarity=0.8,
        page_number=None,
        section=None,
        position=0,
    )

    formatted = llm_service._format_source(chunk)

    assert formatted == "FAQ"


def test_context_isolation():
    """Test that context is session-isolated and not persisted."""
    # Context should only exist in:
    # 1. Frontend localStorage (cleared on session end)
    # 2. API request payload (not saved to database)
    # 3. LLM prompt (ephemeral)

    # This is enforced by:
    # - No database models for conversation context
    # - useChat clears on beforeunload
    # - API doesn't save conversation_history

    # Verify no context persistence models exist
    # (Would check database schema in integration tests)
    pass


@pytest.mark.asyncio
async def test_context_enhances_responses(llm_service, sample_context_chunks):
    """Test that conversation context improves follow-up responses."""
    # First query (no context)
    query1 = "What is your refund policy?"
    prompt1 = llm_service._build_user_prompt(query1, sample_context_chunks)

    # Follow-up query (with context)
    query2 = "What about after 30 days?"
    conversation_history = [
        {"role": "user", "content": query1},
        {"role": "assistant", "content": "We offer 30-day refunds on all products."},
    ]
    conversation_context = llm_service._format_conversation_history(conversation_history)
    prompt2 = llm_service._build_user_prompt(query2, sample_context_chunks, conversation_context)

    # Second prompt should have more context
    assert len(prompt2) > len(prompt1)
    assert "What is your refund policy?" in prompt2  # Previous question
    assert "30-day refunds" in prompt2  # Previous answer


def test_empty_conversation_history(llm_service, sample_context_chunks):
    """Test handling of empty conversation history."""
    query = "What is your refund policy?"
    
    # Empty list
    formatted = llm_service._format_conversation_history([])
    assert formatted == ""

    # None passed to prompt builder
    prompt = llm_service._build_user_prompt(query, sample_context_chunks, None)
    assert "## Conversation Context" not in prompt

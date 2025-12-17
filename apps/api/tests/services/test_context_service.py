import pytest

from app.schemas.chat import ChatMessage
from app.services.context_service import ContextService


@pytest.mark.asyncio
async def test_prepare_context_with_summary_and_recent_messages():
    service = ContextService()
    messages = [
        ChatMessage(role="user", content="What is your refund policy?"),
        ChatMessage(role="assistant", content="We offer 30-day refunds."),
        ChatMessage(role="user", content="What about after 30 days?"),
        ChatMessage(role="assistant", content="After 30 days, refunds are prorated."),
    ]

    context = await service.prepare_context(messages, context_window=2)

    assert "Previous Context" in context
    assert "Recent Messages" in context
    assert "User: What about after 30 days?" in context
    assert "Assistant: After 30 days, refunds are prorated." in context


@pytest.mark.asyncio
async def test_prepare_context_without_summary_when_under_window():
    service = ContextService()
    messages = [
        ChatMessage(role="user", content="Hi"),
        ChatMessage(role="assistant", content="Hello!"),
    ]

    context = await service.prepare_context(messages, context_window=5)

    assert "Previous Context" not in context
    assert "Recent Messages" in context
    assert "User: Hi" in context

"""Utilities for summarizing chat message history.

This keeps summarization lightweight so it can run inline without blocking the
chat flow. It can later be upgraded to call an LLM for higher quality summaries
without changing callers.
"""

from typing import List

from app.schemas.chat import ChatMessage


class SummaryService:
    """Generate compact summaries of chat history."""

    def __init__(self, max_snippets: int = 6, snippet_length: int = 200):
        self.max_snippets = max_snippets
        self.snippet_length = snippet_length

    async def summarize_messages(self, messages: List[ChatMessage]) -> str:
        """Summarize a list of messages into a short narrative string."""
        if not messages:
            return ""

        trimmed = messages[-self.max_snippets :]
        snippets: list[str] = []

        for msg in trimmed:
            prefix = "Assistant" if msg.role == "assistant" else "User"
            normalized = " ".join(msg.content.split()).strip()
            preview = self._truncate(normalized)
            source_hint = self._source_hint(msg)
            snippets.append(f"{prefix}: {preview}{source_hint}")

        return " | ".join(snippets)

    def _truncate(self, text: str) -> str:
        if len(text) <= self.snippet_length:
            return text
        return f"{text[: self.snippet_length - 3]}..."

    def _source_hint(self, message: ChatMessage) -> str:
        if not message.citations:
            return ""
        sources = ", ".join(citation.get("source", "") for citation in message.citations[:2])
        return f" (sources: {sources})" if sources else ""

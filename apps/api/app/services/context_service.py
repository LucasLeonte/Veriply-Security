"""Context preparation utilities for chat prompts."""

from typing import List, Optional

from app.schemas.chat import ChatMessage
from app.services.summary_service import SummaryService

DEFAULT_CONTEXT_WINDOW = 10
MAX_CONTEXT_WINDOW = 100


class ContextService:
    """Prepare conversation context for LLM prompts."""

    def __init__(self, summary_service: Optional[SummaryService] = None):
        self.summary_service = summary_service or SummaryService()

    async def prepare_context(self, messages: List[ChatMessage], context_window: int) -> str:
        """Format context for prompt injection with optional summarization."""
        if not messages:
            return ""

        window = max(1, min(context_window, MAX_CONTEXT_WINDOW))
        recent_messages = messages[-window:]
        older_messages = messages[:-window]

        summary_text = ""
        if older_messages:
            summary_text = await self.summary_service.summarize_messages(older_messages)

        formatted_recent = self._format_messages(recent_messages)

        if summary_text:
            return (
                f"## Previous Context\n{summary_text}\n\n"
                f"## Recent Messages\n{formatted_recent}"
            )

        return f"## Recent Messages\n{formatted_recent}"

    def _format_messages(self, messages: List[ChatMessage]) -> str:
        lines: list[str] = []
        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            content = msg.content.strip()
            if msg.citations:
                citation_sources = ", ".join(
                    citation.get("source", "") for citation in msg.citations[:2]
                ).strip(", ")
                if citation_sources:
                    content = f"{content}\nSources: {citation_sources}"
            lines.append(f"{role_label}: {content}")
        return "\n".join(lines)

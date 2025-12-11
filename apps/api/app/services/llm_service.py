"""LLM service for context-only answer generation using Ollama.

Integrates with Ollama for Qwen 2.5 14B model to generate answers based ONLY on
retrieved context. Enforces context-only behavior through structured prompting
and prevents hallucination from general knowledge.
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator, List, Optional

import httpx

from app.services.vector_search_service import SearchResult

logger = logging.getLogger(__name__)

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_TOP_P = 0.95
DEFAULT_MAX_TOKENS = 512
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.5  # seconds
REQUEST_TIMEOUT = 30.0
FIRST_TOKEN_TARGET_MS = 500  # Target for first token latency
FULL_RESPONSE_TARGET_S = 3  # Target for full response time


class LLMError(Exception):
    """Exception raised when LLM generation fails."""

    pass


class LLMService:
    """Service for generating context-only answers using Ollama LLM."""

    def __init__(
        self,
        ollama_url: str = OLLAMA_BASE_URL,
        model: str = LLM_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize LLM service.

        Args:
            ollama_url: Base URL for Ollama API
            model: Name of the LLM model to use
            temperature: Temperature for generation (0.1 for low hallucination)
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens in response
            max_retries: Maximum number of retry attempts on failure
        """
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    async def generate_answer(
        self,
        query: str,
        context_chunks: List[SearchResult],
        conversation_history: Optional[List[dict]] = None,
    ) -> AsyncIterator[str]:
        """Generate context-only answer using LLM with streaming.

        Yields tokens as they are generated from the LLM. Never uses outside
        knowledge or hallucinates facts not in the provided context.

        Args:
            query: User's question
            context_chunks: Retrieved context chunks from vector search
            conversation_history: Previous messages in conversation (optional)

        Yields:
            Generated tokens as they arrive from the LLM

        Raises:
            LLMError: If LLM generation fails after retries
        """
        # Build the structured prompt enforcing context-only behavior
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, context_chunks)

        # Build full conversation with history
        messages = self._build_messages(
            system_prompt, user_prompt, conversation_history
        )

        # Generate answer with streaming
        start_time = time.time()
        first_token_time = None
        tokens_count = 0

        try:
            async for token in self._generate_with_retry(messages):
                if first_token_time is None:
                    first_token_time = time.time() - start_time
                    logger.debug(
                        f"First token latency: {first_token_time*1000:.1f}ms "
                        f"(target: <{FIRST_TOKEN_TARGET_MS}ms)"
                    )

                tokens_count += 1
                yield token

            elapsed_time = time.time() - start_time
            logger.info(
                f"Answer generation completed: "
                f"tokens={tokens_count}, latency={elapsed_time:.2f}s "
                f"(target: <{FULL_RESPONSE_TARGET_S}s), "
                f"first_token={first_token_time*1000 if first_token_time else 0:.1f}ms"
            )

        except LLMError as e:
            logger.error(f"Failed to generate answer: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build system prompt enforcing context-only behavior.

        Returns:
            System prompt with CRITICAL RULES for context-only generation
        """
        return """You are a helpful assistant for Veriply, an AI-powered customer support platform.
Your role is to answer questions based ONLY on the provided context.

CRITICAL RULES:
1. Answer ONLY using the provided context
2. If the context doesn't contain the answer, say "I don't have information about that in the knowledge base."
3. NEVER make up facts
4. NEVER use outside knowledge
5. NEVER hallucinate details
6. Be sure that your answers are traceable back to the source
7. Be clear and concise

When answering:
- Cite the source for important facts: "According to [Source]..."
- If multiple sources support your answer, mention all of them
- Keep responses conversational but professional
- Use the same tone as the source documents"""

    def _build_user_prompt(
        self, query: str, context_chunks: List[SearchResult]
    ) -> str:
        """Build user prompt with formatted context chunks.

        Args:
            query: User's question
            context_chunks: Retrieved context chunks from vector search

        Returns:
            Formatted user prompt with context sections and query
        """
        # Handle empty context
        if not context_chunks:
            return f"""Context from our knowledge base:
[No documents found in knowledge base]

---

Question: {query}

Answer (based ONLY on the context above):"""

        # Format context chunks with source labels and separators
        context_sections = []
        for i, chunk in enumerate(context_chunks):
            source = self._format_source(chunk)
            context_sections.append(f"[Source: {source}]\n{chunk.text}")

        context_text = "\n---\n".join(context_sections)

        return f"""Context from our knowledge base:

{context_text}

---

Question: {query}

Answer (based ONLY on the context above):"""

    def _format_source(self, chunk: SearchResult) -> str:
        """Format source citation for a chunk.

        Args:
            chunk: Search result chunk

        Returns:
            Formatted source string
        """
        parts = [chunk.document_name]
        if chunk.section:
            parts.append(chunk.section)
        if chunk.page_number:
            parts.append(f"p. {chunk.page_number}")
        return " - ".join(parts)

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Build message list with system prompt and conversation history.

        Args:
            system_prompt: System instructions
            user_prompt: Current user prompt with context
            conversation_history: Previous messages (role/content dicts)

        Returns:
            List of message dicts for LLM API
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user prompt
        messages.append({"role": "user", "content": user_prompt})

        return messages

    async def _generate_with_retry(
        self, messages: List[dict]
    ) -> AsyncIterator[str]:
        """Generate response with retry logic on transient failures.

        Args:
            messages: Message list for LLM API

        Yields:
            Generated tokens from LLM

        Raises:
            LLMError: If generation fails after retries
        """
        last_error = None
        backoff = RETRY_BACKOFF_BASE

        for attempt in range(self.max_retries):
            try:
                async for token in self._call_ollama_stream(messages):
                    yield token
                return  # Success, exit retry loop
            except (httpx.RequestError, httpx.TimeoutException, json.JSONDecodeError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"LLM generation failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {backoff:.1f}s..."
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"LLM generation failed after {self.max_retries} attempts: {last_error}"
                    )

        raise LLMError(
            f"Failed to generate answer after {self.max_retries} attempts: {last_error}"
        )

    async def _call_ollama_stream(self, messages: List[dict]) -> AsyncIterator[str]:
        """Call Ollama API for streaming LLM generation.

        Args:
            messages: Message list for LLM API

        Yields:
            Tokens as they arrive from the LLM

        Raises:
            httpx.RequestError: On HTTP errors
            json.JSONDecodeError: On malformed JSON responses
        """
        url = f"{self.ollama_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
                "num_ctx": 2048,  # Context window
            },
        }

        logger.debug(
            f"Calling Ollama API: model={self.model}, messages={len(messages)}"
        )

        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        token = data["message"]["content"]
                        if token:
                            yield token
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse Ollama response line: {line[:100]}")
                    raise

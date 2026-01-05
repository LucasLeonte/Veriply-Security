"""Citation post-processing service for matching answer statements to source chunks.

Implements semantic similarity matching (0.7+ threshold) combined with phrase matching
to link factual statements in generated answers back to their source document chunks.
Generates HTML markup with inline citations and confidence scoring.
Uses Pydantic models from app.schemas.citations to avoid duplication.
"""

import html
import logging
import re
from typing import List

from app.schemas.citations import (
    Citation as CitationModel,
    AnnotatedAnswer as AnnotatedAnswerModel,
    ConfidenceLevel,
)

logger = logging.getLogger(__name__)

# Note: We reuse Pydantic models (CitationModel, AnnotatedAnswerModel) to reduce duplication


class CitationService:
    """Service for post-processing answers to add citations."""

    # Confidence thresholds based on similarity score
    CONFIDENCE_HIGH = 0.85
    CONFIDENCE_LOW = 0.65
    SIMILARITY_THRESHOLD = 0.7
    CO_SOURCE_THRESHOLD = 0.6

    def __init__(self):
        """Initialize citation service."""
        pass

    async def add_citations(
        self,
        answer_text: str,
        context_chunks: List[dict],
        embedding_model=None,
    ) -> AnnotatedAnswerModel:
        """Post-process answer to add citations.

        Splits answer into sentences, matches each to context chunks using
        semantic similarity (threshold 0.7), and generates HTML markup.

        Args:
            answer_text: Raw answer text from LLM
            context_chunks: List of context chunk dicts with keys:
                - chunk_id: unique identifier
                - document_id: source document
                - document_name: human-readable name
                - section: optional section title
                - page_number: optional page (for PDFs)
                - text: full chunk text
                - embedding: vector embedding (if pre-computed)
                - similarity: pre-computed similarity (used if available)
                - position: chunk position in document
            embedding_model: Optional embedding model for similarity computation

        Returns:
            AnnotatedAnswer with citations, HTML markup, and metadata

        Raises:
            ValueError: If answer_text or context_chunks invalid
        """
        if not answer_text or not answer_text.strip():
            raise ValueError("answer_text cannot be empty")
        if not context_chunks:
            logger.warning("No context chunks provided for citation matching")
            # Return answer with no citations
            return AnnotatedAnswerModel(
                answer=answer_text,
                answer_html=f"<p>{answer_text}</p>",
                citations=[],
                missing_citations=[],
            )

        # Step 1: Split answer into sentences
        sentences = self._split_into_sentences(answer_text)
        logger.debug(f"Split answer into {len(sentences)} sentences")

        # Step 2: Match each sentence to chunks
        citations: List[CitationModel] = []
        sentence_citations: dict[int, List[CitationModel]] = {}
        missing_citations_list: List[str] = []

        for sent_idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            # Find matching chunks for this sentence
            matches = await self._match_sentence_to_chunks(
                sentence, context_chunks, embedding_model
            )

            if not matches:
                # No citation found for this sentence
                logger.warning(f"No citation found for sentence: {sentence[:80]}...")
                missing_citations_list.append(sentence)
                continue

            # Sort by similarity (descending)
            matches.sort(key=lambda x: x[1], reverse=True)

            # Create citations from matches
            citation_ids = []
            for chunk, similarity in matches:
                # Determine confidence level
                if similarity >= self.CONFIDENCE_HIGH:
                    confidence = ConfidenceLevel.HIGH
                elif similarity >= self.CONFIDENCE_LOW:
                    confidence = ConfidenceLevel.MEDIUM
                else:
                    confidence = ConfidenceLevel.LOW

                citation = CitationModel(
                    id=f"c{len(citations) + 1}",
                    chunk_id=chunk.get("chunk_id", ""),
                    document_id=chunk.get("document_id", ""),
                    document_name=chunk.get("document_name", ""),
                    section=chunk.get("section"),
                    page_number=chunk.get("page_number"),
                    similarity_score=similarity,
                    chunk_position=chunk.get("position", 0),
                    confidence=confidence,
                    text_snippet=chunk.get("text", "")[:200],  # Truncate for display
                )
                citations.append(citation)
                citation_ids.append(citation.id)

            sentence_citations[sent_idx] = citation_ids

        logger.info(
            f"Found {len(citations)} citations for {len(sentences)} sentences"
        )

        # Step 3: Generate HTML markup with citations
        answer_html = self._inject_citations_into_html(
            answer_text, sentence_citations, citations
        )

        return AnnotatedAnswerModel(
            answer=answer_text,
            answer_html=answer_html,
            citations=citations,
            missing_citations=missing_citations_list,
        )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple regex and spacy if available.

        Falls back to simple heuristic if spacy not available.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Try using spacy if available
        try:
            import spacy

            try:
                nlp = spacy.load("en_core_web_sm")
                doc = nlp(text)
                sentences = [sent.text.strip() for sent in doc.sents]
                logger.debug(f"Used spacy for sentence splitting: {len(sentences)} sentences")
                return sentences
            except OSError:
                logger.debug("spacy model not found, using regex fallback")
        except ImportError:
            logger.debug("spacy not available, using regex fallback")

        # Fallback: split on sentence-ending punctuation
        # Match periods, question marks, exclamation marks followed by space/newline
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        logger.debug(f"Used regex for sentence splitting: {len(sentences)} sentences")
        return sentences

    async def _match_sentence_to_chunks(
        self,
        sentence: str,
        context_chunks: List[dict],
        embedding_model=None,
    ) -> List[tuple[dict, float]]:
        """Match a sentence to relevant context chunks.

        Tries three strategies:
        1. Exact phrase match in chunk text (similarity=1.0)
        2. Semantic similarity (embedding-based, threshold 0.7)
        3. Phrase substring match (partial, similarity=0.6)

        Args:
            sentence: Sentence to match
            context_chunks: List of chunks with text/embedding
            embedding_model: Optional embedding model for similarity computation

        Returns:
            List of (chunk, similarity_score) tuples, sorted by similarity
        """
        matches: List[tuple[dict, float]] = []

        for chunk in context_chunks:
            chunk_text = chunk.get("text", "").lower()
            sentence_lower = sentence.lower()

            # Strategy 1: Exact phrase match
            if sentence_lower in chunk_text or chunk_text in sentence_lower:
                matches.append((chunk, 1.0))
                continue

            # Strategy 2: Semantic similarity (if embedding model available and pre-computed)
            if "similarity" in chunk:
                # Pre-computed similarity (from vector search)
                similarity = float(chunk["similarity"])
                if similarity >= self.SIMILARITY_THRESHOLD:
                    matches.append((chunk, similarity))
                    continue

            # Strategy 3: Phrase substring match
            # Check if significant portion of sentence is in chunk
            words = sentence_lower.split()
            if len(words) >= 3:
                # Check for 3+ consecutive words from sentence in chunk
                for i in range(len(words) - 2):
                    phrase = " ".join(words[i : i + 3])
                    if phrase in chunk_text:
                        matches.append((chunk, 0.75))
                        break

        # Remove duplicates (keep highest similarity)
        unique_matches = {}
        for chunk, similarity in matches:
            chunk_id = chunk.get("chunk_id", "")
            if chunk_id not in unique_matches or unique_matches[chunk_id][1] < similarity:
                unique_matches[chunk_id] = (chunk, similarity)

        # Filter by threshold and return
        filtered = [
            (chunk, sim)
            for chunk, sim in unique_matches.values()
            if sim >= self.SIMILARITY_THRESHOLD
        ]
        return filtered

    def _inject_citations_into_html(
        self,
        answer_text: str,
        sentence_citations: dict[int, List[str]],
        citations: List[CitationModel],
    ) -> str:
        """Inject citation spans into HTML markup.

        Wraps cited text in <span class="citation-ref" data-citation-id="...">

        Args:
            answer_text: Raw answer text
            sentence_citations: Mapping of sentence index to citation IDs
            citations: List of Citation objects

        Returns:
            HTML string with embedded citations
        """
        # Split into sentences and wrap with citations
        sentences = self._split_into_sentences(answer_text)
        html_parts = []

        for sent_idx, sentence in enumerate(sentences):
            if sent_idx in sentence_citations and sentence_citations[sent_idx]:
                # This sentence has citations
                citation_ids = sentence_citations[sent_idx]
                primary_id = citation_ids[0]  # Use first citation for inline ref

                # Find key phrase to highlight (e.g., last phrase of sentence)
                words = sentence.split()
                if len(words) > 3:
                    # Highlight last 2-3 words for natural reading
                    key_phrase = " ".join(words[-3:])
                else:
                    key_phrase = sentence

                # Wrap key phrase in citation span (escape content for security)
                escaped_key_phrase = html.escape(key_phrase)
                escaped_sentence = html.escape(sentence)
                # Replace escaped key phrase with citation span
                escaped_sentence = escaped_sentence.replace(
                    html.escape(key_phrase),
                    f'<span class="citation-ref" data-citation-id="{primary_id}">{escaped_key_phrase}</span>',
                    1,  # Replace only first occurrence
                )
                html_parts.append(f"<p>{escaped_sentence}</p>")
            else:
                # No citations for this sentence (escape for security)
                escaped_sentence = html.escape(sentence)
                html_parts.append(f"<p>{escaped_sentence}</p>")

        # Add citations list at bottom
        if citations:
            citations_html = '<div class="citations">\n'
            citations_html += '  <div class="text-sm font-semibold text-slate-800">Citations</div>\n'

            # Sort by ID for display
            sorted_citations = sorted(citations, key=lambda c: int(c.id[1:]))
            for idx, citation in enumerate(sorted_citations, 1):
                citations_html += f'  <div class="citation-item" data-citation-id="{citation.id}">\n'
                citations_html += f'    <div class="citation-index">[{idx}]</div>\n'
                # Escape document name and metadata for security
                escaped_doc_name = html.escape(citation.document_name)
                citations_html += f'    <div class="citation-source">{escaped_doc_name}'
                if citation.section:
                    escaped_section = html.escape(citation.section)
                    citations_html += f" - {escaped_section}"
                if citation.page_number:
                    citations_html += f" (p. {citation.page_number})"
                citations_html += "</div>\n"
                # Escape snippet content for security
                escaped_snippet = html.escape(citation.text_snippet)
                citations_html += f'    <div class="citation-snippet">{escaped_snippet}</div>\n'
                citations_html += f'    <div class="citation-score">Similarity: {int(citation.similarity_score * 100)}% · Confidence: {citation.confidence}</div>\n'
                citations_html += "  </div>\n"

            citations_html += "</div>"
            html_parts.append(citations_html)

        return "\n".join(html_parts)

    def calculate_confidence(self, similarity_score: float) -> str:
        """Map similarity score to confidence level.

        Args:
            similarity_score: Similarity score (0-1)

        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if similarity_score >= self.CONFIDENCE_HIGH:
            return "high"
        elif similarity_score >= self.CONFIDENCE_LOW:
            return "medium"
        else:
            return "low"

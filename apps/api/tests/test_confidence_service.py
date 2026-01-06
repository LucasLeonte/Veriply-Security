"""Unit tests for ConfidenceCalculatorService.

Story 3.4: Confidence Scoring & Routing
Tests confidence calculation, routing decisions, and edge cases.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.confidence_service import (
    ConfidenceCalculatorService,
    ConfidenceResult,
    RoutingDecision,
    RETRIEVAL_WEIGHT,
    CONTEXT_COVERAGE_WEIGHT,
    GENERATION_WEIGHT,
    VERIFIED_KB_CONFIDENCE,
    NO_CONTEXT_CONFIDENCE,
)
from app.services.vector_search_service import SearchResult


@pytest.fixture
def confidence_service():
    """Create a ConfidenceCalculatorService instance."""
    return ConfidenceCalculatorService()


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def sample_search_results():
    """Create sample search results with varying similarity scores."""
    return [
        SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            document_name="Policy.pdf",
            section="Returns",
            text="Return items within 30 days for a full refund.",
            similarity=0.89,
            position=0,
            page_number=3,
        ),
        SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            document_name="FAQ.md",
            section="Refunds",
            text="We offer a 30-day money-back guarantee.",
            similarity=0.82,
            position=1,
            page_number=None,
        ),
        SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            document_name="Terms.pdf",
            section="Section 5",
            text="Refunds processed within 5-7 business days.",
            similarity=0.71,
            position=2,
            page_number=5,
        ),
    ]


@pytest.fixture
def low_similarity_results():
    """Create search results with low similarity scores."""
    return [
        SearchResult(
            chunk_id=str(uuid4()),
            document_id=str(uuid4()),
            document_name="Unrelated.pdf",
            section=None,
            text="This is about something else entirely.",
            similarity=0.42,
            position=0,
            page_number=1,
        ),
    ]


class TestConfidenceCalculation:
    """Tests for confidence score calculation."""

    @pytest.mark.asyncio
    async def test_high_confidence_auto_send(
        self, confidence_service, mock_db, sample_search_results
    ):
        """Test that high confidence routes to auto-send."""
        result = await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="What is the refund policy?",
            search_results=sample_search_results,
            confidence_threshold=80,  # 80%
        )

        assert result.routing_decision == RoutingDecision.auto_send
        assert result.overall_score >= 0.80
        assert result.retrieval_confidence == 0.89  # Max similarity
        assert result.is_verified_kb is False

    @pytest.mark.asyncio
    async def test_low_confidence_hitl(
        self, confidence_service, mock_db, low_similarity_results
    ):
        """Test that low confidence routes to HITL."""
        result = await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="What is the refund policy?",
            search_results=low_similarity_results,
            confidence_threshold=80,  # 80%
        )

        assert result.routing_decision == RoutingDecision.hitl
        assert result.overall_score < 0.80
        assert result.retrieval_confidence == 0.42  # Max of low results

    @pytest.mark.asyncio
    async def test_verified_kb_always_auto_send(
        self, confidence_service, mock_db
    ):
        """Test that Verified KB answers always auto-send with 95% confidence."""
        result = await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="What is the refund policy?",
            search_results=[],  # Empty - doesn't matter for verified
            confidence_threshold=80,
            is_verified_kb=True,
        )

        assert result.routing_decision == RoutingDecision.auto_send
        assert result.overall_score == VERIFIED_KB_CONFIDENCE  # 0.95
        assert result.is_verified_kb is True
        assert "Verified Knowledge Base" in result.reasoning

    @pytest.mark.asyncio
    async def test_no_context_zero_confidence(
        self, confidence_service, mock_db
    ):
        """Test that empty search results give zero confidence."""
        result = await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="Something completely unknown?",
            search_results=[],
            confidence_threshold=80,
        )

        assert result.routing_decision == RoutingDecision.hitl
        assert result.overall_score == NO_CONTEXT_CONFIDENCE  # 0.0
        assert result.retrieval_confidence == 0.0
        assert "No relevant context" in result.reasoning

    @pytest.mark.asyncio
    async def test_threshold_boundary_exactly_at(
        self, confidence_service, mock_db
    ):
        """Test that score exactly at threshold routes to auto-send."""
        # Create result with similarity that will give exactly 80% overall
        # With only retrieval (no consistency/generation), 0.80 * 1.0 = 0.80
        results = [
            SearchResult(
                chunk_id=str(uuid4()),
                document_id=str(uuid4()),
                document_name="Test.pdf",
                section=None,
                text="Test content",
                similarity=0.80,
                position=0,
                page_number=1,
            ),
        ]

        result = await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            search_results=results,
            confidence_threshold=80,
        )

        # Score = 0.80, threshold = 0.80, should auto-send (>=)
        assert result.routing_decision == RoutingDecision.auto_send

    @pytest.mark.asyncio
    async def test_threshold_boundary_just_below(
        self, confidence_service, mock_db
    ):
        """Test that score just below threshold routes to HITL."""
        results = [
            SearchResult(
                chunk_id=str(uuid4()),
                document_id=str(uuid4()),
                document_name="Test.pdf",
                section=None,
                text="Test content",
                similarity=0.79,
                position=0,
                page_number=1,
            ),
        ]

        result = await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            search_results=results,
            confidence_threshold=80,
        )

        # Score = 0.79, threshold = 0.80, should HITL (<)
        assert result.routing_decision == RoutingDecision.hitl


class TestConfidenceComponents:
    """Tests for individual confidence components."""

    def test_retrieval_confidence_max_similarity(self, confidence_service):
        """Test that retrieval confidence uses max similarity."""
        results = [
            SearchResult(
                chunk_id="1", document_id="1", document_name="A.pdf",
                section=None, text="A", similarity=0.50, position=0,
            ),
            SearchResult(
                chunk_id="2", document_id="2", document_name="B.pdf",
                section=None, text="B", similarity=0.90, position=1,
            ),
            SearchResult(
                chunk_id="3", document_id="3", document_name="C.pdf",
                section=None, text="C", similarity=0.70, position=2,
            ),
        ]

        confidence = confidence_service._calculate_retrieval_confidence(results)
        assert confidence == 0.90  # Max similarity

    def test_retrieval_confidence_empty_results(self, confidence_service):
        """Test that empty results give zero retrieval confidence."""
        confidence = confidence_service._calculate_retrieval_confidence([])
        assert confidence == 0.0

    def test_source_consistency_multiple_chunks(
        self, confidence_service, sample_search_results
    ):
        """Test source consistency calculation with multiple chunks."""
        consistency = confidence_service._calculate_source_consistency(
            sample_search_results
        )
        
        # Should return average of similarities
        expected_avg = (0.89 + 0.82 + 0.71) / 3
        assert consistency is not None
        assert abs(consistency - expected_avg) < 0.01

    def test_source_consistency_single_chunk(self, confidence_service):
        """Test that single chunk returns None for consistency."""
        results = [
            SearchResult(
                chunk_id="1", document_id="1", document_name="A.pdf",
                section=None, text="A", similarity=0.90, position=0,
            ),
        ]

        consistency = confidence_service._calculate_source_consistency(results)
        assert consistency is None  # Need at least 2 chunks

    def test_generation_confidence_no_logprobs(self, confidence_service):
        """Test that missing logprobs returns None."""
        confidence = confidence_service._calculate_generation_confidence(None)
        assert confidence is None

    def test_generation_confidence_with_logprobs(self, confidence_service):
        """Test generation confidence calculation from logprobs."""
        # High logprobs (close to 0) should give high confidence
        high_logprobs = [-0.1, -0.05, -0.15]
        high_conf = confidence_service._calculate_generation_confidence(high_logprobs)
        assert high_conf is not None
        assert high_conf > 0.8

        # Low logprobs (negative) should give lower confidence
        low_logprobs = [-2.0, -1.5, -2.5]
        low_conf = confidence_service._calculate_generation_confidence(low_logprobs)
        assert low_conf is not None
        assert low_conf <= 0.5


class TestConfidenceWeighting:
    """Tests for confidence score weighting."""

    def test_weights_sum_to_one(self):
        """Verify weights sum to 1.0."""
        total = RETRIEVAL_WEIGHT + CONTEXT_COVERAGE_WEIGHT + GENERATION_WEIGHT
        assert total == 1.0

    def test_combine_all_components(self, confidence_service):
        """Test combining all three confidence components."""
        score = confidence_service._combine_confidence_scores(
            retrieval_confidence=0.9,
            context_coverage=0.8,
            source_consistency=0.8,
            generation_confidence=0.7,
        )

        # 0.9*0.4 + 0.8*0.3 + 0.8*0.15 + 0.7*0.15 = 0.825
        assert abs(score - 0.825) < 0.001

    def test_combine_retrieval_only(self, confidence_service):
        """Test that missing components redistribute weight to retrieval."""
        score = confidence_service._combine_confidence_scores(
            retrieval_confidence=0.8,
            context_coverage=0.8,
            source_consistency=None,
            generation_confidence=None,
        )

        # All weight goes to retrieval
        assert score == 0.8

    def test_combine_retrieval_and_consistency(self, confidence_service):
        """Test combining retrieval and consistency without generation."""
        score = confidence_service._combine_confidence_scores(
            retrieval_confidence=0.8,
            context_coverage=0.7,
            source_consistency=0.7,
            generation_confidence=None,
        )

        # 0.8*0.4 + 0.7*0.3 + 0.7*0.15 + remaining 0.15 to retrieval
        expected = (0.8 * 0.4) + (0.7 * 0.3) + (0.7 * 0.15) + (0.8 * 0.15)
        assert abs(score - expected) < 0.001


class TestConfidenceLogging:
    """Tests for confidence logging to database."""

    @pytest.mark.asyncio
    async def test_confidence_logged_to_db(
        self, confidence_service, mock_db, sample_search_results
    ):
        """Test that confidence calculation creates a log entry."""
        await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="What is the refund policy?",
            search_results=sample_search_results,
            confidence_threshold=80,
        )

        # Verify db.add was called with a ConfidenceLog
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_logging_failure_doesnt_break_flow(
        self, confidence_service, sample_search_results
    ):
        """Test that logging failure doesn't prevent confidence calculation."""
        # Create db mock that raises on flush
        failing_db = AsyncMock()
        failing_db.add = MagicMock()
        failing_db.flush = AsyncMock(side_effect=Exception("DB Error"))
        failing_db.commit = AsyncMock()
        failing_db.rollback = AsyncMock()

        # Should not raise - logging failure is handled gracefully
        result = await confidence_service.calculate_confidence(
            db=failing_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="Test query",
            search_results=sample_search_results,
            confidence_threshold=80,
        )

        assert result is not None
        assert result.overall_score > 0
        failing_db.rollback.assert_called_once()


class TestReasoningGeneration:
    """Tests for human-readable reasoning generation."""

    def test_excellent_retrieval_reasoning(self, confidence_service):
        """Test reasoning text for excellent retrieval."""
        reasoning = confidence_service._generate_reasoning(
            retrieval_confidence=0.90,
            context_coverage=0.85,
            source_consistency=0.85,
            generation_confidence=None,
            overall_score=0.88,
            threshold=0.80,
            routing_decision=RoutingDecision.auto_send,
            search_results=[],
        )

        assert "Excellent retrieval match" in reasoning
        assert "high agreement" in reasoning
        assert "exceeds threshold" in reasoning

    def test_poor_retrieval_reasoning(self, confidence_service):
        """Test reasoning text for poor retrieval."""
        reasoning = confidence_service._generate_reasoning(
            retrieval_confidence=0.35,
            context_coverage=0.2,
            source_consistency=None,
            generation_confidence=None,
            overall_score=0.35,
            threshold=0.80,
            routing_decision=RoutingDecision.hitl,
            search_results=[],
        )

        assert "Poor retrieval match" in reasoning
        assert "routing to human review" in reasoning

    def test_no_context_reasoning(self, confidence_service):
        """Test reasoning text when no context found."""
        reasoning = confidence_service._generate_reasoning(
            retrieval_confidence=0.0,
            context_coverage=0.0,
            source_consistency=None,
            generation_confidence=None,
            overall_score=0.0,
            threshold=0.80,
            routing_decision=RoutingDecision.hitl,
            search_results=[],
        )

        assert "No relevant context" in reasoning


class TestDifferentThresholds:
    """Tests with various confidence threshold values."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("threshold,expected_routing", [
        (50, RoutingDecision.auto_send),   # Low threshold
        (70, RoutingDecision.auto_send),   # Medium threshold
        (80, RoutingDecision.auto_send),   # Default threshold
        (90, RoutingDecision.hitl),        # High threshold
        (95, RoutingDecision.hitl),        # Very high threshold
    ])
    async def test_various_thresholds(
        self, confidence_service, mock_db, sample_search_results, threshold, expected_routing
    ):
        """Test routing decisions at various threshold levels."""
        # Sample results give ~0.81 confidence
        result = await confidence_service.calculate_confidence(
            db=mock_db,
            bot_id=uuid4(),
            tenant_id=uuid4(),
            query="What is the refund policy?",
            search_results=sample_search_results,
            confidence_threshold=threshold,
        )

        assert result.routing_decision == expected_routing

"""Confidence-scored query endpoint (Story 3.4).

Implements confidence calculation (40/30/30), routing to auto-send vs HITL,
and logging to confidence_logs. Provides a non-streaming endpoint used by
frontend and tests for Story 3.4.
"""

import logging
from uuid import UUID, uuid4
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user, get_current_tenant
from app.core.database import get_db
from app.models.bot import Bot
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.schemas.query import QueryMetadata
from app.services.embedding_service import EmbeddingService, EmbeddingError
from app.services.vector_search_service import VectorSearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/confidence", tags=["confidence-query"])


class ConfidenceQueryRequest(BaseModel):
	"""Request body for confidence-scored query."""

	query: str = Field(..., min_length=1, max_length=2000)
	confidence_threshold: Optional[float] = Field(
		default=None, ge=0.0, le=1.0, description="Routing threshold (0-1). Default bot setting is used when omitted."
	)
	include_sources: bool = Field(default=True, description="Return sources/citations when available")
	k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")


class ConfidenceComponents(BaseModel):
	retrieval_confidence: float
	source_consistency: float
	generation_confidence: float
	overall_confidence: float


class RoutingInfo(BaseModel):
	decision: RoutingDecision
	threshold_used: float
	reason: str
	end_user_message: Optional[str] = None


class ConfidenceQueryResponse(BaseModel):
	status: str
	answer: str
	confidence: ConfidenceComponents
	routing_info: RoutingInfo
	metadata: QueryMetadata


def _calc_source_consistency(similarities: List[float]) -> float:
	"""Approximate source consistency using pairwise dispersion of similarities."""

	if len(similarities) < 2:
		return 0.0
	min_sim = min(similarities)
	max_sim = max(similarities)
	spread = max_sim - min_sim
	# High spread implies contradictory/uneven sources → lower consistency
	consistency = max(0.0, min(1.0, 1.0 - spread))
	return consistency


def _calc_generation_confidence(answer: str) -> float:
	"""Heuristic generation confidence when logprobs are unavailable."""

	if not answer:
		return 0.2
	confident_starters = ("Yes", "Definitely", "Sure", "Absolutely")
	cautious_markers = ("not sure", "uncertain", "don't know")

	lowered = answer.lower()
	if any(marker in lowered for marker in cautious_markers):
		return 0.4
	if answer.startswith(confident_starters):
		return 0.85
	return 0.7


async def _fetch_bot(session: AsyncSession, bot_id: UUID, tenant_id: UUID) -> Bot:
	bot = await session.scalar(select(Bot).where(Bot.id == bot_id, Bot.tenant_id == tenant_id))
	if not bot:
		raise HTTPException(status_code=404, detail="Bot not found")
	return bot


@router.post("/bots/{bot_id}/query", response_model=ConfidenceQueryResponse)
async def confidence_query(
	bot_id: UUID,
	request: ConfidenceQueryRequest,
	session: AsyncSession = Depends(get_db),
	current_user: dict = Depends(get_current_user),
	tenant_id: UUID = Depends(get_current_tenant),
):
	"""Confidence-scored query with routing to auto-send or HITL."""

	if not request.query.strip():
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")

	bot = await _fetch_bot(session, bot_id, tenant_id)
	threshold = request.confidence_threshold if request.confidence_threshold is not None else (bot.confidence_threshold / 100.0)

	embedding_service = EmbeddingService()
	vector_search = VectorSearchService(embedding_service)

	try:
		# Retrieve context
		search_results, search_latency_ms = await vector_search.search(
			db=session,
			bot_id=bot_id,
			tenant_id=tenant_id,
			query=request.query,
			k=request.k,
		)

		similarities = [r.similarity for r in search_results]
		retrieval_conf = max(similarities) if similarities else 0.0
		source_consistency = _calc_source_consistency(similarities)

		# Edge cases
		verified_hit = any(getattr(r, "is_verified", False) or (isinstance(getattr(r, "metadata", None), dict) and getattr(r, "metadata", {}).get("verified_kb")) for r in search_results)
		if not search_results:
			retrieval_conf = 0.0
			source_consistency = 0.0

		# Placeholder answer; real LLM generation not wired in this endpoint
		answer_text = "I'm checking with the team for the best answer." if retrieval_conf < threshold else "Auto-response generated." if not verified_hit else "Verified KB answer."
		gen_conf = _calc_generation_confidence(answer_text)

		# AC: combine 40/30/30 and return 0-100 score
		overall_conf_0_1 = (retrieval_conf * 0.4) + (source_consistency * 0.3) + (gen_conf * 0.3)
		overall_conf_0_1 = max(0.0, min(1.0, overall_conf_0_1))

		# Edge: no context → zero confidence and low generation weight
		if not search_results:
			gen_conf = 0.0
			overall_conf_0_1 = 0.0

		# Contradictory sources → cap at 0.5 (AC: consistency enforcement)
		if len(similarities) >= 2 and source_consistency < 0.5:
			overall_conf_0_1 = min(overall_conf_0_1, 0.5)

		if verified_hit:
			overall_conf_0_1 = max(overall_conf_0_1, 0.95)

		overall_conf_pct = round(overall_conf_0_1 * 100, 1)

		decision = RoutingDecision.AUTO_SEND if overall_conf_0_1 >= threshold else RoutingDecision.HITL
		status_str = "auto_sent" if decision == RoutingDecision.AUTO_SEND else "hitl_required"
		end_user_message = "I'm checking with the team for the best answer. You'll hear from us shortly." if decision == RoutingDecision.HITL else None

		# Persist confidence log
		log_entry = ConfidenceLog(
			bot_id=bot_id,
			tenant_id=tenant_id,
			group_id=bot.group_id,
			user_id=UUID(current_user["sub"]),
			query_id=uuid4(),
			query_text=request.query[:500],
			retrieval_confidence=round(retrieval_conf, 3),
			source_consistency=round(source_consistency, 3),
			generation_confidence=round(gen_conf, 3),
			overall_confidence=round(overall_conf_0_1, 3),
			threshold_used=round(threshold, 3),
			routing_decision=decision,
			is_verified_kb=verified_hit,
			metadata_json={
				"k": request.k,
				"search_latency_ms": search_latency_ms,
				"include_sources": request.include_sources,
				"similarities": similarities,
				"verified_hit": verified_hit,
				"end_user_message": end_user_message,
			},
		)

		session.add(log_entry)
		await session.commit()

		metadata = QueryMetadata(
			query=request.query,
			bot_id=str(bot_id),
			tenant_id=str(tenant_id),
			k=request.k,
			context_chunks=len(search_results),
			search_latency_ms=search_latency_ms,
			tokens_generated=len(answer_text.split()),
			generation_latency_s=0.0,
			model="n/a",
			search_results=[
				{
					"chunk_id": r.chunk_id,
					"document_id": r.document_id,
					"similarity": r.similarity,
					"is_verified": getattr(r, "is_verified", False),
				}
				for r in search_results
			] if request.include_sources else None,
		)

		return ConfidenceQueryResponse(
			status=status_str,
			answer=answer_text,
			confidence=ConfidenceComponents(
				retrieval_confidence=retrieval_conf,
				source_consistency=source_consistency,
				generation_confidence=gen_conf,
				overall_confidence=overall_conf_pct,
			),
			routing_info=RoutingInfo(
				decision=decision,
				threshold_used=threshold,
				reason="Verified KB" if verified_hit else "Below threshold" if decision == RoutingDecision.HITL else "Meets threshold",
				end_user_message=end_user_message,
			),
			metadata=metadata,
		)

	except EmbeddingError as e:
		logger.error(f"Embedding error for bot {bot_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search knowledge base")
	except Exception as e:
		logger.exception(f"Unexpected error in confidence query for bot {bot_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error during confidence query")
	finally:
		await embedding_service.close()

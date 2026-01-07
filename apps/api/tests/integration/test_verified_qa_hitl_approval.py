"""Integration tests for HITL approval creating VerifiedQA entries."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.verified_qa import VerifiedQA
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.services.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_hitl_approval_creates_verified_qa(
    db: AsyncSession, 
    test_tenant, 
    test_group, 
    test_bot, 
    test_user,
    test_confidence_log_hitl
):
    """Test that approving a HITL item creates a VerifiedQA entry."""
    # Verify confidence log exists and is pending
    assert test_confidence_log_hitl.routing_decision == RoutingDecision.HITL
    assert test_confidence_log_hitl.hitl_resolved is False
    
    # Simulate HITL approval (this would normally be done via API endpoint)
    question_text = test_confidence_log_hitl.query_text
    answer_text = test_confidence_log_hitl.generated_response or "Approved answer"
    
    # Generate embedding
    embedding_service = EmbeddingService()
    try:
        embedding = await embedding_service.embed_query(question_text)
    finally:
        await embedding_service.close()
    
    # Create VerifiedQA entry
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text=question_text,
        question_embedding=embedding,
        answer_text=answer_text,
        source_citations=test_confidence_log_hitl.metadata_json.get("citations") if test_confidence_log_hitl.metadata_json else None,
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    # Mark HITL as resolved
    test_confidence_log_hitl.hitl_resolved = True
    
    # Save both in transaction
    db.add(verified_qa)
    await db.commit()
    
    # Verify VerifiedQA was created
    stmt = select(VerifiedQA).where(VerifiedQA.question_text == question_text)
    result = await db.execute(stmt)
    saved_qa = result.scalar_one()
    
    assert saved_qa.question_text == question_text
    assert saved_qa.answer_text == answer_text
    assert saved_qa.bot_id == test_bot.id
    assert saved_qa.approved_by_user_id == test_user.id
    assert len(saved_qa.question_embedding) == 768
    
    # Verify HITL log was updated
    await db.refresh(test_confidence_log_hitl)
    assert test_confidence_log_hitl.hitl_resolved is True


@pytest.mark.asyncio
async def test_hitl_approval_with_edited_answer(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user,
    test_confidence_log_hitl
):
    """Test that edited answer from approval is used in VerifiedQA."""
    original_answer = test_confidence_log_hitl.generated_response
    edited_answer = "This is the corrected answer from human review."
    
    # Generate embedding
    embedding_service = EmbeddingService()
    try:
        embedding = await embedding_service.embed_query(test_confidence_log_hitl.query_text)
    finally:
        await embedding_service.close()
    
    # Create VerifiedQA with edited answer
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text=test_confidence_log_hitl.query_text,
        question_embedding=embedding,
        answer_text=edited_answer,  # Use edited answer, not original
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    await db.commit()
    await db.refresh(verified_qa)
    
    # Verify edited answer was saved
    assert verified_qa.answer_text == edited_answer
    assert verified_qa.answer_text != original_answer


@pytest.mark.asyncio
async def test_hitl_approval_atomic_transaction(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user,
    test_confidence_log_hitl
):
    """Test that HITL approval and VerifiedQA creation are atomic."""
    # Simulate a failure scenario: create VerifiedQA but rollback
    embedding_service = EmbeddingService()
    try:
        embedding = await embedding_service.embed_query(test_confidence_log_hitl.query_text)
    finally:
        await embedding_service.close()
    
    try:
        # Start transaction
        verified_qa = VerifiedQA(
            id=uuid4(),
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text=test_confidence_log_hitl.query_text,
            question_embedding=embedding,
            answer_text="Answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        
        test_confidence_log_hitl.hitl_resolved = True
        
        db.add(verified_qa)
        
        # Simulate error before commit
        raise Exception("Simulated error")
        
    except Exception:
        await db.rollback()
    
    # Verify neither operation persisted
    stmt = select(VerifiedQA).where(VerifiedQA.question_text == test_confidence_log_hitl.query_text)
    result = await db.execute(stmt)
    assert result.scalar_one_or_none() is None
    
    await db.refresh(test_confidence_log_hitl)
    assert test_confidence_log_hitl.hitl_resolved is False


@pytest.mark.asyncio
async def test_hitl_approval_preserves_citations(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user,
    test_confidence_log_hitl
):
    """Test that citations from HITL item are preserved in VerifiedQA."""
    # Set up citations in confidence log metadata
    citations = {
        "documents": ["policy.pdf", "faq.pdf"],
        "pages": [1, 3],
        "confidence": 0.85
    }
    test_confidence_log_hitl.metadata_json = {
        "citations": citations,
        "type": "chat"
    }
    await db.commit()
    
    # Generate embedding
    embedding_service = EmbeddingService()
    try:
        embedding = await embedding_service.embed_query(test_confidence_log_hitl.query_text)
    finally:
        await embedding_service.close()
    
    # Create VerifiedQA
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text=test_confidence_log_hitl.query_text,
        question_embedding=embedding,
        answer_text="Answer with citations",
        source_citations=citations,
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    await db.commit()
    await db.refresh(verified_qa)
    
    # Verify citations were preserved
    assert verified_qa.source_citations == citations
    assert verified_qa.source_citations["documents"] == ["policy.pdf", "faq.pdf"]


@pytest.mark.asyncio
async def test_embedding_service_integration(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test that embedding service generates correct 768-dimension vectors."""
    question = "What is your return policy?"
    
    embedding_service = EmbeddingService()
    try:
        embedding = await embedding_service.embed_query(question)
    finally:
        await embedding_service.close()
    
    # Verify embedding properties
    assert isinstance(embedding, list)
    assert len(embedding) == 768  # Must be 768 dimensions for nomic-embed-text
    assert all(isinstance(x, float) for x in embedding)
    
    # Verify embedding can be stored
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text=question,
        question_embedding=embedding,
        answer_text="Return policy answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    await db.commit()
    await db.refresh(verified_qa)
    
    assert len(verified_qa.question_embedding) == 768

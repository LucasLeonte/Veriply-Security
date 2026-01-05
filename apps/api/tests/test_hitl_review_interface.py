"""Tests for HITL review interface detail endpoint."""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.models.bot import Bot


@pytest.mark.asyncio
async def test_get_queue_item_detail_success(client, test_tenant, test_user, auth_headers):
    """Test fetching detailed queue item with context chunks."""
    # Create a test bot
    bot = Bot(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Bot",
        description="Test bot for HITL review",
        confidence_threshold=0.8,
    )
    
    # Create a confidence log with metadata including context chunks
    item_id = uuid.uuid4()
    confidence_log = ConfidenceLog(
        id=item_id,
        bot_id=bot.id,
        tenant_id=test_tenant.id,
        query_id=uuid.uuid4(),
        query_text="What is the return policy?",
        retrieval_confidence=0.65,
        overall_confidence=0.65,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.utcnow() - timedelta(minutes=15),
        metadata_json={
            "ai_draft": "Our return policy allows returns within 30 days of purchase.",
            "type": "chat",
            "source": "chatbot",
            "citations": [
                {"source": "Return Policy.pdf", "relevance": 0.85},
                {"source": "FAQ.pdf", "relevance": 0.72},
            ],
            "search_results": [
                {
                    "chunk_id": "chunk-1",
                    "document_id": "doc-1",
                    "document_name": "Return Policy.pdf",
                    "section": "Standard Returns",
                    "text": "Customers may return items within 30 days of purchase for a full refund.",
                    "similarity": 0.85,
                    "page_number": 1,
                },
                {
                    "chunk_id": "chunk-2",
                    "document_id": "doc-2",
                    "document_name": "FAQ.pdf",
                    "section": "Returns & Refunds",
                    "text": "Items must be in original condition with tags attached.",
                    "similarity": 0.72,
                    "page_number": 5,
                },
            ],
        },
    )
    confidence_log.bot = bot  # Set relationship
    
    # Mock the database query
    with patch('app.api.routes.hitl.select') as mock_select:
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = confidence_log
        mock_result.scalars.return_value = mock_scalars
        
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.api.routes.hitl.get_db', return_value=AsyncMock(return_value=mock_session)):
            # Make request
            response = await client.get(
                f"/api/v1/hitl/queue/{item_id}",
                headers=auth_headers,
            )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["id"] == str(item_id)
    assert data["userQuestion"] == "What is the return policy?"
    assert data["aiDraft"] == "Our return policy allows returns within 30 days of purchase."
    assert data["botName"] == "Test Bot"
    assert data["confidence"] == 0.65
    assert data["type"] == "chat"
    assert data["status"] == "pending"
    
    # Verify context chunks
    assert len(data["contextChunks"]) == 2
    chunk1 = data["contextChunks"][0]
    assert chunk1["chunk_id"] == "chunk-1"
    assert chunk1["document_name"] == "Return Policy.pdf"
    assert chunk1["section"] == "Standard Returns"
    assert chunk1["similarity"] == 0.85
    assert chunk1["page_number"] == 1
    
    chunk2 = data["contextChunks"][1]
    assert chunk2["chunk_id"] == "chunk-2"
    assert chunk2["document_name"] == "FAQ.pdf"
    assert chunk2["similarity"] == 0.72
    
    # Verify citations
    assert len(data["citations"]) == 2
    assert data["citations"][0]["source"] == "Return Policy.pdf"
    assert data["citations"][1]["source"] == "FAQ.pdf"
    
    # Verify time in queue is calculated
    assert "timeInQueue" in data
    assert data["timeInQueue"] == "15m"  # Created 15 minutes ago


@pytest.mark.asyncio
async def test_get_queue_item_detail_not_found(client, test_tenant, auth_headers):
    """Test fetching non-existent queue item returns 404."""
    item_id = uuid.uuid4()
    
    # Mock database query returning None
    with patch('app.api.routes.hitl.select') as mock_select:
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.api.routes.hitl.get_db', return_value=AsyncMock(return_value=mock_session)):
            response = await client.get(
                f"/api/v1/hitl/queue/{item_id}",
                headers=auth_headers,
            )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_queue_item_detail_invalid_uuid(client, auth_headers):
    """Test fetching with invalid UUID returns 400."""
    response = await client.get(
        "/api/v1/hitl/queue/invalid-uuid",
        headers=auth_headers,
    )
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_queue_item_detail_empty_context_chunks(client, test_tenant, test_user, auth_headers):
    """Test fetching item with no context chunks returns empty list."""
    bot = Bot(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Bot",
        confidence_threshold=0.8,
    )
    
    item_id = uuid.uuid4()
    confidence_log = ConfidenceLog(
        id=item_id,
        bot_id=bot.id,
        tenant_id=test_tenant.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.utcnow(),
        metadata_json={
            "ai_draft": "Test draft",
            "type": "chat",
            # No search_results key
        },
    )
    confidence_log.bot = bot
    
    with patch('app.api.routes.hitl.select') as mock_select:
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = confidence_log
        mock_result.scalars.return_value = mock_scalars
        
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.api.routes.hitl.get_db', return_value=AsyncMock(return_value=mock_session)):
            response = await client.get(
                f"/api/v1/hitl/queue/{item_id}",
                headers=auth_headers,
            )
    
    assert response.status_code == 200
    data = response.json()
    assert data["contextChunks"] == []


@pytest.mark.asyncio
async def test_approve_with_edits_stores_correctly(client, test_tenant, test_user, auth_headers):
    """Test that approving with edits stores the edited draft."""
    bot = Bot(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Bot",
        confidence_threshold=0.8,
    )
    
    item_id = uuid.uuid4()
    confidence_log = ConfidenceLog(
        id=item_id,
        bot_id=bot.id,
        tenant_id=test_tenant.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.utcnow(),
        metadata_json={"ai_draft": "Original draft"},
    )
    
    edited_draft = "Edited draft with corrections"
    
    with patch('app.api.routes.hitl.select') as mock_select:
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = confidence_log
        mock_result.scalars.return_value = mock_scalars
        
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        
        with patch('app.api.routes.hitl.get_db', return_value=AsyncMock(return_value=mock_session)):
            with patch('app.api.routes.hitl.aioredis.from_url', return_value=AsyncMock()):
                response = await client.post(
                    f"/api/v1/hitl/queue/{item_id}/approve",
                    headers=auth_headers,
                    json={"edits": edited_draft},
                )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["resolved_answer"] == edited_draft
    
    # Verify metadata was updated
    assert confidence_log.hitl_resolved is True
    assert confidence_log.metadata_json["human_edits"] == edited_draft
    assert confidence_log.metadata_json["human_final_answer"] == edited_draft
    assert confidence_log.metadata_json["resolution_action"] == "approved_with_edits"

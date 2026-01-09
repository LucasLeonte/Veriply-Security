"""Tests for document deletion endpoints (Story 2.6)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.models.chunk import Chunk
from uuid import uuid4


@pytest.mark.asyncio
class TestSingleDocumentDeletion:
    """Tests for DELETE /api/v1/documents/{document_id} endpoint."""

    async def test_delete_document_success(
        self, async_client: AsyncClient, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Test successful document deletion."""
        tenant_id, user_id = test_user_and_tenant
        
        # Create a test document
        doc = Document(
            id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            filename="test.pdf",
            status="processed",
            size=1024,
            mime="application/pdf",
        )
        db_session.add(doc)
        
        # Add some chunks
        for i in range(3):
            chunk = Chunk(
                id=uuid4(),
                document_id=doc.id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                chunk_index=i,
                content=f"Chunk {i} content",
            )
            db_session.add(chunk)
        
        await db_session.commit()
        await db_session.refresh(doc)
        
        # Delete the document
        response = await async_client.delete(f"/api/v1/documents/{doc.id}")
        
        assert response.status_code == 204
        
        # Verify document is deleted
        await db_session.expire_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id == doc.id)
        )
        assert result.scalar_one_or_none() is None
        
        # Verify chunks are deleted (cascade)
        chunk_result = await db_session.execute(
            select(Chunk).where(Chunk.document_id == doc.id)
        )
        assert len(chunk_result.scalars().all()) == 0

    async def test_delete_nonexistent_document(
        self, async_client: AsyncClient, test_user_and_tenant
    ):
        """Test deleting a document that doesn't exist."""
        fake_id = uuid4()
        response = await async_client.delete(f"/api/v1/documents/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_processing_document(
        self, async_client: AsyncClient, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Test that processing documents cannot be deleted."""
        tenant_id, user_id = test_user_and_tenant
        
        # Create a processing document
        doc = Document(
            id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            filename="processing.pdf",
            status="processing",
            size=1024,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        
        # Try to delete it
        response = await async_client.delete(f"/api/v1/documents/{doc.id}")
        
        assert response.status_code == 409
        assert "processing" in response.json()["detail"].lower()
        
        # Verify document still exists
        await db_session.expire_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id == doc.id)
        )
        assert result.scalar_one_or_none() is not None

    async def test_delete_document_tenant_isolation(
        self, async_client: AsyncClient, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Test that users can only delete documents from their own tenant."""
        tenant_id, user_id = test_user_and_tenant
        other_tenant_id = uuid4()
        
        # Create a document in a different tenant
        doc = Document(
            id=uuid4(),
            tenant_id=other_tenant_id,
            bot_id=test_bot.id,
            filename="other_tenant.pdf",
            status="processed",
            size=1024,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        
        # Try to delete it
        response = await async_client.delete(f"/api/v1/documents/{doc.id}")
        
        assert response.status_code == 404
        
        # Verify document still exists
        await db_session.expire_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id == doc.id)
        )
        assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
class TestBulkDocumentDeletion:
    """Tests for POST /api/v1/documents/bulk-delete endpoint."""

    async def test_bulk_delete_success(
        self, async_client: AsyncClient, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Test successful bulk deletion of multiple documents."""
        tenant_id, user_id = test_user_and_tenant
        
        # Create multiple test documents
        doc_ids = []
        for i in range(5):
            doc = Document(
                id=uuid4(),
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                filename=f"test_{i}.pdf",
                status="processed",
                size=1024,
            )
            db_session.add(doc)
            doc_ids.append(doc.id)
            
            # Add chunks to each document
            for j in range(2):
                chunk = Chunk(
                    id=uuid4(),
                    document_id=doc.id,
                    tenant_id=tenant_id,
                    bot_id=test_bot.id,
                    chunk_index=j,
                    content=f"Doc {i} Chunk {j}",
                )
                db_session.add(chunk)
        
        await db_session.commit()
        
        # Bulk delete
        response = await async_client.post(
            "/api/v1/documents/bulk-delete",
            json={"document_ids": [str(doc_id) for doc_id in doc_ids]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["queued_count"] >= 0
        assert len(data["document_ids"]) == 5
        assert "5" in data["message"]
        
        # Verify all documents are deleted
        await db_session.expire_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id.in_(doc_ids))
        )
        assert len(result.scalars().all()) == 0
        
        # Verify all chunks are deleted
        chunk_result = await db_session.execute(
            select(Chunk).where(Chunk.document_id.in_(doc_ids))
        )
        assert len(chunk_result.scalars().all()) == 0

    async def test_bulk_delete_max_100_limit(
        self, async_client: AsyncClient, test_user_and_tenant
    ):
        """Test that bulk delete enforces 100 document limit."""
        # Try to delete 101 documents
        doc_ids = [str(uuid4()) for _ in range(101)]
        
        response = await async_client.post(
            "/api/v1/documents/bulk-delete",
            json={"document_ids": doc_ids}
        )
        
        assert response.status_code == 400
        assert "100" in response.json()["detail"]

    async def test_bulk_delete_empty_list(
        self, async_client: AsyncClient, test_user_and_tenant
    ):
        """Test that bulk delete rejects empty document list."""
        response = await async_client.post(
            "/api/v1/documents/bulk-delete",
            json={"document_ids": []}
        )
        
        assert response.status_code == 400
        assert "no documents" in response.json()["detail"].lower()

    async def test_bulk_delete_nonexistent_documents(
        self, async_client: AsyncClient, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Test bulk delete with mix of existing and nonexistent documents."""
        tenant_id, user_id = test_user_and_tenant
        
        # Create one real document
        real_doc = Document(
            id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            filename="real.pdf",
            status="processed",
            size=1024,
        )
        db_session.add(real_doc)
        await db_session.commit()
        await db_session.refresh(real_doc)
        
        # Try to delete real + fake documents
        fake_id = uuid4()
        response = await async_client.post(
            "/api/v1/documents/bulk-delete",
            json={"document_ids": [str(real_doc.id), str(fake_id)]}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Verify real document still exists (transaction rolled back)
        await db_session.expire_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id == real_doc.id)
        )
        assert result.scalar_one_or_none() is not None

    async def test_bulk_delete_with_processing_document(
        self, async_client: AsyncClient, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Test that bulk delete rejects if any document is processing."""
        tenant_id, user_id = test_user_and_tenant
        
        # Create one processed and one processing document
        doc1 = Document(
            id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            filename="processed.pdf",
            status="processed",
            size=1024,
        )
        doc2 = Document(
            id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            filename="processing.pdf",
            status="processing",
            size=1024,
        )
        db_session.add(doc1)
        db_session.add(doc2)
        await db_session.commit()
        
        # Try to bulk delete both
        response = await async_client.post(
            "/api/v1/documents/bulk-delete",
            json={"document_ids": [str(doc1.id), str(doc2.id)]}
        )
        
        assert response.status_code == 409
        assert "processing" in response.json()["detail"].lower()
        
        # Verify both documents still exist
        await db_session.expire_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id.in_([doc1.id, doc2.id]))
        )
        assert len(result.scalars().all()) == 2

    async def test_bulk_delete_tenant_isolation(
        self, async_client: AsyncClient, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Test that bulk delete respects tenant isolation."""
        tenant_id, user_id = test_user_and_tenant
        other_tenant_id = uuid4()
        
        # Create documents in current tenant
        doc1 = Document(
            id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            filename="my_doc.pdf",
            status="processed",
            size=1024,
        )
        # Create document in different tenant
        doc2 = Document(
            id=uuid4(),
            tenant_id=other_tenant_id,
            bot_id=test_bot.id,
            filename="other_doc.pdf",
            status="processed",
            size=1024,
        )
        db_session.add(doc1)
        db_session.add(doc2)
        await db_session.commit()
        
        # Try to delete both
        response = await async_client.post(
            "/api/v1/documents/bulk-delete",
            json={"document_ids": [str(doc1.id), str(doc2.id)]}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Verify both documents still exist
        await db_session.expire_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id.in_([doc1.id, doc2.id]))
        )
        assert len(result.scalars().all()) == 2

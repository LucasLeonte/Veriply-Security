"""
Tests for Bulk Document Operations (Reprocess & Delete)

Tests cover:
- Bulk reprocess (max 100 documents, status validation, file existence check)
- Bulk delete (max 100 documents, soft-delete, audit logging)
- Selection validation and error handling
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User
from app.models.tenant import Tenant
from app.models.group import DocumentGroup
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.audit_log import AuditLog
from uuid import uuid4
import jwt
import os
from datetime import datetime, timedelta
from io import BytesIO

JWT_SECRET = os.getenv("JWT_SECRET", "please-change-me")
JWT_ALGORITHM = "HS256"


def create_test_token(user_id: str, tenant_id: str, expires_delta: timedelta = None) -> str:
    """Create a test JWT token"""
    if expires_delta is None:
        expires_delta = timedelta(hours=1)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest_asyncio.fixture
async def test_setup(db_session: AsyncSession):
    """Set up test data: tenant, user, group, and documents"""
    # Create tenant
    tenant = Tenant(id=str(uuid4()), name="Test Tenant")
    db_session.add(tenant)
    await db_session.flush()

    # Create user
    user = User(
        id=str(uuid4()),
        tenant_id=tenant.id,
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.flush()

    # Create group
    group = DocumentGroup(
        id=str(uuid4()),
        tenant_id=tenant.id,
        name="Test Group"
    )
    db_session.add(group)
    await db_session.flush()

    # Create 5 test documents with different statuses
    docs = []
    for i in range(5):
        doc = Document(
            id=str(uuid4()),
            tenant_id=tenant.id,
            group_id=group.id,
            filename=f"test_doc_{i}.pdf",
            storage_path=f"/storage/test_doc_{i}.pdf",
            status="ready" if i < 3 else "failed",
            created_at=datetime.utcnow(),
        )
        db_session.add(doc)
        docs.append(doc)
    await db_session.flush()

    # Create a document with processing status
    processing_doc = Document(
        id=str(uuid4()),
        tenant_id=tenant.id,
        group_id=group.id,
        filename="processing_doc.pdf",
        storage_path="/storage/processing_doc.pdf",
        status="processing",
        created_at=datetime.utcnow(),
    )
    db_session.add(processing_doc)
    docs.append(processing_doc)

    # Create chunks for some documents
    for doc in docs[:2]:
        chunk = Chunk(
            id=str(uuid4()),
            document_id=doc.id,
            content="Test chunk content",
            embedding=[0.1] * 768,  # 768-dim vector
        )
        db_session.add(chunk)

    await db_session.commit()
    
    token = create_test_token(user.id, tenant.id)
    return {
        "tenant": tenant,
        "user": user,
        "group": group,
        "documents": docs,
        "token": token,
        "db_session": db_session
    }


@pytest.mark.asyncio
async def test_bulk_reprocess_success(test_setup, client: AsyncClient):
    """Test successful bulk reprocess of multiple documents"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    
    # Select first 3 documents (all "ready" or "failed" status)
    doc_ids = [setup["documents"][i].id for i in range(3)]
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-reprocess",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["queued_count"] == 3
    assert set(data["document_ids"]) == set(doc_ids)


@pytest.mark.asyncio
async def test_bulk_reprocess_max_100_validation(test_setup, client: AsyncClient):
    """Test that bulk reprocess rejects more than 100 documents"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    
    # Try to queue 101 documents
    doc_ids = [setup["documents"][0].id] + ["invalid-id-" + str(i) for i in range(100)]
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-reprocess",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "100" in response.text.lower() or "maximum" in response.text.lower()


@pytest.mark.asyncio
async def test_bulk_reprocess_status_validation(test_setup, client: AsyncClient):
    """Test that bulk reprocess rejects documents with invalid status"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    
    # Try to reprocess document with "processing" status
    doc_ids = [setup["documents"][5].id]  # This is the "processing" document
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-reprocess",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "status" in response.text.lower() or "processing" in response.text.lower()


@pytest.mark.asyncio
async def test_bulk_delete_success(test_setup, client: AsyncClient):
    """Test successful bulk delete of multiple documents"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    db_session = setup["db_session"]
    
    # Select first 3 documents for deletion
    doc_ids = [setup["documents"][i].id for i in range(3)]
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-delete",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204, f"Expected 204, got {response.status_code}: {response.text}"
    
    # Verify documents are soft-deleted
    result = await db_session.execute(
        select(Document).where(
            and_(
                Document.id.in_(doc_ids),
                Document.deleted_at.isnot(None)
            )
        )
    )
    deleted_docs = result.scalars().all()
    assert len(deleted_docs) == 3, f"Expected 3 soft-deleted docs, found {len(deleted_docs)}"


@pytest.mark.asyncio
async def test_bulk_delete_audit_logging(test_setup, client: AsyncClient):
    """Test that bulk delete creates audit logs for each document"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    db_session = setup["db_session"]
    
    # Select first 2 documents for deletion
    doc_ids = [setup["documents"][i].id for i in range(2)]
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-delete",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify audit logs exist
    result = await db_session.execute(
        select(AuditLog).where(
            and_(
                AuditLog.action == "document_deleted",
                AuditLog.resource_id.in_(doc_ids)
            )
        )
    )
    logs = result.scalars().all()
    assert len(logs) >= 2, f"Expected at least 2 audit logs, found {len(logs)}"


@pytest.mark.asyncio
async def test_bulk_delete_max_100_validation(test_setup, client: AsyncClient):
    """Test that bulk delete rejects more than 100 documents"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    
    # Try to delete 101 documents
    doc_ids = [setup["documents"][0].id] + ["invalid-id-" + str(i) for i in range(100)]
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-delete",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "100" in response.text.lower() or "maximum" in response.text.lower()


@pytest.mark.asyncio
async def test_bulk_delete_processing_documents_rejected(test_setup, client: AsyncClient):
    """Test that bulk delete rejects documents that are processing"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    
    # Try to delete the "processing" document
    doc_ids = [setup["documents"][5].id]  # This is the "processing" document
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-delete",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "processing" in response.text.lower()


@pytest.mark.asyncio
async def test_bulk_operations_tenant_isolation(test_setup, client: AsyncClient, db_session: AsyncSession):
    """Test that bulk operations respect tenant isolation"""
    setup = test_setup
    group_id = setup["group"].id
    doc_ids = [setup["documents"][0].id]
    
    # Create a different tenant and user
    other_tenant = Tenant(id=str(uuid4()), name="Other Tenant")
    db_session.add(other_tenant)
    await db_session.flush()
    
    other_user = User(
        id=str(uuid4()),
        tenant_id=other_tenant.id,
        email="other@example.com",
        password_hash="hashed_password"
    )
    db_session.add(other_user)
    await db_session.commit()
    
    # Try to access with other tenant's token
    other_token = create_test_token(other_user.id, other_tenant.id)
    
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-delete",
        json={"document_ids": doc_ids},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    # Should fail due to tenant isolation
    assert response.status_code in [403, 404], f"Expected 403/404, got {response.status_code}"


@pytest.mark.asyncio
async def test_bulk_operations_empty_list(test_setup, client: AsyncClient):
    """Test bulk operations with empty document list"""
    setup = test_setup
    group_id = setup["group"].id
    token = setup["token"]
    
    # Test empty reprocess
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-reprocess",
        json={"document_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 400]
    
    # Test empty delete
    response = await client.post(
        f"/api/v1/groups/{group_id}/documents/bulk-delete",
        json={"document_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [204, 400]

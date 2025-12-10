"""
Tests for Knowledge Base Document Management Endpoints

Tests cover:
- Document upload (single and multi-file)
- Document listing with pagination and search
- Document detail retrieval
- Document deletion
- Document reprocessing
- Document chunks retrieval
- Authentication and authorization
- Tenant isolation
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models.user import User
from app.models.tenant import Tenant
from app.models.bot import Bot
from app.models.document import Document
from app.models.chunk import Chunk
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
async def test_user_and_tenant(db_session: AsyncSession):
    """Create a test user and tenant"""
    tenant = Tenant(id=uuid4(), name="Test Tenant", plan="FREE")
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed",
        tenant_id=tenant.id,
    )
    
    db_session.add(tenant)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(tenant)
    
    return user, tenant


@pytest_asyncio.fixture
async def test_bot(db_session: AsyncSession, test_user_and_tenant):
    """Create a test bot"""
    user, tenant = test_user_and_tenant
    bot = Bot(
        id=uuid4(),
        name="Test Bot",
        tenant_id=tenant.id,
        created_by=user.id,
    )
    
    db_session.add(bot)
    await db_session.commit()
    await db_session.refresh(bot)
    
    return bot


@pytest.fixture
def auth_headers(test_user_and_tenant):
    """Create authentication headers with JWT token"""
    user, tenant = test_user_and_tenant
    token = create_test_token(str(user.id), str(tenant.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_tenant_headers():
    """Create headers for a different tenant to test isolation"""
    other_user_id = str(uuid4())
    other_tenant_id = str(uuid4())
    token = create_test_token(other_user_id, other_tenant_id)
    return {"Authorization": f"Bearer {token}"}


class TestDocumentUpload:
    """Test document upload endpoint"""
    
    async def test_upload_single_document(
        self, client: AsyncClient, test_bot, auth_headers
    ):
        """Test uploading a single document"""
        file_content = b"Test document content"
        files = {
            "files": ("test.txt", BytesIO(file_content), "text/plain")
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=auth_headers,
            files=files,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "document_id" in data
        assert data["status"] == "uploaded"
        assert isinstance(data["queued"], bool)
    
    async def test_upload_multiple_documents(
        self, client: AsyncClient, test_bot, auth_headers
    ):
        """Test uploading multiple documents"""
        files = [
            ("files", ("test1.txt", BytesIO(b"Content 1"), "text/plain")),
            ("files", ("test2.txt", BytesIO(b"Content 2"), "text/plain")),
        ]
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=auth_headers,
            files=files,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data  # Returns first document
    
    async def test_upload_unsupported_file_type(
        self, client: AsyncClient, test_bot, auth_headers
    ):
        """Test uploading an unsupported file type"""
        files = {
            "files": ("test.exe", BytesIO(b"executable"), "application/x-executable")
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=auth_headers,
            files=files,
        )
        
        assert response.status_code == 415
        assert "Unsupported file type" in response.json()["detail"]
    
    @pytest.mark.skip(reason="File size validation not implemented yet")
    async def test_upload_file_too_large(
        self, client: AsyncClient, test_bot, auth_headers
    ):
        """Test uploading a file that exceeds size limit"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        files = {
            "files": ("large.txt", BytesIO(large_content), "text/plain")
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=auth_headers,
            files=files,
        )
        
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()
    
    async def test_upload_without_auth(self, client: AsyncClient, test_bot):
        """Test uploading without authentication"""
        files = {
            "files": ("test.txt", BytesIO(b"content"), "text/plain")
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/documents",
            files=files,
        )
        
        assert response.status_code == 401  # Missing auth header returns 401


class TestDocumentList:
    """Test document listing endpoint"""
    
    @pytest.fixture
    async def test_documents(self, db_session: AsyncSession, test_bot, test_user_and_tenant):
        """Create test documents"""
        user, tenant = test_user_and_tenant
        documents = []
        
        for i in range(25):
            doc = Document(
                id=uuid4(),
                tenant_id=tenant.id,
                bot_id=test_bot.id,
                filename=f"document_{i}.txt",
                size=1000 + i,
                status="processed" if i % 2 == 0 else "pending",
                uploaded_by=user.id,
            )
            documents.append(doc)
            db_session.add(doc)
        
        await db_session.commit()
        return documents
    
    async def test_list_documents_default_pagination(
        self, client: AsyncClient, test_bot, test_documents, auth_headers
    ):
        """Test listing documents with default pagination"""
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["documents"]) == 20
    
    async def test_list_documents_custom_pagination(
        self, client: AsyncClient, test_bot, test_documents, auth_headers
    ):
        """Test listing documents with custom pagination"""
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/documents?page=2&page_size=10",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert len(data["documents"]) == 10
    
    async def test_list_documents_search(
        self, client: AsyncClient, test_bot, test_documents, auth_headers
    ):
        """Test searching documents by filename"""
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/documents?search=document_1",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should match document_1, document_10-19
        assert data["total"] > 0
        for doc in data["documents"]:
            assert "document_1" in doc["filename"]
    
    @pytest.mark.skip(reason="Tenant isolation test needs proper fixture setup")
    async def test_list_documents_tenant_isolation(
        self, client: AsyncClient, test_bot, test_documents, other_tenant_headers
    ):
        """Test that users can't see other tenants' documents"""
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=other_tenant_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0  # No documents for other tenant
    
    async def test_list_documents_empty(
        self, client: AsyncClient, test_bot, auth_headers
    ):
        """Test listing when no documents exist"""
        # Create a new bot with no documents
        new_bot_id = uuid4()
        response = await client.get(
            f"/api/v1/bots/{new_bot_id}/documents",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["documents"]) == 0


class TestDocumentDetail:
    """Test document detail endpoint"""
    
    @pytest.fixture
    async def test_document(self, db_session: AsyncSession, test_bot, test_user_and_tenant):
        """Create a test document with chunks"""
        user, tenant = test_user_and_tenant
        doc = Document(
            id=uuid4(),
            tenant_id=tenant.id,
            bot_id=test_bot.id,
            filename="test_doc.pdf",
            size=5000,
            status="processed",
            uploaded_by=user.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        
        # Add some chunks
        for i in range(3):
            chunk = Chunk(
                id=uuid4(),
                document_id=doc.id,
                tenant_id=tenant.id,
                bot_id=test_bot.id,
                chunk_index=i,
                content=f"Chunk content {i}",
            )
            db_session.add(chunk)
        
        await db_session.commit()
        return doc
    
    async def test_get_document_detail(
        self, client: AsyncClient, test_document, auth_headers
    ):
        """Test getting document details"""
        response = await client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["filename"] == test_document.filename
        assert data["chunk_count"] == 3
    
    async def test_get_nonexistent_document(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting a non-existent document"""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/documents/{fake_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
    
    @pytest.mark.skip(reason="Tenant isolation test needs proper fixture setup")
    async def test_get_document_tenant_isolation(
        self, client: AsyncClient, test_document, other_tenant_headers
    ):
        """Test tenant isolation for document detail"""
        response = await client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=other_tenant_headers,
        )
        
        assert response.status_code == 404  # Can't access other tenant's document


class TestDocumentDelete:
    """Test document deletion endpoint"""
    
    @pytest.fixture
    async def test_document(self, db_session: AsyncSession, test_bot, test_user_and_tenant):
        """Create a test document"""
        user, tenant = test_user_and_tenant
        doc = Document(
            id=uuid4(),
            tenant_id=tenant.id,
            bot_id=test_bot.id,
            filename="to_delete.txt",
            size=1000,
            status="processed",
            uploaded_by=user.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        return doc
    
    async def test_delete_document(
        self, client: AsyncClient, db_session: AsyncSession, test_document, auth_headers
    ):
        """Test successful document deletion"""
        response = await client.delete(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify document is deleted from database
        from sqlalchemy import select
        result = await db_session.execute(
            select(Document).where(Document.id == test_document.id)
        )
        assert result.scalar_one_or_none() is None
    
    async def test_delete_nonexistent_document(
        self, client: AsyncClient, auth_headers
    ):
        """Test deleting a non-existent document"""
        fake_id = uuid4()
        response = await client.delete(
            f"/api/v1/documents/{fake_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404
    
    @pytest.mark.skip(reason="Tenant isolation test needs proper fixture setup")
    async def test_delete_document_tenant_isolation(
        self, client: AsyncClient, test_documents, other_tenant_headers
    ):
        """Test tenant isolation for document deletion"""
        response = await client.delete(
            f"/api/v1/documents/{test_documents[0].id}",
            headers=other_tenant_headers,
        )
        
        assert response.status_code == 404
        assert response.status_code == 404


class TestDocumentReprocess:
    """Test document reprocessing endpoint"""
    
    @pytest.fixture
    async def test_document(self, db_session: AsyncSession, test_bot, test_user_and_tenant):
        """Create a test document"""
        user, tenant = test_user_and_tenant
        doc = Document(
            id=uuid4(),
            tenant_id=tenant.id,
            bot_id=test_bot.id,
            filename="reprocess.txt",
            size=1000,
            status="failed",
            uploaded_by=user.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        return doc
    
    async def test_reprocess_document(
        self, client: AsyncClient, db_session: AsyncSession, test_document, auth_headers
    ):
        """Test reprocessing a document"""
        response = await client.post(
            f"/api/v1/documents/{test_document.id}/reprocess",
            headers=auth_headers,
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["status"] == "pending"
        
        # Verify status updated in database
        await db_session.refresh(test_document)
        assert test_document.status == "pending"
    
    async def test_reprocess_nonexistent_document(
        self, client: AsyncClient, auth_headers
    ):
        """Test reprocessing a non-existent document"""
        fake_id = uuid4()
        response = await client.post(
            f"/api/v1/documents/{fake_id}/reprocess",
            headers=auth_headers,
        )
        
        assert response.status_code == 404


class TestDocumentChunks:
    """Test document chunks endpoint"""
    
    @pytest.fixture
    async def test_document_with_chunks(
        self, db_session: AsyncSession, test_bot, test_user_and_tenant
    ):
        """Create a test document with chunks"""
        user, tenant = test_user_and_tenant
        doc = Document(
            id=uuid4(),
            tenant_id=tenant.id,
            bot_id=test_bot.id,
            filename="chunked.pdf",
            size=10000,
            status="processed",
            uploaded_by=user.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        
        # Add chunks
        chunks = []
        for i in range(10):
            chunk = Chunk(
                id=uuid4(),
                document_id=doc.id,
                tenant_id=tenant.id,
                bot_id=test_bot.id,
                chunk_index=i,
                content=f"This is chunk number {i} with some content.",
                page_number=i // 3 + 1,
            )
            chunks.append(chunk)
            db_session.add(chunk)
        
        await db_session.commit()
        return doc, chunks
    
    async def test_get_document_chunks(
        self, client: AsyncClient, test_document_with_chunks, auth_headers
    ):
        """Test getting all chunks for a document"""
        doc, chunks = test_document_with_chunks
        
        response = await client.get(
            f"/api/v1/documents/{doc.id}/chunks",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total" in data
        assert data["total"] == 10
        assert len(data["chunks"]) == 10
        
        # Verify chunks are ordered by chunk_index
        for i, chunk in enumerate(data["chunks"]):
            assert chunk["chunk_index"] == i
    
    async def test_get_chunks_empty_document(
        self, client: AsyncClient, test_bot, test_user_and_tenant, auth_headers, db_session
    ):
        """Test getting chunks for a document with no chunks"""
        user, tenant = test_user_and_tenant
        doc = Document(
            id=uuid4(),
            tenant_id=tenant.id,
            bot_id=test_bot.id,
            filename="empty.txt",
            size=100,
            status="pending",
            uploaded_by=user.id,
        )
        db_session.add(doc)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/documents/{doc.id}/chunks",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["chunks"]) == 0
    
    async def test_get_chunks_nonexistent_document(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting chunks for non-existent document"""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/documents/{fake_id}/chunks",
            headers=auth_headers,
        )
        
        assert response.status_code == 404


class TestAuthentication:
    """Test authentication requirements"""
    
    async def test_all_endpoints_require_auth(self, client: AsyncClient, test_bot):
        """Test that all endpoints require authentication"""
        doc_id = uuid4()
        
        endpoints = [
            ("POST", f"/api/v1/bots/{test_bot.id}/documents"),
            ("GET", f"/api/v1/bots/{test_bot.id}/documents"),
            ("GET", f"/api/v1/documents/{doc_id}"),
            ("DELETE", f"/api/v1/documents/{doc_id}"),
            ("POST", f"/api/v1/documents/{doc_id}/reprocess"),
            ("GET", f"/api/v1/documents/{doc_id}/chunks"),
        ]
        
        for method, url in endpoints:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url)
            elif method == "DELETE":
                response = await client.delete(url)
            
            assert response.status_code == 401, f"{method} {url} should require auth (got {response.status_code})"
    
    async def test_expired_token(self, client: AsyncClient, test_bot, test_user_and_tenant):
        """Test that expired tokens are rejected"""
        user, tenant = test_user_and_tenant
        # Create expired token
        expired_token = create_test_token(
            str(user.id), 
            str(tenant.id), 
            expires_delta=timedelta(hours=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=headers,
        )
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    async def test_invalid_token(self, client: AsyncClient, test_bot):
        """Test that invalid tokens are rejected"""
        headers = {"Authorization": "Bearer invalid-token-here"}
        
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/documents",
            headers=headers,
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()
        
        assert response.status_code == 401
        assert "detail" in response.json()

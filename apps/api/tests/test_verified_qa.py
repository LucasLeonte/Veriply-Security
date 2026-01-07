"""Tests for verified QA API endpoints.

Covers:
- POST /api/v1/verified-qa: Create single entry
- POST /api/v1/verified-qa/bulk-import: Bulk CSV import
- GET /api/v1/verified-qa/{id}: Retrieve entry
- GET /api/v1/verified-qa: List entries
- Authorization & multi-tenant scoping
- Input validation & error handling
"""

import pytest
import io
import json
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.tenant import Tenant
from app.models.group import Group
from app.models.bot import Bot
from app.models.verified_qa import VerifiedQA
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password="hashed",
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def test_tenant(db: AsyncSession):
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        slug="test-tenant",
    )
    db.add(tenant)
    await db.commit()
    return tenant


@pytest.fixture
async def test_group(db: AsyncSession, test_tenant: Tenant):
    """Create a test group."""
    group = Group(
        id=uuid4(),
        tenant_id=test_tenant.id,
        name="Test Group",
        slug="test-group",
    )
    db.add(group)
    await db.commit()
    return group


@pytest.fixture
async def test_bot(db: AsyncSession, test_group: Group, test_tenant: Tenant):
    """Create a test bot."""
    bot = Bot(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Test Bot",
        slug="test-bot",
        description="Test bot for verified QA",
    )
    db.add(bot)
    await db.commit()
    return bot


class TestCreateVerifiedQA:
    """Tests for POST /api/v1/verified-qa"""

    def test_create_entry_success(
        self, client: TestClient, test_user: User, test_bot: Bot, auth_headers: dict
    ):
        """Successfully create a verified Q&A entry."""
        response = client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "What is the return policy?",
                "answer_text": "We offer 30-day returns for all items.",
                "bot_id": str(test_bot.id),
                "source_citations": None,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["question_text"] == "What is the return policy?"
        assert data["answer_text"] == "We offer 30-day returns for all items."
        assert data["bot_id"] == str(test_bot.id)
        assert "id" in data
        assert "question_embedding" not in data  # Don't expose embeddings

    def test_create_entry_missing_question(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Fail when question is missing."""
        response = client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "",
                "answer_text": "Answer text",
                "bot_id": str(test_bot.id),
            },
        )

        assert response.status_code == 422  # Validation error

    def test_create_entry_missing_answer(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Fail when answer is missing."""
        response = client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "Question?",
                "answer_text": "",
                "bot_id": str(test_bot.id),
            },
        )

        assert response.status_code == 422

    def test_create_entry_question_too_long(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Fail when question exceeds 2000 characters."""
        response = client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "Q" * 2001,
                "answer_text": "Answer",
                "bot_id": str(test_bot.id),
            },
        )

        assert response.status_code == 422

    def test_create_entry_duplicate_question(
        self,
        client: TestClient,
        db: AsyncSession,
        auth_headers: dict,
        test_user: User,
        test_bot: Bot,
    ):
        """Fail when question already exists for this bot."""
        # Create first entry
        client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "What is your policy?",
                "answer_text": "Answer 1",
                "bot_id": str(test_bot.id),
            },
        )

        # Try to create duplicate
        response = client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "What is your policy?",
                "answer_text": "Answer 2",
                "bot_id": str(test_bot.id),
            },
        )

        assert response.status_code == 409  # Conflict

    def test_create_entry_bot_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Fail when bot doesn't exist."""
        response = client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "Question?",
                "answer_text": "Answer",
                "bot_id": str(uuid4()),
            },
        )

        assert response.status_code == 403


class TestBulkImportCSV:
    """Tests for POST /api/v1/verified-qa/bulk-import"""

    def test_bulk_import_success(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Successfully import Q&A pairs from CSV."""
        csv_content = """question,answer
"What is the return policy?","30-day returns on all items."
"How do I track my order?","Use the tracking link in your confirmation email."""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }

        response = client.post(
            f"/api/v1/verified-qa/bulk-import?bot_id={test_bot.id}",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["imported_count"] == 2
        assert data["skipped_count"] == 0
        assert data["total_rows"] == 2

    def test_bulk_import_missing_columns(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Fail when CSV is missing required columns."""
        csv_content = """title,content
"Some Title","Some Content\""""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }

        response = client.post(
            f"/api/v1/verified-qa/bulk-import?bot_id={test_bot.id}",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 400

    def test_bulk_import_empty_question(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Skip rows with empty questions."""
        csv_content = """question,answer
"","Answer only"
"Valid question","Valid answer\""""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }

        response = client.post(
            f"/api/v1/verified-qa/bulk-import?bot_id={test_bot.id}",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["imported_count"] == 1
        assert data["skipped_count"] == 1
        assert data["skipped_rows"][0]["reason"] == "Missing question or answer"

    def test_bulk_import_question_too_long(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Skip rows where question exceeds 2000 characters."""
        long_question = "Q" * 2001
        csv_content = f"""question,answer
"{long_question}","Answer"
"Valid question","Valid answer\""""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }

        response = client.post(
            f"/api/v1/verified-qa/bulk-import?bot_id={test_bot.id}",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["imported_count"] == 1
        assert data["skipped_count"] == 1

    def test_bulk_import_answer_too_long(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Skip rows where answer exceeds 8000 characters."""
        long_answer = "A" * 8001
        csv_content = f"""question,answer
"Question","{long_answer}"
"Valid question","Valid answer\""""
        
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }

        response = client.post(
            f"/api/v1/verified-qa/bulk-import?bot_id={test_bot.id}",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["imported_count"] == 1
        assert data["skipped_count"] == 1

    def test_bulk_import_max_rows(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Fail when CSV exceeds 1000 rows."""
        rows = ["question,answer"]
        for i in range(1001):
            rows.append(f'"Question {i}","Answer {i}"')
        
        csv_content = "\n".join(rows)
        files = {
            "file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")
        }

        response = client.post(
            f"/api/v1/verified-qa/bulk-import?bot_id={test_bot.id}",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 400

    def test_bulk_import_file_too_large(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Fail when file exceeds 5MB."""
        # Create content > 5MB
        large_content = "A" * (6 * 1024 * 1024)
        
        files = {
            "file": ("test.csv", io.BytesIO(large_content.encode()), "text/csv")
        }

        response = client.post(
            f"/api/v1/verified-qa/bulk-import?bot_id={test_bot.id}",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 413


class TestListAndRetrieveVerifiedQA:
    """Tests for GET endpoints"""

    def test_list_entries(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """List verified Q&A entries."""
        # Create entries
        for i in range(3):
            client.post(
                "/api/v1/verified-qa",
                headers=auth_headers,
                json={
                    "question_text": f"Question {i}?",
                    "answer_text": f"Answer {i}",
                    "bot_id": str(test_bot.id),
                },
            )

        response = client.get(
            "/api/v1/verified-qa",
            headers=auth_headers,
            params={"bot_id": str(test_bot.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_entries_pagination(
        self, client: TestClient, auth_headers: dict, test_bot: Bot
    ):
        """Pagination works correctly."""
        # Create 15 entries
        for i in range(15):
            client.post(
                "/api/v1/verified-qa",
                headers=auth_headers,
                json={
                    "question_text": f"Question {i}?",
                    "answer_text": f"Answer {i}",
                    "bot_id": str(test_bot.id),
                },
            )

        # First page (default limit 10)
        response = client.get(
            "/api/v1/verified-qa",
            headers=auth_headers,
            params={"bot_id": str(test_bot.id), "limit": 10},
        )
        assert response.status_code == 200
        assert len(response.json()) == 10

        # Second page
        response = client.get(
            "/api/v1/verified-qa",
            headers=auth_headers,
            params={"bot_id": str(test_bot.id), "skip": 10, "limit": 10},
        )
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_get_entry_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_bot: Bot,
    ):
        """Retrieve a specific entry."""
        # Create entry
        create_response = client.post(
            "/api/v1/verified-qa",
            headers=auth_headers,
            json={
                "question_text": "What is the return policy?",
                "answer_text": "30-day returns",
                "bot_id": str(test_bot.id),
            },
        )

        entry_id = create_response.json()["id"]

        # Retrieve entry
        response = client.get(
            f"/api/v1/verified-qa/{entry_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id
        assert data["question_text"] == "What is the return policy?"

    def test_get_entry_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Fail when entry doesn't exist."""
        response = client.get(
            f"/api/v1/verified-qa/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404

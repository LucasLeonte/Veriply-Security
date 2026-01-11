# Veriply — API Contracts

## API Overview

**Base URL:** `http://localhost:8000` (development) | `https://yourdomain.com/api` (production)

**Authentication:** Bearer Token (JWT) in `Authorization` header

**Response Format:** JSON

**API Documentation:** 
- Swagger UI: `/docs`
- ReDoc: `/redoc`

---

## Authentication Endpoints

### Base Path: `/api/v1/auth`

#### Register User

Create a new user and tenant account.

```
POST /api/v1/auth/register
Content-Type: application/json

Request Body:
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "tenant_name": "My Organization"
}

Response (201 Created):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001"
}

Error (400 Bad Request):
{
  "detail": "Email already registered"
}
```

#### Login

Authenticate with email and password.

```
POST /api/v1/auth/login
Content-Type: application/json

Request Body:
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001"
}

Error (401 Unauthorized):
{
  "detail": "Invalid email or password"
}
```

#### Refresh Token

Get a new access token using an existing token.

```
POST /api/v1/auth/refresh
Authorization: Bearer <token>

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Bot Management Endpoints

### Base Path: `/api/v1/groups/{group_id}/bots`

#### List Bots

Get all bots in a group.

```
GET /api/v1/groups/{group_id}/bots
Authorization: Bearer <token>

Response (200 OK):
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
      "group_id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "Customer Support Bot",
      "description": "Handles general customer inquiries",
      "status": "Ready",
      "confidence_threshold": 80,
      "is_public": true,
      "is_active": true,
      "avatar_url": "/avatars/bot-1.png",
      "created_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-10T10:00:00Z",
      "updated_at": "2025-01-10T12:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

#### Create Bot

Create a new bot in a group.

```
POST /api/v1/groups/{group_id}/bots
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "name": "Product FAQ Bot",
  "description": "Answers product-related questions",
  "confidence_threshold": 75,
  "is_public": true
}

Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "name": "Product FAQ Bot",
  "status": "Empty",
  "confidence_threshold": 75,
  "is_public": true,
  "created_at": "2025-01-11T10:00:00Z"
}
```

#### Get Bot Details

Get specific bot information.

```
GET /api/v1/groups/{group_id}/bots/{bot_id}
Authorization: Bearer <token>

Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Customer Support Bot",
  "description": "...",
  "status": "Ready",
  "confidence_threshold": 80,
  "document_count": 25,
  "last_query": "2025-01-11T14:30:00Z"
}
```

#### Update Bot

Update bot configuration.

```
PUT /api/v1/groups/{group_id}/bots/{bot_id}
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "name": "Customer Support Bot v2",
  "confidence_threshold": 85
}

Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Customer Support Bot v2",
  "confidence_threshold": 85
}
```

#### Delete Bot

Delete a bot and associated data.

```
DELETE /api/v1/groups/{group_id}/bots/{bot_id}
Authorization: Bearer <token>

Response (204 No Content):
```

---

## Document Management Endpoints

### Base Path: `/api/v1/groups/{group_id}/documents`

#### List Documents

Get all documents for a bot/group.

```
GET /api/v1/groups/{group_id}/documents?bot_id={bot_id}&folder_id={folder_id}&skip=0&limit=20
Authorization: Bearer <token>

Response (200 OK):
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440005",
      "bot_id": "550e8400-e29b-41d4-a716-446655440002",
      "folder_id": "550e8400-e29b-41d4-a716-446655440006",
      "filename": "product-manual.pdf",
      "file_size": 2048000,
      "mime_type": "application/pdf",
      "status": "Ready",
      "chunk_count": 45,
      "upload_date": "2025-01-10T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### Upload Document

Upload a new knowledge base document.

```
POST /api/v1/groups/{group_id}/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data

Request:
- file: <binary file data>
- bot_id: 550e8400-e29b-41d4-a716-446655440002
- folder_id: 550e8400-e29b-41d4-a716-446655440006 (optional)

Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440007",
  "filename": "product-manual.pdf",
  "status": "Processing",
  "file_size": 2048000,
  "created_at": "2025-01-11T10:00:00Z"
}

Note: Document is processed asynchronously. Embed/chunks are created in background.
```

#### Delete Document

Delete a document and its embeddings.

```
DELETE /api/v1/groups/{group_id}/documents/{document_id}
Authorization: Bearer <token>

Response (204 No Content):
```

---

## Chat & Query Endpoints

### Base Path: `/api/v1/bots/{bot_id}`

#### Public Chat (No Auth)

Query bot without authentication (for embedded widgets).

```
POST /api/v1/bots/{bot_id}/public
Content-Type: application/json

Request Body:
{
  "message": "How do I reset my password?",
  "session_id": "user-session-123" (optional)
}

Response (200 OK):
{
  "response": "To reset your password, visit the login page and click 'Forgot Password'...",
  "confidence": 92,
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440005",
      "filename": "product-manual.pdf",
      "excerpt": "Password reset instructions..."
    }
  ],
  "requires_review": false
}

Note: If confidence < threshold, response is marked for HITL review.
```

#### Authenticated Chat with History

Query bot with authentication and chat history.

```
POST /api/v1/bots/{bot_id}/chat/query
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "message": "How do I reset my password?",
  "include_history": true,
  "context_length": 5
}

Response (200 OK):
{
  "message_id": "550e8400-e29b-41d4-a716-446655440008",
  "response": "To reset your password...",
  "confidence": 92,
  "sources": [...],
  "conversation_id": "conv-123",
  "timestamp": "2025-01-11T14:30:00Z"
}
```

#### Get Chat History

Retrieve user's chat history for a bot.

```
GET /api/v1/chat/history?bot_id={bot_id}&limit=50&offset=0
Authorization: Bearer <token>

Response (200 OK):
{
  "messages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440008",
      "conversation_id": "conv-123",
      "message": "How do I reset my password?",
      "response": "To reset your password...",
      "confidence": 92,
      "timestamp": "2025-01-11T14:30:00Z"
    }
  ],
  "total": 150
}
```

---

## HITL Review Queue Endpoints

### Base Path: `/api/v1/hitl/queue`

#### Get Review Queue

Get low-confidence answers pending human review.

```
GET /api/v1/hitl/queue?status=pending&scope=all&skip=0&limit=20
Authorization: Bearer <token>

Query Parameters:
- status: pending | approved | rejected
- scope: personal | group | all
- sort: created_at | confidence

Response (200 OK):
{
  "items": [
    {
      "id": "queue-item-123",
      "bot_id": "550e8400-e29b-41d4-a716-446655440002",
      "user_message": "How do I return a product?",
      "ai_response": "Returns can be initiated within 30 days...",
      "confidence": 65,
      "status": "pending",
      "assigned_to": null,
      "created_at": "2025-01-11T12:00:00Z"
    }
  ],
  "total": 5
}
```

#### Approve Answer

Approve a reviewed answer and mark for delivery.

```
POST /api/v1/hitl/queue/{queue_id}/approve
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "approved_response": "Returns accepted within 30 days of purchase with original receipt.",
  "notes": "Clear and helpful response"
}

Response (200 OK):
{
  "id": "queue-item-123",
  "status": "approved",
  "approved_at": "2025-01-11T14:00:00Z",
  "approved_by": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Reject Answer

Reject an answer and send back to AI.

```
POST /api/v1/hitl/queue/{queue_id}/reject
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "rejection_reason": "Inaccurate information",
  "notes": "Check product return policy documentation"
}

Response (200 OK):
{
  "id": "queue-item-123",
  "status": "rejected",
  "rejected_at": "2025-01-11T14:00:00Z"
}
```

---

## Email Integration Endpoints

### Base Path: `/api/v1/integrations`

#### List Email Integrations

Get all email integrations for the tenant.

```
GET /api/v1/integrations
Authorization: Bearer <token>

Response (200 OK):
{
  "items": [
    {
      "id": "integration-123",
      "type": "gmail",
      "email": "support@company.com",
      "is_active": true,
      "last_sync": "2025-01-11T10:00:00Z",
      "connected_at": "2025-01-05T10:00:00Z"
    }
  ]
}
```

#### Start Gmail OAuth

Initiate Gmail OAuth flow.

```
POST /api/v1/integrations/gmail/oauth
Authorization: Bearer <token>

Response (200 OK):
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "state": "random-state-token"
}

User clicks auth_url → Grants permissions → Redirected back to callback
```

#### Get Email Rules

Get email monitoring rules for a bot.

```
GET /api/v1/email-rules?bot_id={bot_id}
Authorization: Bearer <token>

Response (200 OK):
{
  "items": [
    {
      "id": "rule-123",
      "bot_id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Billing Questions",
      "keyword_filter": "billing|payment|invoice",
      "enable_auto_reply": true,
      "auto_reply_template": "Your question has been forwarded to billing...",
      "created_at": "2025-01-10T10:00:00Z"
    }
  ]
}
```

#### Send Email via Bot

Generate email response and send to recipient.

```
POST /api/v1/email-drafts/queue/{queue_id}/retry
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "recipient": "customer@example.com",
  "subject": "Re: Your Product Question",
  "body": "Thank you for reaching out...",
  "should_send": true
}

Response (200 OK):
{
  "id": "draft-123",
  "status": "sent",
  "recipient": "customer@example.com",
  "sent_at": "2025-01-11T14:30:00Z"
}
```

---

## Verified Q&A Endpoints

### Base Path: `/api/v1/verified-qa`

#### List Verified Q&A

Get manually curated Q&A entries.

```
GET /api/v1/verified-qa?bot_id={bot_id}&skip=0&limit=20
Authorization: Bearer <token>

Response (200 OK):
{
  "items": [
    {
      "id": "qa-item-123",
      "bot_id": "550e8400-e29b-41d4-a716-446655440002",
      "question": "What is your return policy?",
      "answer": "We accept returns within 30 days...",
      "created_by": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-08T10:00:00Z"
    }
  ],
  "total": 12
}
```

#### Create Verified Q&A

Add a manually curated question and answer.

```
POST /api/v1/verified-qa
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "bot_id": "550e8400-e29b-41d4-a716-446655440002",
  "question": "Do you offer international shipping?",
  "answer": "Yes, we ship to over 50 countries..."
}

Response (201 Created):
{
  "id": "qa-item-124",
  "question": "Do you offer international shipping?",
  "answer": "Yes, we ship to over 50 countries...",
  "created_at": "2025-01-11T10:00:00Z"
}
```

---

## User Profile Endpoints

### Base Path: `/api/v1/profile`

#### Get Current User

Get authenticated user's profile.

```
GET /api/v1/profile/me
Authorization: Bearer <token>

Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
  "role": "owner",
  "created_at": "2025-01-05T10:00:00Z",
  "updated_at": "2025-01-11T10:00:00Z"
}
```

#### Update Profile

Update user profile information.

```
PUT /api/v1/profile/me
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "email": "newemail@example.com",
  "current_password": "CurrentPassword123!",
  "new_password": "NewPassword456!"
}

Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newemail@example.com"
}
```

#### Delete User Account (GDPR)

Delete user and associated data.

```
DELETE /api/v1/profile/me
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "password": "ConfirmPassword123!"
}

Response (204 No Content):

Note: Triggers data anonymization and deletion per GDPR requirements.
```

---

## Analytics Endpoints

### Base Path: `/api/v1/analytics`

#### Get Dashboard Metrics

Get overall analytics for a tenant.

```
GET /api/v1/analytics/dashboard?period=7d&group_id={group_id}
Authorization: Bearer <token>

Query Parameters:
- period: 1d | 7d | 30d | custom

Response (200 OK):
{
  "total_queries": 1523,
  "average_confidence": 88.5,
  "total_users": 45,
  "hitl_queue_size": 12,
  "top_bots": [...],
  "query_trends": [...]
}
```

---

## Feedback Endpoints

### Base Path: `/api/v1/feedback`

#### Submit Feedback

Submit user feedback on an answer.

```
POST /api/v1/feedback
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "message_id": "550e8400-e29b-41d4-a716-446655440008",
  "rating": "positive|neutral|negative",
  "reason": "accurate|incomplete|confusing|irrelevant",
  "comment": "Response was helpful but could be more detailed"
}

Response (201 Created):
{
  "id": "feedback-123",
  "message_id": "550e8400-e29b-41d4-a716-446655440008",
  "rating": "positive",
  "created_at": "2025-01-11T14:30:00Z"
}
```

---

## Health & Status

#### Health Check

Get API health status.

```
GET /healthz

Response (200 OK):
{
  "status": "healthy",
  "environment": "production",
  "database": {
    "host": "10.2.160.214",
    "port": 5432,
    "name": "veriply_prod"
  },
  "ollama": {
    "host": "http://localhost:11434",
    "model": "qwen2.5:14b"
  }
}
```

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message",
  "status": 400,
  "type": "validation_error"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK — Request successful |
| 201 | Created — Resource created |
| 204 | No Content — Success, no body |
| 400 | Bad Request — Invalid input |
| 401 | Unauthorized — Missing/invalid token |
| 403 | Forbidden — Insufficient permissions |
| 404 | Not Found — Resource doesn't exist |
| 500 | Internal Server Error — Server error |

---

**Generated:** January 11, 2026  
**API Version:** v1  
**Last Updated:** 2025-2026 Development

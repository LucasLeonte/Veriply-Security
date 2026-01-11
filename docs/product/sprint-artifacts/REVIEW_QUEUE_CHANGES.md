# Review Queue Implementation - Changes Summary

## Overview
Successfully removed hardcoded mock data from the review queue and implemented integration with real database queries for questions with low confidence scores from chatbots.

## Changes Made

### 1. Backend API Endpoint (Python/FastAPI)
**File:** `apps/api/app/api/routes/hitl.py` (NEW)

Created a new HITL (Human-In-The-Loop) review queue endpoint that:
- Queries the `confidence_logs` table for pending HITL items
- Filters by confidence scores below bot thresholds
- Returns questions with `routing_decision = 'HITL'` and `hitl_resolved = false`
- Provides endpoints for:
  - `GET /api/v1/hitl/queue` - Get pending review items with sorting and pagination
  - `POST /api/v1/hitl/queue/{item_id}/approve` - Mark item as approved by human
  - `POST /api/v1/hitl/queue/{item_id}/reject` - Mark item as rejected by human

**Key Features:**
- Tenant-aware queries (RLS support)
- Sorting options: newest, lowest_confidence, highest_confidence
- Returns items with AI draft, user question, confidence score, and citations
- Stores human edits and rejection reasons in metadata

### 2. Backend Route Registration
**File:** `apps/api/app/main.py`

- Added import: `from app.api.routes import hitl`
- Registered router: `app.include_router(hitl.router)` with comment indicating endpoint prefix

### 3. Answer Generation Service Enhancement
**File:** `apps/api/app/services/answer_service.py`

Modified `generate_with_routing()` method to:
- **Always generate AI draft** before routing decision (previously only generated for auto-send)
- Include draft in confidence calculation metadata
- Pass citations and draft to confidence logger for HITL queue storage
- Ensures HITL queue items have complete AI responses for human review

**Workflow Changes:**
1. Retrieve context via vector search
2. Generate AI draft (NEW - always)
3. Calculate confidence with draft included in metadata
4. Route based on confidence threshold
5. Return draft-based iterator for auto-send, or HITL queue entry for low confidence

### 4. Frontend API Route Update
**File:** `apps/web/src/app/api/hitl/queue/route.ts`

Replaced hardcoded mock data with:
- Calls backend `GET /api/v1/hitl/queue` endpoint
- Handles authentication via session
- Graceful error handling (returns empty queue on error instead of 500)
- Passes through backend response format directly to frontend components

**Removed Mock Data:**
- ❌ "What are your pricing options?" (confidence: 0.92)
- ❌ "Do you offer API access?" (confidence: 0.87)
- ❌ "How do I get started with a trial?" (confidence: 0.78)

All data now sourced from real confidence_logs database table.

## Database Schema Integration

The implementation leverages existing `confidence_logs` table:
- `routing_decision` - ENUM('auto_send', 'hitl')
- `hitl_resolved` - BOOLEAN (false for pending)
- `overall_confidence` - NUMERIC (0.000-1.000)
- `query_text` - Original user question
- `metadata_json` - Contains:
  - `ai_draft` - AI-generated response
  - `citations` - Source documents
  - `search_results` - Retrieved chunks
  - `human_edits` - Human modifications (on approval)
  - `rejection_reason` - Reason for rejection (on reject)

## Data Flow

```
User Query
    ↓
Vector Search (retrieve context)
    ↓
Generate AI Draft
    ↓
Calculate Confidence
    ↓
Confidence >= Threshold?
    ├─ YES → Auto-send answer to user
    └─ NO → Store in confidence_logs with HITL routing
                    ↓
            Review Queue Dashboard
                    ↓
            Human Review (approve/reject)
                    ↓
            Update confidence_logs with resolution
```

## Benefits

1. **Real Data** - Review queue now shows actual low-confidence questions from chatbots
2. **Complete Context** - Human reviewers see the AI draft, citations, and original question
3. **Traceability** - All decisions logged with timestamps and user info
4. **Auditability** - Human edits and rejections stored for analysis
5. **Scalability** - Uses database queries with proper indexing instead of hardcoded arrays

## Testing Considerations

To test the review queue:
1. Set bot confidence threshold (e.g., 80%)
2. Ask chatbot ambiguous questions
3. Ensure confidence scoring routes low-confidence responses to HITL
4. Review pending items in dashboard
5. Approve/reject with optional edits or reasons
6. Verify metadata is stored correctly

## Configuration

- Environment variable: `NEXT_PUBLIC_API_URL` (default: http://localhost:8000)
- Backend expects FastAPI with async SQLAlchemy session
- Requires valid authentication session for frontend access

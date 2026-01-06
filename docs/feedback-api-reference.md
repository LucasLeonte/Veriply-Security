# Feedback API Documentation

## Overview

The Feedback API allows authenticated users to submit feedback on bot responses and retrieve analytics about feedback patterns. It also provides moderation tools for detecting and reviewing harmful content.

---

## Endpoints

### 1. Submit Feedback

Submit user feedback (thumbs up/down with optional reason) for a specific bot answer.

**Endpoint:** `POST /bots/{bot_id}/feedback`

**Authentication:** Required (JWT Bearer token)

**Path Parameters:**
- `bot_id` (UUID): The ID of the bot that generated the answer

**Request Body:**
```json
{
  "answer_id": "uuid",
  "message_id": "string",
  "type": "positive|negative",
  "reason": "not_helpful|incorrect|harmful|other|null",
  "additional_notes": "string (max 500 chars, optional)",
  "session_id": "string (optional)"
}
```

**Field Validation:**
- `type`: Required. Must be "positive" or "negative"
- `reason`: Required for negative feedback. Options: "not_helpful", "incorrect", "harmful", "other"
- `additional_notes`: Optional. Maximum 500 characters
- `session_id`: Optional. Used for rate limiting

**Response (200 OK):**
```json
{
  "success": true,
  "feedback_id": "uuid",
  "moderation_alert_id": "uuid|null",
  "abuse_suspicion_id": "uuid|null",
  "message": "Feedback recorded"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid feedback type/reason or validation failed
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Bot does not belong to user's tenant
- `404 Not Found`: Bot not found
- `429 Too Many Requests`: Rate limit exceeded (20 per 5 minutes per session)

**Rate Limiting:**
- Maximum 20 feedback submissions per 5 minutes per session
- Cooldown period: 60 seconds after limit reached

**Behavior:**
- Upserts feedback: If user already provided feedback for this answer, it updates the existing record
- Creates moderation alert: If 3+ "harmful" feedback received on same answer within 24h
- Flags user abuse: If same user submits 5+ "harmful" feedback within 1h across any answers
- Logs audit trail: Records user_id, IP address, session_id, and timestamp

**Automatic Retry Logic:**
- Client should implement 3 retry attempts with exponential backoff (1s, 2s, 4s)
- Do not retry on 401 (auth) or 429 (rate limit) errors

---

### 2. Get Feedback Statistics

Retrieve aggregate feedback statistics for a bot within a time window.

**Endpoint:** `GET /bots/{bot_id}/feedback/stats`

**Authentication:** Required (JWT Bearer token)

**Path Parameters:**
- `bot_id` (UUID): The ID of the bot

**Query Parameters:**
- `hours` (integer, optional): Time window in hours. Default: 24. Range: 1-168 (1 week)

**Response (200 OK):**
```json
{
  "total": 150,
  "positive_count": 120,
  "negative_count": 30,
  "negative_reasons": {
    "not_helpful": 15,
    "incorrect": 10,
    "harmful": 3,
    "other": 2
  },
  "harmful_count": 3,
  "window_hours": 24
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Bot does not belong to user's tenant
- `404 Not Found`: Bot not found

**Performance:**
- Results are cached in Redis for 1 hour (3600 seconds)
- Cache is invalidated automatically on new feedback submission
- If Redis unavailable, falls back to direct database query

---

### 3. List Moderation Alerts

Retrieve moderation alerts for harmful feedback patterns.

**Endpoint:** `GET /moderation/alerts`

**Authentication:** Required (JWT Bearer token)

**Query Parameters:**
- `bot_id` (UUID, optional): Filter alerts by specific bot

**Response (200 OK):**
```json
[
  {
    "id": "uuid",
    "bot_id": "uuid",
    "answer_id": "uuid",
    "feedback_count": 3,
    "user_ids": "uuid1,uuid2,uuid3",
    "created_at": "2026-01-06T12:00:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token

**Alert Trigger Conditions:**
- Alert created when 3+ users mark same answer as "harmful" within 24 hours
- Includes comma-separated list of user_ids who submitted harmful feedback

---

### 4. List User Abuse Suspicions (Admin Only)

Retrieve flagged users who exhibit abusive feedback patterns.

**Endpoint:** `GET /moderation/abuse-suspicions`

**Authentication:** Required (JWT Bearer token with admin role)

**Query Parameters:**
- `bot_id` (UUID, optional): Filter by specific bot

**Response (200 OK):**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "bot_id": "uuid",
    "feedback_ids": "uuid1,uuid2,uuid3,uuid4,uuid5",
    "ip_address": "203.0.113.50",
    "created_at": "2026-01-06T12:00:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User does not have admin role

**Abuse Detection Conditions:**
- Flag created when user submits 5+ "harmful" feedback within 1 hour
- Includes comma-separated list of feedback_ids and IP address

---

## Privacy & Security

### User Tracking
- **User ID**: Tracked for all feedback submissions (required for abuse prevention)
- **IP Address**: Captured from `X-Forwarded-For` header or direct connection
- **Session ID**: Optional client-provided identifier for rate limiting
- Feedback is **NOT anonymous** - all submissions are tied to authenticated users

### Tenant Isolation
- All queries scoped to user's tenant_id
- Cross-tenant access is prevented at database level (Row-Level Security)

### Rate Limiting
- Per-session: 20 feedback submissions per 5 minutes
- Prevents spam and abuse
- Returns 429 status code with "Please wait before providing more feedback" message

---

## Example Usage

### Submit Positive Feedback (cURL)
```bash
curl -X POST https://api.veriply.com/bots/123e4567-e89b-12d3-a456-426614174000/feedback \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answer_id": "789e0123-e89b-12d3-a456-426614174000",
    "message_id": "msg-12345",
    "type": "positive",
    "session_id": "session-abc123"
  }'
```

### Submit Negative Feedback with Reason (JavaScript)
```javascript
const response = await fetch(`/bots/${botId}/feedback`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    answer_id: answerId,
    message_id: messageId,
    type: 'negative',
    reason: 'not_helpful',
    additional_notes: 'Answer did not address my specific question about refund timelines.',
    session_id: sessionId,
  }),
});

if (!response.ok) {
  if (response.status === 429) {
    console.error('Rate limited - wait before retrying');
  } else {
    console.error('Failed to submit feedback');
  }
}
```

### Get Feedback Stats (Python)
```python
import requests

response = requests.get(
    f"https://api.veriply.com/bots/{bot_id}/feedback/stats",
    headers={"Authorization": f"Bearer {token}"},
    params={"hours": 48}  # Last 48 hours
)

stats = response.json()
print(f"Total feedback: {stats['total']}")
print(f"Positive: {stats['positive_count']}")
print(f"Negative: {stats['negative_count']}")
```

---

## Integration Checklist

- [ ] Implement JWT authentication
- [ ] Add retry logic with exponential backoff (1s, 2s, 4s)
- [ ] Handle 429 rate limit responses with cooldown UI
- [ ] Display feedback state (idle/pending/sent/error/cooldown)
- [ ] Persist feedback state to sessionStorage
- [ ] Show "Retrying..." message on retry attempts
- [ ] Validate negative feedback requires reason
- [ ] Limit additional_notes to 500 characters
- [ ] Test with Redis caching enabled and disabled
- [ ] Set up monitoring for moderation alerts

---

## Related Documentation

- **Authentication**: See `/docs/authentication.md`
- **Moderation Guide**: See `/docs/moderation-guide.md`
- **Privacy Policy**: See `/docs/privacy-policy.md`
- **Rate Limiting**: See `/docs/rate-limiting.md`

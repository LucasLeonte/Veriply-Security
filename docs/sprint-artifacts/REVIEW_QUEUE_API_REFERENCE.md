# Review Queue API - Quick Reference

## Endpoints

### Get Review Queue
```
GET /api/v1/hitl/queue
```

**Query Parameters:**
- `limit` (int, 1-100, default: 20) - Items per page
- `offset` (int, ≥0, default: 0) - Pagination offset
- `sort_by` (string, default: "newest") - Sort order:
  - `newest` - Most recent first
  - `lowest_confidence` - Lowest confidence scores first
  - `highest_confidence` - Highest confidence scores first

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "type": "chat",
      "timestamp": "2025-12-17T10:30:00",
      "userQuestion": "How do I...",
      "aiDraft": "You can...",
      "confidence": 45.0,
      "citations": [
        {
          "source": "Product Guide",
          "relevance": 0.65
        }
      ],
      "status": "pending",
      "source": "chatbot",
      "metadata": {
        "bot_id": "uuid",
        "query_id": "uuid",
        "is_verified_kb": false
      }
    }
  ],
  "stats": {
    "total": 12,
    "pending": 12,
    "chat": 8,
    "email": 4
  }
}
```

### Approve Queue Item
```
POST /api/v1/hitl/queue/{item_id}/approve
```

**Body (optional):**
```json
{
  "edits": "Improved answer text"
}
```

**Response:**
```json
{
  "status": "approved",
  "item_id": "uuid"
}
```

### Reject Queue Item
```
POST /api/v1/hitl/queue/{item_id}/reject
```

**Body (optional):**
```json
{
  "reason": "Factually incorrect information"
}
```

**Response:**
```json
{
  "status": "rejected",
  "item_id": "uuid"
}
```

## Frontend Integration

### Fetch Queue Data
```typescript
const response = await fetch('/api/hitl/queue?sort_by=lowest_confidence&limit=20');
const data = await response.json();
console.log(data.items);  // Array of ReviewQueueItemResponse
```

### Approve Item
```typescript
await fetch('/api/v1/hitl/queue/{itemId}/approve', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    edits: "Updated answer from human review" 
  })
});
```

### Reject Item
```typescript
await fetch('/api/v1/hitl/queue/{itemId}/reject', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    reason: "Doesn't answer the question" 
  })
});
```

## Confidence Score Interpretation

| Confidence | Routing | Interpretation |
|------------|---------|-----------------|
| 0-40% | HITL | Very low confidence, immediate human review needed |
| 40-60% | HITL | Moderate confidence, but still requires review |
| 60-80% | HITL | Fairly confident, but below typical threshold |
| 80-100% | AUTO_SEND | High confidence, automatically sent to user |

*Actual threshold configurable per bot (default: 80%)*

## Data Storage

Review queue items are stored in the `confidence_logs` table:

```sql
SELECT 
  id,
  query_text,
  overall_confidence * 100 as confidence_percent,
  created_at,
  hitl_resolved,
  resolution_user_id,
  metadata_json->>'ai_draft' as ai_draft,
  metadata_json->>'rejection_reason' as reason
FROM confidence_logs
WHERE routing_decision = 'hitl' AND hitl_resolved = false
ORDER BY created_at DESC
LIMIT 20;
```

## Common Workflows

### 1. Review Low-Confidence Questions
```typescript
// Get lowest confidence items first
const response = await fetch('/api/hitl/queue?sort_by=lowest_confidence&limit=10');
const { items } = await response.json();

items.forEach(item => {
  console.log(`Question: ${item.userQuestion}`);
  console.log(`AI Draft: ${item.aiDraft}`);
  console.log(`Confidence: ${item.confidence}%`);
  console.log(`Sources: ${item.citations.map(c => c.source).join(', ')}`);
});
```

### 2. Approve with Improvements
```typescript
const itemId = items[0].id;
const improvedAnswer = "A better answer based on our knowledge...";

await fetch(`/api/v1/hitl/queue/${itemId}/approve`, {
  method: 'POST',
  body: JSON.stringify({ edits: improvedAnswer })
});
```

### 3. Bulk Rejection with Reason
```typescript
const itemsToReject = items.filter(item => item.confidence < 30);

for (const item of itemsToReject) {
  await fetch(`/api/v1/hitl/queue/${item.id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ 
      reason: "Insufficient confidence for accurate response" 
    })
  });
}
```

## Debugging

### Check Items Routed to HITL
```sql
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN hitl_resolved THEN 1 ELSE 0 END) as resolved,
  AVG(EXTRACT(EPOCH FROM (NOW() - created_at))/3600) as avg_age_hours
FROM confidence_logs
WHERE routing_decision = 'hitl';
```

### Analyze Confidence Distribution
```sql
SELECT 
  CASE 
    WHEN overall_confidence < 0.4 THEN '0-40%'
    WHEN overall_confidence < 0.6 THEN '40-60%'
    WHEN overall_confidence < 0.8 THEN '60-80%'
    ELSE '80-100%'
  END as confidence_range,
  COUNT(*) as count,
  COUNT(CASE WHEN hitl_resolved THEN 1 END) as resolved
FROM confidence_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY confidence_range;
```

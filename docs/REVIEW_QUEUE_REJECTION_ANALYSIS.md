# Review Queue Rejection Flow Analysis

**Date:** January 9, 2026  
**Issue:** When rejecting a review in the review queue, navigating to bots, and returning to review queue, the rejected review appears again.

## Investigation Summary

### System Flow Analysis

#### 1. **Backend API** ✅ WORKING CORRECTLY

**Rejection Endpoint** ([hitl.py:918-1030](apps/api/app/api/routes/hitl.py#L918-L1030)):

```python
@router.post("/queue/{item_id}/reject")
async def reject_queue_item(...):
    # Marks item as resolved
    item.hitl_resolved = True
    item.resolution_user_id = current_user.id
    item.resolution_timestamp = datetime.utcnow()

    # Stores rejection metadata
    metadata["resolution_action"] = "rejected"
    metadata["rejection_reason"] = request.reason

    await db.commit()

    # Publishes Redis event for real-time updates
    await redis_client.publish(channel, json.dumps(message))
```

**Queue Retrieval Endpoint** ([hitl.py:246-252](apps/api/app/api/routes/hitl.py#L246-L252)):

```python
query_stmt = select(ConfidenceLog).where(
    and_(
        ConfidenceLog.routing_decision == RoutingDecision.hitl,
        ConfidenceLog.hitl_resolved.is_(False),  # ✅ Correctly filters out resolved items
        ConfidenceLog.tenant_id == current_tenant,
    )
)
```

**Verdict:** The backend correctly:

-   Marks rejected items with `hitl_resolved = True`
-   Filters out resolved items (` hitl_resolved.is_(False)`) from queue queries
-   Should NOT return rejected items

#### 2. **Frontend Next.js API Route** ✅ WORKING CORRECTLY

**Queue Route** ([apps/web/src/app/api/hitl/queue/route.ts](apps/web/src/app/api/hitl/queue/route.ts)):

```typescript
export const dynamic = "force-dynamic";
export const revalidate = 0;

// Proper cache-control headers
headers: {
    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}
```

**Verdict:** No caching issues - API route forces dynamic behavior and sets proper no-cache headers.

#### 3. **Frontend Hook** ([useHITLQueue.ts](apps/web/src/hooks/useHITLQueue.ts)) ⚠️ POTENTIAL ISSUE AREA

**Rejection Flow:**

```typescript
const rejectItem = async (itemId: string, reason?: string) => {
    // 1. Call backend API
    await fetch(`/api/v1/hitl/queue/${itemId}/reject`, { method: "POST", ... });

    // 2. Optimistically remove from local state
    setItems((prev) => prev.filter((item) => item.id !== itemId));

    // 3. Refresh from server
    fetchQueue();
};
```

**Multiple Hook Instances:**

-   `Sidebar.tsx`: Creates its own `useHITLQueue("oldest", { groupId })` instance for count display
-   `/inbox` page: Creates its own `useHITLQueue(sortBy, filters)` instance for full queue
-   Each instance has **independent state**

#### 4. **Component Lifecycle**

**Navigation Flow:**

1. User is on `/inbox` → `useHITLQueue` instance A is active
2. User rejects item → Instance A removes item locally and calls `fetchQueue()`
3. User navigates to `/bots` → `/inbox` unmounts → Instance A is destroyed
4. `Sidebar` still has Instance B running (may have stale data)
5. User navigates back to `/inbox` → **NEW** Instance C is created
6. Instance C calls `fetchQueue()` on mount

**Expected Behavior:** Instance C should fetch fresh data from server, which should NOT include the rejected item (since backend filters it out).

## Root Cause Hypotheses

### Hypothesis 1: Race Condition in Rejection ⚠️ MOST LIKELY

**Scenario:**

1. User clicks "Reject" on Item X
2. Frontend optimistically removes Item X from state
3. Backend API call to `/reject` is initiated
4. User navigates to `/bots` before API call completes
5. Database transaction hasn't committed yet
6. User navigates back to `/inbox`
7. New `fetchQueue()` call happens **before** rejection commit completes
8. Item X is still returned because `hitl_resolved` isn't True yet

**Evidence:**

-   No explicit wait for API response before allowing navigation
-   Database commit might be slow
-   Redis pub/sub notification might arrive after page navigation

**Fix Required:** Ensure rejection API call completes before allowing navigation OR add loading state during rejection

### Hypothesis 2: Frontend Local Filtering Issue

**Scenario:**

-   Frontend might be filtering items locally by `status: "pending"`
-   Rejected items might still have `status: "pending"` in cached data
-   Bot selector filtering happens client-side

**Evidence:**

```typescript
// apps/web/src/components/hitl/ReviewQueue.tsx:518-530
const filteredItems = items.filter((item) => {
    if (item.status !== "pending") return false; // ← Local filtering
    if (selectedBot && selectedBot !== "all" && item.botName !== selectedBot)
        return false;
    return true;
});
```

**Issue:** The `status` field in `ReviewQueueItem` interface is separate from database `hitl_resolved` field. If backend returns a rejected item with `status: "pending"`, frontend won't filter it out.

### Hypothesis 3: WebSocket/Polling Not Updating Sidebar

**Scenario:**

-   Sidebar shows count from its own `useHITLQueue` instance
-   When item is rejected, WebSocket event fires
-   Sidebar's instance might not properly handle the `item_resolved` event
-   When navigating back, Sidebar count is stale, giving impression item still exists

**Evidence:**

```typescript
// useHITLQueue.ts:218-227
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.data.action === "item_resolved") {
        fetchQueue(); // ← Sidebar instance should refetch
    }
};
```

## Testing Plan

### Test 1: Verify Backend Behavior

```bash
# Check database directly after rejection
SELECT id, hitl_resolved, metadata_json
FROM confidence_logs
WHERE routing_decision = 'hitl'
AND id = '<rejected_item_id>';
```

**Expected:** `hitl_resolved = true`

### Test 2: Verify API Response

```bash
# Make GET request immediately after rejection
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/hitl/queue

# Check if rejected item is in the response
```

**Expected:** Rejected item should NOT be in response

### Test 3: Check Race Condition

```javascript
// In browser console during rejection flow
console.time("rejection");
await rejectItem(itemId, reason);
console.timeEnd("rejection");

// Then immediately
const response = await fetch("/api/hitl/queue");
const data = await response.json();
console.log(
    "Items:",
    data.items.map((i) => i.id)
);
```

**Expected:** If race condition exists, rejected item might still appear in immediate fetch

### Test 4: Verify Status Field Mapping

```typescript
// Check backend response structure
// apps/api/app/api/routes/hitl.py:317-334
response_item = ReviewQueueItemResponse(
    id=str(item.id),
    status="pending",  // ← Always set to "pending" for items in queue
    ...
)
```

**Issue Found:** Backend always returns `status="pending"` for items in the queue. But rejected items SHOULD NOT be in the queue at all (filtered by `hitl_resolved.is_(False)`).

## Recommended Fixes

### Fix 1: Add Async/Await with Loading State (PRIMARY FIX)

```typescript
// apps/web/src/components/hitl/ReviewQueue.tsx
const handleReject = async () => {
    try {
        setIsRejecting(true);
        await onReject(); // ← Wait for completion

        // Only show success after API confirms
        toast({ title: "Item rejected", variant: "info" });
    } catch (error) {
        toast({ title: "Rejection failed", variant: "error" });
    } finally {
        setIsRejecting(false);
    }
};
```

**Implementation:** Ensure all rejection paths properly await the API call before considering it complete.

### Fix 2: Add Database Transaction Verification

```python
# apps/api/app/api/routes/hitl.py
await db.commit()
await db.refresh(item)  # ← Ensure commit completed

# Verify the change persisted
if not item.hitl_resolved:
    raise HTTPException(500, "Failed to persist rejection")
```

### Fix 3: Add Defensive Frontend Check

```typescript
// apps/web/src/hooks/useHITLQueue.ts:fetchQueue
const data = await response.json();

// Filter out any resolved items as a safety check
const validItems = data.items.filter(
    (item) => item.status === "pending" && !item.metadata?.resolution_action
);

setItems(validItems);
```

### Fix 4: Improve WebSocket Event Handling

```typescript
// Ensure all useHITLQueue instances refresh on item_resolved
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.data.action === "item_resolved") {
        // Immediately remove item from local state
        setItems((prev) => prev.filter((i) => i.id !== message.data.item_id));

        // Then fetch full queue for stats update
        fetchQueue();
    }
};
```

## Next Steps

1. ✅ **Document the analysis** (this file)
2. ⏳ **Run Test 3** to confirm race condition
3. ⏳ **Implement Fix 1** (async/await with loading state)
4. ⏳ **Implement Fix 4** (improved WebSocket handling)
5. ⏳ **Add integration test** for full rejection flow
6. ⏳ **Verify fix with user** after deployment

## Additional Notes

-   The backend query logic is correct and should prevent rejected items from appearing
-   The most likely issue is a **race condition** between rejection commit and queue refetch
-   Frontend optimistic updates are good for UX but need proper error handling
-   Multiple `useHITLQueue` instances (Sidebar + Page) can lead to state inconsistencies
-   WebSocket real-time updates should keep all instances in sync, but may have timing issues

---

**Status:** Investigation Complete | Fixes Identified | Implementation Pending

# Review Queue Group-Scoping Implementation

## Overview

The review queue is now fully group-scoped, meaning only bots from the current group can be accessed. Users can only view and manage review queue items that belong to their current group.

## Changes Made

### Frontend Changes

#### 1. **Inbox Page** (`apps/web/src/app/inbox/page.tsx`)

-   Added `useGroup()` hook to access `currentGroup`
-   Initialize filters with `groupId: currentGroup?.id`
-   Added effect to update `groupId` filter when `currentGroup` changes
-   This ensures the review queue is automatically scoped to the current group

**Key Change:**

```typescript
const { currentGroup } = useGroup();

useEffect(() => {
    setFilters((prev) => ({
        ...prev,
        groupId: currentGroup?.id || undefined,
    }));
}, [currentGroup?.id]);
```

#### 2. **Next.js API Proxies**

-   Queue proxy forwards `group_id` to backend: `apps/web/src/app/api/hitl/queue/route.ts`
-   Bots proxy forwards `group_id` to backend: `apps/web/src/app/api/hitl/bots/route.ts`
-   Ensures backend receives group context even when frontend calls the Next API layer

#### 3. **HITL Queue Hook** (`apps/web/src/hooks/useHITLQueue.ts`)

-   Added `groupId` field to `HITLQueueFilters` interface
-   Updated `fetchQueue` to pass `group_id` query parameter to API
-   Group ID is now sent with every queue fetch request

**Key Change:**

```typescript
export interface HITLQueueFilters {
    groupId?: string; // NEW: scope review queue to specific group
    botId?: string;
    dateFrom?: string;
    dateTo?: string;
    status?: "pending" | "in-progress";
}

// Build query parameters
if (filters?.groupId) {
    params.append("group_id", filters.groupId);
}
```

### Backend Changes

#### 1. **HITL Queue Endpoint** (`apps/api/app/api/routes/hitl.py`)

**GET /api/v1/hitl/queue - Enhanced with group_id parameter:**

-   Added `group_id: Optional[UUID]` query parameter
-   When `group_id` is provided, the endpoint:
    1. Verifies the user has GroupMember access to that group
    2. Returns 403/empty results if user lacks access
    3. Filters items to only that group
-   Without `group_id`, returns items from all groups user has access to

**Security Implementation:**

```python
if group_id:
    # SECURITY: Verify user has access to the specified group
    membership_result = await db.execute(
        select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id,
            )
        )
    )
    if not membership_result.scalars().first():
        # User doesn't have access to this group - return empty results
        logger.warning(...)
        return ReviewQueueResponse(items=[], stats=ReviewQueueStatsResponse(...))
    # Filter to specific group
    query_stmt = query_stmt.where(ConfidenceLog.group_id == group_id)
```

#### 2. **Existing Security Controls (Already in Place)**

**POST /api/v1/hitl/queue/{item_id}/approve:**

-   Verifies user has GroupMember access to item's group
-   Returns 403 Forbidden if user lacks access

**POST /api/v1/hitl/queue/{item_id}/reject:**

-   Verifies user has GroupMember access to item's group
-   Returns 403 Forbidden if user lacks access

**GET /api/v1/hitl/queue/{item_id}:**

-   Verifies user has GroupMember access to item's group
-   Returns 403 Forbidden if user lacks access

## Security Model

### Three-Layer Access Control

1. **Tenant Isolation (Database Level)**

    - All queries filter by `tenant_id`
    - Users cannot see items from other tenants

2. **Group Membership Validation (Application Level)**

    - All HITL endpoints verify user is a GroupMember
    - GET endpoint returns only items user has access to
    - POST endpoints (approve/reject) check GroupMember before processing

3. **Group-Scoped Filtering (Request Level)**
    - Frontend passes current group's ID with every request
    - Backend verifies user has access to specified group
    - Only returns items from that specific group

## Data Flow

```
User Switches Group
    ↓
currentGroup context updates
    ↓
useEffect in Inbox updates filters with new groupId
    ↓
useHITLQueue calls fetch with group_id parameter
    ↓
GET /api/v1/hitl/queue?group_id={uuid}
    ↓
Backend verifies user is member of group (GroupMember table)
    ↓
Returns only items where ConfidenceLog.group_id = {uuid}
```

## Testing

To verify group-scoping works:

1. **Create two groups** with different members
2. **Add HITL items to each group** (via low-confidence chat responses)
3. **Switch between groups** using GroupSwitcher
4. **Verify inbox shows only items from current group**
5. **Attempt to approve/reject items from other group** - should get 403 error

## Backwards Compatibility

-   Existing code that doesn't pass `group_id` still works
-   Items with `NULL group_id` (tenant-wide) are still accessible to all users
-   No breaking changes to API contract

## Related Endpoints

All of the following now enforce group-scoping:

-   `GET /api/v1/hitl/queue` - List items (filtered by group_id)
-   `GET /api/v1/hitl/queue/{item_id}` - Get detail (verify group access)
-   `POST /api/v1/hitl/queue/{item_id}/approve` - Approve (verify group access)
-   `POST /api/v1/hitl/queue/{item_id}/reject` - Reject (verify group access)

## Benefits

✅ **Security**: Users can only access items from their groups  
✅ **Data Isolation**: Clear separation between group data  
✅ **Multi-tenant**: Works with multiple tenants and groups  
✅ **Auditability**: All access attempts logged  
✅ **Flexibility**: Can scope to all groups or specific group

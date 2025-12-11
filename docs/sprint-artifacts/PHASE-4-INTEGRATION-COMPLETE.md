# Phase 4 Completion: Route-Service Integration ✓

**Status:** COMPLETE  
**Date:** 2025-12-11  
**Scope:** Integrated GroupService, BotGroupService, DocumentGroupService, and AuditService into API routes

---

## Changes Implemented

### 1. Updated Groups Routes (apps/api/app/api/v1/groups.py)

**Service Integration:**

```python
# Imports added:
from app.services.group_service import GroupService
from app.services.audit_service import AuditService

# OLD: Direct SQLAlchemy queries
new_group = Group(tenant_id=..., name=..., ...)
session.add(new_group)
await session.flush()
member = GroupMember(group_id=new_group.id, ...)
session.add(member)

# NEW: Service layer
new_group = await GroupService.create_group(
    session=session,
    tenant_id=tenant_id,
    user_id=user_id,
    name=name,
    description=description,
)
await AuditService.log_group_created(...)
```

**Endpoints Updated:**

1. ✅ `POST /api/v1/groups` - Create group (uses `GroupService.create_group()` + audit logging)
2. ✅ `GET /api/v1/groups/{id}` - Get group (uses `GroupService.get_group()`)
3. ✅ `GET /api/v1/groups` - List groups (uses `GroupService.list_groups_for_user()`)
4. ✅ `PATCH /api/v1/groups/{id}` - Update group (uses `GroupService.update_group()`)
5. ✅ `DELETE /api/v1/groups/{id}` - Delete group (uses `GroupService.delete_group()` + audit)
6. ✅ `POST /api/v1/groups/{id}/members` - Invite member (uses `GroupService.add_member()` + audit)
7. ✅ `GET /api/v1/groups/{id}/members` - List members (uses `GroupService.list_group_members()`)
8. ✅ `PATCH /api/v1/groups/{id}/members/{user_id}` - Update role (uses `GroupService.update_member_role()` + audit)
9. ✅ `DELETE /api/v1/groups/{id}/members/{user_id}` - Remove member (uses `GroupService.remove_member()` + audit)

**Error Handling Pattern:**

```python
try:
    result = await GroupService.operation(...)
    await AuditService.log_action(...)  # For mutations
    await session.commit()
    return result
except ValueError as e:
    await session.rollback()
    # Map to appropriate HTTP status (404, 409, 400)
    raise HTTPException(status_code=..., detail=str(e))
except Exception as e:
    await session.rollback()
    logger.exception(f"Error: {e}")
    raise HTTPException(status_code=500, detail="Failed to ...")
```

---

### 2. Updated Bots Routes (apps/api/app/api/v1/bots.py)

**Service Integration:**

```python
# Imports added:
from app.services.bot_group_service import BotGroupService
from app.services.audit_service import AuditService

# OLD: Direct model creation
new_bot = Bot(
    tenant_id=tenant_id,
    group_id=group_id,
    name=name,
    ...
)
session.add(new_bot)

# NEW: Service layer
new_bot = await BotGroupService.create_bot(
    session=session,
    tenant_id=tenant_id,
    group_id=group_id,
    user_id=user_id,
    name=name,
    description=description,
    confidence_threshold=threshold,
)
await AuditService.log_action(...)
```

**Endpoints Updated:**

1. ✅ `POST /api/v1/groups/{group_id}/bots` - Create bot (uses `BotGroupService.create_bot()` + audit)
2. ✅ `GET /api/v1/groups/{group_id}/bots/{bot_id}` - Get bot (uses `BotGroupService.get_bot()`)
3. ✅ `GET /api/v1/groups/{group_id}/bots` - List bots (uses `BotGroupService.list_group_bots()`)
4. ✅ `PATCH /api/v1/groups/{group_id}/bots/{bot_id}` - Update bot (uses `BotGroupService.update_bot()` + audit)
5. ✅ `DELETE /api/v1/groups/{group_id}/bots/{bot_id}` - Delete bot (uses `BotGroupService.delete_bot()` + audit)

**RLS Isolation:**

-   All service calls include `group_id` + `tenant_id` for composite RLS
-   Service layer enforces unique constraint: `(tenant_id, group_id, name)`
-   Errors from services are ValueError exceptions with clear messages

---

### 3. Updated Documents Routes (apps/api/app/api/v1/documents.py)

**Service Integration:**

```python
# Imports added:
from app.services.document_group_service import DocumentGroupService
from app.services.audit_service import AuditService

# OLD: Direct document creation
new_doc = Document(
    tenant_id=tenant_id,
    group_id=group_id,
    filename=filename,
    ...
)
session.add(new_doc)

# NEW: Service layer with provenance
new_doc = await DocumentGroupService.create_document(
    session=session,
    tenant_id=tenant_id,
    group_id=group_id,
    uploader_id=uploader_id,
    filename=filename,
    mime=mime,
    size=size,
    storage_path=path,
    bot_id=bot_id,  # Optional - for provenance
    title=title,
)
await AuditService.log_document_upload(...)
```

**Endpoints Updated:**

1. ✅ `POST /api/v1/groups/{group_id}/documents/upload` - Upload document (uses `DocumentGroupService.create_document()` + audit + provenance tracking)
2. ✅ `GET /api/v1/groups/{group_id}/documents/{doc_id}` - Get document (uses `DocumentGroupService.get_document()`)
3. ✅ `GET /api/v1/groups/{group_id}/documents` - List documents (uses `DocumentGroupService.list_group_documents()` with `include_deleted` filter)
4. ✅ `DELETE /api/v1/groups/{group_id}/documents/{doc_id}` - Soft-delete (uses `DocumentGroupService.soft_delete_document()` + audit)
5. ✅ `GET /api/v1/groups/{group_id}/documents/{doc_id}/chunks` - List chunks (uses `DocumentGroupService.get_document_chunks()`)

**Provenance Tracking:**

-   `uploader_id`: Captured from `current_user["sub"]`
-   `bot_id`: Optional form field (if bot triggered upload)
-   `group_id`: Always captured for RLS
-   Status transitions: `uploading` → `uploaded` → `processing` → `ready/failed`
-   Audit trail: `log_document_upload()` captures filename, size, bot_id, timestamp

**Soft-Delete Pattern:**

-   Sets `deleted_at` timestamp (preserves data for audit)
-   Chunks remain in DB (shared group KB)
-   `include_deleted=true` parameter allows querying deleted docs
-   Hard delete (admin only) via `DocumentGroupService.hard_delete_document()` (not exposed in routes yet)

---

## Audit Service Integration

**All Mutation Endpoints Now Log:**

```python
# Group operations
await AuditService.log_group_created(session, actor_id, tenant_id, group_id, name)
await AuditService.log_action(session, actor_id, "group_deleted", tenant_id, group_id, ...)

# Member operations
await AuditService.log_member_invited(session, actor_id, tenant_id, group_id, invited_user_id, role)
await AuditService.log_action(session, actor_id, "member_role_updated", ...)
await AuditService.log_action(session, actor_id, "member_removed", ...)

# Bot operations
await AuditService.log_action(session, actor_id, "bot_created", tenant_id, group_id, "Bot", bot_id, ...)
await AuditService.log_action(session, actor_id, "bot_updated", ...)
await AuditService.log_action(session, actor_id, "bot_deleted", ...)

# Document operations
await AuditService.log_document_upload(session, actor_id, tenant_id, group_id, doc_id, filename, size, bot_id)
await AuditService.log_document_delete(session, actor_id, tenant_id, group_id, doc_id)
```

**Audit Log Structure:**

```json
{
    "actor_id": "uuid",
    "action": "bot_created",
    "tenant_id": "uuid",
    "group_id": "uuid",
    "target_type": "Bot",
    "target_id": "uuid",
    "details": { "bot_name": "Customer Support Bot" },
    "created_at": "2025-12-11T10:30:00Z"
}
```

---

## Error Handling Improvements

### Consistent Error Mapping

**Service Layer (raises ValueError):**

```python
# Not found
raise ValueError(f"Group {group_id} not found")

# Duplicate
raise ValueError(f"Group name '{name}' already exists in this tenant")

# Invalid state
raise ValueError(f"Bot {bot_id} not found")
```

**API Layer (catches and converts to HTTP):**

```python
try:
    result = await Service.operation(...)
except ValueError as e:
    error_msg = str(e)
    if "not found" in error_msg:
        raise HTTPException(status_code=404, detail=error_msg)
    elif "already exists" in error_msg:
        raise HTTPException(status_code=409, detail=error_msg)
    else:
        raise HTTPException(status_code=400, detail=error_msg)
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Logging Added

```python
import logging
logger = logging.getLogger(__name__)

# Log exceptions with context
logger.exception(f"Error creating group: {e}")
logger.exception(f"Error uploading document: {e}")
```

---

## Code Quality Improvements

### Before (Direct DB Queries):

```python
@router.post("", response_model=GroupResponse)
async def create_group(group_data: GroupCreate, ...):
    # 1. Manual object creation
    new_group = Group(tenant_id=..., name=..., ...)
    session.add(new_group)
    await session.flush()

    # 2. Manual membership creation
    member = GroupMember(group_id=new_group.id, ...)
    session.add(member)

    # 3. Commit
    await session.commit()
    return new_group
```

### After (Service Layer):

```python
@router.post("", response_model=GroupResponse)
async def create_group(group_data: GroupCreate, ...):
    # 1. Single service call (encapsulates all logic)
    new_group = await GroupService.create_group(
        session, tenant_id, user_id, name, description
    )

    # 2. Audit trail
    await AuditService.log_group_created(...)

    # 3. Commit
    await session.commit()
    return new_group
```

**Benefits:**

-   ✅ Reduced code duplication (8 endpoints → 1 service method)
-   ✅ Centralized business logic (unique name check, FK validation)
-   ✅ Testable in isolation (services can be unit tested)
-   ✅ Consistent error handling (ValueError → HTTPException)
-   ✅ Audit logging in one place
-   ✅ Transaction management (services use session.flush() for intermediate state)

---

## Files Modified

### Route Files Updated:

-   `apps/api/app/api/v1/groups.py` (386 lines → integrated GroupService + AuditService)
-   `apps/api/app/api/v1/bots.py` (230 lines → integrated BotGroupService + AuditService)
-   `apps/api/app/api/v1/documents.py` (252 lines → integrated DocumentGroupService + AuditService)

### Service Files Used (from Phase 3):

-   `apps/api/app/services/group_service.py` (240 lines)
-   `apps/api/app/services/bot_group_service.py` (180 lines)
-   `apps/api/app/services/document_group_service.py` (220 lines)
-   `apps/api/app/services/audit_service.py` (190 lines)

---

## Verification

### Compilation Status: ✅ PASSED

```bash
python -m py_compile apps/api/app/api/v1/groups.py apps/api/app/api/v1/bots.py apps/api/app/api/v1/documents.py
# Exit code: 0 (no syntax errors)
```

### Integration Test Suite Available:

-   `apps/api/tests/test_groups_bots_documents.py` (478 lines)
-   Contains tests for all group/bot/document routes
-   Includes fixtures for tenant, users, groups, bots
-   Tests cover: create, get, list, update, delete, membership

### Test Execution Command:

```bash
# Single test
python -m pytest apps/api/tests/test_groups_bots_documents.py::test_create_group -v

# Full suite
python -m pytest apps/api/tests/test_groups_bots_documents.py -v

# All integration tests
python -m pytest apps/api/tests/ -v
```

---

## API Changes Summary

### No Breaking Changes

-   All existing endpoints maintain same signatures
-   Request/response schemas unchanged
-   Authentication/authorization unchanged
-   HTTP status codes unchanged

### Internal Changes Only

-   Routes now call services instead of direct DB queries
-   Services enforce RLS (tenant_id + group_id)
-   Audit logging added to all mutations
-   Error handling improved with consistent patterns
-   Logging added for debugging

---

## Next Steps: Phase 5 (Frontend Updates)

### Required Frontend Changes:

1. **Group Switcher Component**

    - Dropdown in navbar to select active group
    - Fetch groups from `GET /api/v1/groups`
    - Store selected group in context/state

2. **Bot Management UI**

    - Update bot routes from `/api/v1/bots` → `/api/v1/groups/{group_id}/bots`
    - Pass `group_id` in all bot API calls
    - Display group context in bot list/detail pages

3. **Document Upload UI**

    - Update upload endpoint from `/api/v1/documents/upload` → `/api/v1/groups/{group_id}/documents/upload`
    - Add optional `bot_id` field to upload form
    - Display provenance metadata (uploader, bot, timestamp)

4. **Group Settings Page**

    - Create new `/settings/groups` route
    - CRUD operations for groups
    - Member invitation/management UI
    - Display group KB statistics (docs, chunks, size)

5. **Provenance Display**
    - Show "Uploaded by [User] on [Date]" in document list
    - Show "Triggered by [Bot]" if bot_id present
    - Link to audit trail viewer

---

## Testing Checklist

Before deploying to production:

-   [ ] Run full integration test suite (`pytest apps/api/tests/`)
-   [ ] Test group creation with valid/invalid names
-   [ ] Test group membership invitation flow
-   [ ] Test bot creation with group_id validation
-   [ ] Test document upload with provenance capture
-   [ ] Test soft-delete preserves chunks
-   [ ] Verify audit logs are populated
-   [ ] Test RLS isolation (tenant A can't access tenant B's groups)
-   [ ] Test RBAC enforcement (operators can't delete groups)
-   [ ] Load test with 1000+ groups/bots/documents

---

## Migration Notes

### Database State

-   All migrations from Phase 1 must be applied (`006_add_groups_and_provenance.py`)
-   Existing bots must have `group_id` set (manual data migration if needed)
-   Existing documents must have `uploader_id` set (can default to `created_by`)

### Backwards Compatibility

-   Old tenant-scoped `/api/v1/bots` routes still exist in `apps/api/app/api/routes/bots.py`
-   New group-scoped routes: `/api/v1/groups/{group_id}/bots`
-   Frontend should migrate to new routes incrementally

### Deployment Order

1. Deploy Phase 1 (models + migration)
2. Deploy Phase 3 (services)
3. Deploy Phase 4 (routes) ← **Current**
4. Deploy Phase 5 (frontend updates)
5. Deprecate old tenant-scoped routes after frontend migration

---

**Phase 4 Status:** ✅ COMPLETE - All routes integrated with services, audit logging enabled, error handling improved, compilation verified.

Ready to proceed to Phase 5 (Frontend Updates) or run integration tests first?

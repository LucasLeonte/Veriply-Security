# Phase 3 Completion: Services & Business Logic ✓

**Status:** COMPLETE  
**Date:** 2025-12-11  
**Scope:** Group-scoped service layer with provenance tracking

---

## Changes Implemented

### 1. Group Service (NEW - group_service.py)

**Core Operations:**

```python
GroupService.create_group()          # Create group + add creator as admin
GroupService.get_group()             # Get by ID with tenant isolation
GroupService.list_groups_for_user()  # List user's groups
GroupService.update_group()          # Update name/description
GroupService.delete_group()          # Delete (preserves KB)
GroupService.get_group_kb_stats()    # KB stats (docs, chunks, bots)
```

**Membership Management:**

```python
GroupService.add_member()            # Invite user to group
GroupService.get_member_role()       # Check user's role
GroupService.update_member_role()    # Change role (group_admin only)
GroupService.remove_member()         # Remove from group
GroupService.list_group_members()    # List all members
```

**Features:**

-   Unique group name per tenant
-   RLS isolation (tenant_id check)
-   Role-based enforcement
-   Audit logging for membership changes
-   KB statistics aggregation

### 2. Bot Group Service (NEW - bot_group_service.py)

**Operations:**

```python
BotGroupService.create_bot()         # Create bot in group with group_id FK
BotGroupService.get_bot()            # Get by ID (group + tenant isolation)
BotGroupService.list_group_bots()    # List bots in group with pagination
BotGroupService.update_bot()         # Update name/description/threshold
BotGroupService.delete_bot()         # Delete (preserves group KB)
BotGroupService.set_bot_status()     # Update processing status
```

**Key Differences from Old BotService:**

-   **Group-scoped:** All bots must belong to a group
-   **Unique constraint:** (tenant_id, group_id, name) not just (tenant_id, name)
-   **KB preservation:** Deleting bot doesn't delete documents (shared KB)
-   **RLS composites:** group_id included in all queries
-   **Provenance:** Tracks created_by for audit

### 3. Document Group Service (NEW - document_group_service.py)

**Operations:**

```python
DocumentGroupService.create_document()      # Create doc record + capture provenance
DocumentGroupService.get_document()         # Get by ID (group isolation)
DocumentGroupService.list_group_documents() # List KB docs with pagination
DocumentGroupService.soft_delete_document() # Mark deleted_at (audit trail)
DocumentGroupService.hard_delete_document() # Permanently delete (admin only)
DocumentGroupService.get_document_chunks()  # Retrieve chunks for document
DocumentGroupService.update_document_status() # Update processing status
DocumentGroupService.get_document_provenance() # Get upload metadata
DocumentGroupService.get_group_kb_stats()   # KB stats (docs, chunks, size)
```

**Provenance Tracking:**

```python
Document captures:
  - uploader_id: Who uploaded
  - bot_id: Which bot triggered (optional)
  - created_at/updated_at: When
  - filename: Original file
  - size: File size bytes
  - mime: Content type
  - status: processing state (uploading → uploaded → processing → ready/failed)
  - deleted_at: Soft-delete timestamp
```

**Soft-Delete Pattern:**

-   deleted_at timestamp marks deletion
-   Chunks remain (shared KB)
-   Can query with include_deleted=true for audit
-   Restore by clearing deleted_at if needed

### 4. Audit Service (NEW - audit_service.py)

**Core Operations:**

```python
AuditService.log_action()                 # Generic action logging
AuditService.log_document_upload()        # Document upload event
AuditService.log_document_delete()        # Document deletion event
AuditService.log_bot_created()            # Bot creation event
AuditService.log_group_created()          # Group creation event
AuditService.log_member_invited()         # Member invitation event
AuditService.log_chunk_created()          # Chunk creation event (provenance)
AuditService.get_audit_log()              # Retrieve audit entries
AuditService.get_document_audit_trail()   # Get all events for a document
```

**Audit Trail Structure:**

```python
AuditLog:
  - actor_id: User performing action
  - action: Action name
  - details: JSON with metadata
  - created_at: Timestamp
  - (Example) document_uploaded: {filename, size_bytes, bot_id, timestamp}
```

---

## Service Integration Pattern

All services follow consistent async/await pattern:

```python
class XxxService:
    @staticmethod
    async def operation(db: AsyncSession, id: UUID, tenant_id: UUID) -> Model:
        # 1. RLS query with (tenant_id, [group_id]) filters
        entity = await db.scalar(
            select(Model).where(
                (Model.id == id) &
                (Model.tenant_id == tenant_id) &
                (Model.group_id == group_id)
            )
        )
        if not entity:
            raise ValueError(f"{Model} {id} not found")

        # 2. Business logic
        # 3. Mutation with db.flush()
        # 4. Logging
        return entity
```

**Isolation Levels:**

-   **Tenant RLS:** tenant_id in all queries
-   **Group RLS:** group_id for documents, bots, chunks
-   **User RBAC:** Enforced in API routes (services don't check roles)

---

## Provenance Implementation

### Document Upload Flow:

```
1. API route receives file upload
2. DocumentGroupService.create_document() called with:
   - tenant_id, group_id (required)
   - uploader_id (current user)
   - bot_id (optional - which bot triggered)
   - filename, mime, size
3. Document created with:
   - status: "uploaded"
   - uploader_id captured
   - bot_id stored
   - source_metadata available for citation
4. AuditService.log_document_upload() called
5. Background job processes document
6. Chunks created with group_id, bot_id, source_metadata
7. AuditService.log_chunk_created() called
8. Document status updated to "ready"
```

### Provenance Query:

```python
# Get who uploaded a document and from which bot
provenance = await DocumentGroupService.get_document_provenance(
    db, doc_id, group_id, tenant_id
)
# Returns: {id, filename, uploader_id, bot_id, uploaded_at, status, size_bytes}

# Get all events related to a document
trail = await AuditService.get_document_audit_trail(db, doc_id)
# Returns: [AuditLog, ...] with upload, chunk_created, status_update events
```

---

## Error Handling

All services raise `ValueError` for business logic errors:

```python
# Duplicate group name
raise ValueError(f"Group name '{name}' already exists in this tenant")

# Not found
raise ValueError(f"Bot {bot_id} not found")

# Invalid state
raise ValueError(f"Group {group_id} not found")
```

**API routes catch and convert to HTTP responses:**

```python
try:
    bot = await BotGroupService.create_bot(...)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

---

## Database Performance

### Indexes Leveraged:

-   `(tenant_id)` - primary RLS filter
-   `(tenant_id, group_id)` - composite RLS
-   `(group_id, user_id)` - group membership lookup
-   `(tenant_id, group_id, name)` - unique constraint check
-   `(deleted_at)` - soft-delete queries
-   `(tenant_id, group_id, vector)` - similarity search (chunks)

### Query Count:

-   Single-entity get: 1 query
-   List with count: 2 queries (count + list)
-   Create with foreign key check: 2 queries (FK verify + insert)
-   Soft delete: 1 query (UPDATE)
-   Audit log: 1 query (INSERT)

---

## Files Created

**New Services:**

-   `apps/api/app/services/group_service.py` (240 lines)
-   `apps/api/app/services/bot_group_service.py` (180 lines)
-   `apps/api/app/services/document_group_service.py` (220 lines)
-   `apps/api/app/services/audit_service.py` (190 lines)

---

## Integration Checklist for Phase 4

-   [ ] Update API routes to use new services
    -   `groups.py` → use `GroupService`
    -   `bots.py` → use `BotGroupService`
    -   `documents.py` → use `DocumentGroupService`
    -   All routes → use `AuditService` for logging
-   [ ] Add service calls to routes

    ```python
    @router.post("", response_model=GroupResponse)
    async def create_group(group_data: GroupCreate, ...):
        new_group = await GroupService.create_group(
            session, current_user["tenant_id"], current_user["sub"],
            group_data.name, group_data.description
        )
        await AuditService.log_group_created(
            session, current_user["sub"], current_user["tenant_id"],
            new_group.id, new_group.name
        )
        await session.commit()
        return new_group
    ```

-   [ ] Test services directly (unit tests)
-   [ ] Test services through API routes (integration tests)
-   [ ] Verify audit trail is populated
-   [ ] Verify provenance metadata captured

---

## Key Design Decisions

### 1. Separate Service Classes

-   `BotGroupService` ≠ `BotService` (old tenant-scoped)
-   Prevents confusion and accidental tenant-scope queries
-   Clear migration path for legacy code

### 2. Soft-Delete Pattern

-   Documents marked deleted_at instead of cascaded
-   Chunks remain (shared group KB)
-   Audit trail preserved
-   Can restore if needed

### 3. Service Layer Doesn't Check Roles

-   RBAC only enforced in API routes
-   Services assume caller is authorized
-   Allows reuse from workers/jobs that have different auth context

### 4. Logging via AuditService

-   Not scattered in each service
-   Centralized audit trail
-   Single source of truth for compliance

### 5. Explicit FK Checks

-   GroupService checks group exists before operations
-   Prevents orphaned documents
-   Clear error messages

---

## Next Steps: Phase 4

### API Route Integration (1 day)

-   [ ] Import services in route modules
-   [ ] Replace direct DB queries with service calls
-   [ ] Add audit logging to all mutations
-   [ ] Test routes end-to-end

### Integration Testing (1 day)

-   [ ] Test group creation → member invitation → bot creation → document upload flow
-   [ ] Verify RLS isolation (group_id, tenant_id)
-   [ ] Verify provenance captured
-   [ ] Verify audit trail populated

---

**Phase 3 Status:** ✅ COMPLETE - All service layer created with group scoping, provenance, and audit logging. Ready for route integration.

Proceed to Phase 4 (Route Integration) or run tests first?

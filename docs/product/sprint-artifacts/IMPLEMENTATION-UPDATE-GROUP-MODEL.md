# Implementation Update: Models & APIs for Group Model

**Status:** Ready for Development  
**Priority:** Critical (blocks bot/document implementation)  
**Date Created:** 2025-12-11  
**Scope:** Update existing code from tenant-scoped to group-scoped with provenance

---

## Overview

Existing implementation was built with: **Tenant → Bots (isolated KB per bot)**

New model requires: **Tenant → Groups → Bots (shared KB per group with provenance)**

This guide specifies code changes needed in models, APIs, and services.

---

## 1. Database Models

### 1.1 Create New Model: `Group` (apps/api/app/models/group.py)

```python
from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Text, Index
from datetime import datetime
from .base import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_groups_tenant_id', 'tenant_id'),
        Index('ix_groups_tenant_name', 'tenant_id', 'name'),
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'name', name='uq_groups_tenant_name'),
    )
```

### 1.2 Create New Model: `GroupMember` (apps/api/app/models/group_member.py)

```python
from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Enum as SQLEnum, Index
from datetime import datetime
import enum
from .base import Base

class GroupRole(str, enum.Enum):
    GROUP_ADMIN = "group_admin"
    MANAGER = "manager"
    OPERATOR = "operator"

class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(GroupRole), nullable=False)  # group_admin, manager, operator
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    invited_by_id = Column(Uuid, ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        Index('ix_group_members_group_id', 'group_id'),
        Index('ix_group_members_user_id', 'user_id'),
        Index('ix_group_members_group_user', 'group_id', 'user_id'),
        __import__('sqlalchemy').UniqueConstraint('group_id', 'user_id', name='uq_group_members_group_user'),
    )
```

### 1.3 Update Model: `Bot` (apps/api/app/models/bot.py)

**Changes:**

-   Add `group_id` column
-   Update unique constraint from (tenant_id, name) → (tenant_id, group_id, name)
-   Update indexes to include group_id for RLS

```python
class Bot(Base):
    __tablename__ = "bots"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)  # NEW
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    confidence_threshold = Column(Integer, default=80, nullable=False)
    status = Column(SQLEnum(BotStatus), default=BotStatus.EMPTY, nullable=False)
    created_by = Column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_bots_tenant_id', 'tenant_id'),
        Index('ix_bots_group_id', 'group_id'),  # NEW
        Index('ix_bots_tenant_group', 'tenant_id', 'group_id'),  # NEW: RLS composite
        Index('ix_bots_tenant_group_created', 'tenant_id', 'group_id', 'created_at'),  # NEW
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'group_id', 'name', name='uq_bots_tenant_group_name'),  # UPDATED
    )
```

### 1.4 Update Model: `Document` (apps/api/app/models/document.py)

**Changes:**

-   Add `group_id` column (from bot's group)
-   Add `uploader_id` to replace/supplement `uploaded_by`
-   Update indexes to (tenant_id, group_id) for RLS
-   Add deleted_at for soft-delete audit trail

```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)  # NEW
    bot_id = Column(Uuid, ForeignKey("bots.id"), nullable=True)  # Which bot uploaded
    title = Column(String(255), nullable=True)
    filename = Column(String(255), nullable=True)
    mime = Column(String(100), nullable=True)
    size = Column(Integer, nullable=True)
    storage_path = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="uploaded")
    uploader_id = Column(Uuid, ForeignKey("users.id"), nullable=False)  # UPDATED: was uploaded_by
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # NEW: soft-delete for audit

    __table_args__ = (
        Index('ix_documents_tenant_id', 'tenant_id'),
        Index('ix_documents_group_id', 'group_id'),  # NEW
        Index('ix_documents_tenant_group', 'tenant_id', 'group_id'),  # NEW: RLS composite
        Index('ix_documents_bot_id', 'bot_id'),
        Index('ix_documents_status', 'status'),
        Index('ix_documents_deleted', 'deleted_at'),  # NEW: soft-delete queries
    )
```

### 1.5 Update Model: `Chunk` (apps/api/app/models/chunk.py)

**Changes:**

-   Add `group_id` column
-   Update composite index for RLS to (tenant_id, group_id, vector)
-   Add source_metadata column for citation tracking

```python
class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    document_id = Column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)  # NEW
    bot_id = Column(Uuid, ForeignKey("bots.id", ondelete="CASCADE"), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    vector = Column(Vector(1024), nullable=True)
    metadata_json = Column('metadata', Text, nullable=True)
    source_metadata = Column('source_metadata', Text, nullable=True)  # NEW: {filename, page, row}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_chunks_document_id', 'document_id'),
        Index('idx_chunks_group_id', 'group_id'),  # NEW
        Index('idx_chunks_tenant_group_vector', 'tenant_id', 'group_id', 'vector'),  # NEW: RLS-aware similarity
        Index('idx_chunks_bot_id', 'bot_id'),
        Index('idx_chunks_bot_document', 'bot_id', 'document_id'),
        Index('idx_chunks_bot_tenant_group', 'bot_id', 'tenant_id', 'group_id'),  # NEW: provenance query
        {'extend_existing': True},
    )
```

---

## 2. Alembic Migration

Create migration: `apps/api/alembic/versions/006_add_groups_and_provenance.py`

```python
"""Add groups, group_members, and update bot/document/chunk models for group scoping and provenance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

def upgrade():
    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_groups_tenant_name'),
    )
    op.create_index('ix_groups_tenant_id', 'groups', ['tenant_id'])
    op.create_index('ix_groups_tenant_name', 'groups', ['tenant_id', 'name'])

    # Create group_members table
    op.create_table(
        'group_members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.Enum('group_admin', 'manager', 'operator', name='grouprole'), nullable=False),
        sa.Column('invited_at', sa.DateTime(), nullable=False),
        sa.Column('invited_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_members_group_user'),
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_user_id', 'group_members', ['user_id'])
    op.create_index('ix_group_members_group_user', 'group_members', ['group_id', 'user_id'])

    # Add group_id to bots
    op.add_column('bots', sa.Column('group_id', sa.UUID(), nullable=False))
    op.create_foreign_key('fk_bots_group_id', 'bots', 'groups', ['group_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_bots_group_id', 'bots', ['group_id'])
    op.create_index('ix_bots_tenant_group', 'bots', ['tenant_id', 'group_id'])
    op.drop_constraint('uq_bots_tenant_name', 'bots', type_='unique')
    op.create_unique_constraint('uq_bots_tenant_group_name', 'bots', ['tenant_id', 'group_id', 'name'])

    # Add group_id and update columns to documents
    op.add_column('documents', sa.Column('group_id', sa.UUID(), nullable=False))
    op.add_column('documents', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_documents_group_id', 'documents', 'groups', ['group_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_documents_group_id', 'documents', ['group_id'])
    op.create_index('ix_documents_tenant_group', 'documents', ['tenant_id', 'group_id'])
    op.create_index('ix_documents_deleted', 'documents', ['deleted_at'])
    op.alter_column('documents', 'uploaded_by', new_column_name='uploader_id')

    # Add group_id and source_metadata to chunks
    op.add_column('chunks', sa.Column('group_id', sa.UUID(), nullable=False))
    op.add_column('chunks', sa.Column('source_metadata', sa.Text(), nullable=True))
    op.create_foreign_key('fk_chunks_group_id', 'chunks', 'groups', ['group_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_chunks_group_id', 'chunks', ['group_id'])
    op.create_index('idx_chunks_tenant_group_vector', 'chunks', ['tenant_id', 'group_id', 'vector'], postgresql_using='ivfflat')
    op.create_index('idx_chunks_bot_tenant_group', 'chunks', ['bot_id', 'tenant_id', 'group_id'])

def downgrade():
    op.drop_table('group_members')
    op.drop_table('groups')
    op.drop_column('bots', 'group_id')
    op.drop_column('documents', 'group_id')
    op.drop_column('documents', 'deleted_at')
    op.drop_column('chunks', 'group_id')
    op.drop_column('chunks', 'source_metadata')
    # Restore uq_bots_tenant_name constraint
    op.drop_constraint('uq_bots_tenant_group_name', 'bots')
    op.create_unique_constraint('uq_bots_tenant_name', 'bots', ['tenant_id', 'name'])
```

---

## 3. API Routes & Schemas

### 3.1 Create New Schemas (apps/api/app/api/v1/schemas.py)

Add to existing schemas:

```python
# Group Schemas
class GroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

class GroupResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# GroupMember Schemas
class GroupMemberCreate(BaseModel):
    email: str
    role: Literal["group_admin", "manager", "operator"]

class GroupMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    invited_at: datetime

    class Config:
        from_attributes = True

# Bot Schemas (UPDATE)
class BotCreate(BaseModel):
    group_id: UUID  # NEW: required
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    confidence_threshold: int = Field(80, ge=0, le=100)

class BotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    confidence_threshold: Optional[int] = Field(None, ge=0, le=100)

class BotResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    group_id: UUID  # NEW
    name: str
    description: Optional[str]
    confidence_threshold: int
    status: str
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Document Schemas (UPDATE)
class DocumentUpload(BaseModel):
    group_id: UUID  # NEW: required (infer bot_id if needed)
    bot_id: Optional[UUID] = None  # NEW: optional, tracks which bot triggered upload

class DocumentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    group_id: UUID  # NEW
    bot_id: Optional[UUID]
    filename: str
    status: str
    uploader_id: UUID  # NEW
    created_at: datetime

    class Config:
        from_attributes = True

# Chunk Schemas (NEW)
class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    source_metadata: Optional[str]  # {filename, page, row}
    created_at: datetime

    class Config:
        from_attributes = True
```

### 3.2 Create Group Routes (apps/api/app/api/v1/groups.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from ...models import Group, GroupMember, User
from ...core.security import get_current_user
from ...core.database import get_session
from .schemas import GroupCreate, GroupUpdate, GroupResponse, GroupMemberCreate, GroupMemberResponse

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new group (current_user becomes group_admin)"""
    # Verify user belongs to tenant
    new_group = Group(
        tenant_id=current_user.tenant_id,
        name=group.name,
        description=group.description,
        created_by=current_user.id,
    )
    session.add(new_group)
    await session.flush()

    # Add creator as group_admin
    member = GroupMember(
        group_id=new_group.id,
        user_id=current_user.id,
        role="group_admin",
    )
    session.add(member)
    await session.commit()
    return new_group

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get group details (must be member)"""
    # Verify membership
    stmt = select(Group).where(
        (Group.id == group_id) &
        (Group.tenant_id == current_user.tenant_id)
    )
    group = await session.scalar(stmt)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.post("/{group_id}/members", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    group_id: UUID,
    invite: GroupMemberCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Invite a user to group (group_admin+ only)"""
    # Verify current user is group_admin
    # Find user by email, add to group_members
    # Send invitation email
    pass

@router.delete("/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove member from group (group_admin+ only)"""
    pass
```

### 3.3 Update Bot Routes (apps/api/app/api/v1/bots.py)

```python
# Key changes:
# - POST /groups/{group_id}/bots (group-scoped creation)
# - GET /groups/{group_id}/bots (list group bots)
# - DELETE /groups/{group_id}/bots/{bot_id} (delete bot, preserve KB)
# - Require group membership + role check (Manager+)

@router.post("/groups/{group_id}/bots", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    group_id: UUID,
    bot: BotCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create bot in group (Manager+ only)"""
    # Verify group membership
    # Verify role is Manager or group_admin
    # Create bot with group_id
    pass
```

### 3.4 Update Document Upload Routes (apps/api/app/api/v1/documents.py)

```python
# Key changes:
# - POST /groups/{group_id}/documents (upload to group KB)
# - Capture uploader_id, bot_id (optional), group_id in document
# - Status: uploading → processing → ready/failed
# - Return metadata including uploader and source

@router.post("/groups/{group_id}/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    group_id: UUID,
    file: UploadFile,
    bot_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload document to group KB (Operator+)"""
    # Verify group membership (any role)
    # Store document with group_id, uploader_id, bot_id
    # Enqueue processing task
    # Return 202 Accepted with document ID
    pass
```

---

## 4. Services & Business Logic

### 4.1 Update Bot Service (apps/api/app/services/bot_service.py)

```python
# Methods to update:
# - create_bot(tenant_id, group_id, ...) → add group_id
# - get_bots(tenant_id, group_id) → filter by group_id
# - delete_bot(bot_id) → delete bot only, NOT documents (KB is shared)
# - check_bot_membership(user_id, bot_id) → verify via group_members
```

### 4.2 Update Document Service (apps/api/app/services/document_service.py)

```python
# Methods to update:
# - upload_document(tenant_id, group_id, user_id, bot_id, file) → capture all
# - list_documents(tenant_id, group_id, include_deleted=False) → group-scoped
# - delete_document(doc_id, user_id) → soft-delete, log to audit
# - process_document(doc_id) → store chunks with group_id, bot_id, source_metadata
```

### 4.3 Update Ingestion Service (apps/api/app/services/ingestion_service.py)

```python
# Updates:
# - extract_text() → no change
# - chunk_text() → no change
# - embed_chunks(tenant_id, group_id, bot_id, chunks) → add group_id, bot_id, source_metadata
# - store_chunks(chunks, metadata) → store with (tenant_id, group_id, vector) index
```

---

## 5. RLS Policies (PostgreSQL)

Create migration to add RLS policies on groups, group_members, bots, documents, chunks:

```sql
-- Enable RLS
ALTER TABLE groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

-- groups: user must have matching tenant_id (implied via group_members)
CREATE POLICY groups_user_isolation ON groups
  USING (tenant_id = (SELECT tenant_id FROM users WHERE id = current_user_id()));

-- group_members: user can see groups they're members of
CREATE POLICY group_members_user ON group_members
  USING (user_id = current_user_id() OR group_id IN (SELECT group_id FROM group_members WHERE user_id = current_user_id()));

-- bots: (tenant_id, group_id) = current user's tenant + groups
CREATE POLICY bots_user_isolation ON bots
  USING (
    tenant_id = (SELECT tenant_id FROM users WHERE id = current_user_id())
    AND group_id IN (SELECT group_id FROM group_members WHERE user_id = current_user_id())
  );

-- documents: (tenant_id, group_id) = current user's tenant + groups
CREATE POLICY documents_user_isolation ON documents
  USING (
    tenant_id = (SELECT tenant_id FROM users WHERE id = current_user_id())
    AND group_id IN (SELECT group_id FROM group_members WHERE user_id = current_user_id())
  );

-- chunks: (tenant_id, group_id) = current user's tenant + groups
CREATE POLICY chunks_user_isolation ON chunks
  USING (
    tenant_id = (SELECT tenant_id FROM users WHERE id = current_user_id())
    AND group_id IN (SELECT group_id FROM group_members WHERE user_id = current_user_id())
  );
```

---

## 6. Permission Decorators (FastAPI)

Create new decorators in `apps/api/app/core/security.py`:

```python
from functools import wraps
from fastapi import HTTPException, status

def require_group_role(*allowed_roles: str):
    """Verify user is in group with required role"""
    async def decorator(request, group_id: UUID, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
        # Query group_members for (current_user.id, group_id) and check role
        member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.user_id == current_user.id) &
                (GroupMember.group_id == group_id)
            )
        )
        if not member or member.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return decorator

# Usage:
# @router.post("/groups/{group_id}/bots")
# @require_group_role("group_admin", "manager")
# async def create_bot(...):
#     pass
```

---

## 7. Frontend Updates (apps/web)

### 7.1 Update Bot Page Component

```typescript
// Before: showed all bots for tenant
// After: show bots for current_group only
// Add group switcher in header
// Add "New Bot" button that requires Manager+ role
// Show "You cannot create bots" for Operators
```

### 7.2 Update Document Upload

```typescript
// Before: upload to bot KB
// After: upload to group KB
// Metadata: group_id (required), bot_id (optional)
// Show uploader name and upload timestamp
```

### 7.3 Add Group Management Page

```typescript
// Create groups page component
// List groups user is member of
// Show group members with roles
// Group Admin can invite/remove members
```

---

## 8. Testing Updates

### 8.1 Unit Tests

Update/create tests in `apps/api/tests/`:

-   `test_group_crud.py` → Create, read, update groups
-   `test_group_membership.py` → Invite, remove members
-   `test_bot_group_scoped.py` → Create bot with group_id, delete (KB preserved)
-   `test_document_provenance.py` → Upload with bot_id, uploader_id, verify chunks

### 8.2 Integration Tests (Story 9 test stories)

-   Story 9.1: KB provenance metadata
-   Story 9.2: RLS isolation by group
-   Story 9.3: Multi-bot group KB E2E
-   Story 9.4: RBAC enforcement
-   Story 9.5: Audit trail

---

## Implementation Checklist

-   [ ] Create Group and GroupMember models
-   [ ] Update Bot, Document, Chunk models with group_id, provenance fields
-   [ ] Create and run Alembic migration
-   [ ] Add group-related schemas
-   [ ] Create group routes (CRUD + membership)
-   [ ] Update bot routes to be group-scoped with role checks
-   [ ] Update document upload to capture group_id, bot_id, uploader_id
-   [ ] Update ingestion service to store chunks with provenance
-   [ ] Create/update RLS policies in database
-   [ ] Add permission decorators in security module
-   [ ] Update frontend group switcher component
-   [ ] Update bot creation UI (group-scoped, role restrictions)
-   [ ] Update document upload UI (group KB, metadata display)
-   [ ] Create group management page
-   [ ] Run all tests (unit + integration + E2E)
-   [ ] Verify cross-group data isolation
-   [ ] Verify provenance tracking end-to-end

---

## Files Modified

**Backend (apps/api):**

-   `app/models/bot.py` (add group_id, update constraint)
-   `app/models/document.py` (add group_id, uploader_id, deleted_at)
-   `app/models/chunk.py` (add group_id, source_metadata, update index)
-   `app/models/group.py` (NEW)
-   `app/models/group_member.py` (NEW)
-   `app/api/v1/schemas.py` (add group, group_member, update bot/document schemas)
-   `app/api/v1/bots.py` (group-scoped routes, role checks)
-   `app/api/v1/documents.py` (group-scoped upload, provenance)
-   `app/api/v1/groups.py` (NEW: CRUD + membership)
-   `app/services/bot_service.py` (update to group-scoped)
-   `app/services/document_service.py` (update to group-scoped)
-   `app/services/ingestion_service.py` (add provenance tracking)
-   `app/core/security.py` (add role decorators)
-   `alembic/versions/006_add_groups_and_provenance.py` (NEW: migration)

**Frontend (apps/web):**

-   `src/app/settings/page.tsx` (update to group-scoped)
-   `src/components/GroupSwitcher.tsx` (NEW)
-   `src/app/bots/page.tsx` (update for group-scoped, role checks)
-   `src/app/documents/page.tsx` (update for group KB, metadata)
-   `src/app/groups/page.tsx` (NEW: group management)

---

## Timeline

-   **Phase 1:** Models + Migration (1-2 days)
-   **Phase 2:** API Routes + Schemas (2 days)
-   **Phase 3:** Services + RLS (2 days)
-   **Phase 4:** Frontend (2 days)
-   **Phase 5:** Testing (1-2 days)

**Total:** ~1 week for full implementation

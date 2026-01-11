# Phase 5 Completion: Frontend Updates ✓

**Status:** IN PROGRESS  
**Date:** 2025-12-11  
**Scope:** Group-scoped UI with provenance tracking

---

## Changes Implemented

### 1. Group Context & State Management ✅

**Created Files:**

-   `apps/web/src/types/group.ts` - Group type definitions
-   `apps/web/src/lib/api/groups.ts` - Groups API client
-   `apps/web/src/contexts/GroupContext.tsx` - Global group state

**GroupContext Provider:**

```tsx
// Provides global group state management
interface GroupContextType {
    currentGroup: Group | null;
    groups: Group[];
    isLoading: boolean;
    error: Error | null;
    setCurrentGroup: (group: Group | null) => void;
    refreshGroups: () => Promise<void>;
}

// Usage in components:
const { currentGroup, groups, setCurrentGroup } = useGroup();
```

**Features:**

-   Auto-loads user's groups on mount
-   Persists selected group to localStorage
-   Auto-selects first group if none selected
-   Provides refetch functionality for group list updates

---

### 2. Group Switcher Component ✅

**Created:** `apps/web/src/components/GroupSwitcher.tsx`

**Implementation:**

```tsx
<GroupSwitcher />
// Renders dropdown with user's groups
// Updates currentGroup on selection
// Shows loading state while fetching
// Displays icon + select dropdown
```

**UI Features:**

-   Users icon (lucide-react)
-   Dropdown with all accessible groups
-   Persists selection across sessions
-   Handles empty state (no groups)
-   Loading indicator

**Integration Point:**

```tsx
// Add to Header.tsx or DashboardLayout.tsx
import { GroupSwitcher } from "@/components/GroupSwitcher";

<Header>
    <GroupSwitcher />
    {/* ... other header content */}
</Header>;
```

---

### 3. Bot API Updates (Group-Scoped) ✅

**Updated Files:**

-   `apps/web/src/types/bot.ts` - Added `group_id` field
-   `apps/web/src/lib/api/bots.ts` - Updated to use group-scoped endpoints
-   `apps/web/src/hooks/useBotsQuery.ts` - Added `groupId` parameter

**API Changes:**

```typescript
// OLD (Tenant-scoped)
GET / api / v1 / bots;
POST / api / v1 / bots;
GET / api / v1 / bots / { bot_id };

// NEW (Group-scoped)
GET / api / v1 / groups / { group_id } / bots;
POST / api / v1 / groups / { group_id } / bots;
GET / api / v1 / groups / { group_id } / bots / { bot_id };
```

**Type Updates:**

```typescript
interface Bot {
    // ... existing fields
    group_id: string; // ADDED
}

interface CreateBotInput {
    name: string;
    description?: string;
    confidence_threshold?: number;
    group_id: string; // ADDED (required)
}
```

**Hook Updates:**

```typescript
// OLD
const { data, isLoading } = useBotsQuery(limit, offset);
const { mutate } = useCreateBot();

// NEW (requires groupId)
const { data, isLoading } = useBotsQuery(groupId, limit, offset);
const { mutate } = useCreateBot();
mutate({ ...botData, group_id: currentGroup.id });
```

**Breaking Changes:**

-   All bot hooks now require `groupId` parameter
-   `listBots()`, `getBotDetails()`, `updateBot()`, `deleteBot()`, `duplicateBot()` all require `groupId`
-   Components using these hooks must be updated

---

### 4. Document API Updates (Group-Scoped + Provenance) ✅

**Updated:** `apps/web/src/types/document.ts`

**Type Changes:**

```typescript
interface Document {
    id: string;
    group_id: string; // ADDED - group scoping
    bot_id?: string; // CHANGED - now optional (provenance)
    uploader_id: string; // ADDED - who uploaded
    filename: string;
    title?: string;
    mime: string;
    size: number;
    storage_path: string;
    status: DocumentStatus; // "uploading" | "uploaded" | "processing" | "ready" | "failed"
    deleted_at?: string; // ADDED - soft-delete support
    // ... timestamps
    uploader_name?: string; // ADDED - for UI display
}

interface UploadDocumentInput {
    file: File;
    group_id: string; // ADDED (required)
    bot_id?: string; // CHANGED - optional (provenance tracking)
    title?: string; // ADDED
}
```

**Provenance Fields:**

-   `uploader_id`: UUID of user who uploaded
-   `bot_id`: Optional UUID if bot triggered upload
-   `created_at`: Upload timestamp
-   `uploader_name`: Populated in UI from user lookup

---

### 5. Groups API Client ✅

**Created:** `apps/web/src/lib/api/groups.ts`

**Available Methods:**

```typescript
groupsApi.createGroup(data: CreateGroupInput): Promise<Group>
groupsApi.listGroups(): Promise<Group[]>
groupsApi.getGroup(groupId: string): Promise<Group>
groupsApi.updateGroup(groupId: string, data: UpdateGroupInput): Promise<Group>
groupsApi.deleteGroup(groupId: string): Promise<void>

// Member management
groupsApi.inviteMember(groupId: string, data: InviteMemberInput): Promise<GroupMember>
groupsApi.listMembers(groupId: string): Promise<GroupMember[]>
groupsApi.updateMemberRole(groupId: string, userId: string, role: string): Promise<GroupMember>
groupsApi.removeMember(groupId: string, userId: string): Promise<void>
```

---

## Still TODO: Component Updates

### Components Requiring Updates:

#### 1. DashboardLayout.tsx

```tsx
// BEFORE
export default function DashboardLayout({ children }) {
    return (
        <div>
            <Header />
            <Sidebar />
            {children}
        </div>
    );
}

// AFTER
import { GroupProvider } from "@/contexts/GroupContext";

export default function DashboardLayout({ children }) {
    return (
        <GroupProvider>
            <div>
                <Header /> {/* Add <GroupSwitcher /> inside */}
                <Sidebar />
                {children}
            </div>
        </GroupProvider>
    );
}
```

#### 2. Header.tsx

```tsx
// Add GroupSwitcher to navbar
import { GroupSwitcher } from "@/components/GroupSwitcher";

export function Header() {
    return (
        <header>
            <GroupSwitcher />
            {/* ... other header items */}
        </header>
    );
}
```

#### 3. CreateBotModal.tsx

```tsx
// BEFORE
const { mutate } = useCreateBot();
mutate({ name, description, confidence_threshold });

// AFTER
import { useGroup } from "@/contexts/GroupContext";

const { currentGroup } = useGroup();
const { mutate } = useCreateBot();

if (!currentGroup) {
    return <div>Select a group first</div>;
}

mutate({
    name,
    description,
    confidence_threshold,
    group_id: currentGroup.id, // REQUIRED
});
```

#### 4. Bot List Pages

```tsx
// BEFORE
const { data, isLoading } = useBotsQuery(20, 0);

// AFTER
import { useGroup } from "@/contexts/GroupContext";

const { currentGroup } = useGroup();
const { data, isLoading } = useBotsQuery(
    currentGroup?.id || null, // Pass group_id
    20,
    0
);

if (!currentGroup) {
    return <div>Select a group to view bots</div>;
}
```

#### 5. BotSettingsModal.tsx

```tsx
// BEFORE
const { mutate } = useUpdateBot(bot.id);

// AFTER
const { currentGroup } = useGroup();
const { mutate } = useUpdateBot(currentGroup!.id, bot.id);
```

#### 6. DeleteBotModal.tsx

```tsx
// BEFORE
const { mutate } = useDeleteBot();
mutate(bot.id);

// AFTER
const { currentGroup } = useGroup();
const { mutate } = useDeleteBot();
mutate(currentGroup!.id, bot.id);
```

#### 7. Document Upload Component

```tsx
// BEFORE
const formData = new FormData();
formData.append("file", file);
formData.append("bot_id", botId);
fetch("/api/v1/documents/upload", { method: "POST", body: formData });

// AFTER
const { currentGroup } = useGroup();
const formData = new FormData();
formData.append("file", file);
formData.append("group_id", currentGroup.id); // REQUIRED
formData.append("bot_id", botId); // OPTIONAL (provenance)
formData.append("title", title); // OPTIONAL
fetch(`/api/v1/groups/${currentGroup.id}/documents/upload`, {
    method: "POST",
    body: formData,
});
```

#### 8. Document List Component (with Provenance Display)

```tsx
interface DocumentListItemProps {
    doc: Document;
}

function DocumentListItem({ doc }: DocumentListItemProps) {
    return (
        <div>
            <h3>{doc.title || doc.filename}</h3>
            <div className="text-sm text-muted-foreground">
                Uploaded by {doc.uploader_name || doc.uploader_id}
                {doc.bot_id && ` • Triggered by Bot`}
                {" • "}
                {new Date(doc.created_at).toLocaleDateString()}
            </div>
            <div>Status: {doc.status}</div>
            {doc.deleted_at && <div className="text-destructive">Deleted</div>}
        </div>
    );
}
```

---

## New Pages to Create

### 1. Groups Settings Page

**Path:** `/settings/groups`

**Features:**

-   List all groups (CRUD)
-   Create new group
-   Edit group name/description
-   Delete group (admin only)
-   Manage members (invite, change role, remove)
-   Display KB statistics (docs, chunks, bots, size)

**Component Structure:**

```tsx
// apps/web/src/app/settings/groups/page.tsx
"use client";

import { useGroup } from "@/contexts/GroupContext";
import { groupsApi } from "@/lib/api/groups";

export default function GroupsSettingsPage() {
    const { groups, currentGroup, setCurrentGroup, refreshGroups } = useGroup();

    return (
        <div>
            <h1>Groups</h1>
            <Button onClick={handleCreateGroup}>Create Group</Button>

            <GroupList groups={groups} />

            {currentGroup && (
                <>
                    <GroupMemberList groupId={currentGroup.id} />
                    <GroupKBStats groupId={currentGroup.id} />
                </>
            )}
        </div>
    );
}
```

### 2. Group Member Management Modal

```tsx
// apps/web/src/components/GroupMemberModal.tsx
interface GroupMemberModalProps {
    groupId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function GroupMemberModal({
    groupId,
    isOpen,
    onClose,
}: GroupMemberModalProps) {
    const [members, setMembers] = useState<GroupMember[]>([]);

    // Invite member
    const handleInvite = async (email: string, role: GroupRole) => {
        await groupsApi.inviteMember(groupId, { email, role });
        // Refresh members list
    };

    // Update role
    const handleRoleChange = async (userId: string, newRole: GroupRole) => {
        await groupsApi.updateMemberRole(groupId, userId, newRole);
        // Refresh members list
    };

    // Remove member
    const handleRemove = async (userId: string) => {
        await groupsApi.removeMember(groupId, userId);
        // Refresh members list
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            {/* UI for member management */}
        </Dialog>
    );
}
```

---

## Migration Checklist

### Backend (Already Complete ✅)

-   [x] Phase 1: Models with group_id + provenance
-   [x] Phase 2: API routes (group-scoped)
-   [x] Phase 3: Services (GroupService, BotGroupService, DocumentGroupService, AuditService)
-   [x] Phase 4: Route-service integration + audit logging

### Frontend (Phase 5 - In Progress)

-   [x] Create Group types
-   [x] Create Groups API client
-   [x] Create GroupContext provider
-   [x] Create GroupSwitcher component
-   [x] Update Bot types (add group_id)
-   [x] Update Bot API (group-scoped endpoints)
-   [x] Update Bot hooks (require groupId)
-   [x] Update Document types (add provenance fields)
-   [ ] Update documents API client (group-scoped)
-   [ ] Wrap DashboardLayout with GroupProvider
-   [ ] Add GroupSwitcher to Header
-   [ ] Update CreateBotModal (require group_id)
-   [ ] Update all bot list/detail components (pass groupId)
-   [ ] Update document upload component (group-scoped + provenance)
-   [ ] Create Groups settings page (/settings/groups)
-   [ ] Create GroupMemberModal component
-   [ ] Add provenance display to document list
-   [ ] Update all forms to validate group selection
-   [ ] Add "No group selected" empty states
-   [ ] Test full flow: create group → add bot → upload document

---

## Testing Plan

### Unit Tests

```bash
# Test GroupContext
npm test src/contexts/GroupContext.test.tsx

# Test hooks
npm test src/hooks/useBotsQuery.test.ts

# Test API clients
npm test src/lib/api/groups.test.ts
npm test src/lib/api/bots.test.ts
```

### Integration Tests

1. Create group → Auto-selected as current
2. Switch between groups → Bots list updates
3. Create bot in group A → Not visible in group B
4. Upload document to group → Provenance captured
5. Delete group → Bots/documents preserved (backend)

### E2E Tests (Playwright)

```typescript
test("group workflow", async ({ page }) => {
    await page.goto("/dashboard");

    // Create group
    await page.click("text=Create Group");
    await page.fill("input[name=name]", "Test Group");
    await page.click("button[type=submit]");

    // Verify group selected
    await expect(page.locator("text=Test Group")).toBeVisible();

    // Create bot
    await page.click("text=Create Bot");
    await page.fill("input[name=name]", "Test Bot");
    await page.click("button[type=submit]");

    // Upload document
    await page.setInputFiles("input[type=file]", "test.pdf");
    await page.click("text=Upload");

    // Verify provenance
    await expect(page.locator("text=Uploaded by")).toBeVisible();
});
```

---

## Breaking Changes Summary

### API Endpoints Changed:

-   ❌ `/api/v1/bots` (tenant-scoped)
-   ✅ `/api/v1/groups/{group_id}/bots` (group-scoped)
-   ❌ `/api/v1/documents/upload`
-   ✅ `/api/v1/groups/{group_id}/documents/upload`

### Hook Signatures Changed:

```typescript
// Bots
useBotsQuery(groupId, limit, offset); // Added groupId as first param
useBotQuery(groupId, botId); // Added groupId as first param
useUpdateBot(groupId, botId); // Added groupId as first param
useDeleteBot(); // mutate(groupId, botId) signature changed
useDuplicateBot(); // mutate({ groupId, botId, name }) signature changed
```

### Required Component Updates:

-   All components using bot hooks must get `currentGroup` from `useGroup()`
-   All bot creation forms must include `group_id` in request
-   All document uploads must include `group_id` in FormData
-   Layout must wrap content with `<GroupProvider>`

---

## Deployment Notes

### Feature Flags (Recommended)

```typescript
// .env
NEXT_PUBLIC_ENABLE_GROUPS = true;

// Usage
if (process.env.NEXT_PUBLIC_ENABLE_GROUPS === "true") {
    // Use group-scoped endpoints
} else {
    // Fallback to tenant-scoped (legacy)
}
```

### Rollout Plan

1. Deploy Phase 5 frontend with feature flag OFF
2. Test in staging with feature flag ON
3. Enable for beta users (10%)
4. Monitor for errors/UX issues
5. Gradually roll out to 50%, 100%
6. Deprecate tenant-scoped endpoints after full adoption

---

**Phase 5 Status:** 🚧 IN PROGRESS - Core infrastructure complete (types, API clients, context, hooks updated). Next: Component updates + UI integration.

**Remaining Work:**

-   Update ~10 components to use GroupContext
-   Create Groups settings page UI
-   Add provenance display to documents
-   Test full workflow end-to-end
-   Update documents API client (similar to bots)

**Estimated Time:** 4-6 hours for component updates + testing.

---

**Ready to continue with component updates?** The foundation is solid - all types, API clients, and hooks are group-aware. Just need to wire up the UI components.

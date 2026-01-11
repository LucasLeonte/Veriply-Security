# Story Update: Epic 2 Refactor - COMPLETED

**Status:** ✅ Applied  
**Date Completed:** 2025-12-11  
**Updated Stories:** 2.1, 2.2, 2.4, 2.5  
**Modified File:** docs/epics.md

---

## Summary of Changes Applied

All updates from **STORY-UPDATE-EPIC2-GROUP-MODEL.md** have been successfully applied to the Epic 2 stories in `docs/epics.md`.

### Story 2.1: Bot Creation & Configuration

✅ **Permissions:** Updated to "Manager or Group Admin" (Operators cannot create)
✅ **Technical Notes:** Changed "All bots in a group read/write to the same KB" with emphasis on "not isolated per bot"
✅ **Database:** Explicitly stated "RLS enforced"
✅ **Prereq:** Confirmed Story 1.8

### Story 2.2: Bot Update & Deletion

✅ **Deletion Warning:** Enhanced message to include "All chat sessions for this bot will be deleted"
✅ **KB Preservation:** Changed "shared across group" → "shared with other group bots"
✅ **Provenance:** Added AC: "documents contributed by this bot remain in Group KB (provenance preserved)"
✅ **Cascade Delete:** Updated technical note to state "bot → chat_sessions only (NOT documents/chunks)"

### Story 2.4: Document Upload to Group KB

✅ **Metadata Recording:** Expanded AC to show all metadata fields:

-   tenant_id (for RLS)
-   group_id (group-scoped KB)
-   bot_id (optional; which bot triggered upload)
-   uploader_id (user who uploaded)
-   created_at (timestamp)
    ✅ **Visibility:** Added AC: "all uploaded documents are visible to all group members in the shared KB"
    ✅ **Database:** Updated tech note from "tenant/group/bot path prefix" → "tenant/group path prefix"
    ✅ **Covers:** Explicitly listed "group-scoped"

### Story 2.5: Document Processing Pipeline with Provenance

✅ **Title & Goal:** Updated "we can track which bot contributed to the KB" → "provenance is preserved for audit and tracking"
✅ **Metadata Expanded:** Each metadata field now has explicit purpose:

-   tenant_id (for RLS)
-   group_id (group-scoped KB)
-   bot_id (which bot the doc was uploaded for)
-   document_id (reference to parent document)
-   chunk_index (position in document)
-   created_at (when processed)
-   source metadata (filename, page/row)
    ✅ **Indexing:** Changed from "IVFFlat" → "composite index (tenant_id, group_id, embedding)" for RLS-aware queries
    ✅ **Source Metadata:** Updated "for citation" instead of generic inclusion
    ✅ **Technical Notes Comprehensive:** Complete table schema, composite index strategy, RLS policy, embedding model specified
    ✅ **Covers:** Updated to "FR14, FR15, FR16 (with group/bot provenance)"

---

## Verification Checklist

-   [x] Story 2.1 permissions restricted to Manager+
-   [x] Story 2.2 deletion behavior updated (KB preserved, documents remain)
-   [x] Story 2.4 metadata fields documented
-   [x] Story 2.5 provenance details expanded with composite index strategy
-   [x] All technical notes clarified with RLS context
-   [x] All stories reference group-scoped model (not tenant-scoped)
-   [x] Prerequisite chains verified (1.8 → 2.1 → 2.2/2.3 → 2.4 → 2.5)
-   [x] Coverage map reflects group/bot provenance (FRs 7-16 group-scoped)
-   [x] Embedding model confirmed: nomic-embed-text (1024 dimensions)
-   [x] RLS policy explicitly stated in 2.5 technical notes

---

## Next Steps for Dev

1. **Implement Stories 2.1–2.5** in order per prerequisite chain
2. **Cross-reference with Story 9 tests** (especially 9.1, 9.2, 9.3, 9.5 for provenance and RLS validation)
3. **Database migration**: Create `bots(tenant_id, group_id, ...)` and `document_chunks(tenant_id, group_id, bot_id, ...)` with composite RLS policy
4. **API endpoints** should enforce RBAC decorators (Manager+ for create/delete, Operator for upload)
5. **FAQ from update guide**:
    - ✓ Duplication feature: Not mentioned in final stories (kept focus on create/update/delete)
    - ✓ Embedding model: Confirmed nomic-embed-text
    - ✓ Soft-delete: Should track in audit_logs table (covered in Story 9.5)

---

## Files Updated

-   **Primary:** `docs/epics.md` (Epic 2, Stories 2.1, 2.2, 2.4, 2.5)
-   **Reference:** `docs/sprint-artifacts/STORY-UPDATE-EPIC2-GROUP-MODEL.md` (update guide)
-   **Related:**
    -   `docs/tech-spec.md` (already aligned with group model)
    -   `docs/architecture.md` (already aligned with group/bot/KB sections)

---

## Ready for Implementation

Epic 2 stories are now **aligned with the group model** (Tenant → Group → Bots with shared KB and provenance).

Dev can proceed with implementation using these updated stories as the source of truth.

# Story 2-5: Knowledge Base Management UI - Design Specification

**Story ID:** 2-5-knowledge-base-management-ui  
**Designer:** Soulaymane  
**Date:** 2025-12-10  
**Status:** In Progress

---

## 1. Overview

This design spec covers the Knowledge Base Management UI, which allows users to:
- View all documents uploaded to a bot's knowledge base
- Search and filter documents
- Upload new documents
- View document details (metadata, processing status, chunks)
- Delete documents
- Trigger reprocessing of documents

The UI follows Veriply's design system (shadcn/ui + Tailwind CSS) with the "Simple SaaS" aesthetic inspired by Chatbase.

---

## 2. User Stories & Acceptance Criteria

### Primary User Story
> As a **Bot Administrator**, I want to **manage my bot's knowledge base documents** so that I can **ensure my bot has accurate, up-to-date information to answer questions**.

### Acceptance Criteria
- **AC1:** User can view a list of all documents for a selected bot
- **AC2:** User can upload new documents (PDF, TXT, DOCX, MD) via drag-and-drop or file picker
- **AC3:** User can search documents by name
- **AC4:** User can view document details including processing status, chunk count, and metadata
- **AC5:** User can delete documents with confirmation
- **AC6:** User can trigger document reprocessing
- **AC7:** UI shows real-time processing status updates
- **AC8:** UI is responsive (desktop-first, mobile-friendly)
- **AC9:** UI is accessible (keyboard navigation, ARIA labels, screen reader support)

---

## 3. Information Architecture

### Route Structure
```
/dashboard/bots/[botId]/knowledge-base
  ├─ / (main list view)
  ├─ /upload (upload modal overlay)
  └─ /[documentId] (document detail view)
```

### Navigation
- Access from Bot Settings or Bot Card → "Knowledge Base" button
- Breadcrumb: Dashboard → Bots → [Bot Name] → Knowledge Base
- Tab navigation within bot context: Overview | Knowledge Base | Settings

---

## 4. Wireframes

### 4.1 Desktop - List View (Main Screen)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [Header]                                              [User Menu] ▼     │
├─────────────────────────────────────────────────────────────────────────┤
│ Sidebar │                                                               │
│         │  Dashboard > Bots > HR Support Bot > Knowledge Base          │
│ Bots    │                                                               │
│ Inbox   │  ┌────────────────────────────────────────────────────────┐  │
│ KB      │  │ Knowledge Base                                         │  │
│ Settings│  │                                                         │  │
│         │  │ ┌──────────────────────────┐  [+ Upload Documents]    │  │
│         │  │ │ 🔍 Search documents...   │                          │  │
│         │  │ └──────────────────────────┘                          │  │
│         │  │                                                         │  │
│         │  │ Showing 8 documents                                    │  │
│         │  │                                                         │  │
│         │  │ ┌─────────────────────────────────────────────────┐   │  │
│         │  │ │ 📄 Employee Handbook 2024.pdf                   │   │  │
│         │  │ │ ✓ Processed • 42 chunks • 128 KB                │   │  │
│         │  │ │ Uploaded Jan 15, 2025                      [⋮]  │   │  │
│         │  │ └─────────────────────────────────────────────────┘   │  │
│         │  │                                                         │  │
│         │  │ ┌─────────────────────────────────────────────────┐   │  │
│         │  │ │ 📄 PTO Policy.docx                              │   │  │
│         │  │ │ ⏳ Processing... 60%                            │   │  │
│         │  │ │ Uploaded Jan 20, 2025                      [⋮]  │   │  │
│         │  │ └─────────────────────────────────────────────────┘   │  │
│         │  │                                                         │  │
│         │  │ ┌─────────────────────────────────────────────────┐   │  │
│         │  │ │ 📄 Benefits Guide.pdf                           │   │  │
│         │  │ │ ❌ Failed • Error: File corrupted               │   │  │
│         │  │ │ Uploaded Jan 18, 2025                      [⋮]  │   │  │
│         │  │ └─────────────────────────────────────────────────┘   │  │
│         │  │                                                         │  │
│         │  │ [Show more...] Page 1 of 3                            │  │
│         │  └────────────────────────────────────────────────────────┘  │
│         │                                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Desktop - Upload Modal

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [Dimmed Background]                                                     │
│                                                                          │
│         ┌───────────────────────────────────────────────────┐          │
│         │ Upload Documents                             [×]  │          │
│         ├───────────────────────────────────────────────────┤          │
│         │                                                   │          │
│         │  ┌─────────────────────────────────────────────┐ │          │
│         │  │                                             │ │          │
│         │  │         📤  Drag & drop files here         │ │          │
│         │  │                    or                       │ │          │
│         │  │            [Browse Files]                   │ │          │
│         │  │                                             │ │          │
│         │  │  Supported: PDF, TXT, DOCX, MD             │ │          │
│         │  │  Max size: 10 MB per file                  │ │          │
│         │  └─────────────────────────────────────────────┘ │          │
│         │                                                   │          │
│         │  Selected Files:                                 │          │
│         │  ✓ onboarding-guide.pdf (2.4 MB)          [×]   │          │
│         │  ✓ faq-internal.txt (45 KB)               [×]   │          │
│         │                                                   │          │
│         │                    [Cancel]  [Upload 2 files]   │          │
│         └───────────────────────────────────────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Desktop - Document Detail View

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [Header]                                              [User Menu] ▼     │
├─────────────────────────────────────────────────────────────────────────┤
│ Sidebar │                                                               │
│         │  Dashboard > Bots > HR Bot > KB > Employee Handbook.pdf      │
│         │                                                               │
│         │  ┌────────────────────────────────────────────────────────┐  │
│         │  │ ← Back to Knowledge Base                               │  │
│         │  │                                                         │  │
│         │  │ 📄 Employee Handbook 2024.pdf                          │  │
│         │  │ ✓ Processed successfully                               │  │
│         │  │                                                         │  │
│         │  │ ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐ │  │
│         │  │ │ 📊 Details   │ │ 📑 Chunks    │ │ ⚙️ Actions      │ │  │
│         │  │ └──────────────┘ └──────────────┘ └─────────────────┘ │  │
│         │  │                                                         │  │
│         │  │ Details                                                │  │
│         │  │ ────────────────────────────────────────────────────── │  │
│         │  │ File name:     Employee Handbook 2024.pdf             │  │
│         │  │ File size:     128 KB                                 │  │
│         │  │ Uploaded:      Jan 15, 2025 2:30 PM                   │  │
│         │  │ Status:        Processed                              │  │
│         │  │ Chunks:        42 chunks                              │  │
│         │  │ Embeddings:    42 vectors indexed                     │  │
│         │  │                                                         │  │
│         │  │ Chunks Preview (42 total)                             │  │
│         │  │ ────────────────────────────────────────────────────── │  │
│         │  │ Chunk 1: "Welcome to the company! This handbook..."   │  │
│         │  │ Chunk 2: "Our mission is to provide exceptional..."   │  │
│         │  │ Chunk 3: "Employee benefits include health..."        │  │
│         │  │ [Load more chunks...]                                 │  │
│         │  │                                                         │  │
│         │  │ Actions                                                │  │
│         │  │ ────────────────────────────────────────────────────── │  │
│         │  │ [🔄 Reprocess Document]  [🗑️ Delete Document]         │  │
│         │  │                                                         │  │
│         │  └────────────────────────────────────────────────────────┘  │
│         │                                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Mobile - List View

```
┌──────────────────────────┐
│ [☰]  Knowledge Base  [👤]│
├──────────────────────────┤
│                          │
│ ┌──────────────────────┐ │
│ │ 🔍 Search...         │ │
│ └──────────────────────┘ │
│                          │
│ [+ Upload Documents]     │
│                          │
│ 8 documents              │
│                          │
│ ┌──────────────────────┐ │
│ │ 📄 Employee Handbook │ │
│ │ ✓ Processed          │ │
│ │ 42 chunks • 128 KB   │ │
│ │ Jan 15, 2025    [⋮] │ │
│ └──────────────────────┘ │
│                          │
│ ┌──────────────────────┐ │
│ │ 📄 PTO Policy        │ │
│ │ ⏳ Processing 60%    │ │
│ │ Jan 20, 2025    [⋮] │ │
│ └──────────────────────┘ │
│                          │
│ [Load more...]           │
│                          │
└──────────────────────────┘
```

---

## 5. Component Breakdown

### 5.1 Core Components

| Component | File | Purpose |
|-----------|------|---------|
| `KnowledgeBaseList` | `components/kb/KnowledgeBaseList.tsx` | Main list container with search, upload button, document cards |
| `DocumentCard` | `components/kb/DocumentCard.tsx` | Individual document card with status, metadata, actions menu |
| `DocumentDetail` | `components/kb/DocumentDetail.tsx` | Detail view with tabs for metadata, chunks, actions |
| `UploadModal` | `components/kb/UploadModal.tsx` | Modal for drag-drop upload with file list |
| `SearchBar` | `components/kb/SearchBar.tsx` | Debounced search input |
| `StatusBadge` | `components/kb/StatusBadge.tsx` | Status indicator (Processed/Processing/Failed) |
| `ConfirmDeleteDialog` | `components/kb/ConfirmDeleteDialog.tsx` | Confirmation dialog for deletion |
| `Pagination` | `components/kb/Pagination.tsx` | Pagination controls |

### 5.2 Component Hierarchy

```
KnowledgeBasePage
├─ DashboardLayout
│  └─ KnowledgeBaseList
│     ├─ SearchBar
│     ├─ Button (Upload)
│     ├─ DocumentCard[] (list)
│     │  ├─ StatusBadge
│     │  └─ DropdownMenu (actions)
│     └─ Pagination
├─ UploadModal (dialog)
└─ ConfirmDeleteDialog (dialog)

DocumentDetailPage
└─ DashboardLayout
   └─ DocumentDetail
      ├─ Tabs
      │  ├─ TabPanel (Details)
      │  ├─ TabPanel (Chunks)
      │  └─ TabPanel (Actions)
      └─ ActionButtons
```

---

## 6. Interactions & State Management

### 6.1 Key User Flows

#### Flow 1: Upload Document
1. User clicks "+ Upload Documents"
2. UploadModal opens
3. User drags file OR clicks "Browse Files"
4. File(s) added to selected list
5. User clicks "Upload N files"
6. API call to POST /api/v1/bots/{botId}/documents
7. Modal shows progress
8. On success: Modal closes, list refreshes, toast notification
9. On error: Error message shown in modal

#### Flow 2: Delete Document
1. User clicks "⋮" menu on DocumentCard
2. User clicks "Delete"
3. ConfirmDeleteDialog opens
4. User confirms deletion
5. API call to DELETE /api/v1/kb/{documentId}
6. On success: Card removed from list, toast notification
7. On error: Error dialog

#### Flow 3: View Document Details
1. User clicks on DocumentCard
2. Navigate to /dashboard/bots/{botId}/knowledge-base/{documentId}
3. DocumentDetail component loads document data
4. Display metadata, chunks, processing status
5. User can trigger reprocess or delete from this view

#### Flow 4: Reprocess Document
1. User clicks "Reprocess" from detail view or card menu
2. Confirmation dialog opens
3. User confirms
4. API call to POST /api/v1/kb/{documentId}/reprocess
5. Status updates to "Processing"
6. Real-time status updates via polling or WebSocket
7. On complete: Status updates to "Processed"

### 6.2 State Requirements

```typescript
interface KnowledgeBaseState {
  documents: Document[]
  loading: boolean
  error: string | null
  searchQuery: string
  currentPage: number
  totalPages: number
  selectedDocument: Document | null
  uploadModalOpen: boolean
  deleteDialogOpen: boolean
  documentToDelete: Document | null
}

interface Document {
  id: string
  botId: string
  filename: string
  fileSize: number
  status: 'pending' | 'processing' | 'processed' | 'failed'
  processingProgress?: number
  errorMessage?: string
  chunkCount: number
  embeddingCount: number
  uploadedAt: string
  processedAt?: string
}
```

---

## 7. Visual Design

### 7.1 Status Colors (from Tailwind config)

- **Processed (Success):** `emerald-600` (#16a34a)
- **Processing (In Progress):** `amber-500` (#f59e0b)
- **Failed (Error):** `red-600` (#dc2626)
- **Pending:** `slate-400` (#94a3b8)

### 7.2 Typography

- **Page Title:** `text-2xl font-semibold text-slate-900`
- **Card Title:** `text-lg font-medium text-slate-900`
- **Body Text:** `text-sm text-slate-600`
- **Metadata:** `text-xs text-slate-500`

### 7.3 Spacing & Layout

- Card padding: `p-4`
- Card gap: `space-y-4`
- Border: `border border-slate-200 rounded-lg`
- Hover effect: `hover:shadow-md transition-shadow`

---

## 8. Accessibility Requirements

### 8.1 Keyboard Navigation
- Tab order: Search → Upload button → Document cards → Pagination
- Enter/Space to activate buttons
- Escape to close modals
- Arrow keys for dropdown menus

### 8.2 ARIA Labels
- `<button aria-label="Upload documents">`
- `<input aria-label="Search documents" role="searchbox">`
- `<div role="status" aria-live="polite">` for processing status
- `<dialog aria-labelledby="modal-title" aria-modal="true">`

### 8.3 Screen Reader Support
- Status announcements for upload/delete actions
- Loading states announced
- Error messages associated with form fields

### 8.4 Color Contrast
- All text meets WCAG AA (4.5:1 for normal text)
- Status badges have sufficient contrast
- Focus indicators visible on all interactive elements

---

## 9. Responsive Behavior

### Desktop (≥1024px)
- Sidebar navigation visible
- Cards in grid layout (2-3 columns)
- Full search bar width
- Detailed metadata visible

### Tablet (768px - 1023px)
- Sidebar collapsible
- Cards in 2-column grid
- Condensed metadata

### Mobile (<768px)
- Bottom navigation OR hamburger menu
- Single column card layout
- Simplified card view (hide some metadata)
- Sticky upload button
- Bottom sheet for actions menu

---

## 10. Error States & Edge Cases

### Empty State
```
┌────────────────────────────────────┐
│   📄                               │
│   No documents yet                 │
│                                    │
│   Upload your first document to    │
│   build your knowledge base        │
│                                    │
│   [+ Upload Documents]             │
└────────────────────────────────────┘
```

### Error States
- **Upload failed:** Show error message in modal with retry option
- **Delete failed:** Show error toast with retry option
- **Processing failed:** Show error badge on card with "View Error" link
- **Network error:** Global error toast with retry

### Loading States
- **Initial load:** Skeleton cards
- **Upload in progress:** Progress bar in modal
- **Document processing:** Progress indicator on card
- **Pagination load:** Loading spinner on "Load more" button

---

## 11. Technical Notes

### API Endpoints (to be implemented)
- `GET /api/v1/bots/{botId}/documents` - List documents
- `GET /api/v1/documents/{documentId}` - Get document details
- `POST /api/v1/bots/{botId}/documents` - Upload document(s)
- `DELETE /api/v1/documents/{documentId}` - Delete document
- `POST /api/v1/documents/{documentId}/reprocess` - Trigger reprocessing

### Real-time Updates
- Use polling (every 5s) for processing status updates
- Consider WebSocket for real-time updates in future iteration

### File Upload
- Client-side validation: file type, size
- Multi-file upload support
- Progress tracking per file

---

## 12. Future Enhancements (Out of Scope for v1)

- Bulk actions (select multiple, delete multiple)
- Document versioning
- Document preview (PDF viewer, text preview)
- Advanced filters (by date, status, file type)
- Sorting options
- Export document list
- Document tags/categories
- Duplicate detection

---

## 13. Design Assets

### Mockup Files
- Desktop wireframe: See section 4.1-4.3
- Mobile wireframe: See section 4.4
- Interactive prototype: TBD (Figma link)

### Icon Set
Using Lucide React icons:
- `FileText` - Document icon
- `Upload` - Upload icon
- `Search` - Search icon
- `MoreVertical` - Actions menu
- `Trash2` - Delete icon
- `RefreshCw` - Reprocess icon
- `CheckCircle` - Success status
- `AlertCircle` - Error status
- `Clock` - Processing status

---

## 14. Acceptance Checklist

- [ ] All wireframes reviewed and approved
- [ ] Component list finalized
- [ ] Interaction flows documented
- [ ] Accessibility requirements defined
- [ ] Responsive breakpoints specified
- [ ] Error states covered
- [ ] API contracts defined
- [ ] Design tokens aligned with Tailwind config
- [ ] Ready for implementation handoff

---

**Next Steps:**
1. Review this spec with team
2. Create components in `web/src/components/kb/`
3. Implement pages in `web/src/app/knowledge-base/`
4. Build API endpoints in `apps/api/`
5. Write tests
6. Conduct accessibility audit
7. Visual QA pass

---

_End of Design Specification_

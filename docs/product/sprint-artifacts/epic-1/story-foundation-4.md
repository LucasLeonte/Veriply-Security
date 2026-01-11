# Story 1.4: App Shell & Dashboard Layout

**Epic:** 1. Foundation & App Shell
**Status:** Done
**Context:** [Tech Spec](../tech-spec.md)

## Description

Build the main application layout using the "Deep Ocean" design system and Shadcn UI.

## Tasks

1. **Design System Setup:** ✅

    - Configure Tailwind colors (`slate-900`, `emerald-500`, `amber-500`) in `tailwind.config.ts`.
    - Install `shadcn-ui` components: Button, Avatar, ScrollArea, Sheet (for mobile).

2. **Layout Components:** ✅

    - Create `Sidebar` component (Desktop & Mobile).
    - Create `Header` component (User menu, Breadcrumbs).
    - Create `DashboardLayout` wrapper.

3. **Navigation:** ✅
    - Links: Dashboard, Inbox, Knowledge Base, Settings.
    - Active state styling (Emerald accent).

## Acceptance Criteria

-   [x] Sidebar matches the "Deep Ocean" theme (Slate 900 bg).
-   [x] Layout is responsive (Sidebar collapses to hamburger menu on mobile).
-   [x] Navigation links work and show active state.
-   [x] User avatar is displayed in the header.

## Technical Notes

-   **Reference:** `docs/ux-color-themes.html`.
-   **Icons:** Use `lucide-react`.
-   **Components Created:**
    -   `src/components/Sidebar.tsx` - Desktop/mobile sidebar with navigation
    -   `src/components/Header.tsx` - Header with user menu and avatar
    -   `src/components/DashboardLayout.tsx` - Main layout wrapper
    -   `src/components/ui/button.tsx` - Button component
    -   `src/components/ui/avatar.tsx` - Avatar component
    -   `src/components/ui/scroll-area.tsx` - Scroll area component
    -   `src/components/ui/sheet.tsx` - Mobile drawer component
-   **Config Updated:** `tailwind.config.ts` with Deep Ocean color palette and CSS variables in `globals.css`
-   **Test Pages:** Created routes for dashboard, inbox, knowledge-base, settings
-   **Dev Server:** Running on `http://localhost:3000`

## Dev Agent Record

### Completion Notes

**Completed:** 2025-12-03
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing, Tailwind CSS v3 properly configured, accessibility compliance achieved, all UI alignment issues resolved

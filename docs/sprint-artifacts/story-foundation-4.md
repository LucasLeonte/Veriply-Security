# Story 1.4: App Shell & Dashboard Layout

**Epic:** 1. Foundation & App Shell
**Status:** Ready for Development
**Context:** [Tech Spec](../tech-spec.md)

## Description
Build the main application layout using the "Deep Ocean" design system and Shadcn UI.

## Tasks
1.  **Design System Setup:**
    *   Configure Tailwind colors (`slate-900`, `emerald-500`, `amber-500`) in `tailwind.config.ts`.
    *   Install `shadcn-ui` components: Button, Avatar, ScrollArea, Sheet (for mobile).

2.  **Layout Components:**
    *   Create `Sidebar` component (Desktop & Mobile).
    *   Create `Header` component (User menu, Breadcrumbs).
    *   Create `DashboardLayout` wrapper.

3.  **Navigation:**
    *   Links: Dashboard, Inbox, Knowledge Base, Settings.
    *   Active state styling (Electric Teal accent).

## Acceptance Criteria
*   [ ] Sidebar matches the "Deep Ocean" theme (Slate 900 bg).
*   [ ] Layout is responsive (Sidebar collapses to hamburger menu on mobile).
*   [ ] Navigation links work and show active state.
*   [ ] User avatar is displayed in the header.

## Technical Notes
*   **Reference:** `docs/ux-color-themes.html`.
*   **Icons:** Use `lucide-react`.

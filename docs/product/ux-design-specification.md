# Veriply UX Design Specification

_Created on 2025-11-27 by Dario_
_Generated using BMad Method - Create UX Design Workflow v1.0_

---

## Executive Summary

Veriply is a **Trust-First AI Customer Service Platform** that prioritizes accuracy over speed. It features an **Internal Human-in-the-Loop (HITL)** workflow where support agents verify AI drafts before they are sent, building a "Verified Knowledge Base" over time.

**Target Users:**
*   **Support Agents:** Who need a productivity tool to review and approve AI drafts quickly.
*   **Admins/Knowledge Managers:** Who manage the knowledge base, integrations, and team roles.
*   **End-Customers:** Who receive accurate, safe answers (via chat or email) without knowing the complex verification process behind it.

---

## 1. Design System Foundation

### 1.1 Design System Choice

**System:** shadcn/ui (built on Radix UI + Tailwind CSS).
**Rationale:**
*   **Aesthetic:** Perfectly matches the "Simple SaaS" vibe (Chatbase style).
*   **Flexibility:** Provides unstyled primitives (Radix) for custom interactions (like the HITL diff view) while offering beautiful defaults.
*   **Accessibility:** Best-in-class keyboard navigation and screen reader support (critical for agent efficiency).
*   **Customization:** Easy to theme for the "Trust-First" color coding (Amber/Green).

---

## 2. Core User Experience

### 2.1 Defining Experience

**Core Experience:** Handling HITL (Human-in-the-Loop) reviews for unsolved tickets.
**Primary User Action:** Reviewing, editing, and approving AI-generated drafts for support tickets.
**Platform:** Web-based Dashboard (Desktop optimized for agents).

### 2.2 Desired Emotional Response

**Primary:** Safe & Confident ("The AI has my back, I just need to check").
**Secondary:** Efficient & Fast ("Let's crush this queue").
**Vibe:** A safety net that empowers speed. The UI should feel stable and trustworthy, not frantic.

### 2.3 Inspiration

**Chatbase:**
*   **Why:** Captures the "Simple SaaS" aesthetic perfectly. Clean, minimalist, card-based configuration.
*   **Application:** Use this vibe for the **Admin/Setup** pages (Knowledge Base management, Settings).

**Zendesk:**
*   **Why:** The gold standard for "Support Density". Handles lists, queues, and status indicators clearly without clutter.
*   **Application:** Use this structure for the **HITL Dashboard** (Ticket queues, diff views, status toggles).

**Synthesis:**
We aim for the **cleanliness of Chatbase** for setup, but the **utility/density of Zendesk** for the active workspace.

### 2.4 Novel UX Patterns

**The "Trust Gap" Visual System:**
AI-generated content lives in a visually distinct "Draft Zone" (amber border, subtle amber tint) until explicitly approved by a human. This creates a clear mental model: amber = unverified, green = safe to send.

**Flag-First Review Interface:**
When agents review a draft, the FIRST thing they see is WHY it was flagged—not the draft itself. This prioritizes understanding the risk before reading the content, enabling faster and more confident decisions.

**Keyboard-First Productivity:**
Inspired by Linear and Superhuman, power users can navigate the entire HITL workflow without touching a mouse:
- `J/K` - Navigate queue
- `Enter` - Open conversation
- `A` - Approve draft
- `E` - Edit draft
- `R` - Reject draft
- `⌘K` - Command palette

**Confidence-Driven Density:**
High-confidence AI responses (>90%) show a condensed view. Lower-confidence responses expand automatically to show more context, citations, and the specific flag trigger.

---

## 3. Visual Foundation

### 3.1 Design Direction: Cool Slate

**Theme Name:** Cool Slate
**Personality:** Professional, Tech-Trustworthy, Clean
**Inspiration:** Linear + Stripe (polished, keyboard-first, fast)
**Mode:** Light mode native (dark mode as secondary option)

**Primary Palette:**
*   **Background:** `#F8FAFC` (Slate 50) - Light, cool-toned canvas
*   **Surface:** `#FFFFFF` (White) - Cards and elevated elements
*   **Text Primary:** `#0F172A` (Slate 900) - High contrast for readability
*   **Text Secondary:** `#64748B` (Slate 500) - Muted labels and hints
*   **Border:** `#E2E8F0` (Slate 200) - Subtle dividers

**Accent Palette:**
*   **Primary Accent:** `#0EA5E9` (Sky 500) - Interactive elements, focus states
*   **Accent Hover:** `#0284C7` (Sky 600) - Hover states
*   **Accent Light:** `#E0F2FE` (Sky 100) - Selected backgrounds

**Semantic Palette (Trust Signals):**
*   **Verified/Success:** `#22C55E` (Green 500) - Human-verified, approved actions
*   **Pending/Warning:** `#F59E0B` (Amber 500) - AI drafts needing review
*   **Rejected/Error:** `#EF4444` (Red 500) - Errors, rejections, hallucinations

**Typography:**
*   **Font Family:** `Inter` - Clean, legible, standard for SaaS
*   **Headings:** Semibold (600), tight tracking (-0.02em)
*   **Body:** Regular (400), relaxed line height (1.6)
*   **UI Labels:** Medium (500), normal tracking

**Spacing & Layout:**
*   **Base Unit:** 4px (Tailwind standard)
*   **Layout:** 12-column grid with 24px gutters
*   **Border Radius:** XL for cards (12px), LG for buttons (8px), MD for inputs (6px)
*   **Shadows:** Subtle (`shadow-sm`) for depth, stronger on hover

**Interactive Visualizations:**

- Color Theme Explorer: [ux-color-themes-light.html](./ux-color-themes-light.html)
- Design Direction Mockup: [mockups/design-direction-coolslate.html](./mockups/design-direction-coolslate.html)
- Design Comparison: [mockups/design-comparison.html](./mockups/design-comparison.html)

---

## 4. Design Direction & Mockups

### 4.1. Layout Strategy: "Focused Density"
To balance the "Simple SaaS" setup with "Professional Support" density, we utilize a **3-Column Layout** for the primary Agent Dashboard.

1.  **Navigation (Left - Narrow)**:
    *   **Style**: Chatbase-inspired simplicity. Icon-only sidebar to maximize screen real estate.
    *   **Theme**: Deep Ocean (Slate 900) to anchor the app visually.

2.  **Ticket List (Middle - Compact)**:
    *   **Style**: Zendesk-inspired density. Compact rows with high information density (Status, Time, Preview).
    *   **Theme**: Light (White/Slate 50) for readability.

3.  **Workspace (Right - Wide)**:
    *   **Style**: Focus-driven. The conversation thread and AI tools take center stage.
    *   **Theme**: Clean canvas with distinct "Trust Zones" (Amber for AI, Green for Verified).

### 4.2. Mockups
We have generated interactive HTML mockups to visualize these concepts.

*   **[Color Theme Explorer](./ux-color-themes.html)**: Visualizes the "Deep Ocean Trust" palette and core UI components.
*   **[Agent Dashboard Wireframe](./mockups/agent-dashboard.html)**: Demonstrates the HITL workflow, showing how AI drafts are presented to agents for verification.

### 4.3. Key UX Patterns
*   **The "Trust Gap"**: AI content is visually separated from the conversation stream until approved. It lives in a distinct "Draft Card" (Amber) that requires an explicit "Bridge Action" (Clicking 'Approve') to enter the verified stream (Green/White).
*   **Confidence Indicators**: AI drafts display a confidence score to help agents prioritize their review effort.

---

## 5. User Journey Flows

### 5.0 User Personas & Priorities

**Sarah, the Support Agent**
- **Goal:** Process HITL queue efficiently with confidence
- **Priority Information (in order):**
  1. 🚩 Why it was flagged (the specific trigger)
  2. 😊 Customer sentiment indicator
  3. 💬 Conversation history + AI confidence score
- **Desired Emotion:** "I've got this, it's organized" → "I understand exactly what's needed" → "That was satisfying, next!"

**Marcus, the Operations Manager**
- **Goal:** Monitor team performance and AI effectiveness
- **Priority Views:** KPI dashboard, approval rates, agent performance, AI training feedback
- **Desired Emotion:** "I can see everything that matters" → "I know exactly where to dig in"

**Jamie, the End Customer**
- **Goal:** Get a quick, accurate answer to their question
- **Experience:** Seamless chat that feels helpful, not robotic
- **Desired Emotion:** "Wow that was fast AND helpful" (even if a human reviewed it behind the scenes)

### 5.1. Flow A: The "Trust-First" Ingestion Loop
This flow describes how a customer query is processed before it ever reaches a human agent.

1.  **Trigger**: Customer sends an email or submits a ticket via widget.
2.  **Ingestion & Safety**:
    *   System sanitizes input and redacts PII (Credit Cards, SSN).
    *   System queries the **Verified Knowledge Base** (Golden Dataset) first.
3.  **AI Processing**:
    *   **Scenario A (Verified Match)**: If a semantic match is found in the Verified KB (>95% similarity), the system retrieves the approved answer.
    *   **Scenario B (New Query)**: If no verified match, RAG retrieves context from raw documents and generates a fresh draft.
4.  **Output**:
    *   Ticket is created in the Dashboard.
    *   **Status**: "Needs Review".
    *   **Trust Signal**:
        *   *Verified Match* → **Green Badge** ("Verified Answer Available").
        *   *New Draft* → **Amber Badge** ("AI Draft - Confidence: 78%").

### 5.2. Flow B: The HITL Verification Loop (Core Workflow)
This is the primary interaction for the Support Agent, turning them from a "writer" into an "editor."

1.  **Select**: Agent clicks a ticket from the "Inbox" list.
2.  **Review**:
    *   Agent reads the Customer Query.
    *   Agent reviews the **Amber Draft Card**.
    *   *Crucial Step*: Agent checks the **Citations** (Sources) listed at the bottom of the card to verify accuracy.
3.  **Action**:
    *   **Path 1: Approve (The "Happy Path")**
        *   Agent clicks **"Approve & Send"** (Green Button).
        *   System sends response to customer.
        *   System saves the Q&A pair to the **Verified Knowledge Base**.
    *   **Path 2: Edit & Learn**
        *   Agent clicks **"Edit"**.
        *   Agent corrects the text (e.g., fixing a hallucinated policy).
        *   Agent clicks **"Approve & Send"**.
        *   System sends response.
        *   System records the **Diff** (AI vs. Human) to retrain the model.
    *   **Path 3: Reject**
        *   Agent clicks **"Discard"**.
        *   Draft is removed. Agent writes manually.
        *   System flags the query as a "Miss" for analysis.

---

## 6. Component Inventory (shadcn/ui)

To accelerate development, we will utilize the **shadcn/ui** component library. Below is the mapping of our UX requirements to specific components.

### 6.1. Core Layout & Navigation
*   **Sidebar**: Custom implementation using `flex-col` + `Button` (ghost variant) for navigation items.
*   **Ticket List**: `ScrollArea` for the list container.
*   **Ticket Item**: `Card` (hover variant) with `Badge` for status.
*   **Main Workspace**: `Resizable` (PanelGroup) to allow adjusting the width of the ticket list vs. workspace.

### 6.2. The "Trust Gap" Interface
*   **Draft Card**: `Card` with custom border colors (`border-amber-200`).
    *   **Header**: `CardHeader` with `CardTitle` (small).
    *   **Content**: `Textarea` (for editing the draft).
    *   **Actions**: `CardFooter` containing:
        *   `Button` (variant: `default` / `emerald`) for "Approve".
        *   `Button` (variant: `outline`) for "Edit".
        *   `Button` (variant: `ghost` / `destructive`) for "Discard".
*   **Trust Badges**: `Badge` component.
    *   Verified: `bg-emerald-100 text-emerald-800`.
    *   AI Draft: `bg-amber-100 text-amber-800`.

### 6.3. Conversation & Input
*   **Message Bubble**: Custom styled `div`.
*   **Avatar**: `Avatar` + `AvatarImage` / `AvatarFallback`.
*   **Reply Box**: `Textarea` (auto-resizing).
*   **Send Button**: `Button` with `Send` icon.

### 6.4. Feedback & Overlays
*   **Toast Notifications**: `Toast` (via `use-toast`) for "Draft Approved" or "Changes Saved" confirmation.
*   **Diff View**: `Dialog` or `Sheet` to show the comparison between AI Draft and Human Edit before final submission (optional but recommended for training).
*   **Loading States**: `Skeleton` for loading ticket lists and message threads.

---

## 7. UX Pattern Decisions

### 7.1 Consistency Rules

**Navigation Patterns:**
- Left sidebar: Icon-only (collapsed) or icon + label (expanded), slate-900 background
- Breadcrumbs: Only for deep navigation (Settings > Integrations > Slack)
- Command palette (`⌘K`): Global access to all actions

**Button Hierarchy:**
- Primary: Sky-500 fill, white text (main CTA per context)
- Success: Green-500 fill (Approve actions only)
- Danger: Red-500 fill (Reject/delete, requires confirmation)
- Secondary: White fill, slate border
- Ghost: No border, text only (navigation, tertiary actions)

**Trust Signal Badges:**
- Verified: Green-100 bg, Green-700 text, checkmark icon
- Pending: Amber-100 bg, Amber-700 text, clock icon
- Flagged: Red-100 bg, Red-700 text, alert icon

**Card Patterns:**
- Default: White bg, slate-200 border, shadow-sm
- Hover: shadow-md, sky-500 left border accent
- Selected: sky-50 bg, sky-500 left border
- Draft (AI): Amber-50 bg, amber-300 border (left accent)
- Approved: Green-50 bg, green-300 border (left accent)

**Empty States:**
- Centered illustration (simple, monochrome)
- Headline + explanation
- Single primary action button

**Loading States:**
- Skeleton loaders matching content shape
- Subtle pulse animation
- Never show spinners for < 300ms

**Feedback Patterns:**
- Toast notifications: Bottom-right, auto-dismiss after 3s
- Inline validation: Below input, red-500 text
- Success states: Green checkmark + brief message

---

## 8. Responsive Design & Accessibility

### 8.1 Responsive Strategy

**Breakpoints (Tailwind defaults):**
- `sm`: 640px (Mobile landscape)
- `md`: 768px (Tablet)
- `lg`: 1024px (Desktop)
- `xl`: 1280px (Large desktop)
- `2xl`: 1536px (Ultra-wide)

**Desktop-First Approach:**
The primary experience is optimized for desktop (1280px+) since support agents work on full-sized screens. Mobile serves as a "monitoring" view for managers, not a primary workflow.

**Layout Adaptations:**
- **Desktop (lg+):** Full 3-column layout (sidebar + list + workspace)
- **Tablet (md):** Collapsible sidebar, 2-column (list + workspace)
- **Mobile (sm):** Single column, bottom tab navigation, list-first view

**Chat Widget:**
- Fixed 400px width on desktop
- Full-screen takeover on mobile
- Respects system dark/light mode preference

### 8.2 Accessibility Requirements

**WCAG 2.1 AA Compliance:**
- Color contrast: Minimum 4.5:1 for body text, 3:1 for large text
- All interactive elements: Minimum 44x44px touch target
- Focus indicators: Visible 2px sky-500 ring on all focusable elements

**Keyboard Navigation:**
- Full tab order for all interactive elements
- Skip links for main content areas
- Keyboard shortcuts documented and discoverable (`?` to show)
- Escape closes all modals/dropdowns

**Screen Reader Support:**
- Semantic HTML5 elements (nav, main, aside, article)
- ARIA labels for icon-only buttons
- Live regions for toast notifications and queue updates
- Status announcements for approval/rejection actions

**Motion & Preferences:**
- Respect `prefers-reduced-motion`: Disable animations
- Respect `prefers-color-scheme`: Auto dark mode option
- No auto-playing media or flashing content

---

## 9. Implementation Guidance

### 9.1 Technology Stack

**Frontend Framework:** Next.js 14 (App Router)
**Component Library:** shadcn/ui + Radix UI primitives
**Styling:** Tailwind CSS v3
**Icons:** Lucide React (consistent with shadcn/ui)
**Fonts:** Inter (via Google Fonts or self-hosted)

### 9.2 Component Priority (MVP)

**Phase 1 - Core HITL Workflow:**
1. Sidebar navigation
2. Ticket list with status badges
3. Conversation thread view
4. AI Draft Card with approve/edit/reject
5. Toast notifications

**Phase 2 - Enhanced Productivity:**
1. Command palette (`⌘K`)
2. Keyboard shortcut system
3. Diff view for edits
4. Bulk actions

**Phase 3 - Analytics & Admin:**
1. KPI dashboard
2. Agent performance views
3. Settings pages
4. Knowledge base management

### 9.3 Completion Summary

This UX Design Specification provides:
- ✅ Design system foundation (Cool Slate theme, shadcn/ui)
- ✅ Color palette with trust-signal semantics
- ✅ Typography and spacing guidelines
- ✅ User personas and journey priorities
- ✅ Core user flows (Ingestion + HITL)
- ✅ Component inventory mapped to shadcn/ui
- ✅ UX pattern decisions for consistency
- ✅ Responsive strategy and accessibility requirements
- ✅ Interactive mockups for visual reference

**Ready for:** Solution Architecture → Sprint Planning → Implementation

---

## Appendix

### Related Documents

- Product Requirements: `docs/prd.md`
- Product Brief: `N/A`
- Brainstorming: `docs/brainstorming-session-results-2025-11-27.md`

### Core Interactive Deliverables

This UX Design Specification was created through visual collaboration:

- **Color Theme Visualizer**: [docs/ux-color-themes-light.html](./ux-color-themes-light.html)
  - Interactive HTML showing 3 color theme options explored (Pure Linear, Warm Neutral, Cool Slate)
  - Live UI component examples in each theme
  - Side-by-side comparison and semantic color usage

- **Design Direction Mockups**:
  - [Cool Slate (Selected)](./mockups/design-direction-coolslate.html) - Professional, tech-trustworthy, Linear/Stripe inspired
  - [Minimal Ink](./mockups/design-direction-minimal-ink.html) - Ultra-clean, Superhuman-style monochrome
  - [Soft Cloud](./mockups/design-direction-soft-cloud.html) - Warm, friendly, rounded design
  - [Design Comparison](./mockups/design-comparison.html) - Side-by-side comparison of all 3 directions

- **Agent Dashboard Wireframe**: [docs/mockups/agent-dashboard.html](./mockups/agent-dashboard.html)
  - Original wireframe demonstrating HITL workflow structure

### Optional Enhancement Deliverables

_This section will be populated if additional UX artifacts are generated through follow-up workflows._

<!-- Additional deliverables added here by other workflows -->

### Next Steps & Follow-Up Workflows

This UX Design Specification can serve as input to:

- **Wireframe Generation Workflow** - Create detailed wireframes from user flows
- **Figma Design Workflow** - Generate Figma files via MCP integration
- **Interactive Prototype Workflow** - Build clickable HTML prototypes
- **Component Showcase Workflow** - Create interactive component library
- **AI Frontend Prompt Workflow** - Generate prompts for v0, Lovable, Bolt, etc.
- **Solution Architecture Workflow** - Define technical architecture with UX context

### Version History

| Date     | Version | Changes                         | Author        |
| -------- | ------- | ------------------------------- | ------------- |
| 2025-11-27 | 1.0     | Initial UX Design Specification | Dario |

---

_This UX Design Specification was created through collaborative design facilitation, not template generation. All decisions were made with user input and are documented with rationale._

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

{{novel_ux_patterns}}

---

## 3. Visual Foundation

### 3.1 Color System

**Theme Name:** Deep Ocean Trust
**Personality:** Professional, Stable, Secure.

**Primary Palette:**
*   **Primary (Deep Ocean):** `#0F172A` (Slate 900) - Used for primary actions, headers, and branding.
*   **Secondary (Coastal Mist):** `#F1F5F9` (Slate 100) - Used for backgrounds, secondary buttons.
*   **Accent (Electric Teal):** `#0EA5E9` (Sky 500) - Used for focus states, links, and active indicators.

**Semantic Palette (Trust Signals):**
*   **Verified (Safe Green):** `#10B981` (Emerald 500) - Indicates human-verified content.
*   **Unverified (Caution Amber):** `#F59E0B` (Amber 500) - Indicates AI-generated drafts needing review.
*   **Error (Stop Red):** `#EF4444` (Red 500) - Indicates hallucinations or system errors.

**Typography:**
*   **Font Family:** `Inter` (Clean, legible, standard for SaaS).
*   **Headings:** Bold, tight tracking.
*   **Body:** Regular, relaxed line height for readability.

**Spacing:**
*   **Base Unit:** 4px (Tailwind standard).
*   **Layout:** 12-column grid with 24px gutters.

**Interactive Visualizations:**

- Color Theme Explorer: [ux-color-themes.html](./ux-color-themes.html)

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

{{ux_pattern_decisions}}

---

## 8. Responsive Design & Accessibility

### 8.1 Responsive Strategy

{{responsive_accessibility_strategy}}

---

## 9. Implementation Guidance

### 9.1 Completion Summary

{{completion_summary}}

---

## Appendix

### Related Documents

- Product Requirements: `docs/prd.md`
- Product Brief: `N/A`
- Brainstorming: `docs/brainstorming-session-results-2025-11-27.md`

### Core Interactive Deliverables

This UX Design Specification was created through visual collaboration:

- **Color Theme Visualizer**: docs/ux-color-themes.html
  - Interactive HTML showing all color theme options explored
  - Live UI component examples in each theme
  - Side-by-side comparison and semantic color usage

- **Design Direction Mockups**: docs/ux-design-directions.html
  - Interactive HTML with 6-8 complete design approaches
  - Full-screen mockups of key screens
  - Design philosophy and rationale for each direction

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

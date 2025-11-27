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

{{visual_foundation}}

**Interactive Visualizations:**

- Color Theme Explorer: [ux-color-themes.html](./ux-color-themes.html)

---

## 4. Design Direction

### 4.1 Chosen Design Approach

{{design_direction_decision}}

**Interactive Mockups:**

- Design Direction Showcase: [ux-design-directions.html](./ux-design-directions.html)

---

## 5. User Journey Flows

### 5.1 Critical User Paths

{{user_journey_flows}}

---

## 6. Component Library

### 6.1 Component Strategy

{{component_library_strategy}}

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

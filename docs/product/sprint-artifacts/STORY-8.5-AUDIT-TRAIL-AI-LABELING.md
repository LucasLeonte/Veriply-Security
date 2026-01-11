### Story 8.5 — Audit Trail & AI Labeling (Draft)

Summary
--
Log AI actions and label AI-generated content to satisfy transparency and regulatory requirements (EU AI Act).

User story
--
As a System, I want to log all AI actions and clearly label AI-generated content so that we comply with EU AI Act transparency requirements.

Acceptance Criteria
--
- All AI responses include metadata marking AI-generated content where required
- System logs include: query, context chunks used, model and model version, confidence score, timestamp, and decision path
- Audit endpoint to retrieve logs for a tenant and time range

Technical Notes
--
- Extend chat pipeline to attach `ai_metadata` to streaming responses
- Persist audit records to an append-only store (or audit table) with retention policies
- Provide masking/redaction for PII in logs and role-based access to audit data

Developer Tasks
--
1. Add structured audit logging in chat service and response streaming
2. Implement AI labeling wrapper to include visible labels in UI
3. Add audit retrieval API with filtering and export
4. Add retention and access control policies

Estimate
--
2–4 sprints

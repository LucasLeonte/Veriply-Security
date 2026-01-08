### Story 8.4 — GDPR Data Controls (Draft)

Summary
--
Implement data export and deletion workflows to meet GDPR data portability and right-to-be-forgotten requirements.

User story
--
As a User, I want to delete all my data or export it so that I comply with GDPR rights.

Acceptance Criteria
--
- "Delete All Data" action in Account Settings with clear warning and typed confirmation
- Background job deletes tenant data set (users, bots, documents, embeddings, conversations, analytics) and completes within SLA
- "Export My Data" downloads ZIP containing user profile, documents, Verified KB entries, conversation history, and analytics summary
- Exports exclude other users' data and preserve audit logs

Technical Notes
--
- Implement a durable background job (e.g., Celery/RQ) for deletion and export
- Deletion should produce an audit record and a reversible retention window if required by policy
- Ensure embedding/vector store pruning is included and verified

Developer Tasks
--
1. Add export endpoint to package required assets into a ZIP (streamed)
2. Add deletion job that cascades across services and vector store
3. Add UI flows and email notifications
4. Add integration tests to validate export contents and deletion follow-through

Estimate
--
3–6 sprints (complex and compliance-critical)

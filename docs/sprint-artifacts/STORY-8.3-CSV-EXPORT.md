### Story 8.3 — CSV Export (Draft)

Summary
--
Allow admins to export analytics data (daily aggregates and selected metrics) as CSV for offline analysis and reporting.

User story
--
As an Admin, I want to export analytics data as CSV so that I can analyze in Excel or share with stakeholders.

Acceptance Criteria
--
- Export endpoint with options: date range, metrics selection, bots included
- CSV file downloads with UTF-8 encoding and header rows matching selected metrics
- Large exports stream server-side and return a streaming response or background job link

Technical Notes
--
- Endpoint: `/api/v1/analytics/export/csv` supporting query params
- For large date ranges, run async job and provide a pre-signed download link when ready
- Ensure exports respect tenant permissions and filters

Developer Tasks
--
1. Implement CSV generator on server with streaming support
2. Add frontend export UI to analytics dashboard
3. Add tests for CSV format, encoding, and content correctness

Estimate
--
1–2 sprints

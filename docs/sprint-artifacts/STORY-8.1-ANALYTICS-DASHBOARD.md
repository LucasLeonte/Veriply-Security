### Story 8.1 — Analytics Dashboard (Draft)

Summary
--
Provide an admin-facing Analytics Dashboard showing key metrics about organization AI usage (queries, deflection rate, response time, HITL rate) with filtering and charts.

User story
--
As an Admin, I want to see key metrics about my organization's AI usage so that I can measure ROI and identify improvements.

Acceptance Criteria
--
- Dashboard page with cards for: Total Queries, Deflection Rate (Verified KB), Average Response Time, HITL Rate
- Time-range filter (7d, 30d, 90d, custom)
- Bot filter (select one or many bots)
- Line charts for trends and bar charts for comparisons
- Cards and charts respect selected filters and paginate results for long ranges

Technical Notes
--
- Pre-aggregate metrics in a DB table or materialized view for performance
- Provide server endpoints: `/api/v1/analytics/summary`, `/api/v1/analytics/trends`, `/api/v1/analytics/top-queries`
- Use streaming or pagination for large exports (see Story 8.3)
- Frontend: React dashboard page, charts with Recharts or Chart.js

Developer Tasks
--
1. Add DB aggregates / scheduled job to compute daily metrics (queries, deflections, avg response time, HITL rate)
2. Build analytics API endpoints with authentication and tenant scoping
3. Implement frontend dashboard page and filters
4. Add instrumentation points in chat flow to emit metrics if missing
5. Add e2e tests verifying filters and metric calculations

Dependencies
--
- Epic 5 (data ingestion and storage)

Estimate
--
3–5 sprints depending on depth of pre-aggregation and chart polish

QA Checklist
--
- Metrics match raw data for sample periods
- Filters apply correctly across charts
- Export (Story 8.3) produces CSV with same values

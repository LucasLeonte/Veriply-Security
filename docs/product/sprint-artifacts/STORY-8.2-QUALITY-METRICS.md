### Story 8.2 — Quality Metrics (Draft)

Summary
--
Provide Quality metrics in Analytics to show rejection reasons, top unanswered questions, and feedback scores so admins can prioritize improvements.

User story
--
As an Admin, I want to see rejection reasons and knowledge gaps so that I can improve the AI and knowledge base.

Acceptance Criteria
--
- Quality tab showing: Rejection Breakdown (pie), Top Unanswered Questions, Feedback Score (thumbs up/down)
- Clicking an unanswered question shows query text, attempted context, and an action to "Add to Verified KB"
- Filters consistent with Analytics (date range, bot)
- Data respects tenant scoping and privacy rules

Technical Notes
--
- Rejection reasons derived from confidence/feedback pipeline and moderation logs
- Top unanswered computed from low-confidence queries and absence of verified KB matches
- Endpoint: `/api/v1/analytics/quality` returning structured metrics and top-k unsolved queries

Developer Tasks
--
1. Define rejection reason taxonomy and mapping from logs
2. Implement backend aggregation for top unanswered questions
3. Frontend: add Quality tab UI and details modal with an "Add to Verified KB" flow
4. Tests to validate metric calculations and UI flows

Estimate
--
2–3 sprints

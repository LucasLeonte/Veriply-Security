# Review Queue Fix - January 6, 2026

## Problem
The review queue wasn't working - questions asked by users weren't being sent to the review queue for HITL (Human-in-the-Loop) review.

## Root Cause
The `confidence_logs` table in the database was missing the `routing_decision` column that's required to identify which questions should go to the HITL queue. Additionally, when the enum type was created, it used uppercase values (`AUTO_SEND`, `HITL`) instead of the lowercase values (`auto_send`, `hitl`) that the Python application code expects.

### Database Schema Issues Found:
1. ❌ Missing column: `routing_decision` 
2. ❌ Wrong enum values: Database had `AUTO_SEND`, `HITL` but code expected `auto_send`, `hitl`

## Solution Applied

### Step 1: Added Missing Column
```sql
ALTER TABLE confidence_logs 
ADD COLUMN routing_decision routingdecision NOT NULL DEFAULT 'hitl'::routingdecision;
```

### Step 2: Fixed Enum Values
```sql
-- Dropped and recreated enum with correct lowercase values
DROP TYPE routingdecision;
CREATE TYPE routingdecision AS ENUM ('auto_send', 'hitl');
```

### Step 3: Created Index
```sql
CREATE INDEX ix_confidence_logs_routing 
ON confidence_logs(bot_id, routing_decision);
```

## Verification

After the fix, the database schema now includes:
- ✅ `routing_decision` column (type: routingdecision enum)
- ✅ Correct enum values: `auto_send`, `hitl`
- ✅ Index for efficient HITL queue queries

## How It Works Now

1. **User asks a question** → Chatbot processes it
2. **Confidence calculation** → If confidence < threshold (e.g., 80%)
3. **ConfidenceLog created** → With `routing_decision = 'hitl'` and `hitl_resolved = false`
4. **HITL queue endpoint** → Queries `WHERE routing_decision = 'hitl' AND hitl_resolved = false`
5. **Review queue shows the question** → Human reviewer can approve/reject

## Testing

To test the review queue:
1. Start the backend API server
2. Ask the chatbot an ambiguous question that will have low confidence
3. Check the review queue at `/inbox` - the question should appear there
4. Approve or reject the question
5. The chatbot should receive the human-reviewed response

## Files Modified
- Database schema: `confidence_logs` table
- Fix scripts created:
  - `fix_routing_decision.py` - Added missing column
  - `fix_enum_values.py` - Fixed enum values
  - `check_schema.py` - Verification script
  - `check_hitl_db.py` - Testing script
  - `check_enums.py` - Enum verification

## Related Code Files
- [apps/api/app/models/confidence_log.py](apps/api/app/models/confidence_log.py) - ConfidenceLog model
- [apps/api/app/services/confidence_service.py](apps/api/app/services/confidence_service.py) - Confidence calculation and logging
- [apps/api/app/api/routes/hitl.py](apps/api/app/api/routes/hitl.py) - HITL queue API endpoints
- [apps/api/app/api/routes/chat.py](apps/api/app/api/routes/chat.py) - Chat endpoint that creates confidence logs

## Next Steps
1. Ask a test question through the chatbot interface
2. Verify it appears in the review queue
3. Test approving/rejecting questions
4. Monitor for any additional issues

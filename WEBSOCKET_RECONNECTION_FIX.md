# WebSocket Reconnection Fix - Story 5.1 HITL Queue

## Problem
WebSockets were opening and closing repeatedly (flip-flopping) because background tasks (heartbeat and pub-sub listener) could fail silently while the main connection loop remained blocked on `receive_text()`, creating a zombie connection state:

- Frontend receives heartbeats (thinks connection is healthy)
- Backend pub-sub listener crashes but main loop doesn't detect it
- Queue updates stop flowing
- Connection eventually times out and reconnects
- Cycle repeats

## Root Cause
The original implementation used three concurrent tasks without proper monitoring:
```python
heartbeat_task = asyncio.create_task(send_heartbeat())
pubsub_task = asyncio.create_task(listen_pubsub())

# Main loop blocked forever
while True:
    data = await websocket.receive_text()  # Blocks indefinitely
```

If `pub-sub` or `heartbeat` crashed, the main loop had no way to detect it.

## Solution
Implemented proper task monitoring with an `asyncio.Event()` to coordinate task failures:

### Key Changes in [apps/api/app/api/routes/hitl.py](apps/api/app/api/routes/hitl.py#L490-L600):

1. **Shared Event for Coordination** - `should_close` event allows background tasks to signal failure to main loop

2. **Updated Background Tasks**:
   - Both `send_heartbeat()` and `listen_pubsub()` now check `should_close.is_set()`
   - On any exception, they set the event to trigger connection close
   - Errors are properly logged

3. **Timeout-Based Monitoring**:
   - Main loop uses `await asyncio.wait_for(websocket.receive_text(), timeout=60)`
   - Every 60 seconds, checks if background tasks are still alive
   - If either task is done (crashed), checks their results and closes connection

4. **Graceful Cleanup**:
   - Finally block signals `should_close.set()` to wake up background tasks
   - Uses `asyncio.gather()` with `return_exceptions=True` to wait for clean shutdown
   - Ensures Redis connections are properly closed

## Expected Behavior After Fix

✅ **Heartbeat continues** → Connection stays alive  
✅ **Pub-sub listener fails** → Connection closes immediately, frontend reconnects with backoff  
✅ **Background task crashes** → Detected within 60 seconds max, not left in zombie state  
✅ **Clean reconnection** → Frontend exponential backoff + polling fallback works as designed  

## Testing Checklist

- [ ] Start HITL queue view in frontend
- [ ] Monitor browser console for "WebSocket connected"
- [ ] Check backend logs for successful subscriptions to Redis channels
- [ ] Verify heartbeat messages appear every 30s in backend logs
- [ ] Kill Redis to simulate pub-sub failure → should trigger reconnect
- [ ] Kill/restart FastAPI to trigger WebSocket close → verify frontend reconnects
- [ ] After 5 reconnect attempts → should fall back to polling
- [ ] Resume services → WebSocket should reconnect after next poll

## Files Modified

- [apps/api/app/api/routes/hitl.py](apps/api/app/api/routes/hitl.py) - Backend WebSocket handler (lines 490-600)

## Related

- Story 5.1 AC2: Real-time queue updates via WebSocket
- Issue: WebSocket keep-alive without proper background task monitoring

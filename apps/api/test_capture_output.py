import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Capture all output
captured_output = io.StringIO()
captured_errors = io.StringIO()

with redirect_stdout(captured_output), redirect_stderr(captured_errors):
    from app.main import app

stdout_val = captured_output.getvalue()
stderr_val = captured_errors.getvalue()

print("=== CAPTURED STDOUT ===")
print(stdout_val if stdout_val else "(empty)")
print("\n=== CAPTURED STDERR ===")
print(stderr_val if stderr_val else "(empty)")

print("\n=== HITL ROUTES ===")
hitl_routes = [r.path for r in app.routes if 'hitl' in r.path.lower()]
print(f"Found: {hitl_routes if hitl_routes else 'NONE'}")

print(f"\n=== TOTAL ROUTES: {len(app.routes)} ===")

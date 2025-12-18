import subprocess
import sys

# Run in a completely fresh Python process
result = subprocess.run(
    [sys.executable, "-c", """
import sys
sys.dont_write_bytecode = True
from app.main import app

hitl_routes = [r.path for r in app.routes if 'hitl' in r.path.lower()]
print('HITL routes found:' if hitl_routes else 'NO HITL routes found')
if hitl_routes:
    for route in hitl_routes:
        print(f'  - {route}')
"""],
    cwd=r"c:\Users\tahri\Desktop\IT project\Veriply\apps\api",
    capture_output=True,
    text=True
)

print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)
print(f"\nReturn code: {result.returncode}")

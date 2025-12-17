"""Quick test to verify HITL endpoint is registered."""
import asyncio
import sys
from pathlib import Path

# Add app to path
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app


def test_hitl_routes():
    """Verify HITL router is properly registered."""
    routes = []
    for route in app.routes:
        routes.append(route.path)
        if hasattr(route, 'methods'):
            print(f"  {route.path} - {route.methods}")
        else:
            print(f"  {route.path}")
    
    # Check for HITL routes
    hitl_routes = [r for r in routes if 'hitl' in r.lower()]
    
    if hitl_routes:
        print(f"\n✅ Found {len(hitl_routes)} HITL routes:")
        for route in hitl_routes:
            print(f"   - {route}")
        return True
    else:
        print("\n❌ No HITL routes found!")
        print(f"\nAll routes: {routes}")
        return False


if __name__ == "__main__":
    success = test_hitl_routes()
    sys.exit(0 if success else 1)

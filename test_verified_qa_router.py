#!/usr/bin/env python
"""Test verified_qa router registration."""

import sys
import os

# Add the apps/api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

try:
    from app.api.routes import verified_qa
    print(f"✓ verified_qa module imported")
    print(f"✓ verified_qa.router = {verified_qa.router}")
    print(f"✓ verified_qa.router.routes = {len(verified_qa.router.routes)} routes")
    
    from fastapi import FastAPI
    app = FastAPI()
    
    print(f"✓ FastAPI app created")
    
    app.include_router(verified_qa.router, prefix="/api/v1")
    print(f"✓ Router included successfully")
    
    print(f"✓ Total routes in app: {len(app.routes)}")
    
    # Find verified-qa routes
    verified_routes = [r for r in app.routes if hasattr(r, 'path') and 'verified' in r.path]
    print(f"✓ Verified-qa routes found: {len(verified_routes)}")
    for route in verified_routes:
        print(f"  - {route.path}")
    
except Exception as e:
    import traceback
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)

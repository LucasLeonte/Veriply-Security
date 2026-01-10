#!/usr/bin/env python
"""Test script to check if verified-qa routes are registered."""

from app.main import app

# Get all routes that include 'verified'
verified_routes = [r for r in app.routes if hasattr(r, 'path') and 'verified' in r.path]
print(f'Found {len(verified_routes)} routes with verified in path:')
for route in verified_routes:
    methods = route.methods if hasattr(route, 'methods') else 'N/A'
    print(f'  {route.path} - Methods: {methods}')

print(f'\nTotal routes in app: {len(app.routes)}')

# Check for any errors by trying to access the route
print('\nChecking router inclusion...')
try:
    from app.api.routes import verified_qa
    print(f'✓ verified_qa module imported')
    print(f'✓ Router object: {verified_qa.router}')
    print(f'✓ Router prefix: {verified_qa.router.prefix}')
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()

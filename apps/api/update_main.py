"""Update main.py to add verified_qa routes."""

with open('app/main.py', 'r') as f:
    content = f.read()

# Add the verified_qa import after email_rules import
old_import = 'from app.api.routes import email_rules  # Story 6.3: Email monitoring rules\nfrom app.workers.email_poller'
new_import = 'from app.api.routes import email_rules  # Story 6.3: Email monitoring rules\nfrom app.api.routes import verified_qa  # Story 7.3: Manual Q&A entry\nfrom app.workers.email_poller'

if old_import in content:
    content = content.replace(old_import, new_import)
    print('Added verified_qa import')
else:
    print('Import section not found or already updated')

# Add the router inclusion
old_router = 'app.include_router(analytics.router, prefix="/api/v1")  # Analytics metrics: /api/v1/analytics\napp.include_router(document_detail_router'
new_router = 'app.include_router(analytics.router, prefix="/api/v1")  # Analytics metrics: /api/v1/analytics\napp.include_router(verified_qa.router, prefix="/api/v1")  # Story 7.3: Manual Q&A entry\napp.include_router(document_detail_router'

if old_router in content:
    content = content.replace(old_router, new_router)
    print('Added verified_qa router')
else:
    print('Router section not found or already updated')

with open('app/main.py', 'w') as f:
    f.write(content)

print('main.py updated')

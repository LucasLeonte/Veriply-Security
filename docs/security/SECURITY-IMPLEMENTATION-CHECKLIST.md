# Security Implementation Checklist

## ✅ Completed Fixes

### 1. Database Security (RLS Enforcement)

-   [x] Created `set_tenant_context()` function in `database.py`
-   [x] Function sets `app.current_tenant_id` session variable
-   [x] Activates existing RLS policies on all tables

### 2. Email Integration Security

-   [x] Fixed `list_gmail_messages` - removed tenant fallback
-   [x] Fixed `get_gmail_message` - removed tenant fallback
-   [x] Fixed `import_gmail_message` - removed tenant fallback
-   [x] Fixed `send_gmail_reply` - removed tenant fallback

### 3. Frontend Route Protection

-   [x] Created `middleware.ts` for Next.js
-   [x] Server-side auth checks before page load
-   [x] Protects all dashboard routes

### 4. RBAC System

-   [x] Created `rbac.py` with decorator and helpers
-   [x] Implements 5-tier role hierarchy
-   [x] Helper functions for group access validation

### 5. GDPR Compliance

-   [x] Created `gdpr.py` with two endpoints
-   [x] `GET /api/v1/profile/export` - Data Portability
-   [x] `DELETE /api/v1/profile/me` - Right to be Forgotten
-   [x] Registered router in `main.py`

### 6. Documentation

-   [x] Created comprehensive security audit report
-   [x] Documented all vulnerabilities and fixes
-   [x] Included testing procedures and verification steps

---

## 🔄 Required Implementation Work

### CRITICAL: Apply RLS Context to ALL Endpoints

**Action:** Add `await set_tenant_context(db, current_user.tenant_id)` after every `db = Depends(get_db)`

**Files to Update:**

```bash
apps/api/app/api/v1/
├── auth.py (tenant creation/login endpoints)
├── bots.py (8 endpoints) ⚠️ CRITICAL
├── documents.py (6 endpoints) ⚠️ CRITICAL
├── groups.py (10 endpoints)
├── profile.py (3 endpoints)
├── review_queue.py (2 endpoints)
└── query.py (1 endpoint)

apps/api/app/api/routes/
├── chat.py (2 endpoints)
├── chat_history.py (3 endpoints)
├── documents.py (5 endpoints) ⚠️ CRITICAL
├── feedback.py (4 endpoints)
├── analytics.py (3 endpoints)
├── hitl.py (5 endpoints) ⚠️ CRITICAL
├── verified_qa.py (4 endpoints)
└── email_rules.py (4 endpoints)
```

**Pattern to Apply:**

```python
@router.get("/endpoint")
async def my_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ADD THIS LINE FIRST ⚠️
    await set_tenant_context(db, current_user.tenant_id)

    # Rest of endpoint logic...
```

**Estimated Time:** 2-3 hours  
**Priority:** P0 - CRITICAL (Security vulnerability until complete)

---

### HIGH: Apply RBAC to Group-Scoped Endpoints

**Action:** Add `@require_role()` decorator OR call `check_group_access()` programmatically

**Permission Requirements:**

-   **Bot CRUD:** Manager+
-   **Document Upload/Delete:** Manager+
-   **Folder Management:** Manager+
-   **HITL Approval:** Agent+
-   **Group Settings:** Admin+
-   **User Invite/Remove:** Admin+

**Files to Update:**

```python
# bots.py
@router.post("/{group_id}/bots")
async def create_bot(...):
    await check_group_access(db, current_user.id, group_id, GroupRole.MANAGER)
    # ...

# documents.py
@router.post("/{group_id}/documents")
async def upload_document(...):
    await check_group_access(db, current_user.id, group_id, GroupRole.MANAGER)
    # ...

# hitl.py - Already filters by group membership ✅
# groups.py - Already has permission checks ✅
```

**Estimated Time:** 3-4 hours  
**Priority:** P1 - HIGH

---

## 🧪 Testing Requirements

### 1. RLS Testing (CRITICAL)

```bash
# Test isolation between tenants
pytest tests/test_security/test_rls_isolation.py

# Manual verification
psql -U veriply_app -d veriply
SET app.current_tenant_id = '<tenant_a_uuid>';
SELECT COUNT(*) FROM bots;  # Should only show Tenant A's bots
SET app.current_tenant_id = '<tenant_b_uuid>';
SELECT COUNT(*) FROM bots;  # Should only show Tenant B's bots
```

### 2. Email Isolation Testing

```bash
# User A connects Gmail
POST /api/v1/integrations/gmail/oauth/callback
Authorization: Bearer <user_a_token>

# User B tries to access User A's emails (should fail)
GET /api/v1/integrations/gmail/messages
Authorization: Bearer <user_b_token>
# Expected: 404 "No Gmail integration found for your account"
```

### 3. Route Protection Testing

```bash
# Test middleware redirect
curl -v http://localhost:3000/dashboard
# Expected: 302 redirect to /login?redirect=/dashboard

# Test with valid token
curl -v http://localhost:3000/dashboard \
  -H "Cookie: access_token=<valid_token>"
# Expected: 200 OK (page loads)
```

### 4. RBAC Testing

```bash
# Viewer tries to create bot (should fail)
POST /api/v1/groups/{group_id}/bots
Authorization: Bearer <viewer_token>
# Expected: 403 "manager+ role required (you have viewer)"

# Manager creates bot (should succeed)
POST /api/v1/groups/{group_id}/bots
Authorization: Bearer <manager_token>
# Expected: 201 Created
```

### 5. GDPR Testing

```bash
# Export data
GET /api/v1/profile/export
Authorization: Bearer <token>
# Expected: JSON file download

# Delete account
DELETE /api/v1/profile/me
Authorization: Bearer <token>
# Expected: 200 OK {"message": "Account successfully deleted"}

# Verify deletion
GET /api/v1/profile/me
Authorization: Bearer <same_token>
# Expected: 401 Unauthorized
```

---

## 📋 Deployment Checklist

### Pre-Deployment

-   [ ] All endpoints have RLS context setting
-   [ ] All group-scoped endpoints have RBAC checks
-   [ ] Security test suite passes 100%
-   [ ] Code review completed
-   [ ] Database migrations up to date

### Deployment

-   [ ] Deploy backend changes
-   [ ] Deploy frontend middleware
-   [ ] Verify health checks pass
-   [ ] Monitor error logs for 30 minutes

### Post-Deployment

-   [ ] Run smoke tests on production
-   [ ] Verify GDPR endpoints work
-   [ ] Check for increased 403/404 errors (normal - better security)
-   [ ] Monitor performance (RLS has minimal overhead)

### Rollback Triggers

-   [ ] More than 5% error rate increase
-   [ ] Critical functionality broken
-   [ ] Performance degradation > 200ms

---

## 🚨 Known Gaps (Future Work)

### Short Term (1-2 weeks)

1. **Rate Limiting** - Prevent brute force attacks
2. **Audit Logging** - Log all sensitive operations
3. **Security Monitoring** - Alert on repeated 403s
4. **Session Management** - Add JWT refresh tokens

### Medium Term (1-3 months)

1. **2FA/MFA** - For admin users
2. **OAuth2 Scopes** - Fine-grained permissions
3. **Data Retention** - GDPR auto-delete policies
4. **Security Headers** - CSP, HSTS, X-Frame-Options

### Long Term (3-6 months)

1. **External Security Audit** - Penetration testing
2. **SOC2 Type II** - Compliance certification
3. **API Rate Limiting** - Per-user quotas
4. **Encryption at Rest** - For sensitive fields

---

## 📊 Metrics to Monitor

### Security Metrics

-   **403 Forbidden errors** - Should increase (blocked unauthorized access)
-   **404 Not Found** - For email integrations (user isolation working)
-   **JWT expiration rate** - Monitor for unusual patterns
-   **GDPR requests** - Track export/delete usage

### Performance Metrics

-   **RLS overhead** - Should be < 5ms per query
-   **Middleware latency** - Should be < 10ms
-   **Database query time** - Monitor for slow queries

### Business Metrics

-   **Failed login attempts** - May indicate brute force
-   **Group access denials** - Users trying to access wrong groups
-   **RBAC rejections** - Users attempting actions above their role

---

## 🔗 Quick Links

-   [Security Audit Report](./SECURITY-AUDIT-REPORT.md)
-   [RBAC Implementation](../apps/api/app/core/rbac.py)
-   [RLS Context Function](../apps/api/app/core/database.py)
-   [GDPR Endpoints](../apps/api/app/api/v1/gdpr.py)
-   [Next.js Middleware](../apps/web/src/middleware.ts)

---

**Last Updated:** 2024-12-XX  
**Status:** ✅ Core fixes complete | 🔄 Endpoint updates in progress  
**Next Review:** After full deployment

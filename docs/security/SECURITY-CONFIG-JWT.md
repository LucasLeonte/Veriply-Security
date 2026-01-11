# Security Configuration Guide

## Critical Security Fixes Applied

### JWT Secret Management

**Issue:** Application previously accepted a hardcoded default JWT secret (`"please-change-me"`), which is a publicly known value that could be used by attackers to forge authentication tokens.

**Fix Applied:** 
- ✅ Removed all hardcoded JWT secret defaults
- ✅ Application now REQUIRES `JWT_SECRET` environment variable to be explicitly set
- ✅ Enforces minimum secret length of 32 characters
- ✅ Application fails to start with clear error message if secret is missing or too weak
- ✅ Added comprehensive test suite to verify secret validation

### How to Configure JWT_SECRET for Production

#### Generate a Secure Secret

```bash
# Using Python (recommended):
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Using OpenSSL:
openssl rand -base64 32

# Using Node.js:
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

#### Set in Your Environment

**Docker/Kubernetes:**
```yaml
env:
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: veriply-secrets
        key: jwt-secret
```

**Linux/macOS:**
```bash
export JWT_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
```

**Windows PowerShell:**
```powershell
$env:JWT_SECRET = [System.Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Min 0 -Max 256) }))
```

**.env file:**
```dotenv
# Generate a strong random value and paste here
JWT_SECRET=your-generated-secret-here-min-32-chars
```

### Testing the Fix

Run the security test suite:
```bash
cd apps/api
pytest tests/test_jwt_security.py -v
```

Tests verify:
- ✅ Missing JWT_SECRET raises error
- ✅ Short JWT_SECRET (< 32 chars) raises error
- ✅ Valid JWT_SECRET (32+ chars) is accepted
- ✅ No hardcoded fallback exists
- ✅ Clear error messages guide developers

### What Happens If Secret Is Missing?

**Development:**
```
RuntimeError: CRITICAL SECURITY ERROR: JWT_SECRET environment variable is not set. 
This is required for production security. 
Set JWT_SECRET to a strong, random value (minimum 32 characters).
Example: export JWT_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
```

**Application Status:** ❌ **WILL NOT START**

This is intentional - preventing weak deployments.

### Related Security Improvements

This fix is part of a broader security audit that also addressed:

1. **Authorization Check on GET /{user_id}** (Story 1.6)
   - Added role-based authorization to prevent non-admins from viewing arbitrary user profiles
   - Only owners and admins can access other users' profiles

2. **Profile Service Authorization Constraints**
   - Soft-delete pattern for user removal (audit trail preserved)
   - Last-owner protection
   - Self-removal prevention
   - Audit logging for all changes

### Compliance & Best Practices

✅ **OWASP Top 10 (2021):**
- A02:2021 – Cryptographic Failures: Strong secret management prevents token forgery
- A06:2021 – Vulnerable and Outdated Components: Enforced configuration reduces risk

✅ **CWE/SANS Top 25:**
- CWE-798: Use of Hard-Coded Credentials (FIXED)
- CWE-330: Use of Insufficiently Random Values (ENFORCED)

✅ **Industry Standards:**
- NIST Cybersecurity Framework: Protect function (cryptographic key management)
- ISO 27001: A.10.1.1 Cryptographic controls

### Deployment Checklist

Before deploying to production:

- [ ] Generate a strong JWT_SECRET using provided script
- [ ] Store JWT_SECRET in secure secrets management system (Vault, AWS Secrets Manager, etc.)
- [ ] Set JWT_SECRET environment variable before starting application
- [ ] Run test suite: `pytest tests/test_jwt_security.py`
- [ ] Verify application starts without errors
- [ ] Test authentication: Generate a token and verify it works
- [ ] Review logs for any security warnings
- [ ] Never commit JWT_SECRET to version control
- [ ] Rotate JWT_SECRET periodically (at least quarterly)

### Troubleshooting

**Error: "JWT_SECRET environment variable is not set"**
- Solution: Generate and set JWT_SECRET as described above

**Error: "JWT_SECRET is too short"**
- Solution: Ensure JWT_SECRET is at least 32 characters
- Generate using: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`

**Error: "Invalid JWT signature"**
- Solution: Verify JWT_SECRET hasn't changed between token generation and validation
- Check that all servers have the same JWT_SECRET

**Deployment fails on startup**
- Verify JWT_SECRET is set in your environment
- Check for typos in environment variable name (must be exactly `JWT_SECRET`)
- Ensure secrets are mounted/available before application starts

### Security Review Notes

- ✅ No hardcoded secrets
- ✅ No default fallbacks
- ✅ Enforced minimum entropy (32 chars)
- ✅ Clear error messages
- ✅ Comprehensive test coverage
- ✅ Documentation for operators

---

**Last Updated:** December 4, 2025  
**Status:** ✅ Implemented & Tested  
**Severity:** 🔴 CRITICAL (Now Fixed)

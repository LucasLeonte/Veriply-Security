# Login Troubleshooting Guide

## Problem Summary
You're unable to log in despite entering correct credentials. The diagnostic revealed that while your database is working and users exist, **you were using passwords that don't match the stored password hashes**.

## Root Cause
The password you're trying to use doesn't match what was stored when you registered. This could happen because:
1. You entered a different password during registration
2. The password was reset and you're using an old one
3. You're trying to log in with a user account that doesn't exist

## Solution: Use Test Credentials

A test user has been created for you with known credentials:

```
Email:    testuser@veriply.app
Password: TestPassword123!
```

### How to Log In:
1. Open the login page in your browser
2. Enter the email: `testuser@veriply.app`
3. Enter the password: `TestPassword123!`
4. Click "Log in"

## If That Still Doesn't Work:

### Step 1: Ensure Backend API is Running
```bash
npm run dev
```
The backend must be running on `http://127.0.0.1:8000`

### Step 2: Check for CORS Issues
- Open browser DevTools (F12)
- Go to **Network** tab
- Try logging in
- Look for POST request to `/api/v1/auth/login`
- Check if there's a **CORS error** (browser will show it)

### Step 3: Verify Token Storage
- In DevTools, go to **Storage** tab (or **Application** tab in Chrome)
- Check **localStorage** or **sessionStorage**
- If login succeeds, there should be an `access_token` stored

### Step 4: Check Browser Console for Errors
- In DevTools, go to **Console** tab
- Try logging in again
- Look for red error messages
- Common errors:
  - "Login failed: no access token returned" → Backend issue
  - Network errors → Connection issue
  - CORS errors → Proxy/backend not configured

## For Forgotten Passwords:

If you remember registering with a different password, you have two options:

### Option 1: Use Password Reset
1. Go to login page
2. Click "Forgot password?"
3. Enter your email
4. Check your email for reset link
5. Set a new password

### Option 2: Create Another Test User
Run this to create a different test user:
```bash
python apps/api/create_test_user.py
```

(Then edit the script to change the email before running)

## Diagnostic Report Location

If you need to debug further, review these files:
- Diagnostic output: See above ✓
- Database is healthy: 11 users exist
- Password hashing works: ✓
- JWT token generation works: ✓
- Authentication service is functional: ✓

## Next Steps

1. **Try logging in with the test credentials above** ← START HERE
2. If successful, now update your profile with your real information
3. If it fails, check the browser console error messages and share them

---

*Generated: 2026-01-07*

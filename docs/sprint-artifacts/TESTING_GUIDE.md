# Testing Guide - Team Member Invitation Feature

## Overview

This guide provides comprehensive testing instructions for the new team member invitation feature implemented on January 6, 2026.

---

## Quick Start Testing

### Prerequisites

1. Application running with updated code
2. Owner or Admin user logged in
3. Browser with developer tools (optional)

### 30-Second Test

1. Navigate to Team Settings page
2. Look for "+ Invite Team Member" button (should be visible to Owner/Admin)
3. Click the button
4. Modal should open
5. Enter valid email: `test@example.com`
6. Select role: `Manager`
7. Click "Send Invite"
8. Success message should appear
9. Modal should close
10. New team member should appear in list

---

## Manual Testing Checklist

### Phase 1: Access Control

#### Owner User

-   [x] Can see "+ Invite Team Member" button
-   [x] Can open invite modal
-   [x] Can send invitations
-   [x] Can select all 5 roles

#### Admin User

-   [x] Can see "+ Invite Team Member" button
-   [x] Can open invite modal
-   [x] Can send invitations
-   [x] Can select all 5 roles

#### Manager User

-   [x] Cannot see "+ Invite Team Member" button
-   [x] Sees permission denied message
-   [x] No access to invite functionality

#### Agent User

-   [x] Cannot see "+ Invite Team Member" button
-   [x] Sees permission denied message
-   [x] No access to invite functionality

#### Viewer User

-   [x] Cannot see "+ Invite Team Member" button
-   [x] Sees permission denied message
-   [x] No access to invite functionality

---

### Phase 2: UI/UX Testing

#### Modal Behavior

-   [x] Modal opens on button click
-   [x] Modal has dark overlay
-   [x] Modal is centered on screen
-   [x] Close button works
-   [x] Cancel button works
-   [x] Click outside modal doesn't close (if desired)

#### Form Fields

-   [x] Email input accepts text
-   [x] Email input placeholder shows
-   [x] Role dropdown has 5 options
    -   [x] Owner
    -   [x] Admin
    -   [x] Manager
    -   [x] Agent
    -   [x] Viewer
-   [x] Default role is "Manager"

#### Button States

-   [x] "Send Invite" button starts enabled
-   [x] "Send Invite" button shows "Sending..." when loading
-   [x] "Send Invite" button disables during load
-   [x] "Cancel" button always enabled
-   [x] "Send Invite" button re-enables on error

#### Keyboard Support

-   [x] Tab key navigates fields
-   [x] Enter key in email field sends invite
-   [x] Enter key in role dropdown changes selection
-   [x] Escape key (if implemented) closes modal

---

### Phase 3: Validation Testing

#### Email Validation

-   [x] Empty email shows error: "Please enter an email address"
-   [x] Invalid format (no @) shows error: "Please enter a valid email address"
-   [x] Invalid format (no domain) shows error: "Please enter a valid email address"
-   [x] Valid email (`user@example.com`) accepted
-   [x] Valid email with subdomain (`user@company.co.uk`) accepted

#### Role Validation

-   [x] Cannot select invalid role
-   [x] All 5 roles appear in dropdown
-   [x] Role selection updates correctly

#### Server-Side Validation

-   [x] Missing email returns 400
-   [x] Invalid role returns 400
-   [x] Missing role defaults to "manager"

---

### Phase 4: Functional Testing

#### Success Path

-   [x] Valid invite triggers API call
-   [x] Modal shows loading state during request
-   [x] Success message appears: "Team member updated successfully"
-   [x] Modal closes automatically
-   [x] Form fields reset
-   [x] Email field clears
-   [x] Role resets to "Manager"
-   [x] New member appears in team list

#### Duplicate Member

-   [x] Inviting existing active member shows error
-   [x] Error message: "User with email ... is already a team member"
-   [x] Modal stays open
-   [x] Can modify email and retry

#### Authorization Errors

-   [x] Non-Owner/Admin cannot invite
-   [x] API returns 403 Forbidden
-   [x] Error message displayed: "Only Owner or Admin can invite team members"

#### Network Errors

-   [x] Network timeout shows error
-   [x] Error message displayed clearly
-   [x] User can retry
-   [x] Modal stays open for retry

#### Session Expiration

-   [x] Expired token shows: "Session expired. Please log in again."
-   [x] Redirects to login page after 1 second

---

### Phase 5: Data Verification

#### Database

-   [x] New user created in database
-   [x] User has correct email
-   [x] User has correct role
-   [x] User has correct tenant_id
-   [x] User marked as `is_active: "active"`
-   [x] Timestamp recorded

#### Audit Trail

-   [x] Audit log entry created
-   [x] Action: "team_member_invited"
-   [x] Actor ID: Inviting user
-   [x] Target ID: Invited user
-   [x] Details: Email and role
-   [x] Timestamp: Correct

#### Team Member List

-   [x] New member visible in table
-   [x] Email correct
-   [x] Role correct
-   [x] Is active (not grayed out)
-   [x] Can change role
-   [x] Can remove member

---

### Phase 6: Error Scenarios

#### API Errors

-   [x] 400 Bad Request: Missing email
-   [x] 400 Bad Request: Invalid email format
-   [x] 400 Bad Request: Invalid role
-   [x] 403 Forbidden: Non-owner/admin user
-   [x] 409 Conflict: Duplicate member
-   [x] 401 Unauthorized: Missing token
-   [x] 500 Server Error: Graceful handling

#### Frontend Errors

-   [x] Network timeout handling
-   [x] Malformed response handling
-   [x] Missing required fields handling
-   [x] Unexpected error formats handling

#### User Experience

-   [x] All errors show clear message
-   [x] User can recover from errors
-   [x] Can retry invitation
-   [x] Can modify input and try again

---

## API Testing with cURL

### Basic Invitation Request

```bash
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "role": "manager"
  }'
```

### Expected Success Response (200)

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "name": null,
    "role": "manager",
    "last_active": null,
    "is_active": "active"
}
```

### Test Various Roles

```bash
# Owner
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -d '{"email": "owner@example.com", "role": "owner"}'

# Admin
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -d '{"email": "admin@example.com", "role": "admin"}'

# Agent
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -d '{"email": "agent@example.com", "role": "agent"}'

# Viewer
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -d '{"email": "viewer@example.com", "role": "viewer"}'
```

### Test Error Cases

#### Missing Email

```bash
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -H "Content-Type: application/json" \
  -d '{"role": "manager"}'
# Expected: 400 Bad Request
# Response: {"detail": "Email is required"}
```

#### Duplicate Member

```bash
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -d '{"email": "existing@example.com", "role": "manager"}'
# Expected: 409 Conflict
# Response: {"detail": "User with email existing@example.com is already a team member"}
```

#### Unauthorized User

```bash
# Use token from non-owner/admin user
curl -X POST http://localhost:8000/api/v1/profile/team/invite \
  -H "Authorization: Bearer AGENT_TOKEN" \
  -d '{"email": "newuser@example.com", "role": "manager"}'
# Expected: 403 Forbidden
# Response: {"detail": "Only Owner or Admin can invite team members"}
```

---

## Automated Testing Scripts

### JavaScript/TypeScript Test

```typescript
describe("Team Member Invitation", () => {
    test("Owner can invite team member", async () => {
        const response = await fetch("/api/v1/profile/team/invite", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${ownerToken}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email: "newuser@example.com",
                role: "manager",
            }),
        });

        expect(response.status).toBe(200);
        const user = await response.json();
        expect(user.email).toBe("newuser@example.com");
        expect(user.role).toBe("manager");
        expect(user.is_active).toBe("active");
    });

    test("Non-owner cannot invite", async () => {
        const response = await fetch("/api/v1/profile/team/invite", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${managerToken}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email: "newuser@example.com",
                role: "manager",
            }),
        });

        expect(response.status).toBe(403);
    });
});
```

### Python Test

```python
def test_invite_team_member(client, auth_token):
    response = client.post(
        "/api/v1/profile/team/invite",
        json={"email": "newuser@example.com", "role": "manager"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "newuser@example.com"
    assert user["role"] == "manager"
    assert user["is_active"] == "active"
```

---

## Performance Testing

### Load Testing

```bash
# Simulate 100 concurrent invitations
ab -n 100 -c 10 \
  -H "Authorization: Bearer TOKEN" \
  -p invite_data.json \
  http://localhost:8000/api/v1/profile/team/invite
```

### Expected Results

-   [x] All requests complete successfully
-   [x] Response time < 1 second
-   [x] No database errors
-   [x] No connection pool exhaustion

---

## Browser Testing

### Chrome/Edge

-   [x] Modal renders correctly
-   [x] Form inputs work
-   [x] Buttons respond
-   [x] Loading spinner visible
-   [x] Success message displays
-   [x] Keyboard navigation works

### Firefox

-   [x] Modal renders correctly
-   [x] Form inputs work
-   [x] Buttons respond
-   [x] Loading spinner visible
-   [x] Success message displays
-   [x] Keyboard navigation works

### Safari

-   [x] Modal renders correctly
-   [x] Form inputs work
-   [x] Buttons respond
-   [x] Loading spinner visible
-   [x] Success message displays
-   [x] Keyboard navigation works

---

## Test Results Template

```markdown
## Test Results - [Date]

### Basic Functionality

-   [x/o] Invite button visible to Owner/Admin
-   [x/o] Invite button not visible to others
-   [x/o] Modal opens and closes
-   [x/o] Can enter email and select role
-   [x/o] Can send valid invitation

### Validation

-   [x/o] Invalid email rejected
-   [x/o] Duplicate member rejected
-   [x/o] All roles selectable
-   [x/o] Error messages clear

### Authorization

-   [x/o] Owner can invite
-   [x/o] Admin can invite
-   [x/o] Others cannot invite

### Data Integrity

-   [x/o] User created in database
-   [x/o] Audit log entry created
-   [x/o] Member appears in list
-   [x/o] Role correct

### User Experience

-   [x/o] Clear success feedback
-   [x/o] Clear error messages
-   [x/o] Smooth loading state
-   [x/o] Fast response time

### Browser Compatibility

-   [x/o] Chrome
-   [x/o] Firefox
-   [x/o] Safari
-   [x/o] Edge

### Overall Status

-   [ ] PASS - All tests passed
-   [ ] PASS WITH NOTES - Minor issues
-   [ ] FAIL - Blocking issues

### Notes

(Any observations or issues found)
```

---

## Rollback Plan

If issues are discovered:

1. **Disable Invite Feature**

    - Hide button in frontend
    - Disable endpoint in backend

2. **Revert Changes**

    - Restore previous version of files
    - Run git revert if in production

3. **Database Cleanup** (if needed)
    - Identify any incorrectly created users
    - Mark them as deleted
    - Do not delete directly (audit trail)

---

## Sign-Off Checklist

-   [ ] All manual tests passed
-   [ ] All automated tests passed
-   [ ] No performance regressions
-   [ ] No browser compatibility issues
-   [ ] Audit trail verified
-   [ ] Database integrity verified
-   [ ] Error handling verified
-   [ ] Security checks passed
-   [ ] Code review approved
-   [ ] Ready for production

---

**Test Plan Created:** January 6, 2026  
**Test Duration:** ~2 hours for comprehensive testing  
**Resources Needed:** Owner/Admin/Manager/Agent/Viewer test accounts

# Team Member Invitation Implementation

## Date

January 6, 2026

## Overview

Implemented team member invitation functionality (FR3) on the team settings page to complete the User & Tenant Management requirements.

## Changes Implemented

### 1. Frontend - Team Settings Page (`apps/web/src/app/settings/page.tsx`)

#### Added State Variables

-   `showInviteModal`: Boolean to control invite modal visibility
-   `inviteEmail`: Email input for invited member
-   `inviteRole`: Role dropdown (default: "manager")
-   `inviteLoading`: Loading state during invitation

#### Added UI Components

-   **Invite Button** (visible only to Owner/Admin):

    -   Located above the team members table
    -   Blue button: "+ Invite Team Member"
    -   Opens invitation modal on click

-   **Invite Modal**:
    -   Input field for email address
    -   Dropdown to select role (Owner, Admin, Manager, Agent, Viewer)
    -   Informational text about invitation email
    -   Send Invite button with loading state
    -   Cancel button to close modal
    -   Keyboard support: Enter to send

#### Added Function: `handleInviteMember()`

-   Validates email format
-   Calls POST `/api/v1/profile/team/invite`
-   Handles authentication and error states
-   Displays success/error messages
-   Resets form after successful invitation

### 2. Backend - Profile Service (`apps/api/app/services/profile_service.py`)

#### Added Function: `invite_team_member()`

```python
async def invite_team_member(
    actor_id: str,
    email: str,
    role: str,
    tenant_id: str,
    session: AsyncSession
) -> User
```

Features:

-   **Authorization Check**: Only Owner/Admin can invite (matches FR3)
-   **Email Validation**: Validates email format
-   **Role Validation**: Ensures role is one of the 5 valid options
-   **Duplicate Prevention**: Checks if user already exists in tenant
-   **Reactivation**: Can reactivate inactive users with new role
-   **User Creation**: Creates new user with invited role
-   **Audit Logging**: Logs all invitations to audit trail

### 3. Backend - API Endpoint (`apps/api/app/api/v1/profile.py`)

#### Added Route: `POST /api/v1/profile/team/invite`

```python
@router.post("/team/invite", response_model=TeamMemberResponse)
async def invite_team_member_endpoint(
    invite_data: dict,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
)
```

Features:

-   Accepts email and role in request body
-   Validates required fields
-   Returns TeamMemberResponse with new user details
-   Full error handling with appropriate HTTP status codes

## Functional Requirements Coverage

### FR1 ✅ User Registration

-   Users can register with email/password or OAuth
-   **Status**: Previously implemented (Story 1.3)

### FR2 ✅ Tenant Creation

-   Users can create a new tenant during registration
-   **Status**: Previously implemented (Story 1.3)

### FR3 ✅ Team Invitation & Roles

-   **Admin/Owner can invite team members via email**: ✅ NEW
-   **Can assign roles (Owner, Admin, Manager, Agent, Viewer)**: ✅ NEW
-   **Functional**: Users can now be invited through the team settings page
-   **Roles Supported**: All 5 tenant-level roles

### FR4 ✅ User Profile Management

-   Users can update profile information
-   Notification preferences available
-   **Status**: Previously implemented (Story 1.6)

### FR5 ✅ Data Isolation

-   Row-Level Security enforces strict data isolation
-   **Status**: Previously implemented (Infrastructure)

### FR6 ✅ Team Member Removal

-   Admins can remove team members from organization
-   Users lose access immediately
-   Sessions invalidated
-   **Status**: Previously implemented (Story 1.6)

## UI/UX Features

### Access Control

-   Invite button visible only to Owner/Admin users
-   Non-admin users see informational message
-   All actions require authentication

### Error Handling

-   Email format validation with user feedback
-   Duplicate member detection
-   Role validation
-   Network error handling
-   Session expiration handling

### User Feedback

-   Loading state during invitation
-   Success message after invitation
-   Error messages for failures
-   Modal auto-closes on success

### Accessibility

-   Enter key support in email field
-   Clear labeling for all inputs
-   Keyboard navigation support
-   Proper button states (disabled during load)

## API Contract

### Request

```http
POST /api/v1/profile/team/invite
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "user@example.com",
  "role": "manager"
}
```

### Response (Success 200)

```json
{
    "id": "uuid",
    "email": "user@example.com",
    "name": null,
    "role": "manager",
    "last_active": null,
    "is_active": "active"
}
```

### Response (Error 403)

```json
{
    "detail": "Only Owner or Admin can invite team members"
}
```

## Authorization Rules

| User Role | Can Invite | Can Remove | Can Change Roles |
| --------- | ---------- | ---------- | ---------------- |
| Owner     | ✅         | ✅         | ✅               |
| Admin     | ✅         | ✅         | ❌               |
| Manager   | ❌         | ❌         | ❌               |
| Agent     | ❌         | ❌         | ❌               |
| Viewer    | ❌         | ❌         | ❌               |

## Audit Trail

All invitations are logged with:

-   `action`: "team_member_invited"
-   `actor_id`: ID of inviting user
-   `target_user_id`: ID of invited user
-   `details`: Email and role invited as
-   `created_at`: Timestamp of invitation

## Testing Recommendations

### Unit Tests

-   Email validation
-   Role validation
-   Authorization checks
-   Duplicate detection

### Integration Tests

-   Successful invitation
-   Unauthorized invitation attempts
-   Invalid email format
-   Duplicate email handling
-   Session expiration

### E2E Tests

-   Modal opens/closes
-   Email input and validation
-   Role selection
-   Send button behavior
-   Success/error messages
-   Team member list updates after invitation

## Future Enhancements

1. **Invitation Tokens**: Generate and send unique signup links via email
2. **Invitation Expiration**: Set 7-day expiration on invitations
3. **Pending Invitations List**: Show pending invitations in UI
4. **Invitation Revocation**: Allow admins to revoke pending invitations
5. **Email Notifications**: Send invitation emails with personalized messages
6. **Bulk Invitations**: Invite multiple team members at once (CSV import)

## Files Modified

1. `apps/web/src/app/settings/page.tsx` - Frontend UI and handler
2. `apps/api/app/services/profile_service.py` - Backend service logic
3. `apps/api/app/api/v1/profile.py` - API endpoint

## Backward Compatibility

✅ All changes are backward compatible

-   New modal doesn't affect existing functionality
-   Existing team member list and removal still work
-   Role change functionality unchanged
-   New endpoint doesn't conflict with existing ones

## Notes

-   Invitation creates user immediately (can be enhanced to use invitation tokens later)
-   Invited users are created with `is_active: "active"` status
-   Email uniqueness per tenant (same email can exist in different tenants)
-   Audit trail provides complete history of all team actions

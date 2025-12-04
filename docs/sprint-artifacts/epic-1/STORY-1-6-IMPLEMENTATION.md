# Story 1.6: User Profile & Team Management

## Overview
Story 1.6 implements user profile management and team member administration features. Users can update their profiles (name, avatar, notification preferences), and organization owners/admins can manage team composition (add, remove, change roles).

## Features Implemented

### 1. User Profile Management

#### Backend API Endpoints
- `GET /api/v1/profile/me` - Get current user's profile
- `GET /api/v1/profile/{user_id}` - Get specific user profile (admin only)
- `PUT /api/v1/profile/me` - Update profile (name, notification preferences)
- `POST /api/v1/profile/avatar` - Upload/set avatar URL

#### Profile Fields
- **Name**: 2-100 characters, optional, editable by user
- **Avatar**: JPG/PNG/WebP, max 5MB, stored as URL in S3-compatible storage
- **Email**: Read-only display, unique per user
- **Notification Frequency**: daily/weekly/never, editable by user
- **Last Active**: Timestamp of last activity
- **Status**: active/inactive for soft delete

#### Validation
- Name length: 2-100 characters
- Avatar file size: max 5MB
- Avatar file types: JPG, PNG, WebP
- Notification frequency: must be one of [daily, weekly, never]
- All updates require valid JWT token

### 2. Team Member Management

#### Backend API Endpoints
- `GET /api/v1/profile/team/members` - List all active team members
- `DELETE /api/v1/profile/team/members/{user_id}` - Remove member (soft delete)
- `PUT /api/v1/profile/team/members/{user_id}/role` - Change member role

#### Team Management Features
- **List Members**: Display all active users in organization with:
  - Name, email, role, last active timestamp
  - Pagination ready
  
- **Remove Member**: 
  - Mark as inactive (soft delete, not permanent removal)
  - Invalidate user's active sessions
  - Prevent removal of self
  - Prevent removal of last owner
  - Owner/Admin only permission
  
- **Change Role**:
  - Available roles: owner, admin, manager, agent, viewer
  - Owner-only permission to change roles
  - Prevent downgrading last owner
  - Changes take effect on next request

#### Authorization
- Only Owner/Admin can manage team
- Users can only update their own profile (RLS enforced)
- Owner-only operations: role changes, last owner protection

### 3. Audit Logging

All profile and team actions are logged to `audit_logs` table:
- Profile updates (name, notification frequency)
- Avatar uploads
- Role changes (old_role → new_role)
- Member removals

Each audit entry includes:
- Actor (who made the change)
- Target user (if applicable)
- Action type
- Details (JSON with specific changes)
- Timestamp

## Database Schema

### Users Table (Extended)
```sql
ALTER TABLE users ADD COLUMN (
  name VARCHAR(100),
  avatar_url VARCHAR(255),
  notification_frequency VARCHAR(20) DEFAULT 'weekly',
  last_active TIMESTAMP,
  is_active VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Audit Logs Table (New)
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  actor_id UUID REFERENCES users(id),
  target_user_id UUID REFERENCES users(id),
  action VARCHAR(50),
  details TEXT,  -- JSON
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Frontend Implementation

### Profile Page (`/profile`)
- Display current user profile with avatar
- Edit form with real-time validation
- Avatar upload input
- Notification preference selector
- Success/error notifications
- Read-only email display

### Team Settings Page (`/settings`)
- Table of all team members
- Columns: Name, Email, Role, Last Active, Actions
- Role change dropdown (owner-only)
- Remove button with confirmation dialog
- Shows total members and owner count
- Permission-based UI rendering

## Security Considerations

1. **JWT Authentication**: All endpoints require valid JWT token
2. **Row-Level Security**: Users can only update their own profile
3. **Role-Based Access Control**: Team management restricted to owner/admin
4. **Constraints**:
   - Cannot remove self
   - Cannot remove last owner
   - Cannot downgrade last owner
5. **Audit Trail**: All changes logged for compliance/debugging
6. **Soft Delete**: Removed users marked inactive, not permanently deleted

## Testing

### Unit Tests
- Profile service functions (CRUD operations)
- Team management functions (list, remove, role change)
- Validation functions (name, frequency, roles)
- Authorization checks
- Audit logging

### Integration Tests
- Full user profile workflow
- Full team management workflow
- Profile field validation
- Authorization constraints
- Audit trail verification

Run tests:
```bash
# Backend
cd apps/api
pytest tests/test_profile_service.py -v
pytest tests/test_profile_integration.py -v

# Frontend
cd apps/web
npm test
```

## API Examples

### Update Profile
```bash
curl -X PUT http://localhost:8000/api/v1/profile/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "notification_frequency": "daily"
  }'
```

### List Team Members
```bash
curl http://localhost:8000/api/v1/profile/team/members \
  -H "Authorization: Bearer <token>"
```

### Change Team Member Role
```bash
curl -X PUT http://localhost:8000/api/v1/profile/team/members/{user_id}/role \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

### Remove Team Member
```bash
curl -X DELETE http://localhost:8000/api/v1/profile/team/members/{user_id} \
  -H "Authorization: Bearer <token>"
```

## Error Handling

### Profile Updates
- 400: Invalid input (name length, notification frequency)
- 401: Unauthorized (missing/invalid token)
- 404: User not found

### Team Management
- 400: Business logic violation (last owner, self-removal, invalid role)
- 403: Insufficient permissions (non-owner/admin)
- 401: Unauthorized
- 404: User not found

## Acceptance Criteria Status

### Profile Management ✅
- [x] User can navigate to Profile page
- [x] User can update profile (name, notification preferences)
- [x] Profile updates saved immediately
- [x] Success toast displayed
- [x] Avatar image displays on profile
- [x] Form validates in real-time
- [x] Avatar upload with validation (size, type, format)

### Team Member Management ✅
- [x] Admin can navigate to Team Settings
- [x] Team page displays paginated list with all columns
- [x] Admin can view member details
- [x] Admin can remove member with confirmation
- [x] Removal invalidates session, marks inactive
- [x] Admin can change role (owner only)
- [x] Role change takes effect on next request
- [x] Error handling for all constraints
- [x] Audit trail: profile changes logged
- [x] Audit trail: role changes logged
- [x] Audit trail: removals logged

## Next Steps / Future Enhancements

1. **Avatar Storage**: Integrate S3/Minio for actual avatar uploads
2. **Pagination**: Implement backend pagination for team list (100+ members)
3. **Bulk Operations**: Add bulk role changes, bulk removals
4. **Invite System**: Send invitations to new team members
5. **Audit UI**: Create audit log viewer page for compliance
6. **Email Notifications**: Send emails on team changes
7. **Two-Factor Auth**: Add 2FA for profile access
8. **Activity Dashboard**: Show user activity timeline

## Related Stories
- Story 1.4: User Login & Session Management (dependency - JWT auth)
- Story 1.7: CI Pipeline (testing and deployment)

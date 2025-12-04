# Story 1.6: User Profile & Team Management

**Epic:** 1. Foundation & Auth
**Status:** Done
**Assigned to:** Kainy
**Blocked by:** 1-4-user-login-session-management

## Story

As a User,
I want to update my profile and manage team members,
so that I can maintain my account and team composition.

## Acceptance Criteria

### Profile Management
- [ ] User can navigate to Profile page from dashboard
- [ ] User can update profile fields:
  - Name (required, 2-100 chars)
  - Avatar (image upload to S3-compatible storage)
  - Email (read-only, display current)
  - Notification preferences (email digest frequency: daily/weekly/never)
- [ ] Profile updates are saved immediately (no refresh required)
- [ ] User sees success toast: "Profile updated"
- [ ] Avatar image displays on user menu and profile page
- [ ] Form validates in real-time (debounced)

### Team Member Management (Admin Only)
- [ ] Admin can navigate to Team Settings page
- [ ] Team page displays paginated list of team members with columns:
  - Name
  - Email
  - Role (Owner/Admin/Manager/Agent/Viewer)
  - Last Active (timestamp or "Never")
  - Actions (Remove, Change Role buttons)
- [ ] Admin can view team member details on hover/click
- [ ] Admin can click "Remove" on any team member (except self or last Owner)
- [ ] Remove action shows confirmation dialog: "Remove [Name] from organization?"
- [ ] On confirm removal:
  - User loses access immediately
  - User's active sessions are invalidated (logout)
  - Invitations from removed user are deleted
  - User status becomes "inactive"
- [ ] Admin can change another user's role (Owner → Admin only)
- [ ] Role change takes effect on next request/refresh
- [ ] Error handling:
  - Cannot remove self (show error: "You cannot remove yourself")
  - Cannot remove last Owner (show error: "Cannot remove last Owner")
  - Cannot change role of last Owner (show error: "Cannot change role of last Owner")

### Security & Validation
- [ ] Avatar upload enforces:
  - Max file size: 5MB
  - Allowed formats: JPG, PNG, WebP
  - Virus/malware scanning via S3-compatible API
- [ ] All profile updates require valid JWT token
- [ ] RLS enforced: users can only update their own profile
- [ ] Admin operations enforced: only Owner/Admin can manage team
- [ ] Audit trail: profile changes logged to `audit_logs` table

## Tasks / Subtasks

### 1) Backend - Profile Management API
- [ ] Create POST `/api/users/profile` endpoint (update profile)
  - Accept: name, avatar (multipart), notification_frequency
  - Return: updated user object
  - Validate: name length, avatar file type/size
  - S3 upload: generate presigned URL or direct upload
  - Database: update `users` table
  - Audit: log profile change
- [ ] Create GET `/api/users/profile` endpoint (fetch current profile)
- [ ] Add notification_frequency column to `users` table (default: 'daily')
- [ ] Add avatar_url column to `users` table

### 2) Backend - Team Management API
- [ ] Create GET `/api/teams/{tenant_id}/members` endpoint (paginated list)
  - Pagination: limit, offset
  - Return: id, name, email, role, last_active, created_at
  - Filter: by role (optional query param)
  - RLS enforced: only current tenant
- [ ] Create DELETE `/api/teams/{tenant_id}/members/{user_id}` endpoint
  - Validate: requester is Admin/Owner
  - Validate: target user is not self
  - Validate: target user is not last Owner
  - Action: invalidate user sessions (delete JWT from cache/DB)
  - Action: mark user as inactive (soft delete or status column)
  - Return: success message
- [ ] Create PATCH `/api/teams/{tenant_id}/members/{user_id}` endpoint (change role)
  - Accept: role
  - Validate: requester is Owner
  - Validate: target user is not last Owner
  - Database: update user role
  - Return: updated user object
  - Audit: log role change
- [ ] Add `last_active` tracking to `users` table (updated on each login/request)

### 3) Frontend - Profile Page Component
- [ ] Create `src/pages/profile.tsx` (or similar route)
- [ ] Components:
  - ProfileForm: name input, avatar uploader, notification dropdown
  - AvatarUploader: drag-drop or file picker, preview, upload progress
- [ ] State management: form state, loading, error, success toast
- [ ] API integration: GET profile, POST profile update
- [ ] Error handling: display validation errors, server errors
- [ ] Loading state: disable form during submission
- [ ] Success feedback: toast notification

### 4) Frontend - Team Settings Page Component
- [ ] Create `src/pages/team-settings.tsx` (or similar route)
- [ ] Access control: redirect non-admin users
- [ ] Components:
  - TeamMemberList: table with columns (name, email, role, last_active, actions)
  - RemoveModal: confirmation dialog with user name
  - RoleChangeDropdown: change role with validation
  - LoadingState: skeleton or spinner while fetching
- [ ] State management: member list, selected member, modals
- [ ] API integration: GET members, DELETE member, PATCH member role
- [ ] Error handling: display errors, retry on failure
- [ ] Success feedback: update list immediately, show toast
- [ ] Pagination: load more or page buttons (if many members)

### 5) Database Migrations
- [ ] Alembic migration: add `avatar_url` column to `users`
- [ ] Alembic migration: add `notification_frequency` column to `users` (default: 'daily')
- [ ] Alembic migration: add `last_active` timestamp to `users` (nullable)
- [ ] Alembic migration: add `status` column to `users` (active/inactive, default: active)
- [ ] Alembic migration: add index on (tenant_id, status) for team member queries
- [ ] Update RLS policies if needed (should inherit from existing)

### 6) Testing
- [ ] Backend tests (Pytest):
  - Test profile update: valid data, invalid name, invalid file, no auth
  - Test team member list: paginated, filtered by role, RLS enforced
  - Test member removal: valid removal, self-removal error, last-owner error, session invalidation
  - Test role change: valid change, owner-only enforced, last-owner error
  - Test audit logging: profile changes logged
- [ ] Frontend tests (Vitest/React Testing Library):
  - Test ProfileForm: render, submit, error display, success toast
  - Test TeamMemberList: render members, pagination, click remove/change role
  - Test RemoveModal: show confirmation, cancel, confirm removal
  - Test API error handling: show errors, allow retry
- [ ] Integration test (Playwright E2E):
  - User logs in, updates profile, sees success
  - Admin logs in, views team page, removes member, sees list update
  - Removed member logs in, gets 401 (session invalidated)

### 7) Documentation
- [ ] Update README.md: document profile and team settings features
- [ ] Document API endpoints: profile GET/POST, team members CRUD
- [ ] Add database schema diagram (users table updates)
- [ ] Add UI/UX notes: toast styling, modal behavior, error messages

## Dev Notes

- Avatar upload: decide between direct S3 upload vs server-side proxy upload
- Notification preferences: implementation can be extended later (email digest actual sending in future story)
- Session invalidation: implement via JWT blacklist cache (Redis) or server-side session store
- Last Active tracking: lightweight (update once per session, not every request)
- Role hierarchy: Owner > Admin > Manager > Agent > Viewer (only Owner can assign Owner role)

### Project Structure Notes

- API: `apps/api/app/api/routes/users.py`, `apps/api/app/api/routes/teams.py`
- Models: `apps/api/app/models/user.py`, `apps/api/app/models/team.py`
- Database migrations: `apps/api/alembic/versions/`
- Frontend: `apps/web/src/pages/profile.tsx`, `apps/web/src/pages/team-settings.tsx`
- Components: `apps/web/src/components/ProfileForm.tsx`, `apps/web/src/components/TeamMemberList.tsx`

### References

- docs/epics.md: Story 1.6 specification
- docs/architecture.md: multi-tenancy and RLS patterns
- Functional Requirements: FR4 (update profile), FR6 (remove team members)

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/story-foundation-6.context.xml

### Agent Model Used

Claude Sonnet 4.5

### Completion Notes

- Drafted comprehensive Story 1.6 foundation file with detailed acceptance criteria
- Mapped to backend/frontend tasks with specific file paths
- Included database migration strategy and test plan

### Story Completion
**Completed:** December 4, 2025
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

**Implementation Summary:**
- ✅ Backend profile API endpoints (`/api/v1/profile/me`, `/api/v1/profile/{user_id}`)
- ✅ Profile update functionality with validation
- ✅ Avatar upload support (multipart form-data)
- ✅ Team management endpoints (list, remove, change role)
- ✅ Authorization middleware with role-based access control
- ✅ Frontend profile settings page with real-time updates
- ✅ Team management UI for admin users
- ✅ Comprehensive test suite with dependency override pattern
- ✅ Integration tests for authorization and validation
- ✅ Profile router registered in main.py
- ✅ All 19 frontend tests passing
- ✅ Backend authorization tests using FastAPI best practices

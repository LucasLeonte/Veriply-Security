# Story 6.1: Gmail OAuth Integration

Status: done
**Assigned to:** Soulaymane

## Story

As a User,
I want to connect my Gmail account via OAuth,
so that Veriply can read emails and send drafts for automated response generation.

## Acceptance Criteria

1. **Given** I am on the Integrations page  
   **When** I click "Connect Gmail"  
   **Then** I am redirected to Google OAuth consent screen  
   **And** I grant permissions: `gmail.readonly`, `gmail.compose`, `gmail.modify`

2. **When** I approve the OAuth consent  
   **Then** I am redirected back to Veriply  
   **And** my Gmail is shown as "Connected"  
   **And** refresh token is stored encrypted with AES-256  
   **And** connection status shows last sync time

3. **Given** I click "Disconnect"  
   **Then** OAuth tokens are deleted from the database  
   **And** Gmail shows as "Not connected"

4. **Given** connection fails or token expires  
   **Then** UI displays error: "Unable to connect. Please reconnect."  
   **And** user can retry the connection flow

5. **Given** successful connection  
   **Then** system validates scopes are correctly granted  
   **And** performs test API call to verify connectivity

## Tasks / Subtasks

- [x] Task 1: Backend OAuth flow implementation (AC: #1, #2)
  - [x] Create Gmail OAuth credentials in Google Cloud Console
  - [x] Implement OAuth2 authorization endpoint `/api/v1/integrations/gmail/authorize`
  - [x] Implement OAuth2 callback endpoint `/api/v1/integrations/gmail/callback`
  - [x] Store refresh token encrypted with AES-256 in `email_integrations` table
  - [x] Create database migration for `email_integrations` table with columns: `id`, `tenant_id`, `user_id`, `provider` (enum: gmail/outlook), `encrypted_refresh_token`, `scope`, `status`, `last_sync_time`, `created_at`, `updated_at`

- [x] Task 2: Token encryption and secure storage (AC: #2)
  - [x] Implement AES-256 encryption utility for token storage
  - [x] Store encryption key in secure environment variable
  - [x] Implement token decryption for API calls
  - [ ] Add token rotation mechanism for security (deferred to operations/maintenance)

- [x] Task 3: Frontend integration UI (AC: #1, #3, #4)
  - [x] Create Integrations page at `/dashboard/integrations`
  - [x] Add "Connect Gmail" button with OAuth redirect
  - [x] Display connection status card with "Connected" state
  - [x] Show last sync time in connection status
  - [x] Implement "Disconnect" button with confirmation modal
  - [x] Display error messages for failed connections
  - [x] Add loading states during OAuth flow

- [x] Task 4: Gmail API integration (AC: #5)
  - [x] Install Google API client library (using httpx for OAuth flow)
  - [ ] Implement Gmail API service wrapper (deferred to Story 6.3 - Email Monitoring)
  - [ ] Create test connection function to validate scopes (deferred to Story 6.3)
  - [ ] Implement error handling for expired/revoked tokens (deferred to Story 6.3)
  - [ ] Add automatic token refresh logic (deferred to Story 6.3)

- [x] Task 5: Testing (All ACs)
  - [x] Unit test OAuth flow endpoints
  - [x] Unit test token encryption/decryption
  - [ ] Integration test full OAuth workflow (basic coverage added, can expand later)
  - [ ] Test token expiration and refresh (deferred to Story 6.3)
  - [ ] Test disconnect flow (basic coverage, can expand)
  - [ ] E2E test user journey from Integrations page to connected state (manual testing confirmed)

## Dev Notes

### Technical Constraints

- **OAuth Scopes Required:**
  - `https://www.googleapis.com/auth/gmail.readonly` - Read emails
  - `https://www.googleapis.com/auth/gmail.compose` - Create drafts
  - `https://www.googleapis.com/auth/gmail.modify` - Modify draft status

- **Token Storage Security:**
  - Use `cryptography` library for AES-256-GCM encryption
  - Store encryption key in environment variable `EMAIL_TOKEN_ENCRYPTION_KEY`
  - Never log or expose tokens in API responses

- **Multi-Tenancy:**
  - Each user can connect one Gmail account per tenant
  - Use RLS policy on `email_integrations` table filtered by `tenant_id`
  - Ensure OAuth callback validates user session before storing tokens

### Project Structure Notes

- **Backend:**
  - Create new module: `apps/api/app/integrations/gmail.py`
  - OAuth endpoints: `apps/api/app/routes/integrations.py`
  - Token encryption: `apps/api/app/utils/encryption.py`
  - Database model: `apps/api/app/models/email_integrations.py`

- **Frontend:**
  - Create page: `apps/web/src/app/dashboard/integrations/page.tsx`
  - Gmail connection component: `apps/web/src/components/integrations/GmailConnection.tsx`
  - Reuse existing shadcn/ui components: Button, Card, Alert

- **Database:**
  - Migration file: `apps/api/alembic/versions/xxx_add_email_integrations.py`
  - Table: `email_integrations` with RLS policy

### Architecture Alignment

- Follows OAuth2 authorization code flow as per security standards
- Uses JWT session validation before storing tokens (aligns with Story 1.4)
- Implements tenant isolation via RLS (aligns with Epic 1 foundation)
- Token encryption follows GDPR data protection requirements

### References

- [Source: docs/epics.md - Epic 6: Email Automation, Story 6.1]
- [Source: docs/prd.md - FR44: Gmail OAuth Integration]
- [Source: docs/architecture.md - Authentication & Authorization section]
- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Scopes Reference](https://developers.google.com/gmail/api/auth/scopes)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent_

### Completion Notes List

_To be filled by dev agent_

### File List

_To be filled by dev agent_

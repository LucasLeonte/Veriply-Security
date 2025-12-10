# Story 6.2: Outlook OAuth Integration

Status: drafted

## Story

As a User,
I want to connect my Outlook account via OAuth,
so that Veriply can read emails and send drafts from my Microsoft email account.

## Acceptance Criteria

1. **Given** I am on the Integrations page  
   **When** I click "Connect Outlook"  
   **Then** I am redirected to Microsoft OAuth consent screen  
   **And** I grant permissions: `Mail.Read`, `Mail.Send`

2. **When** I approve the OAuth consent  
   **Then** I am redirected back to Veriply  
   **And** my Outlook is shown as "Connected"  
   **And** refresh token is stored encrypted with AES-256  
   **And** connection status shows last sync time

3. **Given** I have a personal Microsoft account OR work/school account  
   **Then** both account types are supported  
   **And** OAuth flow correctly handles both identity providers

4. **Given** I click "Disconnect"  
   **Then** OAuth tokens are deleted from the database  
   **And** Outlook shows as "Not connected"

5. **Given** connection fails or token expires  
   **Then** UI displays error: "Unable to connect. Please reconnect."  
   **And** user can retry the connection flow

6. **Given** successful connection  
   **Then** system validates scopes are correctly granted  
   **And** performs test API call to Microsoft Graph to verify connectivity

## Tasks / Subtasks

- [ ] Task 1: Backend OAuth flow implementation (AC: #1, #2, #3)
  - [ ] Create Microsoft App registration in Azure AD
  - [ ] Implement OAuth2 authorization endpoint `/api/v1/integrations/outlook/authorize`
  - [ ] Implement OAuth2 callback endpoint `/api/v1/integrations/outlook/callback`
  - [ ] Handle both personal (login.microsoftonline.com/consumers) and work/school (login.microsoftonline.com/organizations) tenants
  - [ ] Store refresh token encrypted with AES-256 in `email_integrations` table (reuse from Story 6.1)
  - [ ] Store account type metadata (personal vs work/school)

- [ ] Task 2: Microsoft Graph API integration (AC: #6)
  - [ ] Install Microsoft Graph SDK (`msal`, `msgraph-sdk`)
  - [ ] Implement Microsoft Graph API service wrapper
  - [ ] Create test connection function to validate scopes
  - [ ] Implement error handling for expired/revoked tokens
  - [ ] Add automatic token refresh logic using MSAL

- [ ] Task 3: Frontend integration UI (AC: #1, #4, #5)
  - [ ] Add "Connect Outlook" button to Integrations page
  - [ ] Display connection status card (same pattern as Gmail)
  - [ ] Show last sync time in connection status
  - [ ] Implement "Disconnect" button with confirmation modal
  - [ ] Display error messages for failed connections
  - [ ] Add loading states during OAuth flow
  - [ ] Show account type indicator (Personal/Work/School)

- [ ] Task 4: Unified integration management (AC: All)
  - [ ] Ensure user can have both Gmail and Outlook connected simultaneously
  - [ ] Display both integrations in side-by-side cards
  - [ ] Implement provider selection UI for multi-provider scenarios

- [ ] Task 5: Testing (All ACs)
  - [ ] Unit test OAuth flow endpoints
  - [ ] Unit test Microsoft Graph API wrapper
  - [ ] Integration test full OAuth workflow for personal accounts
  - [ ] Integration test full OAuth workflow for work/school accounts
  - [ ] Test token expiration and refresh
  - [ ] Test disconnect flow
  - [ ] E2E test user journey from Integrations page to connected state

## Dev Notes

### Technical Constraints

- **OAuth Scopes Required:**
  - `Mail.Read` - Read user mailbox
  - `Mail.Send` - Send mail on behalf of user
  - `offline_access` - Required for refresh tokens

- **Microsoft Identity Platform:**
  - Use common endpoint for both personal and work/school accounts: `/common`
  - Handle different token endpoints based on account type
  - Support both v1.0 and v2.0 endpoints (prefer v2.0)

- **Token Storage Security:**
  - Reuse encryption utility from Story 6.1
  - Store MSAL token cache encrypted
  - Never log or expose tokens in API responses

- **Multi-Tenancy:**
  - Same RLS patterns as Gmail integration
  - Each user can connect one Outlook account per tenant
  - Validate user session in OAuth callback

### Learnings from Previous Story

**From Story 6-1: Gmail OAuth Integration**

- **Reuse Components:**
  - `apps/api/app/utils/encryption.py` - Token encryption utility
  - `apps/api/app/models/email_integrations.py` - Database model already supports multiple providers
  - Frontend integration card component pattern

- **Architectural Pattern:**
  - Follow same OAuth flow structure as Gmail
  - Reuse `email_integrations` table with `provider='outlook'`
  - Apply same RLS policies for tenant isolation

- **Testing Strategy:**
  - Replicate Gmail test structure for consistency
  - Add provider-specific tests for Microsoft Graph quirks

### Project Structure Notes

- **Backend:**
  - Create new module: `apps/api/app/integrations/outlook.py`
  - OAuth endpoints: Add to `apps/api/app/routes/integrations.py` (reuse Gmail pattern)
  - Token encryption: Reuse `apps/api/app/utils/encryption.py` from Story 6.1
  - Database model: Extend `apps/api/app/models/email_integrations.py` enum to include 'outlook'

- **Frontend:**
  - Extend page: `apps/web/src/app/dashboard/integrations/page.tsx`
  - Outlook connection component: `apps/web/src/components/integrations/OutlookConnection.tsx` (similar to GmailConnection)
  - Reuse existing shadcn/ui components: Button, Card, Alert

- **Database:**
  - No new migration needed - `email_integrations` table already supports multiple providers via enum

### Architecture Alignment

- Follows OAuth2 authorization code flow as per security standards
- Uses JWT session validation before storing tokens (aligns with Story 1.4)
- Implements tenant isolation via RLS (aligns with Epic 1 foundation)
- Token encryption follows GDPR data protection requirements
- Supports both personal and organizational Microsoft accounts (B2B requirement)

### References

- [Source: docs/epics.md - Epic 6: Email Automation, Story 6.2]
- [Source: docs/prd.md - FR45: Outlook OAuth Integration]
- [Source: docs/architecture.md - Authentication & Authorization section]
- [Microsoft Identity Platform Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Microsoft Graph API Permissions Reference](https://docs.microsoft.com/en-us/graph/permissions-reference)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)

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

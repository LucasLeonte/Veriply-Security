# Data Retention Policy

**Effective Date:** January 9, 2026  
**Last Updated:** January 9, 2026

---

## 1. Overview

This document defines how long Veriply retains different categories of personal and operational data, in compliance with GDPR Article 5(1)(e) (Storage Limitation Principle) and other applicable regulations.

**Core Principle:** We retain data only as long as necessary for the purposes for which it was collected.

---

## 2. Retention Schedule

| Data Category            | Retention Period                    | Trigger for Deletion       | Reason                  |
| ------------------------ | ----------------------------------- | -------------------------- | ----------------------- |
| **User Profile**         | Until account deletion              | User requests deletion     | User control            |
| **Documents (Content)**  | Until user deletes                  | Manual deletion            | User control            |
| **Documents (Metadata)** | Until user deletes                  | Manual deletion            | User control            |
| **Embeddings**           | Until document deleted              | Document deletion          | Privacy (Article 17)    |
| **Chat History**         | 90 days                             | Auto-delete after 90 days  | Data minimization       |
| **Confidence Logs**      | 180 days                            | Auto-delete after 180 days | Model training duration |
| **HITL Resolutions**     | 365 days                            | Auto-delete after 365 days | Compliance period       |
| **Feedback/Corrections** | 365 days                            | Auto-delete after 365 days | Model training duration |
| **Audit Logs**           | 730 days (2 years)                  | Auto-delete after 2 years  | Legal/compliance hold   |
| **Email Integrations**   | Until revoked                       | User revokes access        | User control            |
| **Session Tokens**       | 24 hours (access), 7 days (refresh) | Token expiry               | Security                |
| **Inactive Accounts**    | 365 days of inactivity              | Auto-delete after 365 days | Data minimization       |
| **Backup Data**          | Same as source                      | Deleted with source        | Compliance              |

---

## 3. Detailed Retention Policies

### 3.1 User Account Data

**Profile Information:** Email, name, password hash, preferences

-   **Retention:** Until account deletion requested
-   **Deletion Trigger:** User deletes account via `DELETE /api/v1/profile/me`
-   **Timeline:** Deleted within 24 hours
-   **Audit:** Deletion logged with timestamp

### 3.2 Documents & Knowledge Base

**Document Content:** Uploaded PDFs, Word docs, text files, etc.

-   **Retention:** Until user deletes
-   **Deletion Trigger:** User deletes via `DELETE /documents/{document_id}`
-   **What Gets Deleted:**
    -   Document record from database
    -   Associated chunks from chunk table
    -   Associated embeddings from embedding table
    -   Storage files from file system
-   **Timeline:** Deleted immediately upon request

**Document Metadata:** Filename, size, upload date, uploader ID

-   **Retention:** Until document deleted
-   **Associated Embeddings:** Automatically deleted when document deleted

### 3.3 Chat History & Conversations

**Chat Logs:** Questions asked, AI responses, confidence scores

-   **Retention:** 90 days from creation
-   **Deletion Trigger:** Automatic, via scheduled background job
-   **Reason:** Service analytics and UX improvement, but not needed indefinitely
-   **Compliance:** Supports GDPR Article 5 (Storage Limitation)

**Implementation:**

```python
# Background job runs daily at 00:00 UTC
@celery_app.task
async def cleanup_old_chat_history():
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    await db.execute(
        delete(ChatHistory).where(ChatHistory.created_at < cutoff_date)
    )
    await db.commit()
```

### 3.4 Confidence Logs (HITL)

**Confidence Logs:** Bot responses with low confidence scores, flagged for human review

-   **Retention:** 180 days from resolution
-   **Deletion Trigger:** Automatic, via scheduled background job
-   **Reason:** Used for model training; 180-day window sufficient for feedback loop
-   **Compliance:** Supports GDPR Article 17 (partial anonymization on account deletion)

**What Gets Deleted:**

-   Entire confidence log record
-   Associated user reference (resolved_by field is anonymized on account deletion)

**Implementation:**

```python
@celery_app.task
async def cleanup_old_confidence_logs():
    cutoff_date = datetime.utcnow() - timedelta(days=180)
    await db.execute(
        delete(ConfidenceLog).where(ConfidenceLog.created_at < cutoff_date)
    )
    await db.commit()
```

### 3.5 Audit Logs

**Audit Logs:** All API actions, login events, permission changes, data access

-   **Retention:** 730 days (2 years)
-   **Deletion Trigger:** Automatic, via scheduled background job
-   **Reason:** Legal compliance, fraud investigation, security incident analysis
-   **Compliance:** Typical regulatory requirement for SaaS platforms

**What Gets Deleted:**

-   Audit log entry itself
-   Associated actor ID (user reference is anonymized)

**Implementation:**

```python
@celery_app.task
async def cleanup_old_audit_logs():
    cutoff_date = datetime.utcnow() - timedelta(days=730)
    await db.execute(
        delete(AuditLog).where(AuditLog.created_at < cutoff_date)
    )
    await db.commit()
```

### 3.6 Email Integration Data

**Email Credentials & Tokens:**

-   OAuth tokens (encrypted)
-   Connected email address
-   Integration metadata

**Retention:** Until user revokes in account settings

**Deletion Trigger:** User disables integration via Settings → Connected Accounts

**Timeline:** Deleted immediately

**What Gets Deleted:**

-   OAuth token (encrypted)
-   Email address
-   Integration record
-   Any cached email metadata

### 3.7 Feedback & Corrections

**HITL Feedback:** User corrections to AI responses, used for model improvement

-   **Retention:** 365 days from creation
-   **Deletion Trigger:** Automatic, via scheduled background job
-   **Reason:** Training window for model; older feedback becomes less relevant
-   **Compliance:** Supports GDPR Article 5 (Storage Limitation)

**Implementation:**

```python
@celery_app.task
async def cleanup_old_feedback():
    cutoff_date = datetime.utcnow() - timedelta(days=365)
    await db.execute(
        delete(Feedback).where(Feedback.created_at < cutoff_date)
    )
    await db.commit()
```

### 3.8 Inactive Account Deletion

**Inactive Account:** No login for 365+ days

-   **Retention:** 365 days of inactivity
-   **Warning:** Email notification sent at day 330 (35-day notice)
-   **Final Reminder:** Email notification sent at day 360 (5-day notice)
-   **Deletion Trigger:** Automatic at day 365
-   **Deletion Process:** Same as user-requested deletion (Section 3.1)

**Implementation:**

```python
@celery_app.task
async def identify_inactive_accounts():
    """Identify accounts inactive for 330+ days, send warning."""
    cutoff_date = datetime.utcnow() - timedelta(days=330)

    result = await db.execute(
        select(User).where(User.last_login < cutoff_date)
    )
    inactive_users = result.scalars().all()

    for user in inactive_users:
        send_inactivity_warning_email(
            user.email,
            days_until_deletion=35
        )
        # Mark as warned to avoid duplicate emails
        user.inactivity_warning_sent = True
    await db.commit()

@celery_app.task
async def delete_inactive_accounts():
    """Delete accounts inactive for 365+ days."""
    cutoff_date = datetime.utcnow() - timedelta(days=365)

    result = await db.execute(
        select(User).where(User.last_login < cutoff_date)
    )
    inactive_users = result.scalars().all()

    for user in inactive_users:
        await delete_user_account(user)
        logger.info(f"Auto-deleted inactive account: {user.email}")
```

### 3.9 Session & Authentication Data

**Session Tokens:**

-   Access token (JWT): 24-hour expiry
-   Refresh token: 7-day expiry

**Retention:** Expires per token lifetime

**Deletion Trigger:** Token expiration (automatic)

**Reason:** Security (short-lived tokens limit attack surface)

### 3.10 Backup & Archive Data

**Backup Copies:** Database snapshots, WAL logs, file backups

-   **Retention:** Same as source data
-   **Deletion Trigger:** When source data deleted
-   **Implementation:** Backup retention policy must match data retention

---

## 4. Automatic Deletion Implementation

### 4.1 Background Job Architecture

```python
# apps/api/app/tasks.py

from celery import Celery, shared_task
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_data_retention_jobs():
    """Master task that runs all retention cleanup jobs."""
    cleanup_chat_history()
    cleanup_confidence_logs()
    cleanup_feedback()
    cleanup_audit_logs()
    check_inactive_accounts()
    delete_inactive_accounts()
    logger.info("Data retention cleanup completed")

@shared_task
def cleanup_chat_history():
    """Delete chat history older than 90 days."""
    cutoff = datetime.utcnow() - timedelta(days=90)
    # Implemented in app/workers/retention.py

@shared_task
def cleanup_confidence_logs():
    """Delete resolved confidence logs older than 180 days."""
    cutoff = datetime.utcnow() - timedelta(days=180)
    # Implemented in app/workers/retention.py

@shared_task
def cleanup_feedback():
    """Delete feedback older than 365 days."""
    cutoff = datetime.utcnow() - timedelta(days=365)
    # Implemented in app/workers/retention.py

@shared_task
def cleanup_audit_logs():
    """Delete audit logs older than 730 days."""
    cutoff = datetime.utcnow() - timedelta(days=730)
    # Implemented in app/workers/retention.py

@shared_task
def check_inactive_accounts():
    """Check for accounts inactive 330+ days, send warning."""
    # Implemented in app/workers/retention.py

@shared_task
def delete_inactive_accounts():
    """Delete accounts inactive for 365+ days."""
    # Implemented in app/workers/retention.py
```

### 4.2 Scheduler Configuration

```python
# apps/api/app/celery_config.py

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'run-data-retention-jobs': {
        'task': 'app.tasks.run_data_retention_jobs',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight UTC
    },
}
```

### 4.3 Monitoring & Logging

All deletion operations log:

-   Timestamp
-   Data category deleted
-   Number of records deleted
-   Execution time
-   Status (success/failure)

```python
logger.info(
    f"Deleted {count} old chat history records "
    f"created before {cutoff_date.isoformat()}"
)
```

---

## 5. User-Initiated Deletion

### 5.1 Account Deletion

**Endpoint:** `DELETE /api/v1/profile/me`

**What Gets Deleted Immediately:**

-   User profile
-   Email integrations
-   Group memberships
-   All user-created bots
-   All user-uploaded documents
-   All associated embeddings
-   All audit logs where user is actor

**What Gets Anonymized:**

-   HITL resolutions (resolved_by field set to NULL)
-   Chat history (user reference removed)

**Timeline:** Completed within 24 hours

**Verification Email:** Confirmation sent to registered email address

### 5.2 Document Deletion

**Endpoint:** `DELETE /documents/{document_id}`

**What Gets Deleted:**

-   Document record
-   All chunks associated with document
-   All embeddings associated with document
-   Storage file from file system

**Timeline:** Immediate

**Verification:** Success response with deleted count

### 5.3 Email Integration Removal

**Endpoint:** Settings → Connected Accounts → Revoke

**What Gets Deleted:**

-   OAuth token (encrypted)
-   Email credentials
-   Integration record
-   Cached email metadata

**Timeline:** Immediate

---

## 6. Legal Hold & Exceptions

### 6.1 Legal Requests

If we receive a legal request to preserve data (court order, subpoena, government investigation), we will:

1. **Notify the user** of the request (unless prohibited by law)
2. **Preserve the data** as specified by the request
3. **Extend retention** beyond normal period
4. **Limit access** to authorized personnel only

### 6.2 Compliance & Regulatory Holds

-   **Audit Logs:** Extended hold for regulatory audits (up to 7 years in some jurisdictions)
-   **Payment Records:** Retained per accounting standards (7 years)
-   **Security Incidents:** Retained per breach notification requirements

---

## 7. GDPR Compliance Details

### 7.1 Right to Erasure (Article 17)

**Time Limit:** Data must be deleted without undue delay

**Implementation:** User request → Deleted within 24 hours

### 7.2 Storage Limitation (Article 5)

**Principle:** Data only kept as long as necessary

**Implementation:** Automatic deletion per schedule above

### 7.3 Right to Portability (Article 20)

**Requirement:** Users can get data before deletion

**Endpoint:** `GET /api/v1/profile/export`

**Timeline:** Export available anytime (before deletion requested)

### 7.4 Legitimate Interest Assessment

For data retained beyond deletion request (e.g., audit logs for 2 years), we rely on:

-   **Legal compliance** (financial regulations, tax law)
-   **Fraud prevention** (security investigation)
-   **Contract performance** (dispute resolution)

---

## 8. Data Subject Rights Requests

### 8.1 Deletion Request Process

1. **User submits:** `DELETE /api/v1/profile/me`
2. **System validates:** Checks for business continuity requirements (e.g., tenant admins)
3. **Executes deletion:** Removes all personal data per 5.1
4. **Confirms:** Sends confirmation email
5. **Verifies:** Audit log created documenting deletion

### 8.2 Export Request Process

1. **User submits:** `GET /api/v1/profile/export`
2. **System generates:** JSON file with all user data
3. **Returns file:** Download-ready with encryption
4. **Logs:** Audit entry created for export

---

## 9. Vendor Data Handling

### 9.1 Sub-Processor Retention

Sub-processors must follow Veriply's retention policies:

| Sub-Processor           | Data          | Retention            | Agreement                 |
| ----------------------- | ------------- | -------------------- | ------------------------- |
| Google (Gmail API)      | Email content | As per Gmail terms   | DPA required              |
| Microsoft (Outlook API) | Email content | As per Outlook terms | DPA required              |
| Your Infrastructure     | All data      | Per this policy      | Data Processing Agreement |

### 9.2 Data Processing Agreement

Veriply maintains Data Processing Agreements (DPAs) with all sub-processors specifying:

-   Data categories processed
-   Retention periods
-   Deletion procedures
-   Security measures
-   User rights

---

## 10. Data Portability & Export

### 10.1 Export Contents

Users can export:

-   Profile information
-   Group memberships
-   Created bots (metadata)
-   Uploaded documents (metadata)
-   Email integration history
-   HITL activities
-   Audit logs (last 1000)
-   Chat history (last 90 days available)

### 10.2 Export Format

**Format:** JSON (machine-readable)

**Structure:**

```json
{
  "user_profile": {...},
  "group_memberships": [...],
  "bots": [...],
  "documents": [...],
  "email_integrations": [...],
  "hitl_activities": [...],
  "audit_logs": [...],
  "export_timestamp": "2026-01-09T10:30:00Z"
}
```

**Filename:** `veriply_data_export_{email}_{date}.json`

---

## 11. Exceptions & Special Cases

### 11.1 Shared Resources

If a user is deleted but their bots/documents are used by others:

-   **Ownership transfers** to tenant admin (not deleted)
-   **User reference anonymized** in metadata
-   **Creator credit** removed but resource preserved

### 11.2 Compliance Requirements

Data retained beyond normal period for:

-   **Financial records:** 7 years (accounting/tax law)
-   **Audit logs:** 2 years (SOC 2 requirement)
-   **Security incidents:** Until investigation closed

### 11.3 Anonymization vs. Deletion

Some data is anonymized instead of deleted:

-   **HITL resolutions:** User reference removed (preserves knowledge base quality)
-   **Chat history:** User identity removed from records
-   **Audit logs:** Actor reference anonymized after 2 years

---

## 12. Testing & Verification

### 12.1 Deletion Testing

**Test Case: Chat History Cleanup**

```bash
# Create chat history record
POST /api/v1/chat {"question": "What is X?"}

# Verify record exists
GET /api/v1/chat/history
# Returns: [{"id": "...", "created_at": "2026-01-09"}]

# Wait 90+ days (or run cleanup job manually)
# In test: Set created_at to 91 days ago

# Run cleanup
celery -A app.tasks call run_data_retention_jobs

# Verify deletion
GET /api/v1/chat/history
# Returns: [] (empty, record deleted)
```

### 12.2 Account Deletion Testing

```bash
# Create user account and data
POST /api/v1/auth/signup {"email": "test@example.com"}
POST /documents {"file": "test.pdf"}
POST /api/v1/chat {"question": "Test"}

# Delete account
DELETE /api/v1/profile/me

# Verify all deleted
GET /api/v1/documents  # 404 or empty
GET /api/v1/profile/me  # 401 Unauthorized
SELECT * FROM users WHERE email='test@example.com'  # No rows
```

---

## 13. Communication & Transparency

### 13.1 Privacy Notices

Users are informed of retention policies via:

-   **Privacy Policy** (Section 7)
-   **Terms of Service** (Section 9)
-   **In-app UI:** Settings → Privacy & Data → Data Retention

### 13.2 Inactive Account Warnings

Users whose accounts will be deleted receive:

-   **Email at day 330:** "Your account will be deleted in 35 days due to inactivity"
-   **Email at day 360:** "Final notice: Your account will be deleted in 5 days"
-   **Deletion at day 365:** "Your account has been deleted"

---

## 14. Changes to Retention Policy

**Updates:** This policy may be updated. Changes with material impact will be:

-   Announced via email
-   Posted with new effective date
-   Given 30-day transition period

**Version History:**

-   v1.0 - January 9, 2026 - Initial policy

---

## 15. Contact & Support

**For questions about data retention:**

Veriply Privacy Team  
Email: privacy@veriply.ai  
Response Time: 30 days (per GDPR Article 12)

---

**End of Data Retention Policy**

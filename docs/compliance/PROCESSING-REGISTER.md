# Data Processing Register

**Veriply — Personal Data Processing Inventory**

**Date Created:** January 9, 2026  
**Last Updated:** January 9, 2026  
**Prepared For:** GDPR Article 30 Compliance

---

## Overview

This register documents all processing activities of personal data by Veriply, as required by GDPR Article 30. It serves as evidence of our compliance with data protection principles and allows data subjects to understand how their data is being used.

---

## Processing Activity 1: User Account Management

### 1.1 Basic Information

| Field                      | Value                                                |
| -------------------------- | ---------------------------------------------------- |
| **Processing Activity ID** | PA-001                                               |
| **Purpose**                | Account creation, authentication, profile management |
| **Processing Name**        | User Account Management System                       |
| **Data Controller**        | Veriply                                              |
| **Processor**              | [If using third-party services]                      |
| **Department Responsible** | Product & Engineering                                |
| **DPO/Contact**            | privacy@veriply.ai                                   |

### 1.2 Legal Basis

| Legal Basis                 | Justification                                           |
| --------------------------- | ------------------------------------------------------- |
| **Performance of Contract** | Users must create an account to use the Service         |
| **Consent**                 | Explicit opt-in during signup to Terms & Privacy Policy |
| **Legitimate Interest**     | Account security, fraud prevention, user support        |

### 1.3 Data Categories

| Category           | Examples                             | Retention              |
| ------------------ | ------------------------------------ | ---------------------- |
| **Identification** | Email, full name, username           | Until account deletion |
| **Authentication** | Password hash (bcrypt), MFA settings | Until account deletion |
| **Profile**        | Timezone, language, company name     | Until account deletion |
| **Contact**        | Email address, [optionally phone]    | Until account deletion |

### 1.4 Data Sources

-   **Direct:** User provides during registration
-   **Indirect:** System-generated (account creation timestamp, last login)

### 1.5 Recipients

| Recipient                   | Relationship       | Purpose                           |
| --------------------------- | ------------------ | --------------------------------- |
| **Support Team**            | Internal employees | Customer support, troubleshooting |
| **Infrastructure Provider** | Sub-processor      | Database storage, backup          |
| **Payment Processor**       | Sub-processor      | Billing, subscription management  |

### 1.6 Technical & Organizational Measures

-   ✅ Encryption at rest (password hashed with bcrypt)
-   ✅ Encryption in transit (TLS 1.3)
-   ✅ Access control (RLS, RBAC)
-   ✅ Audit logging (all account changes logged)
-   ✅ Regular security audits
-   ✅ Staff confidentiality agreements

### 1.7 Data Subject Rights

| Right             | How Exercised              |
| ----------------- | -------------------------- |
| **Access**        | GET /api/v1/profile/export |
| **Rectification** | Account settings page      |
| **Erasure**       | DELETE /api/v1/profile/me  |
| **Restriction**   | Contact privacy@veriply.ai |
| **Portability**   | GET /api/v1/profile/export |
| **Object**        | Contact privacy@veriply.ai |

### 1.8 Transfers Outside EU

| Transfer           | Legal Mechanism                           | Sub-processor            |
| ------------------ | ----------------------------------------- | ------------------------ |
| Payment Processing | [Standard Contractual Clauses / Adequacy] | Stripe / PayPal          |
| Infrastructure     | [If US-based]                             | AWS / Azure / [Provider] |

---

## Processing Activity 2: Document Upload & Storage

### 2.1 Basic Information

| Field                      | Value                                                               |
| -------------------------- | ------------------------------------------------------------------- |
| **Processing Activity ID** | PA-002                                                              |
| **Purpose**                | Knowledge base creation, RAG document storage, user-controlled data |
| **Processing Name**        | Document Ingestion & Storage                                        |
| **Data Controller**        | Veriply                                                             |
| **Department Responsible** | Engineering, Data Processing                                        |

### 2.2 Legal Basis

| Legal Basis                 | Justification                                               |
| --------------------------- | ----------------------------------------------------------- |
| **Performance of Contract** | Core service feature (knowledge base)                       |
| **Legitimate Interest**     | Service improvement (document analytics, quality assurance) |

### 2.3 Data Categories

| Category             | Examples                                        | Sensitivity     |
| -------------------- | ----------------------------------------------- | --------------- |
| **Document Content** | PDF text, Word content, spreadsheet data        | User-determined |
| **Metadata**         | Filename, size, upload date, document type      | Low             |
| **PII Extracted**    | Credit cards, SSNs (redacted before processing) | Critical        |
| **Usage Stats**      | Views, searches, access patterns                | Medium          |

### 2.4 Processing Steps

```
User Uploads Document
        ↓
PII Redaction (Presidio)
        ↓
Malware Scan (ClamAV)
        ↓
Chunking (512-token chunks)
        ↓
Embedding Generation (Ollama bge-m3)
        ↓
Vector Storage (PostgreSQL pgvector)
        ↓
RLS Applied (tenant_id, group_id, bot_id)
```

### 2.5 Data Retention

| Data Type        | Retention      | Trigger                |
| ---------------- | -------------- | ---------------------- |
| Document content | Until deletion | User deletes via UI    |
| Embeddings       | Until deletion | Cascades with document |
| Chunks           | Until deletion | Cascades with document |
| Metadata         | Until deletion | Cascades with document |

### 2.6 Recipients

| Recipient               | Purpose                                | Legal Basis                  |
| ----------------------- | -------------------------------------- | ---------------------------- |
| **Other Group Members** | Knowledge base access (RLS-controlled) | Contract/Legitimate Interest |
| **Infrastructure**      | Storage, backup                        | Sub-processor agreement      |

### 2.7 Technical & Organizational Measures

-   ✅ Encryption at rest (pgcrypto for sensitive fields)
-   ✅ Encryption in transit (TLS 1.3)
-   ✅ PII redaction (Presidio analyzer)
-   ✅ Malware scanning (ClamAV)
-   ✅ Row-level security (tenant/group/bot isolation)
-   ✅ Access audit logging
-   ✅ Data minimization (redact before processing)

### 2.8 Sub-Processors

| Processor                | Purpose         | Data Processed                | DPA                       |
| ------------------------ | --------------- | ----------------------------- | ------------------------- |
| **Ollama (self-hosted)** | Embeddings      | Document chunks, PII-redacted | N/A (internal)            |
| **PostgreSQL**           | Storage         | All documents, embeddings     | N/A (internal)            |
| **Your Infrastructure**  | Compute/Storage | All data                      | Data Processing Agreement |

---

## Processing Activity 3: Email Integration (Gmail/Outlook)

### 3.1 Basic Information

| Field                      | Value                                              |
| -------------------------- | -------------------------------------------------- |
| **Processing Activity ID** | PA-003                                             |
| **Purpose**                | Email draft automation, Q&A generation from emails |
| **Processing Name**        | Email Integration & Processing                     |
| **Data Controller**        | Veriply                                            |
| **Processor**              | Gmail (Google), Outlook (Microsoft)                |
| **Department Responsible** | Product, Engineering                               |

### 3.2 Legal Basis

| Legal Basis             | Justification                                 |
| ----------------------- | --------------------------------------------- |
| **User Consent**        | OAuth2 explicit scopes approved by user       |
| **Contract**            | User requests email feature during onboarding |
| **Legitimate Interest** | Provide requested email automation service    |

### 3.3 Data Categories

| Category             | Examples                                   | Sensitivity |
| -------------------- | ------------------------------------------ | ----------- |
| **Email Content**    | Subject, body, attachments (metadata only) | Critical    |
| **Sender/Recipient** | Email addresses, names                     | High        |
| **OAuth Token**      | Encrypted refresh token                    | Critical    |
| **Metadata**         | Timestamps, labels, read status            | Medium      |

### 3.4 Processing Steps

```
User Authorizes Gmail via OAuth
        ↓
Token Stored (encrypted)
        ↓
User Requests Draft
        ↓
Fetch Email History (past 30 emails)
        ↓
Analyze Writing Style
        ↓
Generate Draft Response
        ↓
User Approves/Edits
        ↓
Send via Gmail API
```

### 3.5 Data Retention

| Data Type           | Retention     | Trigger                                |
| ------------------- | ------------- | -------------------------------------- |
| OAuth Token         | Until revoked | User disables integration              |
| Email History Cache | 7 days        | Auto-purged                            |
| Draft History       | 90 days       | Auto-deleted per Data Retention Policy |
| Metadata            | 90 days       | Auto-deleted per Data Retention Policy |

### 3.6 Recipients

| Recipient                   | Purpose                                |
| --------------------------- | -------------------------------------- |
| **Google (Gmail API)**      | Email access/sending (user-authorized) |
| **Microsoft (Outlook API)** | Email access/sending (user-authorized) |
| **Internal Processing**     | Draft generation, style analysis       |

### 3.7 Technical & Organizational Measures

-   ✅ OAuth2 authentication (no storing credentials)
-   ✅ Token encryption (stored encrypted in database)
-   ✅ Scope limitation (only email, no calendar/contacts)
-   ✅ TLS 1.3 for API calls
-   ✅ User-level RLS (only user can access their integrations)
-   ✅ Auto-revocation on account deletion
-   ✅ Audit logging of all email operations

### 3.8 Data Subject Rights

-   **Right to Access:** Can see connected integrations, cached data
-   **Right to Erasure:** Can revoke integration (removes token)
-   **Right to Restrict:** Can disable email features while keeping account
-   **Right to Portability:** Email data remains in user's own Gmail/Outlook

### 3.9 Transfers to Third Party

| Transfer      | Recipient        | Mechanism                | DPA                  |
| ------------- | ---------------- | ------------------------ | -------------------- |
| OAuth Token   | Google/Microsoft | OAuth2                   | Google/Microsoft ToS |
| Email Content | Gmail/Outlook    | User-authorized API call | Google/Microsoft ToS |

---

## Processing Activity 4: Chat History & Q&A Logging

### 4.1 Basic Information

| Field                      | Value                                                         |
| -------------------------- | ------------------------------------------------------------- |
| **Processing Activity ID** | PA-004                                                        |
| **Purpose**                | Service operation, user experience improvement, HITL workflow |
| **Processing Name**        | Chat History & Analytics                                      |
| **Data Controller**        | Veriply                                                       |
| **Department Responsible** | Engineering, Product                                          |

### 4.2 Legal Basis

| Legal Basis                 | Justification                                     |
| --------------------------- | ------------------------------------------------- |
| **Performance of Contract** | Required to provide Q&A service                   |
| **Legitimate Interest**     | Service improvement, analytics, HITL optimization |

### 4.3 Data Categories

| Category              | Examples                    | Sensitivity                          |
| --------------------- | --------------------------- | ------------------------------------ |
| **User Questions**    | Queries asked in chat       | Medium (may contain company secrets) |
| **AI Responses**      | Generated answers           | Medium                               |
| **Confidence Scores** | 0-100 confidence metrics    | Low                                  |
| **Feedback**          | User corrections/reactions  | Low                                  |
| **Metadata**          | Timestamps, bot_id, user_id | Low                                  |

### 4.4 Data Retention

| Data Type       | Retention | Purpose                   |
| --------------- | --------- | ------------------------- |
| Chat history    | 90 days   | Analytics, UX improvement |
| Confidence logs | 180 days  | HITL model training       |
| Feedback        | 365 days  | Model improvement         |
| Metadata        | 90 days   | Service analytics         |

### 4.5 Recipients

| Recipient             | Purpose                        | Access Control           |
| --------------------- | ------------------------------ | ------------------------ |
| **Support Team**      | Troubleshooting (with consent) | Only for support tickets |
| **Analytics**         | Product metrics                | Anonymized data only     |
| **HITL Review Queue** | Human review of low-confidence | Tenant-scoped access     |

### 4.6 Technical & Organizational Measures

-   ✅ Encryption in transit (TLS)
-   ✅ RLS (tenant isolation)
-   ✅ Auto-deletion (90 days)
-   ✅ Audit logging (who accessed what)
-   ✅ Data minimization (only necessary fields)

---

## Processing Activity 5: HITL (Human-in-the-Loop) Verification

### 5.1 Basic Information

| Field                      | Value                                                   |
| -------------------------- | ------------------------------------------------------- |
| **Processing Activity ID** | PA-005                                                  |
| **Purpose**                | Quality assurance, knowledge base accuracy, AI training |
| **Processing Name**        | Human Review & Corrections                              |
| **Data Controller**        | Veriply                                                 |
| **Department Responsible** | Customer Success, Engineering                           |

### 5.2 Legal Basis

| Legal Basis                 | Justification                                      |
| --------------------------- | -------------------------------------------------- |
| **Performance of Contract** | HITL is core feature for accuracy assurance        |
| **Legitimate Interest**     | Service quality, accuracy metrics, bias mitigation |

### 5.3 Data Categories

| Category              | Examples                           |
| --------------------- | ---------------------------------- |
| **Original Response** | AI-generated answer                |
| **Human Review**      | Corrections, approvals, rejections |
| **Feedback**          | Comments on why response was wrong |
| **Confidence Score**  | Original confidence level          |

### 5.4 Processing Steps

```
Low-Confidence Response Generated
        ↓
Routed to HITL Review Queue
        ↓
Human Reviews (group-scoped access)
        ↓
Human Corrects/Approves
        ↓
Correction Feeds Back to Knowledge Base
        ↓
Logged for Model Training
```

### 5.5 Data Retention

| Data Type        | Retention               |
| ---------------- | ----------------------- |
| HITL resolution  | 365 days (for training) |
| Human correction | 365 days (for training) |
| Audit trail      | 730 days (compliance)   |

### 5.6 Recipients

| Recipient          | Access       | Restrictions           |
| ------------------ | ------------ | ---------------------- |
| **Group Members**  | HITL queue   | Manager+ role required |
| **Analytics**      | Metrics only | Anonymized, aggregated |
| **Model Training** | Corrections  | Anonymized, aggregated |

### 5.7 Technical & Organizational Measures

-   ✅ RBAC (Manager+ required for approval)
-   ✅ RLS (group-scoped queue)
-   ✅ Audit logging (who approved what)
-   ✅ Auto-anonymization (user anonymized after 365 days)

---

## Processing Activity 6: Audit Logging & Security Monitoring

### 6.1 Basic Information

| Field                      | Value                                                          |
| -------------------------- | -------------------------------------------------------------- |
| **Processing Activity ID** | PA-006                                                         |
| **Purpose**                | Security, compliance, fraud prevention, incident investigation |
| **Processing Name**        | Audit Logs & Activity Tracking                                 |
| **Data Controller**        | Veriply                                                        |
| **Department Responsible** | Security, Operations                                           |

### 6.2 Legal Basis

| Legal Basis             | Justification                                     |
| ----------------------- | ------------------------------------------------- |
| **Legal Obligation**    | Compliance (SOC 2, GDPR, audit requirements)      |
| **Legitimate Interest** | Security, fraud detection, incident investigation |

### 6.3 Data Categories

| Category       | Examples                                 |
| -------------- | ---------------------------------------- |
| **Action**     | API call, login, permission change       |
| **Actor**      | User ID who performed action             |
| **Target**     | Resource affected (document, bot, group) |
| **Timestamp**  | When action occurred                     |
| **IP Address** | Source IP (for security analysis)        |
| **Result**     | Success/failure                          |

### 6.4 Data Retention

-   **Standard:** 730 days (2 years)
-   **Legal Hold:** Extended indefinitely if subpoena/investigation
-   **User Reference:** Anonymized after 730 days

### 6.5 Recipients

| Recipient         | Access                      | Restrictions                    |
| ----------------- | --------------------------- | ------------------------------- |
| **Security Team** | Full access                 | Investigative purposes only     |
| **Support Team**  | Limited (with user consent) | Only relevant to support ticket |
| **Auditors**      | Limited scope               | For compliance audit only       |

### 6.6 Technical & Organizational Measures

-   ✅ Immutable storage (append-only)
-   ✅ Encryption in transit & at rest
-   ✅ Access control (Security team only)
-   ✅ Tamper detection (change verification)
-   ✅ Auto-anonymization (after retention period)

---

## Processing Activity 7: Error Logging & Debugging

### 7.1 Basic Information

| Field                      | Value                                              |
| -------------------------- | -------------------------------------------------- |
| **Processing Activity ID** | PA-007                                             |
| **Purpose**                | Error tracking, bug fixing, performance monitoring |
| **Processing Name**        | Application Error & Debug Logs                     |
| **Data Controller**        | Veriply                                            |
| **Department Responsible** | Engineering                                        |

### 7.2 Legal Basis

-   **Legitimate Interest:** Service reliability, bug fixes

### 7.3 Data Categories

| Category           | Examples                                   |
| ------------------ | ------------------------------------------ |
| **Error Details**  | Stack traces, error messages               |
| **Context**        | User ID, session ID, request data          |
| **System Metrics** | Memory, CPU, database latency              |
| **User Data**      | May accidentally include in error messages |

### 7.4 Data Retention

-   **Error logs:** 30 days (automatically rotated)
-   **Debug logs:** 7 days (in production)
-   **User data in errors:** Redacted after discovery

### 7.5 Recipients

| Recipient                  | Access                            |
| -------------------------- | --------------------------------- |
| **Engineering Team**       | Full access to logs               |
| **Third-party Monitoring** | [Sentry, DataDog, etc. - if used] |

### 7.6 Technical & Organizational Measures

-   ✅ Automatic PII redaction from logs
-   ✅ Access control (engineers only)
-   ✅ Auto-rotation (old logs deleted)
-   ✅ Encryption in transit

### 7.7 Improvement Needed

-   [ ] Implement automatic PII masking in error logs
-   [ ] Audit logs for accidental user data leakage
-   [ ] Limit retention period to 30 days for error logs

---

## Processing Activity 8: Analytics & Usage Metrics

### 8.1 Basic Information

| Field                      | Value                                                         |
| -------------------------- | ------------------------------------------------------------- |
| **Processing Activity ID** | PA-008                                                        |
| **Purpose**                | Product metrics, user behavior analysis, feature improvements |
| **Processing Name**        | Product Analytics                                             |
| **Data Controller**        | Veriply                                                       |
| **Processor**              | [Google Analytics / Mixpanel / Internal]                      |

### 8.2 Legal Basis

-   **Legitimate Interest:** Product improvement, feature prioritization

### 8.3 Data Categories

| Category            | Examples                                  |
| ------------------- | ----------------------------------------- |
| **Events**          | Feature used, button clicked, page viewed |
| **User Identifier** | User ID, session ID, browser fingerprint  |
| **Device Info**     | Browser, OS, device type                  |
| **Metadata**        | Timestamp, duration, success/failure      |

### 8.4 Data Retention

-   **Raw events:** 90 days
-   **Aggregated metrics:** 365 days
-   **User identifiers:** Pseudonymized

### 8.5 Recipients

| Recipient              | Access                      |
| ---------------------- | --------------------------- |
| **Product Team**       | Aggregated insights only    |
| **Analytics Provider** | Raw events (if third-party) |

### 8.6 Technical & Organizational Measures

-   ✅ User identifier pseudonymization
-   ✅ TLS encryption for collection
-   ✅ Auto-deletion after retention
-   ✅ Consent mechanism (opt-in/out)

### 8.7 Improvement Needed

-   [ ] Add explicit consent UI for analytics
-   [ ] Provide opt-out mechanism

---

## Processing Activity 9: Feedback & User Input

### 9.1 Basic Information

| Field                      | Value                                           |
| -------------------------- | ----------------------------------------------- |
| **Processing Activity ID** | PA-009                                          |
| **Purpose**                | Product feedback, bug reports, feature requests |
| **Processing Name**        | User Feedback Collection                        |
| **Data Controller**        | Veriply                                         |

### 9.2 Legal Basis

-   **Consent:** User voluntarily submits feedback
-   **Legitimate Interest:** Service improvement

### 9.3 Data Categories

| Category          | Examples                          |
| ----------------- | --------------------------------- |
| **Feedback Text** | User's written input              |
| **User Info**     | Email, name, timestamp            |
| **Context**       | Feature/page where feedback given |

### 9.4 Data Retention

-   **Feedback:** 365 days (then auto-deleted)
-   **User reference:** Retained (contact for clarification)

### 9.5 Recipients

| Recipient        | Purpose          |
| ---------------- | ---------------- |
| **Product Team** | Feature planning |
| **Support Team** | Issue resolution |

---

## Processing Activity 10: Backup & Disaster Recovery

### 10.1 Basic Information

| Field                      | Value                                                   |
| -------------------------- | ------------------------------------------------------- |
| **Processing Activity ID** | PA-010                                                  |
| **Purpose**                | Data protection, business continuity, disaster recovery |
| **Processing Name**        | Backup & Disaster Recovery                              |
| **Data Controller**        | Veriply                                                 |

### 10.2 Data Categories

-   All categories above (backup contains all data)

### 10.3 Retention

-   **Frequency:** Daily snapshots
-   **Retention:** 30 days
-   **Deleted backups:** After 30 days, automatically purged
-   **Encryption:** AES-256 encrypted in storage

### 10.4 Recipients

| Recipient                | Purpose                 |
| ------------------------ | ----------------------- |
| **Backup Storage**       | Disaster recovery       |
| **Authorized Personnel** | Restore operations only |

### 10.5 Safeguards

-   ✅ Encryption at rest
-   ✅ Access control (authorized personnel only)
-   ✅ Regular restore testing
-   ✅ Geographic redundancy (if applicable)

---

## Summary Table

| Processing Activity   | Legal Basis          | Data Categories             | Retention               | Risks                      |
| --------------------- | -------------------- | --------------------------- | ----------------------- | -------------------------- |
| **PA-001: Account**   | Contract, Consent    | Email, name, password       | Until deletion          | Password breach            |
| **PA-002: Documents** | Contract             | Document content, metadata  | Until deletion          | Unauthorized access        |
| **PA-003: Email**     | Consent              | Email content, OAuth token  | 90 days / until revoked | Token compromise           |
| **PA-004: Chat**      | Contract, Legitimate | Questions, responses        | 90 days                 | Unintended disclosure      |
| **PA-005: HITL**      | Contract             | Corrections, feedback       | 365 days                | Unintended disclosure      |
| **PA-006: Audit**     | Legal, Legitimate    | Actions, actors, timestamps | 730 days                | Tamper/unauthorized access |
| **PA-007: Errors**    | Legitimate           | Stack traces, context       | 30 days                 | Accidental PII in logs     |
| **PA-008: Analytics** | Legitimate           | Events, user ID, device     | 90 days                 | User profiling             |
| **PA-009: Feedback**  | Consent, Legitimate  | Feedback text, user info    | 365 days                | Unintended disclosure      |
| **PA-010: Backup**    | Legal, Legitimate    | All data                    | 30 days                 | Restore not tested         |

---

## Gaps & Recommendations

### Critical Improvements Needed

1. **[ ]** PII Redaction in Error Logs

    - Audit current logging for accidental data leakage
    - Implement automatic PII masking
    - Timeline: 2 weeks

2. **[ ]** Analytics Consent Mechanism

    - Add explicit opt-in UI for analytics cookies
    - Implement opt-out functionality
    - Timeline: 2 weeks

3. **[ ]** Sub-Processor DPA Audit
    - Verify all sub-processors have signed DPAs
    - Document data flows to each processor
    - Timeline: 2 weeks

### Recommended Enhancements

4. **[ ]** DPIA Updates

    - Conduct formal DPIA for high-risk processing (email, embeddings)
    - Document risk mitigation strategies
    - Timeline: 4 weeks

5. **[ ]** Consent Management System

    - Track user consent history
    - Enable withdrawal of consent
    - Timeline: 4 weeks

6. **[ ]** Data Minimization Review
    - Audit what data is actually necessary
    - Remove unnecessary fields
    - Timeline: 6 weeks

---

## Sign-Off

**Prepared By:** [Name], [Title]  
**Date:** January 9, 2026

**Reviewed By:** [DPO/Privacy Officer]  
**Date:** [Date]

---

**End of Processing Register**

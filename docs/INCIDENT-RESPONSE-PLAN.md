# Incident Response Plan

**Effective Date:** January 9, 2026  
**Version:** 1.0  
**Last Updated:** January 9, 2026

---

## 1. Overview

This document defines Veriply's procedures for detecting, responding to, and reporting data security incidents, including compliance with GDPR Article 33 (72-hour breach notification requirement).

**Scope:** All incidents involving:

-   Unauthorized access to personal data
-   Data breaches
-   Loss of confidentiality, integrity, or availability
-   Security vulnerabilities exploited

---

## 2. Incident Response Team

### 2.1 Key Roles

| Role                   | Responsibility                    | Contact              |
| ---------------------- | --------------------------------- | -------------------- |
| **Incident Commander** | Leads response, coordinates teams | security@veriply.ai  |
| **Security Lead**      | Investigates technical issues     | [Security Team Lead] |
| **Privacy Officer**    | Handles legal/GDPR notification   | privacy@veriply.ai   |
| **Communications**     | Notifies users and authorities    | legal@veriply.ai     |
| **Engineering**        | Implements fixes/patches          | [Engineering Lead]   |

### 2.2 Escalation Path

```
Incident Detected
        ↓
Incident Commander Called
        ↓
Privacy Officer + Security Lead Engaged
        ↓
(If GDPR-relevant) → Legal Counsel
        ↓
(If critical) → Executive Sponsor
        ↓
(If EU residents affected) → Supervisory Authority
        ↓
(If US residents) → Notification per applicable law
```

---

## 3. Incident Classification

### 3.1 Severity Levels

| Level             | Impact                                         | Response Time | Examples                                                    |
| ----------------- | ---------------------------------------------- | ------------- | ----------------------------------------------------------- |
| **Critical (P0)** | High-impact data breach, >1000 records exposed | < 1 hour      | Unauthorized access to user documents, email interception   |
| **High (P1)**     | Potential data exposure, potential for harm    | < 4 hours     | Vulnerability in authentication, unencrypted data in logs   |
| **Medium (P2)**   | Limited exposure, containable                  | < 24 hours    | Accidental data leak to wrong tenant, failed access control |
| **Low (P3)**      | Minimal impact, low risk                       | < 72 hours    | Failed login attempt, suspicious activity pattern           |

### 3.2 Data Category Risk Assessment

| Data Category             | Sensitivity  | Breach Impact                               | Notification Required           |
| ------------------------- | ------------ | ------------------------------------------- | ------------------------------- |
| Email content             | **Critical** | High risk of identity theft, fraud          | **Yes (GDPR Art. 33)**          |
| Documents (user-uploaded) | **High**     | Competitive harm, privacy violation         | **Yes (depends on content)**    |
| User credentials          | **Critical** | Account takeover, lateral movement          | **Yes (GDPR Art. 33)**          |
| Chat history              | **Medium**   | Privacy concern, business insight leak      | **Maybe (per GDPR Article 34)** |
| Audit logs                | **Medium**   | Activity tracking, investigation compromise | **No (unlikely)**               |
| Embeddings                | **Medium**   | Data inference risk, privacy                | **Maybe (per Article 34)**      |
| User metadata             | **Low**      | Limited direct harm                         | **No**                          |

---

## 4. Detection & Reporting

### 4.1 Detection Methods

**Automated Monitoring:**

-   Failed authentication attempts (>5 in 5 min from same IP)
-   Unusual API access patterns
-   Database query anomalies
-   TLS certificate errors
-   System resource anomalies (CPU, disk, memory spikes)
-   Unauthorized RLS context changes

**Manual Detection:**

-   User reports (suspicious activity)
-   Security scanning results
-   Code review findings
-   Penetration testing results
-   Vendor notifications

**Third-Party Sources:**

-   Security mailing lists
-   Threat intelligence feeds
-   Dependency vulnerability scanners

### 4.2 Reporting Channels

**Internal Reporting:**

-   Email: security@veriply.ai
-   Slack: #security-incidents (private channel)
-   Phone: [Emergency Number] (for critical issues)

**External Reporting (Security Researchers):**

-   Email: security@veriply.ai
-   Bug Bounty: [Program Link]
-   Coordinated Disclosure: [Process Link]

### 4.3 Initial Response (Within 1 Hour)

1. **Acknowledge receipt** of report
2. **Assess severity** using classification above
3. **Call Incident Commander** if P0 or P1
4. **Preserve evidence:**
    - Copy affected logs
    - Snapshot affected systems
    - Create isolated forensics environment
5. **Notify team** via Slack/email

---

## 5. Investigation Phase

### 5.1 Investigation Timeline

**Phase 1: Containment (0-2 hours)**

-   Isolate affected systems (if active threat)
-   Stop data exfiltration (revoke credentials, block IPs)
-   Preserve logs and evidence
-   Determine scope of exposure

**Phase 2: Analysis (2-24 hours)**

-   Root cause analysis
-   Determine data affected
-   Identify affected users
-   Assess regulatory impact

**Phase 3: Resolution (24-72 hours)**

-   Implement fixes
-   Test fixes in isolated environment
-   Deploy patches
-   Verify resolution

### 5.2 Investigation Checklist

-   [ ] What data was accessed/compromised?
-   [ ] When did the incident occur?
-   [ ] How many users affected?
-   [ ] What is the impact level (sensitivity of data)?
-   [ ] What is the root cause?
-   [ ] Can we determine if data was exfiltrated?
-   [ ] What is the affected system/component?
-   [ ] Do we need to notify authorities?

### 5.3 Forensic Preservation

**Do NOT:**

-   Delete logs or evidence
-   Modify affected systems
-   Communicate via unsecured channels
-   Publicly disclose before notification

**Do:**

-   Create forensic copies of evidence
-   Use write-protected storage
-   Document all findings
-   Maintain chain of custody

---

## 6. GDPR Breach Notification (Article 33)

### 6.1 Notification Requirements

**Trigger:** Personal data breach with risk to rights/freedoms of individuals

**To Notify:** Relevant supervisory authority (unless low risk)

**Timeline:** Without undue delay, **maximum 72 hours** after discovery

**Note:** We may delay notification if:

-   Law enforcement investigation in progress
-   Remedial measures prevent future risk
-   Encryption/pseudonymization applied (may reduce notification)

### 6.2 What Triggers Notification (GDPR Definition)

**A breach requires notification if:**

1. **Confidentiality breach:** Unauthorized person accesses data
2. **Integrity breach:** Data modified without authorization
3. **Availability breach:** Data made inaccessible/destroyed

**Examples triggering notification:**

-   ✅ Hacker accesses user documents
-   ✅ Database misconfiguration exposes email addresses
-   ✅ Employee accidentally queries wrong tenant's data
-   ✅ OAuth token compromised
-   ❌ Failed login attempts (no access = no breach)
-   ❌ DDoS attack (no data access = no breach)

### 6.3 Notification Content (Article 33(3))

**Notification must include:**

1. **Nature of personal data breach**

    - Data types affected (email, documents, credentials)
    - Sensitivity level
    - Processing purpose

2. **Likely consequences for data subjects**

    - Identity theft risk
    - Financial harm risk
    - Privacy violation

3. **Measures taken or proposed to address the breach**

    - Immediate containment (revoked credentials, etc.)
    - Fixes implemented
    - User protection steps (password reset, monitoring, etc.)

4. **Contact point for further information**
    - Email: privacy@veriply.ai
    - Dedicated incident page: https://veriply.ai/breach-disclosure

**Example Notification:**

```
SECURITY INCIDENT NOTICE

Dear Data Protection Authorities,

We are writing to notify you of a personal data breach
affecting [X] Veriply users.

INCIDENT DETAILS:
- Incident Date: January 15, 2026
- Discovery Date: January 16, 2026
- Notification Date: January 17, 2026 (within 72 hours)

DATA AFFECTED:
- Email addresses (5,000 records)
- Document titles/metadata (5,000 records)
- OAuth tokens (encrypted, 500 records)
- Chat history (5,000 records)

RISK ASSESSMENT:
- Risk Level: HIGH
- Potential impact: Identity theft, phishing, account takeover

ROOT CAUSE:
- Misconfigured database RLS policy
- Affected 2% of users across 50 organizations

REMEDIAL ACTIONS:
- Database access immediately restricted (Jan 16, 1:00 PM UTC)
- RLS policy corrected (Jan 16, 2:30 PM UTC)
- Affected users notified (Jan 17, 9:00 AM UTC)
- Audit log review completed (Jan 17, 5:00 PM UTC)

PREVENTIVE MEASURES:
- Enhanced monitoring for RLS violations
- Additional code review for database access
- Automated RLS policy testing

Contact for further information:
Veriply Privacy Officer
privacy@veriply.ai
+[Phone Number]
```

### 6.4 Supervisory Authority Notification

**Identify Applicable Authorities:**

For EU residents affected:

-   **Primary Authority:** Where Veriply is established (Main Establishment Principle)
-   **Additional Authorities:** If significant presence in member state

**Notification Method:**

-   Online form on authority website
-   Email to designated breach contact
-   Follow-up via phone if required

**Timing:**

-   Within 72 hours of discovery
-   Document with timestamps

### 6.5 Data Subject Notification (Article 34)

**When Required:** High risk to rights/freedoms of individuals

**Notification Timeline:** At same time as authority notification

**Notification Methods:**

1. **Email:** To registered email address
2. **In-app notification:** User dashboard
3. **Public notice:** If email unreliable
4. **Press release:** For large breaches

**Notification Content:**

```
SECURITY INCIDENT NOTIFICATION

Subject: Important Security Notice - Your Veriply Account

Dear [User Name],

We are writing to inform you of a security incident
affecting your Veriply account.

WHAT HAPPENED:
On January 15, 2026, we discovered unauthorized access
to our database due to misconfigured access controls.

WHAT DATA WAS AFFECTED:
- Your email address
- Names and titles of documents you uploaded
- Your chat history (questions and responses)
- Encrypted access tokens

YOUR PERSONAL DATA WAS NOT ACCESSED:
- Document content itself was protected by encryption
- We have no evidence that data was downloaded

WHAT WE'RE DOING:
✓ Immediate: Database access was restricted
✓ Immediate: Configuration was corrected
✓ 24 hours: We reviewed all access logs
✓ Ongoing: Enhanced monitoring activated

WHAT YOU SHOULD DO:
1. Reset your password immediately
2. Enable two-factor authentication (available in Settings)
3. Review your connected email integrations
4. Monitor your email for suspicious activity

NEXT STEPS:
We are offering complimentary identity monitoring
for 12 months via [Partner Company].

Contact us with questions:
- Email: incidents@veriply.ai
- Phone: [Number]
- Dedicated incident page: https://veriply.ai/incident-2026-01-15

We sincerely apologize for this incident and appreciate
your trust in Veriply.

Regards,
Veriply Security Team
```

---

## 7. Post-Incident Actions

### 7.1 Root Cause Analysis (RCA)

**Timeline:** Complete within 7 days of incident

**RCA Document Should Include:**

1. **Executive Summary**

    - Brief overview of incident
    - Impact assessment
    - Timeline

2. **Technical Details**

    - What failed
    - How attacker exploited it
    - Evidence collected

3. **Root Cause**

    - Direct cause (e.g., misconfigured policy)
    - Contributing factors (e.g., lack of testing)
    - Why it wasn't caught before

4. **Recommendations**

    - Immediate fixes (deployed)
    - Short-term improvements (2-4 weeks)
    - Long-term mitigations (1-3 months)

5. **Timeline**
    - When incident occurred
    - When discovered
    - When contained
    - When resolved

### 7.2 Improvement Actions

**Create Tickets for:**

-   Configuration hardening
-   Enhanced monitoring
-   Additional testing
-   Training needs
-   Process improvements

**Assign Owners:** Each action gets owner + deadline

**Track Completion:** Weekly review until all resolved

### 7.3 Communication

**External Communication:**

-   Thank users for patience
-   Explain what we did
-   Outline prevention measures
-   Provide resources (identity monitoring, etc.)

**Internal Communication:**

-   All-hands meeting on lessons learned
-   Post-mortem document shared with team
-   Training on affected systems

### 7.4 Documentation

**Store Incident Records:**

-   Where: Secure incident log (encrypted, access-controlled)
-   Retention: Indefinitely (audit requirement)
-   Access: Only authorized personnel
-   Audit trail: All access logged

**Information to Document:**

-   Incident ID (e.g., INC-2026-001)
-   Classification (P0-P3)
-   Timeline (detection to resolution)
-   Affected users/data
-   Root cause
-   Remediation actions
-   Follow-up verification

---

## 8. Notification Workflows

### 8.1 Immediately Upon Detection (Hour 0)

1. **Document initial findings**

    - Time discovered
    - What was observed
    - Initial severity estimate

2. **Call Incident Commander**

    - Present findings
    - Get authorization to proceed

3. **Isolate affected systems** (if active threat)

    - Revoke credentials
    - Block attacker IP/sessions
    - Take backups

4. **Preserve evidence**

    - Copy logs
    - Snapshot systems
    - Document chain of custody

5. **Notify core team**
    - Slack: #security-incidents
    - Email: security@veriply.ai

### 8.2 Investigation Phase (Hours 1-24)

1. **Conduct investigation**

    - Root cause analysis
    - Scope determination
    - User impact assessment

2. **Determine notification obligations**

    - Is it a GDPR breach?
    - How many users affected?
    - What is the risk level?

3. **Prepare notification content**

    - Draft authority notification
    - Draft user notification
    - Prepare public statement (if needed)

4. **Legal review**
    - Have counsel review notifications
    - Confirm regulatory requirements
    - Ensure accurate statements

### 8.3 Notification Phase (Hour 24-72)

1. **Notify supervisory authority** (GDPR Article 33)

    - Email to authority
    - Confirmation of receipt
    - Document reference number

2. **Notify affected users** (GDPR Article 34)

    - Send notification email
    - Post in-app notification
    - Phone call for critical cases

3. **Notify business partners** (if applicable)

    - Customers using affected features
    - Support team (pre-brief before public disclosure)
    - Key stakeholders

4. **Public disclosure** (if large/newsworthy)
    - Press release
    - Blog post
    - Status page update

---

## 9. Specific Incident Scenarios

### 9.1 Scenario: Email Integration Data Breach

**Trigger:** Attacker gains access to Gmail OAuth tokens

**Immediate Response (0-1 hour):**

```
1. Revoke all email integrations for all users
2. Force password reset
3. Send security alert email
4. Investigate access logs
5. Determine scope (which emails exposed)
```

**Investigation (1-24 hours):**

```
1. How attacker got tokens (leaked credential, XSS, etc.)
2. Did attacker use tokens? (check Gmail access logs)
3. What emails were accessed?
4. How many users affected?
```

**Notification (24-72 hours):**

```
GDPR Notification to Authority:
- Personal data: Email content, sender/recipient info, dates
- Scope: [X] users, [Y] emails accessed
- Impact: High risk - email may contain sensitive data
- Remedy: Tokens revoked, integrations disabled, password reset

User Notification:
- Explain what happened
- Tell them to check Gmail activity log
- Recommend password change
- Offer identity monitoring
```

### 9.2 Scenario: Database Misconfiguration (RLS Bypass)

**Trigger:** RLS policy not enforcing tenant isolation

**Immediate Response (0-1 hour):**

```
1. Identify scope (which tables affected)
2. Check access logs for unauthorized queries
3. Restore correct RLS policy
4. Audit all accessed data
5. Notify Privacy Officer
```

**Investigation (1-24 hours):**

```
1. How long was RLS broken? (when deployed vs. when discovered)
2. Which users' data was exposed to whom?
3. Did anyone query cross-tenant data? (check logs)
4. Impact: High if cross-tenant data accessed, Low if unaccessed
```

**Notification (24-72 hours):**

```
If data was accessed:
- GDPR notification required
- Notify affected users

If data wasn't accessed:
- May be exempt from Article 34 user notification
- Still notify supervisory authority per Article 33
```

### 9.3 Scenario: Credential Theft

**Trigger:** User credentials compromised (brute force or phishing)

**Immediate Response (0-1 hour):**

```
1. Alert user of failed logins
2. Force password reset on next login
3. Enable MFA (if available)
4. Review that account's recent activity
5. Invalidate all active sessions
```

**Investigation (1-24 hours):**

```
1. How was credential obtained (phishing, brute force)?
2. What did attacker access? (login logs, API calls)
3. How long did access last?
4. What data was viewed/downloaded?
```

**Notification (24-72 hours):**

```
Likely No GDPR Notification Required:
- Single user compromised, not a systemic breach
- No indication of unauthorized data access
- Standard account recovery procedures sufficient

User Notification:
- Explain what happened
- Recommend password change
- Enable 2FA
- Monitor account activity
```

---

## 10. Metrics & Monitoring

### 10.1 Monitoring Dashboard

**Real-Time Alerts:**

```
- Failed logins > 5/5min from same IP → Page on-call
- RLS context not set → Alert to security
- Unusual database queries → Flag for review
- TLS certificate errors → Page on-call
- Memory/disk usage > 90% → Alert to ops
```

**Weekly Review:**

```
- Failed authentication attempts (trend analysis)
- Unusual API access patterns
- Database query anomalies
- Security scanner results
- Dependency vulnerabilities
```

### 10.2 MTTR (Mean Time To Respond)

**Target Response Times:**

| Priority      | Detection → Response | Target                 |
| ------------- | -------------------- | ---------------------- |
| P0 (Critical) | < 15 minutes         | On-call engineer paged |
| P1 (High)     | < 1 hour             | Team assembled         |
| P2 (Medium)   | < 4 hours            | Assigned to owner      |
| P3 (Low)      | < 24 hours           | Added to backlog       |

### 10.3 Incident Metrics

**Track:**

-   MTTD (Mean Time To Detect)
-   MTTR (Mean Time To Respond)
-   MTTC (Mean Time To Contain)
-   MTTF (Mean Time To Fix)
-   False positive rate

**Review:** Monthly in security standup

---

## 11. Training & Preparedness

### 11.1 Team Training

**Quarterly Training Topics:**

-   Incident classification
-   Investigation techniques
-   GDPR requirements
-   Notification procedures
-   Forensic evidence preservation

**New Hire Training:**

-   On-boarding includes incident response overview
-   Role-specific training (developers, ops, etc.)

### 11.2 Incident Simulations

**Annual Testing:**

-   Tabletop exercise (walkthrough scenario)
-   Notification template testing
-   Authority contact verification
-   Communication plan rehearsal

---

## 12. Legal & Regulatory References

**GDPR Articles:**

-   Article 32 - Security measures (preventive)
-   Article 33 - Breach notification to authorities (72 hours)
-   Article 34 - Breach notification to individuals (if high risk)
-   Article 35 - DPIA (if high-risk processing)

**Other Regulations:**

-   US State Data Breach Laws (varies by state, typically 30-60 days)
-   CCPA (California, notify "without unreasonable delay")
-   HIPAA (if health data involved, 60 days)
-   SOC 2 (audit requirement for incident response)

---

## 13. Escalation & Approval

### 13.1 Notification Approvals Required

**Before Notifying Supervisory Authority:**

-   [ ] Security Lead approval (technical investigation complete)
-   [ ] Privacy Officer approval (legal/regulatory assessment)
-   [ ] Legal Counsel approval (notification content reviewed)
-   [ ] Executive approval (if incident is significant/newsworthy)

**Before Notifying Users:**

-   [ ] All above + Communications approval

**Before Public Disclosure:**

-   [ ] All above + PR/Marketing approval + Executive Sign-off

### 13.2 Approval Sign-Off Template

```
INCIDENT NOTIFICATION APPROVAL

Incident ID: INC-2026-001
Classification: P0 (Critical)
Date of Incident: January 15, 2026
Date of Discovery: January 16, 2026
Proposed Notification Date: January 17, 2026

APPROVALS:

Security Lead: _________________ Date: _________
Privacy Officer: _______________ Date: _________
Legal Counsel: _________________ Date: _________
Executive Sponsor: _____________ Date: _________

NOTIFICATION RECIPIENTS:
☐ Supervisory Authority (GDPR requirement)
☐ Affected Users (High-risk assessment)
☐ Media / Public (Newsworthy)

NOTIFICATION METHODS:
☐ Email
☐ In-app notification
☐ Phone (for critical)
☐ Press release

Approved for notification on: ________________
```

---

## 14. Post-Incident Review

### 14.1 Postmortem Template

```markdown
# Incident Postmortem

**Incident ID:** INC-2026-001  
**Date:** January 18, 2026  
**Attendees:** [List]

## Timeline

| Time            | Event             |
| --------------- | ----------------- |
| Jan 15, 2:00 PM | Incident occurred |
| Jan 16, 1:00 PM | Discovered        |
| Jan 16, 1:15 PM | Contained         |
| Jan 16, 3:00 PM | Fixed             |
| Jan 17, 9:00 AM | Users notified    |

## Root Cause

RLS policy not enforced due to missing `set_tenant_context()` call in one endpoint.

## Impact

-   1,000 users potentially affected
-   Email content in 500 records exposed
-   No evidence of unauthorized access

## What Went Well

-   Fast detection via monitoring
-   Rapid containment
-   Clear communication

## What We Can Improve

-   Add automated RLS testing
-   Code review checklist for database access
-   Enhanced monitoring for RLS violations

## Action Items

-   [ ] Add RLS enforcement test (Owner: Dev Lead, Due: Jan 25)
-   [ ] Update code review checklist (Owner: Tech Lead, Due: Jan 20)
-   [ ] Implement RLS violation monitoring (Owner: Ops, Due: Jan 31)
```

---

## 15. Contact Information

**Emergency Contacts:**

| Role               | Email               | Phone    |
| ------------------ | ------------------- | -------- |
| Incident Commander | [Email]             | [Number] |
| Security Lead      | security@veriply.ai | [Number] |
| Privacy Officer    | privacy@veriply.ai  | [Number] |
| Legal Counsel      | legal@veriply.ai    | [Number] |

**Supervisory Authority Contacts:**

| Region | Authority    | Contact    | Breach Email            |
| ------ | ------------ | ---------- | ----------------------- |
| EU     | Relevant DPA | [varies]   | [varies]@datenschutz.de |
| UK     | ICO          | ico.org.uk | dpr@ico.org.uk          |
| US     | State AG     | [varies]   | [varies]                |

---

**End of Incident Response Plan**

---

### Related Documents

-   [GDPR Compliance Assessment](GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md)
-   [Privacy Policy](PRIVACY-POLICY.md)
-   [Data Retention Policy](DATA-RETENTION-POLICY.md)
-   [Security Audit Report](SECURITY-AUDIT-REPORT.md)

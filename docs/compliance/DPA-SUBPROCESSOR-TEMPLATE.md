# Data Sub-Processor Agreement (Template)

**For Use With Third-Party Data Processors**

**Effective Date:** January 9, 2026  
**Version:** 1.0

---

## IMPORTANT

This is a **template** for sub-processor agreements. Complete sections marked **[REQUIRED]** and **[OPTIONAL]** before execution.

---

## 1. Parties

**Data Controller:** Veriply Inc.  
Address: [REQUIRED: Company Address]  
Contact: privacy@veriply.ai

**Data Processor:** [REQUIRED: Sub-Processor Name]  
Address: [REQUIRED: Processor Address]  
Contact: [REQUIRED: Processor Contact]

---

## 2. Scope & Purpose

### 2.1 Processing Description

**What data is processed:**

-   [REQUIRED: List specific data categories]
    -   Example: Email content, document metadata, user IDs
    -   [REQUIRED: Add more categories specific to this processor]

**How it's processed:**

-   [REQUIRED: Describe processing activities]
    -   Example: OAuth token storage, encryption/decryption
    -   [REQUIRED: Add more activities specific to this processor]

**Duration:** [REQUIRED: Contract duration or indefinite]

**Subject Matter:** [REQUIRED: Brief description]

-   Example: Email integration service for draft automation

---

### 2.2 Data Subject Categories

-   [REQUIRED: List who the data is about]
    -   Example: Individual users of Veriply platform
    -   Example: End-recipients of customer emails

---

### 2.3 Legal Basis

The processing is based on:

-   ☐ User Consent
-   ☐ Performance of Contract
-   ☐ Legal Obligation
-   ☐ Legitimate Interests of Veriply
-   ☐ [Other - specify: _______________]

---

## 3. Processing Instructions

### 3.1 Processor Obligations

The Processor shall:

1. **Process only on written instructions** from Veriply

    - No processing beyond specified scope without prior written consent
    - Return or delete data upon contract termination

2. **Ensure confidentiality** of staff

    - Staff must be bound by confidentiality obligations
    - Limit staff access to minimum necessary personnel

3. **Implement appropriate security measures** (Article 32)

    - Encryption in transit and at rest
    - Access control (authentication, authorization)
    - Audit logging of all access
    - Regular security testing
    - Incident response procedures

4. **Comply with data subject rights**

    - Assist Veriply in fulfilling data subject requests
    - Provide data in portable format upon request (Article 20)
    - Delete or return data upon request (Article 17)

5. **Sub-contract only with prior written approval**

    - Notify Veriply of any sub-processors
    - Obtain written consent before adding sub-processors
    - Maintain list of current sub-processors

6. **Maintain records of processing**

    - Document all processing activities
    - Maintain audit trails
    - Provide evidence of compliance upon request

7. **Assist with data protection obligations**
    - Cooperate with DPIA assessments
    - Notify Veriply of data breaches (within 24 hours)
    - Cooperate with data subject rights requests
    - Provide information for supervisory authority requests

---

### 3.2 Processor Restrictions

The Processor shall **NOT**:

-   Transfer data outside the [REQUIRED: specify region/country] without prior written consent
-   Use data for own purposes
-   Disclose data to third parties (except sub-processors with approval)
-   Process special category data (unless specifically authorized)
-   Combine data with data from other sources
-   Use data for training ML models (unless explicitly authorized)
-   Retain data beyond contract term (except as required by law)

---

## 4. Security Measures

### 4.1 Technical Measures

Processor shall implement and maintain:

-   ☑ **Encryption in Transit:** TLS 1.2 or higher
-   ☑ **Encryption at Rest:** AES-256 or equivalent
-   ☑ **Access Control:** Authentication (passwords, MFA, certificates)
-   ☑ **Audit Logging:** All data access logged with timestamps
-   ☑ **Network Security:** Firewalls, intrusion detection
-   ☑ **Data Isolation:** Separate databases/storage per tenant
-   ☑ **Regular Backups:** [REQUIRED: Specify frequency and retention]
-   ☑ **Vulnerability Scanning:** Regular security assessments
-   ☑ **Patch Management:** Timely application of security patches
-   ☑ **Incident Response:** Documented procedures for breaches

**[OPTIONAL: Add processor-specific security requirements]**

-   [ ] Multi-region backup/disaster recovery
-   [ ] Compliance certifications (SOC 2, ISO 27001, etc.)
-   [ ] Third-party security audits

---

### 4.2 Organizational Measures

Processor shall implement:

-   **Staff Training:** Regular data protection training
-   **Confidentiality Agreements:** All staff bound by confidentiality
-   **Access Control:** Principle of least privilege
-   **Monitoring:** Regular audits of data handling practices
-   **Incident Investigation:** Procedures for investigating data breaches

---

## 5. Data Subject Rights

### 5.1 Assistance with Data Subject Requests

Processor shall assist Veriply in responding to data subject requests:

| Right                       | Processor Obligation                    | Timeline                          |
| --------------------------- | --------------------------------------- | --------------------------------- |
| **Access (Art. 15)**        | Provide data in requested format        | Within 30 days of Veriply request |
| **Erasure (Art. 17)**       | Delete data upon instruction            | Within [REQUIRED: specify] days   |
| **Rectification (Art. 16)** | Correct inaccurate data                 | Within [REQUIRED: specify] days   |
| **Restriction (Art. 18)**   | Mark data as restricted                 | Within [REQUIRED: specify] days   |
| **Portability (Art. 20)**   | Provide data in machine-readable format | Within [REQUIRED: specify] days   |

---

### 5.2 Breach Notification

Processor shall:

1. **Notify Veriply immediately** upon discovery of data breach

    - Email: incidents@veriply.ai
    - Timeline: Within 24 hours of discovery
    - Include: What data, how many records, when occurred

2. **Cooperate with investigation**

    - Preserve forensic evidence
    - Provide access logs for affected data
    - Assist with root cause analysis

3. **Assist with notification**
    - Provide details for supervisory authority notification
    - Help draft user notifications if required
    - Document all remedial actions

---

## 6. Sub-Processors

### 6.1 Sub-Processor Approval

Processor may engage sub-processors ONLY with:

-   Prior written authorization from Veriply
-   Written notice to Veriply within 30 days
-   Sub-processor contract containing equivalent terms

### 6.2 Sub-Processor List

**Current Sub-Processors:** [REQUIRED: List any sub-processors]

-   Name: ******\_\_\_******
-   Purpose: ******\_\_\_******
-   Location: ******\_\_\_******
-   Contact: ******\_\_\_******

**[REPEAT FOR EACH SUB-PROCESSOR]**

### 6.3 Sub-Processor Changes

Processor shall:

-   Notify Veriply at least 30 days before adding/removing sub-processors
-   Allow Veriply to object to new sub-processors on reasonable grounds
-   Terminate processing if Veriply objects and no resolution found

---

## 7. International Data Transfers

### 7.1 Transfer Location

Data may be transferred to/stored in: [REQUIRED: Specify countries/regions]

-   [Example: US (with Standard Contractual Clauses)]
-   [Example: EU/EEA (adequacy determination)]
-   [Example: [Country] (other legal mechanism)]

### 7.2 Transfer Mechanism

For transfers outside EU/EEA, the following mechanism applies:

☐ **Standard Contractual Clauses (SCCs)**  
☐ **Binding Corporate Rules (BCRs)**  
☐ **Adequacy Decision**  
☐ **User Consent**  
☐ **[Other: ________________]**

**[REQUIRED: Attach signed SCC addendum if applicable]**

---

## 8. Audits & Compliance Verification

### 8.1 Audit Rights

Veriply has the right to:

1. **Request information** about processing and security measures
2. **Conduct audits** at least annually [OPTIONAL: specify frequency]
3. **Require certifications** (SOC 2, ISO 27001, etc.)
4. **Inspect facilities** [OPTIONAL: with reasonable notice]

### 8.2 Audit Timeline

-   **Initial Audit:** Within 90 days of contract execution
-   **Regular Audits:** Annually (or per data protection schedule)
-   **Spot Audits:** Unannounced audits possible upon data breach suspicion

### 8.3 Compliance Evidence

Processor shall provide:

-   ☑ Security certifications (if applicable)
-   ☑ Penetration test results (annually)
-   ☑ Audit reports from independent auditors
-   ☑ Vulnerability scan results
-   ☑ Incident logs (without breaches)

---

## 9. Data Return & Deletion

### 9.1 Upon Contract Termination

Upon expiration or termination, Processor shall:

1. **Return all data** to Veriply within [REQUIRED: 30 days default]
2. **Delete all copies** within [REQUIRED: 60 days default]
3. **Certify deletion** in writing, signed by authorized officer
4. **Destroy any backups** unless required by law

**Exceptions:**

-   Data required to be retained by law [REQUIRED: specify laws]
-   Data required for backup/disaster recovery [REQUIRED: specify retention period]

### 9.2 Verification

Processor shall:

-   Provide written certification of deletion
-   Describe deletion methodology
-   List any data retained (with legal justification)

---

## 10. Liability & Indemnification

### 10.1 Processor Liability

**[OPTIONAL: Include if Veriply chooses to limit processor liability]**

Processor's total aggregate liability for breach of this DPA shall not exceed:

-   Amount paid to Processor in the 12 months preceding the claim
-   [OR] $[REQUIRED: Specify cap]
-   [OR] Unlimited (remove this option if you want a cap)

### 10.2 Indemnification

Processor shall indemnify and hold harmless Veriply from any claims arising from:

-   Processor's breach of this DPA
-   Unauthorized processing by Processor or its sub-processors
-   Processor's violation of applicable data protection laws

---

## 11. Duration & Termination

### 11.1 Contract Duration

**Effective Date:** [REQUIRED: Date]  
**Initial Term:** [REQUIRED: Duration, e.g., 1 year]  
**Renewal:** [REQUIRED: Auto-renewal or upon agreement]

### 11.2 Termination

**Either party may terminate:**

-   For convenience: [REQUIRED: specify notice period, e.g., 30 days]
-   For material breach: Immediately (if not cured within 30 days)
-   For data protection violation: Immediately without cure period

### 11.3 Effect of Termination

Upon termination:

-   All processing ceases
-   Data is returned or deleted per Section 9
-   Processor obligations continue for any retained data
-   Confidentiality obligations survive indefinitely

---

## 12. Liability for Sub-Processors

Processor remains **fully liable** to Veriply for:

-   Performance of sub-processor obligations
-   Sub-processor breaches of this DPA
-   Failures in sub-processor oversight

Veriply may pursue claims against Processor for sub-processor failures.

---

## 13. Cooperation with Authorities

### 13.1 Government Requests

If Processor receives legal demands (court orders, subpoenas, government requests) for personal data:

1. **Notify Veriply immediately** unless legally prohibited

    - Email: legal@veriply.ai
    - Include: What data requested, by whom, legal basis

2. **Challenge requests if possible**

    - Object to overly broad requests
    - Request protective order limiting disclosure
    - Delay disclosure pending Veriply review

3. **Disclose minimum necessary**

    - Only provide data specifically required by legal process
    - Seek confidentiality protection for data disclosed

4. **No waiver of confidentiality**
    - Disclosure under legal process does not waive attorney-client privilege
    - Processor remains bound by confidentiality obligations

---

## 14. Amendments

### 14.1 Changes to DPA

This DPA may be amended:

-   In writing, signed by both parties
-   With 60 days' notice for material changes
-   Immediately for legal compliance changes

### 14.2 Changes to Processor Practices

Processor shall notify Veriply within 30 days of:

-   Changes to sub-processors
-   Changes to processing locations (data transfers)
-   Changes to security measures
-   Changes to data retention policies

---

## 15. Dispute Resolution

### 15.1 Informal Resolution

Disputes shall first be resolved informally through good-faith discussions between:

-   Veriply Privacy Officer (privacy@veriply.ai)
-   Processor Contact ([REQUIRED: contact info])

**Timeline:** 30 days

### 15.2 Escalation

If not resolved informally:

-   Either party may escalate to [REQUIRED: executive contact]
-   Binding arbitration per [REQUIRED: specify jurisdiction/arbitration rules]

---

## 16. Governing Law

This DPA shall be governed by:

-   **Primary:** GDPR (EU Regulation 2016/679)
-   **Secondary:** [REQUIRED: Specify jurisdiction law, e.g., EU/EEA country law]
-   **Disputes:** [REQUIRED: Specify arbitration location/rules]

**For non-EU parties:** Both parties agree to comply with GDPR regardless of where processing occurs.

---

## 17. Language

This DPA is executed in English. Any translations are for convenience only. In case of conflict, the English version prevails.

---

## 18. Entire Agreement

This DPA, together with the [REQUIRED: Service Agreement reference], constitutes the entire agreement regarding data processing between the parties.

**[OPTIONAL: List any other related agreements]**

---

## 19. Severability

If any provision of this DPA is found invalid or unenforceable, the remaining provisions remain in effect.

---

## 20. Signatures

**For Veriply (Data Controller):**

Signature: **********\_\_\_\_**********  
Printed Name: ********\_\_\_\_********  
Title: ************\_\_\_************  
Date: ************\_\_\_\_************  
Email: ************\_\_\_************

**For Processor:**

Signature: **********\_\_\_\_**********  
Printed Name: ********\_\_\_\_********  
Title: ************\_\_\_************  
Date: ************\_\_\_\_************  
Email: ************\_\_\_************

---

## Appendix A: Standard Contractual Clauses (if applicable)

[REQUIRED if data transfers outside EU/EEA: Include signed SCC Module One (Controller-to-Processor) or Module Two (Processor-to-Sub-processor)]

---

## Appendix B: Data Specifications

| Specification          | Value                         |
| ---------------------- | ----------------------------- |
| **Data Categories**    | [REQUIRED: List]              |
| **Subject Categories** | [REQUIRED: List]              |
| **Processing Purpose** | [REQUIRED: Describe]          |
| **Retention Period**   | [REQUIRED: Specify]           |
| **Storage Location**   | [REQUIRED: Countries/regions] |
| **Sub-Processors**     | [REQUIRED: List, if any]      |

---

## Appendix C: Security Measures

[REQUIRED: Attach detailed security documentation from Processor, including:

-   System architecture diagram
-   Encryption methodology
-   Access control procedures
-   Backup/recovery procedures
-   Incident response plan
-   Penetration test results (recent)
-   Compliance certifications]

---

## Appendix D: Sub-Processor Monitoring

**Sub-Processor Changes:**

-   Processor shall maintain current list at: [REQUIRED: Specify URL]
-   Veriply shall receive notice within 30 days of changes
-   [OPTIONAL: Processor shall provide email notification of changes]

---

**END OF DATA SUB-PROCESSOR AGREEMENT TEMPLATE**

---

### How to Use This Template

1. **Complete all [REQUIRED] sections**
2. **Customize for your processor:**
    - Specify data categories
    - Detail processing activities
    - Add security requirements
    - Set retention periods
3. **Add processor-specific schedules** (Appendix C, D)
4. **Have legal counsel review** before execution
5. **Obtain signatures** from authorized representatives
6. **File in compliance folder** for audit trail
7. **Update annually** or when practices change

### Version Control

| Version  | Date        | Changes          |
| -------- | ----------- | ---------------- |
| 1.0      | Jan 9, 2026 | Initial template |
| [FUTURE] | [DATE]      | [CHANGES]        |

---

### Related Documents

-   [Privacy Policy](PRIVACY-POLICY.md)
-   [Processing Register](PROCESSING-REGISTER.md)
-   [Data Retention Policy](DATA-RETENTION-POLICY.md)
-   [GDPR Compliance Assessment](GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md)

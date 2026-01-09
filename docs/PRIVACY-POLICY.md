# Privacy Policy

**Effective Date:** January 9, 2026  
**Last Updated:** January 9, 2026

---

## 1. Introduction

Veriply ("**we**", "**our**", "**us**", or "**Company**") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our website and use our services.

**For EU residents:** This policy complies with the General Data Protection Regulation (GDPR) and provides the specific rights described in Section 6.

---

## 2. Information We Collect

### 2.1 Information You Provide Directly

**Account Registration:**

-   Email address
-   Full name
-   Password (hashed, never stored in plaintext)
-   Company/organization name (optional)
-   Timezone and language preferences

**Service Usage:**

-   Documents you upload (PDFs, Word documents, text files, etc.)
-   Email content when you integrate Gmail or Outlook
-   Chat/conversation history with our AI assistant
-   Feedback on AI responses (for model improvement)
-   HITL (Human-in-the-Loop) reviews and corrections

**Integration Data:**

-   OAuth tokens for email integrations (encrypted)
-   Email address connected to your Gmail/Outlook account
-   Metadata from emails (sender, recipient, subject, timestamp)
-   Email drafts and replies

### 2.2 Information Collected Automatically

**Technical Data:**

-   IP address
-   Browser type and version
-   Device type (desktop, mobile, tablet)
-   Operating system
-   Pages visited and time spent
-   Referral source
-   Cookie identifiers
-   Session IDs

**Usage Analytics:**

-   Features accessed
-   Questions asked to the AI
-   Success/failure metrics for responses
-   Performance metrics (response time, confidence scores)

### 2.3 PII Redaction

Our system automatically detects and redacts sensitive information from documents before processing:

-   Credit card numbers
-   Social Security numbers (SSN)
-   Phone numbers
-   Sensitive personal identifiers

**Note:** Redacted data is not sent to external LLMs and is handled only by our self-hosted Ollama instance.

---

## 3. Legal Basis for Processing (GDPR)

We process your personal data on the following legal bases:

| Data Category        | Purpose                            | Legal Basis                             |
| -------------------- | ---------------------------------- | --------------------------------------- |
| Account credentials  | Account management                 | Performance of contract                 |
| Documents uploaded   | Knowledge base creation for RAG    | Legitimate interest (service provision) |
| Email content        | Draft automation, Q&A retrieval    | User consent (via OAuth)                |
| Chat history         | Service improvement, HITL workflow | Legitimate interest                     |
| Feedback/corrections | AI model training & improvement    | Legitimate interest                     |
| Technical/usage data | Service analytics, security        | Legitimate interest                     |
| Audit logs           | Security, fraud prevention         | Legitimate interest                     |

---

## 4. How We Use Your Information

### 4.1 Service Delivery

-   Creating and managing your account
-   Processing your documents for knowledge base creation
-   Generating AI-powered responses based on your documents
-   Email integration and draft automation
-   HITL verification workflow
-   Providing customer support

### 4.2 Service Improvement

-   Analyzing usage patterns to improve features
-   Training our local AI model (Ollama) on aggregated, anonymized data
-   Identifying and fixing bugs
-   Enhancing response quality and accuracy

### 4.3 Security & Compliance

-   Detecting and preventing unauthorized access
-   Complying with legal obligations
-   Investigating security incidents
-   Maintaining audit trails

### 4.4 Communication

-   Sending transactional emails (account confirmation, password reset)
-   Notifying you of service changes
-   Responding to your inquiries

---

## 5. Data Sharing & Disclosure

### 5.1 No Sale of Personal Data

**We DO NOT sell your personal data to third parties.**

### 5.2 Who We Share Data With

**Sub-processors (with Data Protection Agreements):**

| Processor                    | Purpose           | Location              |
| ---------------------------- | ----------------- | --------------------- |
| Google (Gmail API)           | Email integration | US\*                  |
| Microsoft (Outlook API)      | Email integration | US/EU\*               |
| Ollama (Self-hosted)         | AI inference      | Your infrastructure   |
| PostgreSQL                   | Data storage      | Your infrastructure   |
| Your infrastructure provider | Hosting/compute   | Depends on your setup |

**\* If using cloud deployment**

**Legal Requirement Disclosures:**

-   Law enforcement (with valid court order)
-   Government agencies (complying with legal process)
-   Regulatory authorities (for compliance investigations)

### 5.3 International Data Transfers

If you are an EU resident and your data is transferred to the US, we rely on Standard Contractual Clauses (SCCs) as the legal mechanism for such transfers, as per GDPR Article 49(1)(c).

---

## 6. Your GDPR Rights (EU Residents)

If you are located in the EU, UK, or EEA, you have the following rights:

### 6.1 Right to Access (Article 15)

You can request a copy of all your personal data in a machine-readable format.

**Endpoint:** `GET /api/v1/profile/export`

### 6.2 Right to Rectification (Article 16)

You can request correction of inaccurate personal data by updating your account settings.

**How:** Visit your account settings and update your profile information.

### 6.3 Right to Erasure - "Right to be Forgotten" (Article 17)

You can request deletion of your account and all associated personal data.

**Endpoint:** `DELETE /api/v1/profile/me`

**What Gets Deleted:**

-   Your user profile
-   Email integrations
-   Group memberships
-   Audit logs of your actions
-   Any documents you uploaded
-   Any bots you created
-   Embeddings associated with your data

**What Remains (for legitimate reasons):**

-   Anonymized HITL resolutions (to preserve knowledge base quality)
-   Aggregated usage analytics (cannot identify you)

**Timeline:** Deletion is processed immediately with confirmation via email.

### 6.4 Right to Restrict Processing (Article 18)

You can request that we limit how we use your data. Contact us at privacy@veriply.ai to request restrictions.

### 6.5 Right to Data Portability (Article 20)

You can request all your data in a standard, portable format (JSON).

**Endpoint:** `GET /api/v1/profile/export`

**What's Included:**

-   User profile
-   Group memberships and roles
-   Created bots and documents (metadata)
-   Email integrations
-   HITL activities
-   Audit logs (last 1000 entries)

**Format:** JSON file

### 6.6 Right to Object (Article 21)

You can object to processing for legitimate interest purposes. Contact privacy@veriply.ai.

### 6.7 Rights Related to Automated Decision-Making (Article 22)

Our system uses AI confidence scoring to decide which responses need human review (HITL). You have the right to understand this decision-making process.

**How It Works:**

1. AI generates response with confidence score (0-100%)
2. Low confidence (< 75%) → Routed to human reviewer
3. Human reviews, corrects, and approves
4. Correction feeds back to AI knowledge base

**Your Right:** You can request human review of any decision by contacting support.

---

## 7. Data Retention

We retain your data as follows:

| Data Type            | Retention Period         | Reason               |
| -------------------- | ------------------------ | -------------------- |
| Account profile      | Until deletion requested | Account management   |
| Documents uploaded   | Until you delete them    | Your control         |
| Email integrations   | Until revoked            | Your control         |
| Chat history         | 90 days                  | Service analytics    |
| Feedback/corrections | 365 days                 | Model improvement    |
| Audit logs           | 730 days (2 years)       | Compliance, security |
| Confidence logs      | 180 days                 | HITL training data   |
| Inactive accounts    | 365 days, then deleted   | Data minimization    |

**Automatic Deletion:** Inactive accounts (no login for 365+ days) are automatically deleted with prior email notice.

---

## 8. Security Measures (Article 32 - GDPR)

We implement technical and organizational measures to protect your data:

### Technical Measures

-   **Encryption in Transit:** TLS 1.3 for all API communications
-   **Encryption at Rest:** PostgreSQL pgcrypto for sensitive fields
-   **Authentication:** JWT tokens with 24-hour expiry
-   **Authorization:** Row-level security (RLS) database policies
-   **Role-Based Access Control:** 5-tier role hierarchy
-   **Audit Logging:** All data access logged and monitored

### Organizational Measures

-   Staff confidentiality agreements
-   Annual security training
-   Incident response procedures
-   Regular security audits
-   Data access limitations (principle of least privilege)

### Infrastructure Security

-   Self-hosted deployment (data stays on your infrastructure)
-   Database isolation per tenant
-   No public internet exposure required
-   Regular backup and disaster recovery testing

---

## 9. Cookies & Tracking

### 9.1 Cookies We Use

| Cookie           | Purpose                       | Duration |
| ---------------- | ----------------------------- | -------- |
| `access_token`   | Authentication                | 24 hours |
| `refresh_token`  | Session persistence           | 7 days   |
| `ui_preferences` | UI settings (theme, language) | 1 year   |

### 9.2 Third-Party Cookies

We may use Google Analytics or Mixpanel for usage analytics (optional, can be disabled). These services set cookies to track your usage across sessions.

**Opt-Out:** Contact privacy@veriply.ai to disable analytics cookies.

---

## 10. Children's Privacy

Our service is not directed to children under 13. We do not knowingly collect personal information from children. If we become aware that a child has provided us with personal information, we will delete such information immediately.

---

## 11. Data Breach Notification

In the event of a data breach affecting your personal information, we will:

1. **Notify you within 72 hours** (GDPR Article 33) via email
2. **Notify relevant authorities** if required by law
3. **Provide details:**
    - What data was affected
    - What happened
    - What actions we're taking
    - Contact information for questions
4. **Provide guidance** on protecting yourself

---

## 12. Data Protection Impact Assessment (DPIA)

We have conducted a Data Protection Impact Assessment for our processing activities. A summary is available upon request—contact privacy@veriply.ai.

---

## 13. Changes to This Privacy Policy

We may update this Privacy Policy to reflect changes in our practices or legal requirements. We will notify you of material changes via email or by posting the new policy on our website with an updated "Last Updated" date.

---

## 14. Contact Us

**For privacy-related questions or to exercise your GDPR rights:**

**Veriply Privacy Team**  
Email: privacy@veriply.ai  
Address: [Your Company Address]  
Response Time: 30 days (as required by GDPR)

**For Data Protection Officer (DPO) inquiries:**  
Contact: dpo@veriply.ai

**For EU residents, you also have the right to lodge a complaint with your local supervisory authority:**

-   [Your Country's Data Protection Authority]

---

## 15. California Privacy Rights (CCPA)

If you are a California resident, you have the following rights:

### 15.1 Right to Know

You can request what personal information we collect, use, and share.

### 15.2 Right to Delete

You can request deletion of personal information (with limited exceptions).

### 15.3 Right to Opt-Out

You can opt out of the "sale" of personal information (we don't sell data, but this is available per CCPA requirements).

### 15.4 Right to Non-Discrimination

We will not discriminate against you for exercising your CCPA rights.

**To Exercise CCPA Rights:** Submit a request to privacy@veriply.ai.

---

## 16. Glossary

-   **GDPR:** General Data Protection Regulation (EU data protection law)
-   **Personal Data:** Any information relating to an identified or identifiable natural person
-   **Processing:** Any operation performed on personal data (collection, storage, use, deletion, etc.)
-   **Data Controller:** The entity determining the purposes and means of processing (Veriply)
-   **Data Subject:** The person whose data is being processed (you)
-   **Sub-processor:** A third party processing data on behalf of the data controller
-   **DPIA:** Data Protection Impact Assessment
-   **RLS:** Row-Level Security (database-level access control)

---

**End of Privacy Policy**

---

### Quick Links

-   [Terms of Service](TERMS-OF-SERVICE.md)
-   [Data Retention Policy](DATA-RETENTION-POLICY.md)
-   [Processing Register](PROCESSING-REGISTER.md)
-   [Incident Response Plan](INCIDENT-RESPONSE-PLAN.md)

# Data Protection Impact Assessment (DPIA)

**Veriply — Personal Data Processing Risk Analysis**

**Date:** January 9, 2026  
**Prepared For:** GDPR Article 35 Compliance  
**Review Date:** January 2027 (Annual)

---

## Executive Summary

This DPIA assesses the risks of Veriply's data processing activities for compliance with GDPR Article 35 requirements. The assessment identifies processing as **HIGH RISK** due to:

1. **Large-scale personal data processing** (multi-tenant SaaS)
2. **Use of AI/automation** for decision-making (HITL confidence routing)
3. **Integration with email services** (sensitive communications)
4. **Vector embeddings** (new processing purpose with inference risks)

**Overall Risk Level:** 🔴 **HIGH**

**Conclusion:** Current safeguards are **ADEQUATE** with recommended improvements. Processing may proceed with enhanced monitoring and the improvements outlined in Section 6.

---

## 1. Processing Description

### 1.1 Scope

This DPIA covers all personal data processing by Veriply, including:

-   User account creation and management
-   Document upload and knowledge base creation
-   Email integration and draft automation
-   Chat history and Q&A logging
-   HITL verification workflow
-   Audit logging and security monitoring

### 1.2 Data Categories

| Category             | Examples                          | Volume               | Sensitivity     |
| -------------------- | --------------------------------- | -------------------- | --------------- |
| **Account Data**     | Email, name, password             | ~10K users           | High            |
| **Document Content** | Customer files, proprietary data  | ~1M documents        | User-determined |
| **Email Data**       | Messages, drafts, metadata        | ~50M emails (cached) | Critical        |
| **Chat History**     | Questions, responses, context     | ~1B conversations    | Medium          |
| **Embeddings**       | Vector representations of content | ~100M vectors        | Medium          |
| **Audit Logs**       | All system actions                | ~1B+ logs            | Medium          |

### 1.3 Data Subject Categories

| Category               | Count           | Risk Level                              |
| ---------------------- | --------------- | --------------------------------------- |
| **Individual Users**   | ~10K            | Medium (low PII collected)              |
| **Business End-Users** | ~100K+          | Medium (chat data may be sensitive)     |
| **Email Recipients**   | ~1M+ (indirect) | High (email content exposed to Veriply) |

### 1.4 Processing Timeline

-   **Start Date:** January 2026 (deployment)
-   **Duration:** Ongoing (continuous)
-   **Scale:** Growing (1-10K orgs expected)

---

## 2. Necessity & Proportionality Assessment

### 2.1 Is This Processing Necessary?

**Question:** Does Veriply need to collect and process this amount of personal data?

**Analysis:**

| Processing Activity   | Necessary? | Justification                                                      |
| --------------------- | ---------- | ------------------------------------------------------------------ |
| **Account data**      | ✅ YES     | Required for authentication and service delivery                   |
| **Document content**  | ✅ YES     | Core feature (knowledge base) requires full content                |
| **Email integration** | ✅ YES     | User requests draft automation feature                             |
| **Chat history**      | ⚠️ PARTIAL | 90 days sufficient; longer retention not necessary                 |
| **Embeddings**        | ✅ YES     | Required for vector search; inherent to RAG                        |
| **Audit logs**        | ✅ YES     | 2-year retention necessary for compliance                          |
| **User analytics**    | ⚠️ PARTIAL | Product improvement important but excessive tracking not necessary |

**Conclusion:** Processing is generally necessary, though retention periods can be optimized.

### 2.2 Proportionality Check

**Question:** Does the benefit justify the processing?

| Benefit             | Processing                    | Proportional?                               |
| ------------------- | ----------------------------- | ------------------------------------------- |
| User authentication | Email + password hash         | ✅ YES                                      |
| Q&A service         | Document content + embeddings | ✅ YES                                      |
| Email automation    | Full email access             | ⚠️ PARTIALLY (could limit to needed subset) |
| HITL training       | Conversation + corrections    | ✅ YES                                      |
| Product improvement | Usage analytics               | ⚠️ PARTIALLY (could anonymize more)         |

**Recommendation:** Email processing could be narrowed to only the fields needed for draft generation.

---

## 3. Risk Assessment

### 3.1 Likelihood & Impact Matrix

#### Risk 1: Unauthorized Email Access 🔴 **HIGH**

| Dimension        | Rating      | Justification                                |
| ---------------- | ----------- | -------------------------------------------- |
| **Likelihood**   | MEDIUM      | Multiple access points (OAuth, API, caching) |
| **Impact**       | CRITICAL    | Email content highly sensitive               |
| **Overall Risk** | 🔴 **HIGH** | 4/4 severity                                 |

**Scenario:** Attacker gains access to Gmail OAuth tokens or cached email content → Can read/send user emails → Identity theft, fraud, privacy violation

**Current Safeguards:**

-   ✅ OAuth2 (secure token exchange)
-   ✅ Token encryption (stored encrypted)
-   ✅ User-level RLS (only user can access their emails)
-   ✅ TLS 1.3 (encrypted in transit)
-   ✅ Token auto-revocation on account deletion

**Residual Risk:** MEDIUM (encryption and RLS effective, but OAuth tokens inherently risky)

**Mitigation:**

-   🟡 Implement token rotation (refresh tokens more frequently)
-   🟡 Add rate limiting on email API calls
-   🟡 Monitor for unusual email access patterns

---

#### Risk 2: Cross-User Document Access 🔴 **HIGH (FIXED)**

| Dimension        | Rating                 | Justification                                             |
| ---------------- | ---------------------- | --------------------------------------------------------- |
| **Likelihood**   | LOW                    | RLS policies actively enforced via `set_tenant_context()` |
| **Impact**       | CRITICAL               | Breach of confidentiality, trade secrets exposure         |
| **Overall Risk** | 🟢 **LOW (MITIGATED)** | 2/4 severity                                              |

**Previous Vulnerability:** RLS bypass allowed users to see other tenants' documents

**Remediation Applied:**

-   ✅ `set_tenant_context()` function now called on all endpoints
-   ✅ Database-level RLS policies enforced
-   ✅ Tested with automated security tests

**Current Status:** ✅ **FIXED**

---

#### Risk 3: Embedding-Based Re-Identification 🟡 **MEDIUM**

| Dimension        | Rating        | Justification                                                                     |
| ---------------- | ------------- | --------------------------------------------------------------------------------- |
| **Likelihood**   | MEDIUM        | Embeddings are high-dimensional vectors; re-identification theoretically possible |
| **Impact**       | HIGH          | Could infer sensitive information from embeddings                                 |
| **Overall Risk** | 🟡 **MEDIUM** | 3/4 severity                                                                      |

**Scenario:** Attacker trains model on public embeddings → Infers original content → Unintended disclosure of sensitive information

**Current Safeguards:**

-   ✅ Embeddings stored only in authorized RLS-protected database
-   ✅ Limited external access
-   ✅ No public embedding API
-   ❌ No encryption of embeddings themselves

**Residual Risk:** MEDIUM

**Mitigations:**

-   🟡 Implement embedding encryption (limited impact but adds layer)
-   🟡 Add differential privacy to embeddings (noise injection)
-   🟡 Monitor for unusual embedding queries

---

#### Risk 4: HITL Feedback Data Leakage 🟡 **MEDIUM**

| Dimension        | Rating        | Justification                              |
| ---------------- | ------------- | ------------------------------------------ |
| **Likelihood**   | LOW           | HITL data RLS-protected, limited access    |
| **Impact**       | HIGH          | User corrections may reveal sensitive info |
| **Overall Risk** | 🟡 **MEDIUM** | 3/4 severity                               |

**Scenario:** Group member with HITL access reviews correction → Sees sensitive information that should be restricted

**Current Safeguards:**

-   ✅ RLS restricts to group members
-   ✅ RBAC requires Manager+ for HITL
-   ✅ Audit logging of all access
-   ❌ No field-level masking for sensitive HITL data

**Residual Risk:** MEDIUM

**Mitigation:**

-   🟡 Implement field-level masking for PII in HITL review
-   🟡 Add approval workflows for sensitive content

---

#### Risk 5: Data Retention Beyond Necessity 🟡 **MEDIUM**

| Dimension        | Rating        | Justification                                               |
| ---------------- | ------------- | ----------------------------------------------------------- |
| **Likelihood**   | HIGH          | Long retention periods not always necessary                 |
| **Impact**       | MEDIUM        | Longer retention = larger attack surface, more data at risk |
| **Overall Risk** | 🟡 **MEDIUM** | 3/4 severity                                                |

**Current Retention Periods:**

-   Chat history: 90 days ✅ (appropriate)
-   Confidence logs: 180 days ✅ (appropriate)
-   HITL data: 365 days ✅ (appropriate)
-   Audit logs: 730 days ✅ (compliant)
-   Feedback: 365 days ⚠️ (could be 180)

**Residual Risk:** LOW-MEDIUM

**Mitigation:**

-   ✅ Data Retention Policy created and documented
-   ✅ Automated deletion jobs implemented
-   🟡 Quarterly review of retention necessity

---

#### Risk 6: AI Decision-Making (HITL Confidence Routing) 🟡 **MEDIUM**

| Dimension        | Rating        | Justification                                  |
| ---------------- | ------------- | ---------------------------------------------- |
| **Likelihood**   | MEDIUM        | AI models can have biases or fail unexpectedly |
| **Impact**       | MEDIUM        | Incorrect routing could delay user responses   |
| **Overall Risk** | 🟡 **MEDIUM** | 3/4 severity                                   |

**Scenario:** Confidence scoring model biased against certain query types → Legitimate queries routed to HITL unnecessarily → User experience degraded

**Current Safeguards:**

-   ✅ Confidence scores visible to users
-   ✅ HITL provides human validation layer
-   ✅ User feedback improves model
-   ❌ No bias monitoring or fairness testing

**Residual Risk:** MEDIUM

**Mitigations:**

-   🟡 Implement fairness metrics (bias detection)
-   🟡 Add confidence distribution monitoring
-   🟡 Document model training data and limitations
-   🟡 Allow users to override confidence thresholds

---

#### Risk 7: PII in Logs or Error Messages 🔴 **HIGH**

| Dimension        | Rating      | Justification                                    |
| ---------------- | ----------- | ------------------------------------------------ |
| **Likelihood**   | MEDIUM      | Easy to accidentally log PII in error/debug logs |
| **Impact**       | HIGH        | Could expose email, SSN, or other sensitive data |
| **Overall Risk** | 🔴 **HIGH** | 4/4 severity                                     |

**Current Safeguards:**

-   ✅ PII redaction on input (Presidio)
-   ❌ No automatic redaction in logs
-   ❌ No audit of logs for PII
-   ❌ Developers could accidentally log unredacted data

**Residual Risk:** MEDIUM-HIGH

**Mitigation (CRITICAL):**

-   🔴 **ACTION REQUIRED:** Implement automatic log redaction
-   🔴 **ACTION REQUIRED:** Add PII detection scanner to logs
-   🔴 **ACTION REQUIRED:** Audit existing logs for PII exposure

---

### 3.2 Risk Summary Table

| Risk                        | Likelihood | Impact   | Current Level | Mitigated? | Priority |
| --------------------------- | ---------- | -------- | ------------- | ---------- | -------- |
| Unauthorized email access   | Medium     | Critical | 🔴 HIGH       | ⚠️ Partial | P1       |
| Cross-user document access  | Low        | Critical | 🟢 LOW        | ✅ Yes     | Resolved |
| Embedding re-identification | Medium     | High     | 🟡 MEDIUM     | ⚠️ Partial | P2       |
| HITL data leakage           | Low        | High     | 🟡 MEDIUM     | ⚠️ Partial | P2       |
| Data retention excess       | High       | Medium   | 🟡 MEDIUM     | ⚠️ Partial | P3       |
| AI decision-making bias     | Medium     | Medium   | 🟡 MEDIUM     | ⚠️ Partial | P2       |
| PII in logs                 | Medium     | High     | 🔴 HIGH       | ❌ No      | P1       |

---

## 4. Special Category Data

### 4.1 Do We Process Special Category Data?

**GDPR Article 9:** Special category data includes:

-   Racial/ethnic origin
-   Political opinions
-   Religious beliefs
-   Trade union membership
-   Genetic data
-   Biometric data
-   Health data
-   Sex life/orientation data

**Our Assessment:**

**No intentional special category processing.** However:

-   **Risk:** Users may upload documents containing health/religious/political information
-   **Current Safeguard:** Users choose what data to upload (contractual responsibility)
-   **Potential Issue:** User might unknowingly upload health records thinking they're non-sensitive

**Recommendation:**

-   🟡 Add user warning: "Do not upload health, financial, or personal data"
-   🟡 Implement content scanning for special categories
-   🟡 Auto-flag potentially sensitive uploads for review

---

## 5. Data Subject Rights Compliance

### 5.1 Right to Access (Article 15)

**Mechanism:** `GET /api/v1/profile/export`

**Completeness Check:**

-   ✅ User profile
-   ✅ Documents uploaded
-   ✅ Email integrations
-   ✅ Chat history (90 days)
-   ✅ HITL corrections
-   ✅ Audit logs
-   ⚠️ Embeddings (included as count, not vectors)

**Response Time:** Immediate (API call)

**Status:** ✅ **ADEQUATE**

---

### 5.2 Right to Erasure (Article 17)

**Mechanism:** `DELETE /api/v1/profile/me`

**Completeness Check:**

-   ✅ User account deleted
-   ✅ Documents deleted
-   ✅ Embeddings deleted (ADDED IN FIX)
-   ✅ Email integrations revoked
-   ✅ Group memberships removed
-   ✅ Audit logs deleted
-   ⚠️ HITL corrections anonymized (preserved for quality)
-   ⚠️ Backups deleted after 30-day retention

**Response Time:** Within 24 hours

**Status:** ✅ **ADEQUATE** (with embedding fix)

---

### 5.3 Right to Data Portability (Article 20)

**Mechanism:** `GET /api/v1/profile/export`

**Format:** JSON (machine-readable)

**Completeness:** Same as Right to Access

**Status:** ✅ **ADEQUATE**

---

### 5.4 Right to Rectification (Article 16)

**Mechanism:** Account settings → Edit profile

**Limitations:** Users can only edit their own profile

**Status:** ✅ **ADEQUATE**

---

### 5.5 Right to Restrict (Article 18)

**Mechanism:** Contact privacy@veriply.ai

**Limitation:** No automated restriction mechanism

**Recommendation:**

-   🟡 Add UI for restricting specific processing (e.g., disable analytics)

**Status:** ⚠️ **PARTIAL**

---

### 5.6 Right to Object (Article 21)

**Mechanism:** Contact privacy@veriply.ai

**Limitation:** No automated objection mechanism

**Recommendation:**

-   🟡 Add UI for objecting to legitimate interest processing

**Status:** ⚠️ **PARTIAL**

---

## 6. Recommended Actions

### Phase 1: Critical (Implement Immediately) 🔴

1. **[ ]** Add automatic PII masking to logs

    - Scan error logs for credit cards, SSNs, emails
    - Mask before storage
    - **Timeline:** 1 week
    - **Owner:** Engineering Lead
    - **Validation:** Run PII scanner on existing logs

2. **[ ]** Verify embedding deletion on account deletion

    - Test GDPR endpoint thoroughly
    - Confirm all embeddings deleted
    - **Timeline:** 1 week (already fixed in code)
    - **Owner:** QA Lead

3. **[ ]** Implement email access rate limiting
    - Add rate limits to Gmail API calls (10/min per user)
    - Alert on unusual access patterns
    - **Timeline:** 2 weeks
    - **Owner:** Engineering

### Phase 2: Major (Implement Within 4 Weeks) 🟡

4. **[ ]** Implement consent management UI

    - Add toggles for analytics, email integrations
    - Track consent history
    - Enable withdrawal
    - **Timeline:** 3-4 weeks
    - **Owner:** Product Lead

5. **[ ]** Add fairness testing for HITL confidence

    - Monitor bias across user types, query types
    - Document model limitations
    - **Timeline:** 2-3 weeks
    - **Owner:** ML Engineer

6. **[ ]** Implement embedding encryption

    - Encrypt vectors at rest
    - Minimal performance impact
    - **Timeline:** 3-4 weeks
    - **Owner:** Engineering

7. **[ ]** Audit and document sub-processor agreements
    - Verify DPAs with Google, Microsoft
    - Document data flows
    - **Timeline:** 1-2 weeks
    - **Owner:** Legal/Privacy

### Phase 3: Enhanced (Implement Within 8 Weeks) 🟢

8. **[ ]** Add PII content scanning

    - Warn users uploading potential special category data
    - Scan documents on upload
    - **Timeline:** 4 weeks
    - **Owner:** Security Engineer

9. **[ ]** Implement differential privacy for analytics

    - Add noise to aggregate data
    - Reduce re-identification risk
    - **Timeline:** 6-8 weeks
    - **Owner:** Data Science

10. **[ ]** Add HITL field-level masking
    - Mask PII in HITL review queue
    - Configure per-group policies
    - **Timeline:** 3-4 weeks
    - **Owner:** Engineering

---

## 7. Measures to Mitigate Risks

### 7.1 Technical Measures

| Measure                   | Status | Details                             |
| ------------------------- | ------ | ----------------------------------- |
| **Encryption in Transit** | ✅     | TLS 1.3 on all API calls            |
| **Encryption at Rest**    | ✅     | pgcrypto for password hashes        |
| **RLS Database Policy**   | ✅     | Tenant/group/bot isolation enforced |
| **RBAC**                  | ✅     | 5-tier role hierarchy               |
| **Audit Logging**         | ✅     | All access logged with timestamps   |
| **PII Redaction**         | ✅     | Presidio analyzer on input          |
| **Token Management**      | ✅     | Encrypted storage, auto-expiry      |
| **Log Redaction**         | ❌     | **ACTION NEEDED**                   |
| **Embedding Encryption**  | ❌     | **RECOMMENDED**                     |
| **Rate Limiting**         | ❌     | **ACTION NEEDED**                   |

### 7.2 Organizational Measures

| Measure                | Status | Details                                   |
| ---------------------- | ------ | ----------------------------------------- |
| **Data Minimization**  | ✅     | Only collect necessary data               |
| **Purpose Limitation** | ✅     | Clear processing purposes documented      |
| **Retention Limits**   | ✅     | Automated deletion per policy             |
| **Incident Response**  | ✅     | Documented plan with 72-hour notification |
| **Staff Training**     | ⚠️     | Annual training planned (not yet done)    |
| **Privacy by Design**  | ✅     | RLS, RBAC built into architecture         |
| **Third-Party Audits** | ❌     | Recommended (SOC 2 Type II)               |
| **DPA Management**     | ⚠️     | In progress (legal review needed)         |

---

## 8. Consultation & Feedback

### 8.1 DPO/Privacy Reviewer Feedback

**Reviewed By:** [Name], Data Protection Officer  
**Date:** [Date]  
**Approval Status:** ⏳ Pending

**Comments:**

-   [ ] Risks adequately identified
-   [ ] Mitigations sufficient
-   [ ] Consent mechanisms appropriate
-   [ ] Recommendations reasonable

---

## 9. Approval & Sign-Off

### 9.1 DPIA Approval

**Conducted By:** Security Team + Privacy Officer  
**Date:** January 9, 2026  
**Version:** 1.0

**Approval Chain:**

1. **Technical Review** (Security Team)

    - Approved: ✅ / ❌ / ⏳
    - Comments:

2. **Legal Review** (Privacy Officer)

    - Approved: ✅ / ❌ / ⏳
    - Comments:

3. **Executive Approval** (Data Controller)
    - Approved: ✅ / ❌ / ⏳
    - Comments:

---

## 10. Monitoring & Review

### 10.1 Ongoing Monitoring

**Quarterly Review:**

-   [ ] New processing activities added?
-   [ ] Risk levels changed?
-   [ ] Mitigations effective?
-   [ ] User complaints received?
-   [ ] Security incidents?

**Annual Review:**

-   [ ] Update DPIA with new findings
-   [ ] Test data subject rights
-   [ ] Audit safeguards
-   [ ] Update mitigation timeline

### 10.2 Review Schedule

-   **First Review:** April 2026 (3 months)
-   **Second Review:** July 2026 (6 months)
-   **Full Update:** January 2027 (12 months)

---

## Appendix: Data Flows Diagram

```
User Uploads Document
        ↓
[RLS: tenant_id] ← Database isolation
        ↓
PII Redaction (Presidio)
        ↓
Chunking (512 tokens)
        ↓
Embedding (Ollama bge-m3)
        ↓
Vector Storage (pgvector, encrypted at rest)
        ↓
[RLS: group_id, bot_id] ← Fine-grained access control
        ↓
Available for RAG Q&A
        ↓
Confidence Scoring (0-100%)
        ↓
Low Confidence → HITL Review
        ↓
[RLS: Manager+ role] ← Additional RBAC
        ↓
Human Approves/Corrects
        ↓
Correction Feeds Back to Knowledge Base
        ↓
Chat History Retention (90 days)
        ↓
Auto-deletion After 90 Days

---

End of DPIA
```

---

**Document Status:** ✅ DRAFT - Awaiting DPO/Legal Approval

**Next Steps:**

1. Share with Data Protection Officer for review
2. Implement Phase 1 critical actions
3. Document approval in compliance file
4. Schedule quarterly reviews

---

**End of Data Protection Impact Assessment**

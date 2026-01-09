# Terms of Service

**Effective Date:** January 9, 2026  
**Last Updated:** January 9, 2026

---

## 1. Agreement to Terms

By accessing and using Veriply (the "Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.

---

## 2. Use License

Permission is granted to temporarily download one copy of the materials (information or software) on Veriply for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:

-   Modifying or copying the materials
-   Using the materials for any commercial purpose or for any public display
-   Attempting to decompile or reverse engineer any software contained on Veriply
-   Removing any copyright or other proprietary notations from the materials
-   Transferring the materials to another person or "mirroring" the materials on any other server
-   Violating any applicable laws or regulations
-   Accessing or searching the Service by any means other than our publicly supported interfaces
-   Scraping, crawling, or automated access to Service content

---

## 3. Disclaimer

The materials on Veriply are provided on an 'as is' basis. Veriply makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.

**Specifically regarding AI responses:** While we implement Human-in-the-Loop (HITL) verification to ensure accuracy, **you rely on all information at your own risk**. We recommend verification of critical information, especially for legal, financial, or medical decisions.

---

## 4. Limitations

In no event shall Veriply or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on Veriply, even if Veriply or an authorized representative has been notified orally or in writing of the possibility of such damage.

---

## 5. Accuracy of Materials

The materials appearing on Veriply could include technical, typographical, or photographic errors. Veriply does not warrant that any of the materials on Veriply are accurate, complete, or current. Veriply may make changes to the materials contained on Veriply at any time without notice.

---

## 6. Materials License

Veriply grants you a non-exclusive, revocable license to:

-   Create bots and documents within the Service
-   Upload documents (PDFs, Word docs, text files, etc.) to your knowledge base
-   Integrate with email (Gmail, Outlook)
-   Use AI-generated responses for your business purposes
-   Export your data in portable format

**Restrictions on Your Content:**

-   You must own or have rights to all content you upload
-   You cannot upload content that violates others' intellectual property rights
-   You cannot upload content that is illegal or harmful
-   Veriply retains the right to remove content that violates these terms

---

## 7. Limitations of Liability

In no event shall Veriply or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on Veriply or from any information, content, or material obtained through Veriply.

**Our total liability** in any case shall not exceed the amount you have paid to us in the 12 months preceding the claim.

---

## 8. User Accounts & Responsibilities

### 8.1 Account Creation

-   You are responsible for maintaining the confidentiality of your account credentials
-   You agree to accept responsibility for all activities that occur under your account
-   You must provide accurate and complete information during registration
-   You must be at least 18 years old (or of legal age in your jurisdiction)

### 8.2 Prohibited Uses

You agree not to use the Service to:

-   Upload copyrighted content you don't own
-   Attempt unauthorized access to systems or accounts
-   Send spam or malicious code
-   Engage in illegal activities
-   Harass, abuse, or threaten other users
-   Reverse-engineer or copy our proprietary technology

### 8.3 Account Deletion

-   You can delete your account at any time via `DELETE /api/v1/profile/me`
-   Upon deletion, all personal data is removed within 24 hours
-   Shared resources (bots, documents) may remain if others depend on them
-   HITL resolutions are anonymized to preserve knowledge base quality

---

## 9. Data Processing & GDPR Compliance

### 9.1 Data You Control

-   **Your Documents:** You upload documents; Veriply processes and stores them for your knowledge base
-   **Your Emails:** When you integrate Gmail/Outlook, you authorize us to access your email for draft automation
-   **Your Conversations:** Chat history is retained per our Data Retention Policy
-   **Your Account:** You can delete your account and all associated data anytime

### 9.2 Data We Use

-   **Email Integration:** We process email content only through our self-hosted Ollama (no external LLMs)
-   **Chat History:** Used to improve your experience and train our model (aggregated, anonymized)
-   **Feedback:** Your corrections to AI responses feed back into our knowledge base
-   **Usage Analytics:** We track feature usage to improve the Service

### 9.3 Your GDPR Rights (EU Residents)

You have the right to:

-   **Access** your data: `GET /api/v1/profile/export`
-   **Delete** your account: `DELETE /api/v1/profile/me`
-   **Correct** your information via account settings
-   **Port** your data in machine-readable format
-   **Opt-out** of non-essential processing

See our [Privacy Policy](PRIVACY-POLICY.md) for detailed information.

### 9.4 Consent to Processing

By using the Service, you consent to:

-   Storage of your account information
-   Processing of documents you upload
-   Processing of emails via your integrated email account
-   Use of your feedback for model improvement
-   Audit logging of your account activities

**You can withdraw consent** at any time by disabling integrations or deleting your account.

---

## 10. Third-Party Links

The Service may contain links to third-party websites. These external sites are not operated by Veriply. We have no responsibility for the content, accuracy, or practices of third-party websites. Your use of third-party websites is at your own risk and subject to their terms.

**For Email Integration:**

-   Gmail integration uses Google's OAuth—your email access is governed by Google's terms
-   Outlook integration uses Microsoft's OAuth—your email access is governed by Microsoft's terms
-   We only access email content you explicitly authorize

---

## 11. Tools & Features

### 11.1 AI Response Generation

Our AI assistant generates responses based on your documents. These responses are:

-   **Confidence Scored:** We estimate accuracy (0-100%)
-   **HITL Routed:** Low-confidence responses go to humans for review
-   **Feedback Incorporated:** Your corrections improve future responses

### 11.2 Email Automation

Our email draft feature:

-   Analyzes your writing style from past emails
-   Generates draft responses matching your tone
-   Requires your explicit approval before sending
-   Is subject to your email provider's terms (Gmail, Outlook)

### 11.3 Knowledge Base

Your knowledge base:

-   Stores documents you upload (PDFs, Word, text, CSV, Markdown)
-   Creates vector embeddings for search
-   Is accessible only to your group members (RLS-protected)
-   Can be searched via chat interface or API

---

## 12. Billing & Payments

### 12.1 Pricing

Pricing is displayed during signup and is subject to change with 30 days' notice.

### 12.2 Payment

-   Payments are processed securely via [payment processor]
-   Billing occurs monthly unless you choose annual billing
-   You can cancel anytime via your account settings

### 12.3 Refunds

Refunds are issued per our refund policy: [Link to refund policy]

---

## 13. Intellectual Property Rights

### 13.1 Your Content

-   **You own** all content you create in Veriply (documents, bots, chat history)
-   **You grant us** a license to use your content to operate and improve the Service
-   **You can export** your content anytime via data portability endpoint

### 13.2 Our Content

-   **We own** the Veriply platform, code, algorithms, and brand
-   **You cannot** reverse-engineer, copy, or redistribute our technology
-   **You can use** responses generated by our AI for your business purposes

### 13.3 License Grant

We grant you a limited, non-exclusive, non-transferable license to use the Service for your internal business purposes.

---

## 14. Modifications to Service

Veriply may modify or discontinue the Service or any feature or portion thereof (including, but not limited to, the hours of availability and the equipment or servers needed to access the Service) at any time, with or without cause, with or without notice, and without liability to you.

**For Major Changes:** We will provide at least 30 days' notice via email.

---

## 15. Termination of Use

Veriply may terminate or suspend your account immediately, without prior notice or liability, for any reason, including if you breach the Terms. Upon termination:

-   Your access to the Service ceases immediately
-   Your data is deleted per the GDPR process (within 24 hours)
-   Archived data compliant with law is retained (e.g., audit logs for legal holds)

---

## 16. Governing Law

These Terms and your use of the Service are governed by and construed in accordance with the laws of [Your Jurisdiction], without regard to its conflict of law provisions.

**For EU Residents:** GDPR and local data protection laws apply in addition to these terms.

---

## 17. Dispute Resolution

### 17.1 Informal Resolution

Before pursuing formal legal action, you agree to attempt to resolve disputes informally by contacting us at legal@veriply.ai.

### 17.2 Arbitration (US Residents)

Any disputes arising out of or related to these Terms shall be resolved by binding arbitration, except that:

-   Each party retains the right to seek injunctive relief
-   Either party may bring an action in small claims court

### 17.3 EU Residents

EU residents retain the right to bring disputes before your national courts and have the right to lodge complaints with data protection authorities.

---

## 18. Indemnity

You agree to indemnify and hold harmless Veriply and its officers, directors, employees, and agents from any and all claims, damages, losses, costs, and expenses (including reasonable attorneys' fees) arising out of or related to:

-   Your use of the Service
-   Your violation of these Terms
-   Your violation of any third-party rights
-   Content you upload or create in the Service

---

## 19. Severability

If any provision of these Terms is found to be invalid or unenforceable, the remaining provisions shall remain in full force and effect.

---

## 20. Entire Agreement

These Terms, together with the [Privacy Policy](PRIVACY-POLICY.md) and [Data Retention Policy](DATA-RETENTION-POLICY.md), constitute the entire agreement between you and Veriply regarding the Service and supersede all prior agreements and understandings.

---

## 21. Changes to Terms

Veriply may modify these Terms at any time. If material changes are made, we will notify you via email or by posting an updated version on our website. Your continued use of the Service constitutes acceptance of the modified Terms.

---

## 22. Contact & Support

**For questions about these Terms:**

Veriply Legal Team  
Email: legal@veriply.ai  
Address: [Your Company Address]

**For GDPR & Privacy Inquiries:**

Veriply Privacy Team  
Email: privacy@veriply.ai  
Phone: [Contact Number]

---

## 23. SPECIFIC PROVISIONS BY JURISDICTION

### 23.1 EU/UK Residents

**Additional Rights:**

-   You have the right to withdraw consent to data processing
-   You have the right to lodge complaints with your data protection authority
-   These Terms do not override your consumer protection rights under EU law

**Data Processing Agreement:** Available upon request for enterprise customers—contact legal@veriply.ai

### 23.2 California Residents (CCPA)

**Your Rights:**

-   Right to know what personal information is collected
-   Right to delete your personal information
-   Right to opt-out of data sales (not applicable—we don't sell data)
-   Right to non-discrimination for exercising your rights

Contact privacy@veriply.ai to exercise CCPA rights.

---

**End of Terms of Service**

---

### Quick Links

-   [Privacy Policy](PRIVACY-POLICY.md)
-   [Data Retention Policy](DATA-RETENTION-POLICY.md)
-   [GDPR Compliance Assessment](GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md)

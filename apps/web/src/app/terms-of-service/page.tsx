"use client";

import React from "react";

export default function TermsOfServicePage() {
    return (
        <div className="min-h-screen bg-white py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">
                <h1 className="text-4xl font-bold text-gray-900 mb-8">
                    Terms of Service
                </h1>

                <div className="prose prose-lg max-w-none text-gray-700">
                    <p className="text-sm text-gray-500 mb-8">
                        Last Updated: January 9, 2026
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        1. Acceptance of Terms
                    </h2>
                    <p>
                        By accessing and using Veriply ("Service"), you accept
                        and agree to be bound by the terms and provision of this
                        agreement. If you do not agree to abide by the above,
                        please do not use this service.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        2. Use License
                    </h2>
                    <p>
                        Permission is granted to temporarily download one copy
                        of the materials (information or software) on Veriply
                        for personal, non-commercial transitory viewing only.
                        This is the grant of a license, not a transfer of title,
                        and under this license you may not:
                    </p>
                    <ul className="list-disc pl-6 my-4">
                        <li>Modify or copy the materials</li>
                        <li>
                            Use the materials for any commercial purpose or for
                            any public display
                        </li>
                        <li>
                            Attempt to decompile or reverse engineer any
                            software contained on Veriply
                        </li>
                        <li>
                            Remove any copyright or other proprietary notations
                            from the materials
                        </li>
                        <li>
                            Transfer the materials to another person or "mirror"
                            the materials on any other server
                        </li>
                        <li>Violate any applicable laws or regulations</li>
                        <li>
                            Access or search the Service by any means other than
                            Veriply's publicly supported interfaces
                        </li>
                    </ul>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        3. Disclaimer
                    </h2>
                    <p>
                        The materials on Veriply are provided on an 'as is'
                        basis. Veriply makes no warranties, expressed or
                        implied, and hereby disclaims and negates all other
                        warranties including, without limitation, implied
                        warranties or conditions of merchantability, fitness for
                        a particular purpose, or non-infringement of
                        intellectual property or other violation of rights.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        4. Limitations
                    </h2>
                    <p>
                        In no event shall Veriply or its suppliers be liable for
                        any damages (including, without limitation, damages for
                        loss of data or profit, or due to business interruption)
                        arising out of the use or inability to use the materials
                        on Veriply, even if Veriply or an authorized
                        representative has been notified orally or in writing of
                        the possibility of such damage.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        5. Accuracy of Materials
                    </h2>
                    <p>
                        The materials appearing on Veriply could include
                        technical, typographical, or photographic errors.
                        Veriply does not warrant that any of the materials on
                        its website are accurate, complete, or current. Veriply
                        may make changes to the materials contained on its
                        website at any time without notice.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        6. Modifications
                    </h2>
                    <p>
                        Veriply may revise these Terms of Service for its
                        website at any time without notice. By using this
                        website, you are agreeing to be bound by the then
                        current version of these Terms of Service.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        7. Governing Law
                    </h2>
                    <p>
                        These Terms and Conditions and any separate agreements
                        we may have with you relating to our Services are
                        governed by and construed in accordance with the laws of
                        [Jurisdiction], without regard to its conflict of law
                        provisions.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        8. Data Processing & GDPR Compliance
                    </h2>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        8.1 Data Controller/Processor Relationship
                    </h3>
                    <p>
                        You are the data controller for all documents, emails,
                        and personal data processed by Veriply. Veriply acts as
                        a data processor. We process data only on your
                        documented instructions and maintain written Data
                        Processing Agreements (DPAs) with all sub-processors.
                    </p>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        8.2 User Data Control
                    </h3>
                    <p>
                        You have full control over your data and can at any
                        time:
                    </p>
                    <ul className="list-disc pl-6 my-4">
                        <li>Export your data in portable format (JSON)</li>
                        <li>Delete your account and all associated data</li>
                        <li>Restrict processing of your information</li>
                        <li>Revoke email integration permissions</li>
                        <li>Request a detailed access report</li>
                    </ul>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        8.3 GDPR Rights Exercise
                    </h3>
                    <p>
                        You can exercise your GDPR rights (Articles 15-22) by:
                    </p>
                    <ul className="list-disc pl-6 my-4">
                        <li>
                            <strong>Right to Access:</strong>{" "}
                            <code className="bg-gray-100 px-2 py-1 rounded">
                                GET /api/v1/profile/export
                            </code>
                        </li>
                        <li>
                            <strong>Right to Erasure:</strong>{" "}
                            <code className="bg-gray-100 px-2 py-1 rounded">
                                DELETE /api/v1/profile/me
                            </code>
                        </li>
                        <li>
                            <strong>Right to Restrict/Object:</strong> Email
                            privacy@veriply.ai
                        </li>
                        <li>
                            <strong>Right to Rectification:</strong> Update
                            profile at{" "}
                            <code className="bg-gray-100 px-2 py-1 rounded">
                                /profile/settings
                            </code>
                        </li>
                    </ul>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        8.4 GDPR-Specific Provisions
                    </h3>
                    <ul className="list-disc pl-6 my-4">
                        <li>
                            We maintain a Records of Processing (Article 30) for
                            all data activities
                        </li>
                        <li>
                            We conduct Data Protection Impact Assessments
                            (Article 35) for high-risk processing
                        </li>
                        <li>
                            We notify of data breaches within 72 hours (Article
                            33)
                        </li>
                        <li>
                            We assist with data subject requests within 30 days
                        </li>
                        <li>
                            Sub-processors are bound by DPAs ensuring GDPR
                            compliance
                        </li>
                    </ul>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        8.5 Email Integration
                    </h3>
                    <p>
                        Email integration (Gmail, Outlook) requires explicit
                        OAuth2 consent. You can revoke access at any time. We
                        store OAuth tokens securely and access only the emails
                        you explicitly authorize. We do not monitor, read, or
                        use your emails for any purpose other than processing
                        through Veriply.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        9. AI-Generated Responses
                    </h2>
                    <p>
                        Veriply uses AI models to generate responses to your
                        queries. While we strive for accuracy, AI-generated
                        content may occasionally be inaccurate, incomplete, or
                        biased. You are responsible for reviewing and verifying
                        all AI responses before relying on them. Low-confidence
                        responses are routed to human review (HITL) for
                        verification.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        10. Billing & Payment
                    </h2>
                    <p>
                        If you subscribe to a paid plan, you agree to pay the
                        fees specified in your subscription. Billing occurs on
                        the date specified, and we reserve the right to change
                        pricing with 30 days' notice.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        11. Termination
                    </h2>
                    <p>
                        We reserve the right to terminate your account at any
                        time for violations of these Terms. Upon termination,
                        your data will be handled according to our Data
                        Retention Policy.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        12. Intellectual Property
                    </h2>
                    <p>
                        All content on Veriply, including text, graphics, logos,
                        and images, is the property of Veriply or its content
                        suppliers and protected by international copyright laws.
                        Your documents and data remain your property; we obtain
                        only a limited license to process them.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        13. User Content
                    </h2>
                    <p>
                        You retain all rights to documents and data you upload
                        to Veriply. By uploading, you grant Veriply a limited
                        license to process your content solely to provide the
                        Service. We do not use your content for training our
                        models without explicit consent.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        14. Prohibited Conduct
                    </h2>
                    <p>You agree not to use Veriply to:</p>
                    <ul className="list-disc pl-6 my-4">
                        <li>Upload illegal content or malware</li>
                        <li>Violate intellectual property rights</li>
                        <li>Harass, abuse, or harm others</li>
                        <li>Attempt to gain unauthorized system access</li>
                        <li>
                            Interfere with service availability or integrity
                        </li>
                        <li>Share your account credentials</li>
                    </ul>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        15. Severability
                    </h2>
                    <p>
                        If any provision of these Terms is found to be invalid
                        or unenforceable, such provision shall be severable, and
                        the remaining provisions shall continue in full force
                        and effect.
                    </p>

                    <p className="text-sm text-gray-500 mt-8">
                        See our full{" "}
                        <a
                            href="/privacy-policy"
                            className="text-blue-600 hover:underline"
                        >
                            Privacy Policy
                        </a>{" "}
                        for data handling details.
                    </p>
                </div>
            </div>
        </div>
    );
}

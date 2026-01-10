"use client";

import React from "react";

export default function PrivacyPolicyPage() {
    return (
        <div className="min-h-screen bg-white py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">
                <h1 className="text-4xl font-bold text-gray-900 mb-8">
                    Privacy Policy
                </h1>

                <div className="prose prose-lg max-w-none text-gray-700">
                    <p className="text-sm text-gray-500 mb-8">
                        Last Updated: January 9, 2026
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        1. Introduction
                    </h2>
                    <p>
                        Veriply ("Company," "we," "us," "our") is committed to
                        protecting your privacy and ensuring you have a positive
                        experience on our website and within our services. This
                        Privacy Policy explains how we collect, use, disclose,
                        and safeguard your information when you visit our
                        website and use our services.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        2. Information We Collect
                    </h2>
                    <p>
                        We collect information you provide directly and
                        information collected automatically:
                    </p>
                    <ul className="list-disc pl-6 my-4">
                        <li>
                            <strong>Account Information:</strong> Email address,
                            name, password, company, preferences
                        </li>
                        <li>
                            <strong>Documents & Data:</strong> Files you upload,
                            chat history, responses, feedback
                        </li>
                        <li>
                            <strong>Email Integration:</strong> OAuth tokens for
                            Gmail/Outlook (with your explicit consent)
                        </li>
                        <li>
                            <strong>Usage Data:</strong> How you interact with
                            the service, timestamps, IP addresses
                        </li>
                        <li>
                            <strong>Device Information:</strong> Browser type,
                            operating system, device identifiers
                        </li>
                    </ul>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        3. Legal Basis for Processing (GDPR)
                    </h2>
                    <table className="w-full border-collapse border border-gray-300 my-4">
                        <thead>
                            <tr className="bg-gray-100">
                                <th className="border border-gray-300 px-4 py-2 text-left">
                                    Data Category
                                </th>
                                <th className="border border-gray-300 px-4 py-2 text-left">
                                    Legal Basis
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="border border-gray-300 px-4 py-2">
                                    Account Management
                                </td>
                                <td className="border border-gray-300 px-4 py-2">
                                    Contract (Terms of Service)
                                </td>
                            </tr>
                            <tr>
                                <td className="border border-gray-300 px-4 py-2">
                                    Document Processing
                                </td>
                                <td className="border border-gray-300 px-4 py-2">
                                    Contract + Legitimate Interest
                                </td>
                            </tr>
                            <tr>
                                <td className="border border-gray-300 px-4 py-2">
                                    Email Integration
                                </td>
                                <td className="border border-gray-300 px-4 py-2">
                                    Explicit Consent
                                </td>
                            </tr>
                            <tr>
                                <td className="border border-gray-300 px-4 py-2">
                                    Analytics
                                </td>
                                <td className="border border-gray-300 px-4 py-2">
                                    Legitimate Interest
                                </td>
                            </tr>
                        </tbody>
                    </table>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        4. How We Use Your Information
                    </h2>
                    <ul className="list-disc pl-6 my-4">
                        <li>Provide, maintain, and improve our services</li>
                        <li>Process documents and generate AI responses</li>
                        <li>
                            Respond to your inquiries and provide customer
                            support
                        </li>
                        <li>Send service announcements and updates</li>
                        <li>Detect and prevent fraud or security issues</li>
                        <li>Comply with legal obligations</li>
                        <li>
                            Analyze usage patterns to improve user experience
                        </li>
                    </ul>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        5. Data Retention
                    </h2>
                    <p>
                        We automatically delete data according to the following
                        schedule to minimize storage and comply with GDPR
                        Article 5 (Storage Limitation).
                    </p>
                    <ul className="list-disc pl-6 my-4">
                        <li>
                            <strong>Chat History:</strong> 90 days (auto-deleted
                            daily)
                        </li>
                        <li>
                            <strong>Confidence Logs:</strong> 180 days after
                            resolution (auto-deleted daily)
                        </li>
                        <li>
                            <strong>HITL Review Data:</strong> 365 days after
                            resolution (auto-deleted daily)
                        </li>
                        <li>
                            <strong>Inactive Accounts:</strong> 365 days of
                            inactivity (auto-deleted after warning emails)
                        </li>
                        <li>
                            <strong>Audit Logs:</strong> Retained indefinitely
                            for security and compliance
                        </li>
                    </ul>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        6. Your Privacy Rights (GDPR)
                    </h2>
                    <p>
                        As a resident of the EU, UK, or California, you have
                        specific rights:
                    </p>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        Right to Access (Article 15)
                    </h3>
                    <p>
                        Request a copy of all your personal data by visiting:{" "}
                        <code className="bg-gray-100 px-2 py-1 rounded">
                            /profile/export
                        </code>
                    </p>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        Right to Rectification (Article 16)
                    </h3>
                    <p>Correct inaccurate data through your account settings</p>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        Right to Erasure (Article 17)
                    </h3>
                    <p>
                        Request account deletion at:{" "}
                        <code className="bg-gray-100 px-2 py-1 rounded">
                            /profile/me (DELETE)
                        </code>{" "}
                        - all personal data and embeddings will be permanently
                        deleted
                    </p>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        Right to Data Portability (Article 20)
                    </h3>
                    <p>
                        Export your data in JSON format at:{" "}
                        <code className="bg-gray-100 px-2 py-1 rounded">
                            /profile/export
                        </code>
                    </p>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        Right to Restrict Processing (Article 18)
                    </h3>
                    <p>
                        Email privacy@veriply.ai to restrict processing of your
                        data
                    </p>

                    <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900">
                        Right to Object (Article 21)
                    </h3>
                    <p>Object to processing by emailing privacy@veriply.ai</p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        7. Security Measures (Article 32)
                    </h2>
                    <ul className="list-disc pl-6 my-4">
                        <li>
                            End-to-end TLS 1.2+ encryption for all data in
                            transit
                        </li>
                        <li>AES-256 encryption for sensitive data at rest</li>
                        <li>
                            PostgreSQL Row-Level Security (RLS) for multi-tenant
                            isolation
                        </li>
                        <li>
                            Role-Based Access Control (RBAC) with 5-tier
                            hierarchy
                        </li>
                        <li>JWT token-based authentication (24-hour expiry)</li>
                        <li>Automatic audit logging of all access</li>
                        <li>
                            Regular security assessments and vulnerability
                            scanning
                        </li>
                    </ul>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        8. Data Breach Notification (Article 33)
                    </h2>
                    <p>
                        If a data breach affects your personal data, we will
                        notify you and relevant authorities within 72 hours, as
                        required by law. We maintain an Incident Response Plan
                        with breach notification procedures.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        9. International Data Transfers
                    </h2>
                    <p>
                        If you are located in the EU or UK, we use Standard
                        Contractual Clauses (SCCs) for any necessary transfers
                        to the US or other jurisdictions. We have implemented
                        technical and organizational measures to protect your
                        data.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        10. Cookies and Tracking
                    </h2>
                    <p>
                        We use essential cookies for authentication and session
                        management. Non-essential tracking requires your
                        consent. You can manage cookie preferences in your
                        browser settings.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        11. Children's Privacy
                    </h2>
                    <p>
                        Our services are not intended for children under 13. We
                        do not knowingly collect personal information from
                        children under 13. If we become aware of such
                        collection, we will delete it immediately.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        12. Third-Party Services
                    </h2>
                    <p>
                        We use sub-processors including Google (Gmail API) and
                        Microsoft (Outlook API) for email integration. These
                        services are bound by Data Processing Agreements (DPAs)
                        that ensure GDPR compliance.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900">
                        13. Policy Changes
                    </h2>
                    <p>
                        We may update this Privacy Policy. Material changes will
                        be communicated via email to active users. Your
                        continued use of our services constitutes acceptance of
                        the updated policy.
                    </p>

                    <p className="text-sm text-gray-500 mt-8">
                        See our full documentation in{" "}
                        <a
                            href="/terms-of-service"
                            className="text-blue-600 hover:underline"
                        >
                            Terms of Service
                        </a>
                    </p>
                </div>
            </div>
        </div>
    );
}

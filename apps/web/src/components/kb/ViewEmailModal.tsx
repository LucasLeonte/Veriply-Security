"use client";

import React from "react";
import { X, Mail, Calendar, User, AlignLeft, ArrowRight } from "lucide-react";

interface KBEmail {
    id: string;
    subject?: string;
    from_email?: string;
    to_emails?: string;
    body_text?: string;
    sent_at?: string;
    status: string;
    created_at: string;
    email_metadata?: Record<string, any>;
}

interface ViewEmailModalProps {
    isOpen: boolean;
    onClose: () => void;
    email: KBEmail | null;
}

export function ViewEmailModal({
    isOpen,
    onClose,
    email,
}: ViewEmailModalProps) {
    if (!isOpen || !email) return null;

    return (
        <div
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[85vh] flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-start justify-between p-6 border-b border-slate-200">
                    <div className="flex items-center gap-3">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                            <Mail size={20} className="text-indigo-600" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-slate-900 leading-snug">
                                {email.subject || "(No Subject)"}
                            </h3>
                            <p className="text-xs text-slate-500 mt-1">
                                Imported {new Date(email.created_at).toLocaleDateString()}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 transition-colors"
                        aria-label="Close"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content - Scrollable */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {/* Metadata Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-3 bg-slate-50 rounded-md border border-slate-100">
                            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
                                <User size={14} /> From
                            </div>
                            <div className="text-sm text-slate-900 break-all">
                                {email.from_email || "Unknown"}
                            </div>
                        </div>

                        <div className="p-3 bg-slate-50 rounded-md border border-slate-100">
                            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
                                <ArrowRight size={14} /> To
                            </div>
                            <div className="text-sm text-slate-900 break-all">
                                {email.to_emails || "Unknown"}
                            </div>
                        </div>

                        <div className="p-3 bg-slate-50 rounded-md border border-slate-100">
                            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
                                <Calendar size={14} /> Sent Date
                            </div>
                            <div className="text-sm text-slate-900">
                                {email.sent_at
                                    ? new Date(email.sent_at).toLocaleString()
                                    : "Unknown"}
                            </div>
                        </div>

                        <div className="p-3 bg-slate-50 rounded-md border border-slate-100">
                            <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
                                <AlignLeft size={14} /> Status
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`inline-block w-2 h-2 rounded-full ${email.status === 'ready' ? 'bg-green-500' :
                                        email.status === 'processing' ? 'bg-blue-500' :
                                            email.status === 'failed' ? 'bg-red-500' :
                                                'bg-gray-400'
                                    }`} />
                                <span className="text-sm text-slate-900 capitalize">
                                    {email.status}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Body */}
                    <div>
                        <h4 className="text-sm font-semibold text-slate-900 mb-2 border-b border-slate-100 pb-2">
                            Email Content
                        </h4>
                        <div className="bg-slate-50 rounded-md border border-slate-200 p-4 text-sm text-slate-800 whitespace-pre-wrap font-mono">
                            {email.body_text || "(No content)"}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-slate-200 bg-slate-50 rounded-b-lg flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-white border border-slate-300 hover:border-slate-400 rounded-md transition-all shadow-sm"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}

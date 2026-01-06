"use client";

import React from "react";
import { X, Keyboard } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ShortcutHelpModalProps {
    isOpen: boolean;
    onClose: () => void;
}

interface ShortcutItem {
    key: string;
    description: string;
    category: string;
}

const shortcuts: ShortcutItem[] = [
    { key: "A", description: "Approve current draft", category: "Actions" },
    { key: "R", description: "Reject current draft", category: "Actions" },
    { key: "E", description: "Focus on edit field", category: "Actions" },
    { key: "N", description: "Skip to next item", category: "Navigation" },
    {
        key: "←",
        description: "Navigate to previous item",
        category: "Navigation",
    },
    { key: "→", description: "Navigate to next item", category: "Navigation" },
    { key: "?", description: "Show/hide this help", category: "General" },
    { key: "Esc", description: "Exit edit mode", category: "General" },
];

export function ShortcutHelpModal({ isOpen, onClose }: ShortcutHelpModalProps) {
    if (!isOpen) return null;

    // Group shortcuts by category
    const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
        if (!acc[shortcut.category]) {
            acc[shortcut.category] = [];
        }
        acc[shortcut.category].push(shortcut);
        return acc;
    }, {} as Record<string, ShortcutItem[]>);

    return (
        <div
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-200">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-sky-100 flex items-center justify-center">
                            <Keyboard className="w-5 h-5 text-sky-600" />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-slate-900">
                                Keyboard Shortcuts
                            </h2>
                            <p className="text-sm text-slate-500 mt-0.5">
                                Speed up your workflow with these shortcuts
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 transition-colors"
                        aria-label="Close"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {Object.entries(groupedShortcuts).map(
                        ([category, items]) => (
                            <div key={category}>
                                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
                                    {category}
                                </h3>
                                <div className="space-y-2">
                                    {items.map((shortcut, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-50"
                                        >
                                            <span className="text-slate-700">
                                                {shortcut.description}
                                            </span>
                                            <kbd className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 border border-slate-300 rounded-md shadow-sm min-w-[3rem] text-center">
                                                {shortcut.key}
                                            </kbd>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-6 border-t border-slate-200 bg-slate-50">
                    <p className="text-sm text-slate-500">
                        Press{" "}
                        <kbd className="px-2 py-1 text-xs font-medium bg-white border border-slate-300 rounded">
                            ?
                        </kbd>{" "}
                        anytime to toggle this help
                    </p>
                    <Button onClick={onClose} variant="outline">
                        Got it
                    </Button>
                </div>
            </div>
        </div>
    );
}

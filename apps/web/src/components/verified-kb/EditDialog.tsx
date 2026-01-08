"use client";

import { useState, useEffect } from "react";
import { X } from "lucide-react";
import type { VerifiedQA } from "@/types/verified-qa";

interface EditDialogProps {
    entry: VerifiedQA;
    onSave: (entry: VerifiedQA) => Promise<void>;
    onClose: () => void;
}

export function EditDialog({ entry, onSave, onClose }: EditDialogProps) {
    const [questionText, setQuestionText] = useState(entry.question_text);
    const [answerText, setAnswerText] = useState(entry.answer_text);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string>("");

    const handleSave = async () => {
        if (!questionText.trim() || !answerText.trim()) {
            setError("Question and answer are required");
            return;
        }

        setIsSaving(true);
        setError("");

        try {
            const updatedEntry = {
                ...entry,
                question_text: questionText,
                answer_text: answerText,
            };
            await onSave(updatedEntry);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save entry");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-200">
                    <h2 className="text-xl font-bold">Edit Verified Entry</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6">
                    {error && (
                        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Question
                        </label>
                        <textarea
                            value={questionText}
                            onChange={(e) => setQuestionText(e.target.value)}
                            rows={4}
                            maxLength={2000}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter the question..."
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            {questionText.length}/2000 characters
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Answer
                        </label>
                        <textarea
                            value={answerText}
                            onChange={(e) => setAnswerText(e.target.value)}
                            rows={6}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter the answer..."
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            {answerText.length} characters
                        </p>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-lg">
                        <p className="text-sm text-blue-800">
                            <strong>Note:</strong> When you save changes to the question, the semantic embedding will be automatically regenerated to maintain search accuracy.
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition disabled:bg-gray-400"
                    >
                        {isSaving ? "Saving..." : "Save Changes"}
                    </button>
                </div>
            </div>
        </div>
    );
}

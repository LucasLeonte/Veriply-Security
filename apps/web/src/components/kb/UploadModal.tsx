"use client";

import React, { useState, useCallback } from "react";
import { Upload, X, FileText, AlertCircle } from "lucide-react";

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUpload: (files: File[]) => Promise<void>;
}

const ALLOWED_EXTENSIONS = [".pdf", ".txt", ".docx", ".md"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

export function UploadModal({
    isOpen,
    onClose,
    onUpload,
}: UploadModalProps) {
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string>("");
    const [isUploading, setIsUploading] = useState(false);

    const validateFile = (file: File): string | null => {
        const extension = "." + file.name.split(".").pop()?.toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            return `${file.name}: Unsupported file type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
        }
        if (file.size > MAX_FILE_SIZE) {
            return `${file.name}: File too large. Max size: 10 MB`;
        }
        return null;
    };

    const handleFiles = (files: FileList | File[]) => {
        setError("");
        const fileArray = Array.from(files);
        const errors: string[] = [];
        const validFiles: File[] = [];

        fileArray.forEach((file) => {
            const validationError = validateFile(file);
            if (validationError) {
                errors.push(validationError);
            } else {
                validFiles.push(file);
            }
        });

        if (errors.length > 0) {
            setError(errors.join("; "));
        }

        if (validFiles.length > 0) {
            setSelectedFiles((prev) => [...prev, ...validFiles]);
        }
    };

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files) {
            handleFiles(e.dataTransfer.files);
        }
    }, []);

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            handleFiles(e.target.files);
        }
    };

    const removeFile = (index: number) => {
        setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;

        setIsUploading(true);
        setError("");

        try {
            await onUpload(selectedFiles);
            setSelectedFiles([]);
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Upload failed");
        } finally {
            setIsUploading(false);
        }
    };

    const handleClose = () => {
        if (!isUploading) {
            setSelectedFiles([]);
            setError("");
            onClose();
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
                <div className="bg-white rounded-lg shadow-lg w-full max-w-lg mx-4">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-slate-200">
                        <div>
                            <h2 className="text-lg font-semibold text-slate-900">
                                Upload Documents
                            </h2>
                            <p className="text-sm text-slate-600 mt-1">
                                Add documents to your bot&apos;s knowledge base
                            </p>
                        </div>
                        <button
                            onClick={handleClose}
                            disabled={isUploading}
                            className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-slate-400 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded transition-colors disabled:opacity-50"
                            aria-label="Close upload dialog"
                        >
                            <X size={20} aria-hidden="true" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-6 space-y-4">
                        {/* Drag & Drop Area */}
                        <div
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                                isDragging
                                    ? "border-emerald-500 bg-emerald-50"
                                    : "border-slate-300 bg-slate-50"
                            }`}
                        >
                            <Upload
                                size={48}
                                className={`mx-auto mb-4 ${
                                    isDragging ? "text-emerald-500" : "text-slate-400"
                                }`}
                            />
                            <p className="text-sm font-medium text-slate-700 mb-2">
                                Drag & drop files here
                            </p>
                            <p className="text-sm text-slate-500 mb-4">or</p>
                            <label className="inline-block">
                                <input
                                    type="file"
                                    multiple
                                    accept={ALLOWED_EXTENSIONS.join(",")}
                                    onChange={handleFileInput}
                                    className="hidden"
                                    disabled={isUploading}
                                />
                                <span className="px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 transition-colors cursor-pointer">
                                    Browse Files
                                </span>
                            </label>
                            <p className="text-xs text-slate-500 mt-4">
                                Supported: {ALLOWED_EXTENSIONS.join(", ")} • Max size: 10 MB
                            </p>
                        </div>

                        {/* Selected Files */}
                        {selectedFiles.length > 0 && (
                            <div>
                                <h3 className="text-sm font-medium text-slate-700 mb-2">
                                    Selected Files ({selectedFiles.length})
                                </h3>
                                <div className="space-y-2 max-h-40 overflow-y-auto">
                                    {selectedFiles.map((file, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center justify-between p-2 bg-slate-50 rounded-md"
                                        >
                                            <div className="flex items-center gap-2 flex-1 min-w-0">
                                                <FileText size={16} className="text-slate-400 flex-shrink-0" />
                                                <div className="min-w-0 flex-1">
                                                    <p className="text-sm text-slate-900 truncate">
                                                        {file.name}
                                                    </p>
                                                    <p className="text-xs text-slate-500">
                                                        {formatFileSize(file.size)}
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeFile(index)}
                                                disabled={isUploading}
                                                className="text-slate-400 hover:text-red-600 transition-colors disabled:opacity-50 flex-shrink-0 ml-2"
                                                aria-label="Remove file"
                                            >
                                                <X size={16} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Error Message */}
                        {error && (
                            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
                                <AlertCircle size={16} className="text-red-600 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-red-600">{error}</p>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-200">
                        <button
                            onClick={handleClose}
                            disabled={isUploading}
                            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleUpload}
                            disabled={selectedFiles.length === 0 || isUploading}
                            className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-md hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isUploading
                                ? "Uploading..."
                                : `Upload ${selectedFiles.length} file${selectedFiles.length !== 1 ? "s" : ""}`}
                        </button>
                    </div>
                </div>
            </div>
        </Dialog>
    );
}

"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle, XCircle, Info, AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastVariant = "default" | "success" | "error" | "info" | "warning";

interface Toast {
    id: string;
    title?: string;
    description?: string;
    variant?: ToastVariant;
}

interface ToastContextType {
    toasts: Toast[];
    toast: (options: Omit<Toast, "id">) => void;
    dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const toast = useCallback((options: Omit<Toast, "id">) => {
        const id = Math.random().toString(36).substring(7);
        const newToast = { ...options, id };

        setToasts((prev) => [...prev, newToast]);

        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 3000);
    }, []);

    const dismiss = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ toasts, toast, dismiss }}>
            {children}
            <ToastContainer toasts={toasts} dismiss={dismiss} />
        </ToastContext.Provider>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error("useToast must be used within ToastProvider");
    }
    return context;
}

function ToastContainer({
    toasts,
    dismiss,
}: {
    toasts: Toast[];
    dismiss: (id: string) => void;
}) {
    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onDismiss={dismiss} />
            ))}
        </div>
    );
}

function ToastItem({
    toast,
    onDismiss,
}: {
    toast: Toast;
    onDismiss: (id: string) => void;
}) {
    const variantStyles = {
        default: "bg-white border-slate-200",
        success: "bg-green-50 border-green-200",
        error: "bg-red-50 border-red-200",
        info: "bg-sky-50 border-sky-200",
        warning: "bg-amber-50 border-amber-200",
    };

    const iconVariants = {
        default: <Info className="w-5 h-5 text-slate-600" />,
        success: <CheckCircle className="w-5 h-5 text-green-600" />,
        error: <XCircle className="w-5 h-5 text-red-600" />,
        info: <Info className="w-5 h-5 text-sky-600" />,
        warning: <AlertTriangle className="w-5 h-5 text-amber-600" />,
    };

    const variant = toast.variant || "default";

    return (
        <div
            className={cn(
                "pointer-events-auto flex items-start gap-3 rounded-lg border shadow-lg p-4 min-w-[300px] max-w-[420px] animate-in slide-in-from-right-full duration-300",
                variantStyles[variant]
            )}
        >
            <div className="flex-shrink-0">{iconVariants[variant]}</div>
            <div className="flex-1 min-w-0">
                {toast.title && (
                    <p className="text-sm font-semibold text-slate-900 mb-1">
                        {toast.title}
                    </p>
                )}
                {toast.description && (
                    <p className="text-sm text-slate-600">
                        {toast.description}
                    </p>
                )}
            </div>
            <button
                onClick={() => onDismiss(toast.id)}
                className="flex-shrink-0 text-slate-400 hover:text-slate-600 transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

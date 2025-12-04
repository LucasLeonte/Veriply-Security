// DialogHeader for dialog title/header
interface DialogHeaderProps {
    children: React.ReactNode;
}

export function DialogHeader({ children }: DialogHeaderProps) {
    return <div className="mb-4">{children}</div>;
}
// DialogDescription for dialog description text
interface DialogDescriptionProps {
    children: React.ReactNode;
}

export function DialogDescription({ children }: DialogDescriptionProps) {
    return <p className="text-sm text-gray-600 mt-2">{children}</p>;
}
import * as React from "react";

interface DialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    children: React.ReactNode;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
    if (!open) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
            <div className="bg-white rounded-lg shadow-lg p-6 min-w-[320px] max-w-[90vw]">
                {children}
                <button
                    className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
                    onClick={() => onOpenChange(false)}
                    aria-label="Close dialog"
                >
                    ×
                </button>
            </div>
        </div>
    );
}

// DialogTitle for dialog title
interface DialogTitleProps {
    children: React.ReactNode;
}

export function DialogTitle({ children }: DialogTitleProps) {
    return <h2 className="text-lg font-bold text-gray-900 mb-1">{children}</h2>;
}

// DialogTrigger for opening dialog
interface DialogTriggerProps {
    children: React.ReactNode;
    onClick: () => void;
}

export function DialogTrigger({ children, onClick }: DialogTriggerProps) {
    return (
        <span onClick={onClick} className="cursor-pointer">
            {children}
        </span>
    );
}

// DialogContent for dialog body
interface DialogContentProps {
    children: React.ReactNode;
}

export function DialogContent({ children }: DialogContentProps) {
    return <div>{children}</div>;
}

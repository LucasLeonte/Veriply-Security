type ToastVariant = "default" | "destructive" | "success" | "info";

interface ToastOptions {
    title?: string;
    description?: string;
    variant?: ToastVariant;
}

export function useToast() {
    return {
        // Accepts 0 or 1 argument to satisfy current usages
        toast: (opts?: ToastOptions) => {
            if (!opts) return;
            // Minimal placeholder: log to console for visibility
            // Integrate with a real toast system later (e.g., shadcn/ui toast)
            // eslint-disable-next-line no-console
            console.debug("toast:", opts);
        },
    };
}

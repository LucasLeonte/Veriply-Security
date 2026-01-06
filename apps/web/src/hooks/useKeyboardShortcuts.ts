import { useEffect, useCallback, useRef } from "react";

export interface KeyboardShortcut {
    key: string;
    action: () => void;
    description: string;
    disabled?: boolean;
}

export interface UseKeyboardShortcutsOptions {
    shortcuts: KeyboardShortcut[];
    enabled?: boolean;
    ignoreWhenInputFocused?: boolean;
}

/**
 * Custom hook for managing keyboard shortcuts in the HITL dashboard (AC 5.5).
 *
 * Supported shortcuts:
 * - A = Approve current draft
 * - R = Reject current draft
 * - E = Focus on edit field
 * - N = Skip to next item
 * - ArrowLeft/ArrowRight = Navigate between items
 * - ? = Show shortcut help
 *
 * @param options Configuration options for keyboard shortcuts
 */
export function useKeyboardShortcuts({
    shortcuts,
    enabled = true,
    ignoreWhenInputFocused = true,
}: UseKeyboardShortcutsOptions) {
    const shortcutsRef = useRef(shortcuts);

    // Update ref when shortcuts change
    useEffect(() => {
        shortcutsRef.current = shortcuts;
    }, [shortcuts]);

    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            if (!enabled) return;

            // Check if we should ignore this event (e.g., when typing in input/textarea)
            if (ignoreWhenInputFocused) {
                const target = event.target as HTMLElement;
                const isInput =
                    target.tagName === "INPUT" ||
                    target.tagName === "TEXTAREA" ||
                    target.isContentEditable;

                // Allow 'Escape' even when input is focused (to exit edit mode)
                if (isInput && event.key !== "Escape") {
                    return;
                }
            }

            // Find matching shortcut
            const shortcut = shortcutsRef.current.find(
                (s) =>
                    s.key.toLowerCase() === event.key.toLowerCase() &&
                    !s.disabled
            );

            if (shortcut) {
                event.preventDefault();
                shortcut.action();
            }
        },
        [enabled, ignoreWhenInputFocused]
    );

    useEffect(() => {
        if (!enabled) return;

        window.addEventListener("keydown", handleKeyDown);
        return () => {
            window.removeEventListener("keydown", handleKeyDown);
        };
    }, [enabled, handleKeyDown]);

    return {
        shortcuts: shortcutsRef.current,
    };
}

/**
 * Tests for Story 5.3: Approve & Edit Flow
 *
 * Tests frontend functionality for:
 * - AC1: Approve sends response, updates KB, removes item, auto-loads next
 * - AC2: Edit field allows modification, diff tracking
 * - AC3: Approve button disabled for >3s, success toast
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
    ReviewQueueItemCard,
    ReviewQueue,
} from "@/components/hitl/ReviewQueue";
import type { ReviewQueueItem } from "@/hooks/useHITLQueue";
import { ToastProvider } from "@/components/ui/toast";

// Mock data
const mockItem: ReviewQueueItem = {
    id: "test-item-1",
    type: "chat",
    timestamp: new Date().toISOString(),
    userQuestion: "What is your return policy?",
    aiDraft: "Our return policy allows 30-day returns for most items.",
    botName: "Test Bot",
    confidence: 0.65,
    citations: [{ source: "FAQ Document", relevance: 0.95 }],
    status: "pending",
    source: "chatbot",
};

const mockItems: ReviewQueueItem[] = [
    mockItem,
    {
        ...mockItem,
        id: "test-item-2",
        userQuestion: "How do I track my order?",
        aiDraft:
            "You can track your order using the tracking number sent to your email.",
    },
    {
        ...mockItem,
        id: "test-item-3",
        userQuestion: "What payment methods do you accept?",
        aiDraft: "We accept credit cards, PayPal, and bank transfers.",
    },
];

const mockStats = {
    total: 3,
    pending: 3,
    chat: 3,
    email: 0,
};

describe("ReviewQueueItemCard - Approve/Edit Flow", () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.restoreAllMocks();
        vi.useRealTimers();
    });

    describe("AC3: Approve Button 3-Second Timer", () => {
        it("disables approve button initially when item selected", () => {
            const onApprove = vi.fn();
            const onReject = vi.fn();

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={onApprove}
                        onReject={onReject}
                    />
                </ToastProvider>
            );

            const approveButton = screen.getByRole("button", {
                name: /approve/i,
            });
            expect(approveButton).toBeDisabled();
        });

        it("shows countdown timer text when button is disabled", () => {
            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={vi.fn()}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            expect(screen.getByText(/review for 3s more/i)).toBeInTheDocument();
        });

        it("enables approve button after 3 seconds", async () => {
            const onApprove = vi.fn();

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={onApprove}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            const approveButton = screen.getByRole("button", {
                name: /approve/i,
            });
            expect(approveButton).toBeDisabled();

            // Fast-forward 1 second
            act(() => {
                vi.advanceTimersByTime(1000);
            });
            expect(screen.getByText(/review for 2s more/i)).toBeInTheDocument();

            // Fast-forward another 2 seconds (total 3s)
            act(() => {
                vi.advanceTimersByTime(2000);
            });

            await waitFor(() => {
                expect(approveButton).not.toBeDisabled();
            });

            expect(screen.queryByText(/review for/i)).not.toBeInTheDocument();
        });

        it("calls onApprove when approve button clicked after timer expires", async () => {
            const onApprove = vi.fn().mockResolvedValue(undefined);
            const user = userEvent.setup({ delay: null });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={onApprove}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            // Fast-forward 3 seconds
            act(() => {
                vi.advanceTimersByTime(3000);
            });

            const approveButton = screen.getByRole("button", {
                name: /approve/i,
            });
            await user.click(approveButton);

            await waitFor(() => {
                expect(onApprove).toHaveBeenCalledWith(undefined);
            });
        });
    });

    describe("AC2: Edit Functionality", () => {
        it("enables edit mode when edit button clicked", async () => {
            const user = userEvent.setup({ delay: null });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={vi.fn()}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            const editButton = screen.getByRole("button", { name: /edit/i });
            await user.click(editButton);

            expect(screen.getByText(/editing mode/i)).toBeInTheDocument();
            expect(screen.getByRole("textbox")).toHaveValue(mockItem.aiDraft);
        });

        it("allows modifying draft text in edit mode", async () => {
            const user = userEvent.setup({ delay: null });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={vi.fn()}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            // Enter edit mode
            await user.click(screen.getByRole("button", { name: /edit/i }));

            const textarea = screen.getByRole("textbox");
            await user.clear(textarea);
            await user.type(textarea, "Updated return policy answer");

            expect(textarea).toHaveValue("Updated return policy answer");
        });

        it("calls onApprove with edited text when approved in edit mode", async () => {
            const onApprove = vi.fn().mockResolvedValue(undefined);
            const user = userEvent.setup({ delay: null });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={onApprove}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            // Enter edit mode and modify text
            await user.click(screen.getByRole("button", { name: /edit/i }));
            const textarea = screen.getByRole("textbox");
            await user.clear(textarea);
            await user.type(textarea, "Edited answer");

            // Wait for timer
            act(() => {
                vi.advanceTimersByTime(3000);
            });

            // Approve with edits
            await user.click(screen.getByRole("button", { name: /approve/i }));

            await waitFor(() => {
                expect(onApprove).toHaveBeenCalledWith("Edited answer");
            });
        });

        it("cancels edit mode and restores original text when cancel clicked", async () => {
            const user = userEvent.setup({ delay: null });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={vi.fn()}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            // Enter edit mode and modify
            await user.click(screen.getByRole("button", { name: /edit/i }));
            const textarea = screen.getByRole("textbox");
            await user.clear(textarea);
            await user.type(textarea, "Modified text");

            // Cancel
            await user.click(screen.getByRole("button", { name: /cancel/i }));

            // Should exit edit mode and show original text
            expect(screen.queryByText(/editing mode/i)).not.toBeInTheDocument();
            expect(screen.getByText(mockItem.aiDraft)).toBeInTheDocument();
        });
    });

    describe("AC3: Success Toast", () => {
        it("shows success toast after successful approval", async () => {
            const onApprove = vi.fn().mockResolvedValue(undefined);
            const user = userEvent.setup({ delay: null });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={onApprove}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            // Wait for timer
            act(() => {
                vi.advanceTimersByTime(3000);
            });

            // Approve
            await user.click(screen.getByRole("button", { name: /approve/i }));

            await waitFor(() => {
                expect(
                    screen.getByText(/response sent and verified!/i)
                ).toBeInTheDocument();
            });
        });

        it("shows error toast on approval failure", async () => {
            const onApprove = vi
                .fn()
                .mockRejectedValue(new Error("Network error"));
            const user = userEvent.setup({ delay: null });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={onApprove}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            // Wait for timer
            act(() => {
                vi.advanceTimersByTime(3000);
            });

            // Approve (should fail)
            await user.click(screen.getByRole("button", { name: /approve/i }));

            await waitFor(() => {
                expect(
                    screen.getByText(/approval failed/i)
                ).toBeInTheDocument();
            });
        });
    });

    describe("AC1: Copy Functionality", () => {
        it("shows toast when copy button clicked", async () => {
            const user = userEvent.setup({ delay: null });

            // Mock clipboard API
            Object.assign(navigator, {
                clipboard: {
                    writeText: vi.fn().mockResolvedValue(undefined),
                },
            });

            render(
                <ToastProvider>
                    <ReviewQueueItemCard
                        item={mockItem}
                        isSelected={true}
                        onSelect={() => {}}
                        onApprove={vi.fn()}
                        onReject={vi.fn()}
                    />
                </ToastProvider>
            );

            await user.click(screen.getByRole("button", { name: /copy/i }));

            await waitFor(() => {
                expect(
                    screen.getByText(/copied to clipboard/i)
                ).toBeInTheDocument();
            });
        });
    });
});

describe("ReviewQueue - Auto-Load Next Item", () => {
    it("AC1: automatically selects first item when items are available", () => {
        render(
            <ToastProvider>
                <ReviewQueue
                    items={mockItems}
                    stats={mockStats}
                    isLoading={false}
                    onApprove={vi.fn()}
                    onReject={vi.fn()}
                />
            </ToastProvider>
        );

        // First item should be auto-selected (expanded view)
        expect(screen.getByText(mockItems[0].userQuestion)).toBeInTheDocument();
    });

    it("AC1: auto-loads next item after current item is removed", async () => {
        const onApprove = vi.fn().mockResolvedValue(undefined);

        const { rerender } = render(
            <ToastProvider>
                <ReviewQueue
                    items={mockItems}
                    stats={mockStats}
                    isLoading={false}
                    onApprove={onApprove}
                    onReject={vi.fn()}
                />
            </ToastProvider>
        );

        // Verify first item is selected
        expect(screen.getByText(mockItems[0].userQuestion)).toBeInTheDocument();

        // Simulate approval removing first item
        const itemsAfterApproval = mockItems.slice(1);
        rerender(
            <ToastProvider>
                <ReviewQueue
                    items={itemsAfterApproval}
                    stats={{ ...mockStats, total: 2, pending: 2 }}
                    isLoading={false}
                    onApprove={onApprove}
                    onReject={vi.fn()}
                />
            </ToastProvider>
        );

        // Second item should now be selected (first in new list)
        await waitFor(() => {
            expect(
                screen.getByText(mockItems[1].userQuestion)
            ).toBeInTheDocument();
        });
    });

    it("shows empty state when all items are processed", () => {
        render(
            <ToastProvider>
                <ReviewQueue
                    items={[]}
                    stats={{ total: 0, pending: 0, chat: 0, email: 0 }}
                    isLoading={false}
                    onApprove={vi.fn()}
                    onReject={vi.fn()}
                />
            </ToastProvider>
        );

        expect(
            screen.getByText(/no items pending review. nice work!/i)
        ).toBeInTheDocument();
    });
});

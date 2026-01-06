import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import FeedbackBar, { FeedbackSnapshot } from "@/components/FeedbackBar";
import { FeedbackType } from "@/lib/api/feedback";

describe("FeedbackBar", () => {
    const mockOnSubmit = vi.fn();
    const defaultProps = {
        messageId: "msg-123",
        answerId: "ans-456",
        onSubmit: mockOnSubmit,
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    // TC1: Renders thumbs-up and thumbs-down icons
    it("renders thumbs-up and thumbs-down icons", () => {
        render(<FeedbackBar {...defaultProps} />);
        
        const thumbsUpButton = screen.getByTitle("Helpful response");
        const thumbsDownButton = screen.getByTitle("Not helpful");
        
        expect(thumbsUpButton).toBeInTheDocument();
        expect(thumbsDownButton).toBeInTheDocument();
    });

    // TC2: Icons are clickable in default state
    it("allows clicking thumbs-up icon", async () => {
        mockOnSubmit.mockResolvedValue({ success: true });
        render(<FeedbackBar {...defaultProps} />);
        
        const thumbsUpButton = screen.getByTitle("Helpful response");
        fireEvent.click(thumbsUpButton);
        
        await waitFor(() => {
            expect(mockOnSubmit).toHaveBeenCalledWith({
                messageId: "msg-123",
                answerId: "ans-456",
                type: "positive",
            });
        });
    });

    // TC3: Thumbs-down opens modal
    it("opens feedback reason modal on thumbs-down click", async () => {
        render(<FeedbackBar {...defaultProps} />);
        
        const thumbsDownButton = screen.getByTitle("Not helpful");
        fireEvent.click(thumbsDownButton);
        
        await waitFor(() => {
            expect(screen.getByText("What was wrong?")).toBeInTheDocument();
        });
    });

    // TC4: Displays tooltip on hover
    it("shows tooltip on thumbs-up hover", () => {
        render(<FeedbackBar {...defaultProps} />);
        
        const thumbsUpButton = screen.getByTitle("Helpful response");
        expect(thumbsUpButton).toHaveAttribute("title", "Helpful response");
    });

    // TC5: Shows success message after positive feedback
    it("shows success message after positive feedback submission", async () => {
        const state: FeedbackSnapshot = {
            type: "positive",
            status: "sent",
            timestamp: Date.now(),
        };
        
        render(<FeedbackBar {...defaultProps} state={state} />);
        
        expect(screen.getByText("Thank you for the feedback!")).toBeInTheDocument();
    });

    // TC6: Shows error message on submission failure
    it("shows error message when feedback submission fails", () => {
        const state: FeedbackSnapshot = {
            type: "positive",
            status: "error",
            timestamp: Date.now(),
            message: "Could not send feedback",
        };
        
        render(<FeedbackBar {...defaultProps} state={state} />);
        
        expect(screen.getByText("Could not send feedback")).toBeInTheDocument();
    });

    // TC7: Shows loading spinner during pending state
    it("shows loading spinner when feedback is pending", () => {
        const state: FeedbackSnapshot = {
            type: "positive",
            status: "pending",
            timestamp: Date.now(),
        };
        
        render(<FeedbackBar {...defaultProps} state={state} />);
        
        const thumbsUpButton = screen.getByTitle("Helpful response");
        expect(thumbsUpButton).toBeDisabled();
    });

    // TC8: Icons remain filled after feedback submitted
    it("shows filled icon after positive feedback", () => {
        const state: FeedbackSnapshot = {
            type: "positive",
            status: "sent",
            timestamp: Date.now(),
        };
        
        render(<FeedbackBar {...defaultProps} state={state} />);
        
        const thumbsUpButton = screen.getByTitle("Helpful response");
        expect(thumbsUpButton).toHaveClass("bg-green-600");
    });

    // TC9: Shows filled negative icon after negative feedback
    it("shows filled icon after negative feedback", () => {
        const state: FeedbackSnapshot = {
            type: "negative",
            status: "sent",
            timestamp: Date.now(),
            reason: "not_helpful",
        };
        
        render(<FeedbackBar {...defaultProps} state={state} />);
        
        const thumbsDownButton = screen.getByTitle("Not helpful");
        expect(thumbsDownButton).toHaveClass("bg-red-600");
    });

    // TC10: Disables icons during cooldown
    it("disables icons during cooldown period", () => {
        const state: FeedbackSnapshot = {
            type: "positive",
            status: "cooldown",
            timestamp: Date.now(),
            cooldownUntil: Date.now() + 60000,
        };
        
        render(<FeedbackBar {...defaultProps} state={state} />);
        
        const thumbsUpButton = screen.getByTitle("Helpful response");
        const thumbsDownButton = screen.getByTitle("Not helpful");
        
        expect(thumbsUpButton).toBeDisabled();
        expect(thumbsDownButton).toBeDisabled();
    });

    // TC11: Shows cooldown message during rate limit
    it("shows cooldown message when rate limited", () => {
        const state: FeedbackSnapshot = {
            type: "positive",
            status: "cooldown",
            timestamp: Date.now(),
            cooldownUntil: Date.now() + 60000,
        };
        
        render(<FeedbackBar {...defaultProps} state={state} />);
        
        expect(screen.getByText("Please wait before providing more feedback")).toBeInTheDocument();
    });

    // TC12: Allows changing feedback (click opposite icon)
    it("allows changing from positive to negative feedback", async () => {
        const state: FeedbackSnapshot = {
            type: "positive",
            status: "sent",
            timestamp: Date.now(),
        };
        
        const { rerender } = render(<FeedbackBar {...defaultProps} state={state} />);
        
        const thumbsDownButton = screen.getByTitle("Not helpful");
        fireEvent.click(thumbsDownButton);
        
        await waitFor(() => {
            expect(screen.getByText("What was wrong?")).toBeInTheDocument();
        });
    });

    // TC13: Handles missing answerId gracefully
    it("handles missing answerId", async () => {
        mockOnSubmit.mockResolvedValue({ success: false, error: "Missing answer identifier" });
        render(<FeedbackBar messageId="msg-123" onSubmit={mockOnSubmit} />);
        
        const thumbsUpButton = screen.getByTitle("Helpful response");
        fireEvent.click(thumbsUpButton);
        
        await waitFor(() => {
            expect(mockOnSubmit).toHaveBeenCalledWith({
                messageId: "msg-123",
                answerId: undefined,
                type: "positive",
            });
        });
    });

    // TC14: Accessibility - aria labels present
    it("has proper aria labels for accessibility", () => {
        render(<FeedbackBar {...defaultProps} />);
        
        const thumbsUpButton = screen.getByLabelText("Helpful response");
        const thumbsDownButton = screen.getByLabelText("Not helpful");
        
        expect(thumbsUpButton).toBeInTheDocument();
        expect(thumbsDownButton).toBeInTheDocument();
    });

    // TC15: Visual feedback for pending state
    it("shows pending state correctly for both icons", () => {
        const positiveState: FeedbackSnapshot = {
            type: "positive",
            status: "pending",
            timestamp: Date.now(),
        };
        
        const { rerender } = render(<FeedbackBar {...defaultProps} state={positiveState} />);
        expect(screen.getByTitle("Helpful response")).toBeDisabled();
        
        const negativeState: FeedbackSnapshot = {
            type: "negative",
            status: "pending",
            timestamp: Date.now(),
        };
        
        rerender(<FeedbackBar {...defaultProps} state={negativeState} />);
        expect(screen.getByTitle("Not helpful")).toBeDisabled();
    });
});

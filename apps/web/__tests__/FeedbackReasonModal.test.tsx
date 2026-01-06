import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import FeedbackReasonModal from "@/components/FeedbackReasonModal";
import { FeedbackReason } from "@/lib/api/feedback";

describe("FeedbackReasonModal", () => {
    const mockOnSubmit = vi.fn();
    const mockOnClose = vi.fn();
    const defaultProps = {
        open: true,
        onClose: mockOnClose,
        onSubmit: mockOnSubmit,
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    // TC1: Modal renders when open
    it("renders modal when open prop is true", () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        expect(screen.getByText("What was wrong?")).toBeInTheDocument();
        expect(screen.getByText("Help us improve responses by sharing why this answer was not helpful.")).toBeInTheDocument();
    });

    // TC2: Modal does not render when closed
    it("does not render modal when open prop is false", () => {
        render(<FeedbackReasonModal {...defaultProps} open={false} />);
        
        expect(screen.queryByText("What was wrong?")).not.toBeInTheDocument();
    });

    // TC3: Shows all 5 reason options
    it("displays all five feedback reason options", () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        expect(screen.getByText("Incorrect information")).toBeInTheDocument();
        expect(screen.getByText("Not helpful / Irrelevant")).toBeInTheDocument();
        expect(screen.getByText("Incomplete answer")).toBeInTheDocument();
        expect(screen.getByText("Harmful or unsafe")).toBeInTheDocument();
        expect(screen.getByText("Other")).toBeInTheDocument();
    });

    // TC4: Allows selecting a reason
    it("allows selecting a reason via radio button", () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        const incorrectRadio = screen.getByLabelText("Incorrect information");
        fireEvent.click(incorrectRadio);
        
        expect(incorrectRadio).toBeChecked();
    });

    // TC5: Shows text field when "Other" is selected
    it('shows text input field when "Other" is selected', () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        const otherRadio = screen.getByLabelText("Other");
        fireEvent.click(otherRadio);
        
        const textInput = screen.getByPlaceholderText("Tell us more...");
        expect(textInput).toBeInTheDocument();
    });

    // TC6: Character counter for "Other" text field
    it("displays character counter for Other text field", () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        const otherRadio = screen.getByLabelText("Other");
        fireEvent.click(otherRadio);
        
        const textInput = screen.getByPlaceholderText("Tell us more...");
        fireEvent.change(textInput, { target: { value: "Test feedback" } });
        
        expect(screen.getByText("13/500 characters")).toBeInTheDocument();
    });

    // TC7: Validates minimum 10 characters for "Other"
    it("shows error if Other selected with less than 10 characters", async () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        const otherRadio = screen.getByLabelText("Other");
        fireEvent.click(otherRadio);
        
        const textInput = screen.getByPlaceholderText("Tell us more...");
        fireEvent.change(textInput, { target: { value: "Short" } });
        
        const submitButton = screen.getByText("Send Feedback");
        fireEvent.click(submitButton);
        
        await waitFor(() => {
            expect(screen.getByText("Please provide at least 10 characters for Other")).toBeInTheDocument();
        });
        
        expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    // TC8: Validates reason is selected before submit
    it("shows error if no reason is selected", async () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        const submitButton = screen.getByText("Send Feedback");
        fireEvent.click(submitButton);
        
        await waitFor(() => {
            expect(screen.getByText("Please select a reason")).toBeInTheDocument();
        });
        
        expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    // TC9: Submit button calls onSubmit with selected reason
    it("calls onSubmit with correct reason when submitted", async () => {
        mockOnSubmit.mockResolvedValue(undefined);
        render(<FeedbackReasonModal {...defaultProps} />);
        
        const notHelpfulRadio = screen.getByLabelText("Not helpful / Irrelevant");
        fireEvent.click(notHelpfulRadio);
        
        const submitButton = screen.getByText("Send Feedback");
        fireEvent.click(submitButton);
        
        await waitFor(() => {
            expect(mockOnSubmit).toHaveBeenCalledWith("not_helpful", undefined);
        });
        
        expect(mockOnClose).toHaveBeenCalled();
    });

    // TC10: Cancel button closes modal without submitting
    it("closes modal when Cancel button is clicked", () => {
        render(<FeedbackReasonModal {...defaultProps} />);
        
        const cancelButton = screen.getByText("Cancel");
        fireEvent.click(cancelButton);
        
        expect(mockOnClose).toHaveBeenCalled();
        expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    // TC11: Disables buttons when pending
    it("disables buttons when pending prop is true", () => {
        render(<FeedbackReasonModal {...defaultProps} pending={true} />);
        
        const submitButton = screen.getByText("Send Feedback");
        const cancelButton = screen.getByText("Cancel");
        
        expect(submitButton).toBeDisabled();
        expect(cancelButton).toBeDisabled();
    });

    // TC12: Clears form state when modal reopens
    it("resets form state when modal is closed and reopened", async () => {
        const { rerender } = render(<FeedbackReasonModal {...defaultProps} />);
        
        const notHelpfulRadio = screen.getByLabelText("Not helpful / Irrelevant");
        fireEvent.click(notHelpfulRadio);
        
        rerender(<FeedbackReasonModal {...defaultProps} open={false} />);
        rerender(<FeedbackReasonModal {...defaultProps} open={true} />);
        
        await waitFor(() => {
            const radios = screen.getAllByRole("radio");
            radios.forEach(radio => {
                expect(radio).not.toBeChecked();
            });
        });
    });
});

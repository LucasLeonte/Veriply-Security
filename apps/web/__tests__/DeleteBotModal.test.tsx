import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeleteBotModal } from "@/components/DeleteBotModal";
import { useDeleteBot } from "@/hooks/useBotsQuery";
import { Bot } from "@/types/bot";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock the hook
vi.mock("@/hooks/useBotsQuery", () => ({
    useDeleteBot: vi.fn(() => ({
        mutate: vi.fn(),
        isPending: false,
        error: null,
    })),
}));

describe("DeleteBotModal", () => {
    const mockBot: Bot = {
        id: "bot-1",
        name: "Test Bot",
        description: "A test bot",
        confidence_threshold: 80,
        status: "Ready",
        created_by: "user-1",
        created_at: "2025-01-01T00:00:00Z",
        updated_at: "2025-01-01T00:00:00Z",
        tenant_id: "tenant-1",
        doc_count: 42,
    };

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let mockMutate: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let mockOnClose: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let mockOnSuccess: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let mockOnError: any;

    beforeEach(() => {
        mockMutate = vi.fn();
        mockOnClose = vi.fn();
        mockOnSuccess = vi.fn();
        mockOnError = vi.fn();

        vi.mocked(useDeleteBot).mockReturnValue(
            {
                mutate: mockMutate,
                isPending: false,
                error: null,
            } as any // eslint-disable-line @typescript-eslint/no-explicit-any
        );
    });

    it("renders when isOpen is true", () => {
        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(
            screen.getByRole("heading", { name: "Delete Bot" })
        ).toBeInTheDocument();
        expect(
            screen.getByText(/This action cannot be undone/)
        ).toBeInTheDocument();
    });

    it("does not render when isOpen is false", () => {
        const { container } = render(
            <DeleteBotModal
                isOpen={false}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(container).toBeEmptyDOMElement();
    });

    it("does not render when bot is null", () => {
        const { container } = render(
            <DeleteBotModal
                isOpen={true}
                bot={null}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(container).toBeEmptyDOMElement();
    });

    it("displays bot document count in warning", () => {
        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(
            screen.getByText(/All 42 documents will be removed/)
        ).toBeInTheDocument();
    });

    it("displays 0 documents when doc_count is undefined", () => {
        const botWithoutDocCount = { ...mockBot, doc_count: undefined };
        render(
            <DeleteBotModal
                isOpen={true}
                bot={botWithoutDocCount}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(
            screen.getByText(/All 0 documents will be removed/)
        ).toBeInTheDocument();
    });

    it("disables delete button until name is confirmed", async () => {
        const user = userEvent.setup();
        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const deleteButton = screen.getByRole("button", {
            name: /Delete Bot/,
        });
        expect(deleteButton).toBeDisabled();

        // Type wrong name
        const input = screen.getByPlaceholderText(mockBot.name);
        await user.type(input, "Wrong Name");
        expect(deleteButton).toBeDisabled();

        // Clear and type correct name
        await user.clear(input);
        await user.type(input, mockBot.name);
        expect(deleteButton).not.toBeDisabled();
    });

    it("shows error when name doesn't match exactly", async () => {
        const user = userEvent.setup();
        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText(mockBot.name);
        await user.type(input, "test bot");

        expect(screen.getByText(/Name doesn't match/)).toBeInTheDocument();
    });

    it("case-sensitive name matching", async () => {
        const user = userEvent.setup();
        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText(mockBot.name);
        const deleteButton = screen.getByRole("button", {
            name: /Delete Bot/,
        });

        // Lowercase won't match (case-sensitive)
        await user.type(input, "test bot");
        expect(deleteButton).toBeDisabled();

        // Correct case matches
        await user.clear(input);
        await user.type(input, "Test Bot");
        expect(deleteButton).not.toBeDisabled();
    });

    it("calls mutate and onSuccess when form is submitted", async () => {
        const user = userEvent.setup();
        mockMutate.mockResolvedValue(undefined);

        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText(mockBot.name);
        await user.type(input, mockBot.name);

        const deleteButton = screen.getByRole("button", {
            name: /Delete Bot/,
        });
        await user.click(deleteButton);

        await waitFor(() => {
            expect(mockMutate).toHaveBeenCalledWith(mockBot.group_id, mockBot.id);
            expect(mockOnSuccess).toHaveBeenCalled();
        });
    });

    it("shows error message when deletion fails", async () => {
        const user = userEvent.setup();
        const errorMessage = "Failed to delete bot";
        mockMutate.mockRejectedValue(new Error(errorMessage));

        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
                onError={mockOnError}
            />
        );

        const input = screen.getByPlaceholderText(mockBot.name);
        await user.type(input, mockBot.name);

        const deleteButton = screen.getByRole("button", {
            name: /Delete Bot/,
        });
        await user.click(deleteButton);

        await waitFor(() => {
            expect(screen.getByText(errorMessage)).toBeInTheDocument();
            expect(mockOnError).toHaveBeenCalledWith(errorMessage);
        });
    });

    it("closes modal when Cancel button is clicked", async () => {
        const user = userEvent.setup();
        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const cancelButton = screen.getByRole("button", { name: "Cancel" });
        await user.click(cancelButton);

        expect(mockOnClose).toHaveBeenCalled();
    });

    it("displays deletion warning details", () => {
        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(
            screen.getByText(/Warning: Permanent Deletion/)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Bot record will be deleted/)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/All embeddings will be deleted/)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Chat history will be cleared/)
        ).toBeInTheDocument();
    });

    it("resets confirmation input when modal closes", async () => {
        const user = userEvent.setup();
        const { rerender } = render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText(
            mockBot.name
        ) as HTMLInputElement;
        await user.type(input, mockBot.name);
        expect(input.value).toBe(mockBot.name);

        // Close and reopen
        rerender(
            <DeleteBotModal
                isOpen={false}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        rerender(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const newInput = screen.getByPlaceholderText(
            mockBot.name
        ) as HTMLInputElement;
        expect(newInput.value).toBe("");
    });

    it("displays deletion status while pending", () => {
        vi.mocked(useDeleteBot).mockReturnValue(
            {
                mutate: mockMutate,
                isPending: true,
                error: null,
            } as any // eslint-disable-line @typescript-eslint/no-explicit-any
        );

        render(
            <DeleteBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(screen.getByText(/Deleting\.\.\./)).toBeInTheDocument();
    });
});

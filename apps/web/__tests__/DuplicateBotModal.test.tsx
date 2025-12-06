import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DuplicateBotModal } from "@/components/DuplicateBotModal";
import { useDuplicateBot } from "@/hooks/useBotsQuery";
import { Bot } from "@/types/bot";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock the hook
vi.mock("@/hooks/useBotsQuery", () => ({
    useDuplicateBot: vi.fn(() => ({
        mutate: vi.fn(),
        isPending: false,
        error: null,
    })),
}));

describe("DuplicateBotModal", () => {
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
        doc_count: 5,
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

        // Update the mock to return our mock function
        vi.mocked(useDuplicateBot).mockReturnValue({
            mutate: mockMutate,
            isPending: false,
            error: null,
        } as any); // eslint-disable-line @typescript-eslint/no-explicit-any
    });

    it("renders when isOpen is true", () => {
        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(screen.getByRole("heading", { name: "Duplicate Bot" })).toBeInTheDocument();
        expect(screen.getByDisplayValue(mockBot.name)).toBeInTheDocument();
    });

    it("does not render when isOpen is false", () => {
        const { container } = render(
            <DuplicateBotModal
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
            <DuplicateBotModal
                isOpen={true}
                bot={null}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(container).toBeEmptyDOMElement();
    });

    it("sets default name with (Copy) suffix", () => {
        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText(
            "e.g., HR Bot (Copy)"
        ) as HTMLInputElement;
        expect(input.value).toBe("Test Bot (Copy)");
    });

    it("validates name length on change", async () => {
        const user = userEvent.setup();
        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText("e.g., HR Bot (Copy)");

        // Test too short
        await user.clear(input);
        await user.type(input, "A");
        expect(
            screen.getByText("Name must be at least 2 characters")
        ).toBeInTheDocument();

        // Test valid length
        await user.clear(input);
        await user.type(input, "Valid Name");
        expect(
            screen.queryByText("Name must be at least 2 characters")
        ).not.toBeInTheDocument();
    });

    it("disables submit button when name is invalid", async () => {
        const user = userEvent.setup();
        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText("e.g., HR Bot (Copy)");
        const submitButton = screen.getByRole("button", {
            name: /Duplicate Bot/,
        });

        // Default is valid
        expect(submitButton).not.toBeDisabled();

        // Make it invalid
        await user.clear(input);
        await user.type(input, "A");
        expect(submitButton).toBeDisabled();
    });

    it("calls mutate and onSuccess when form is submitted", async () => {
        const user = userEvent.setup();
        const newBot = { ...mockBot, name: "Test Bot Copy", id: "bot-2" };
        mockMutate.mockResolvedValue(newBot);

        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const submitButton = screen.getByRole("button", {
            name: /Duplicate Bot/,
        });
        await user.click(submitButton);

        await waitFor(() => {
            expect(mockMutate).toHaveBeenCalledWith({
                botId: mockBot.id,
                name: "Test Bot (Copy)",
            });
            expect(mockOnSuccess).toHaveBeenCalledWith(newBot);
        });
    });

    it("shows error message when duplication fails", async () => {
        const user = userEvent.setup();
        const errorMessage = "Bot name already exists";
        mockMutate.mockRejectedValue(new Error(errorMessage));

        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
                onError={mockOnError}
            />
        );

        const submitButton = screen.getByRole("button", {
            name: /Duplicate Bot/,
        });
        await user.click(submitButton);

        await waitFor(() => {
            expect(screen.getByText(errorMessage)).toBeInTheDocument();
            expect(mockOnError).toHaveBeenCalledWith(errorMessage);
        });
    });

    it("closes modal when Cancel button is clicked", async () => {
        const user = userEvent.setup();
        render(
            <DuplicateBotModal
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

    it("displays info about what the new bot will inherit", () => {
        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        expect(screen.getByText("The new bot will:")).toBeInTheDocument();
        expect(
            screen.getByText(/Inherit the description and confidence threshold/)
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Start with status "Empty" \(no documents\)/)
        ).toBeInTheDocument();
    });

    it("uses custom name when provided", async () => {
        const user = userEvent.setup();
        const newBot = {
            ...mockBot,
            name: "My Custom Copy",
            id: "bot-2",
        };
        mockMutate.mockResolvedValue(newBot);

        render(
            <DuplicateBotModal
                isOpen={true}
                bot={mockBot}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        const input = screen.getByPlaceholderText("e.g., HR Bot (Copy)");
        await user.clear(input);
        await user.type(input, "My Custom Copy");

        const submitButton = screen.getByRole("button", {
            name: /Duplicate Bot/,
        });
        await user.click(submitButton);

        await waitFor(() => {
            expect(mockMutate).toHaveBeenCalledWith({
                botId: mockBot.id,
                name: "My Custom Copy",
            });
        });
    });
});

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInterface from "@/components/chat/ChatInterface";
import * as chatHook from "@/hooks/useChat";

// Mock the useChat hook
vi.mock("@/hooks/useChat");

describe("ChatInterface", () => {
    const mockSendMessage = vi.fn();
    const mockClearHistory = vi.fn();
    const mockRetryLastMessage = vi.fn();

    const defaultProps = {
        botId: "bot-123",
        botName: "Test Bot",
        botAvatar: undefined,
        welcomeMessage: "Welcome to Test Bot!",
        isPublic: true,
        confidenceThreshold: 80,
    };

    beforeEach(() => {
        vi.clearAllMocks();

        // Default mock implementation
        vi.mocked(chatHook.useChat).mockReturnValue({
            messages: [],
            loading: false,
            streaming: false,
            error: null,
            sendMessage: mockSendMessage,
            clearHistory: mockClearHistory,
            retryLastMessage: mockRetryLastMessage,
        });
    });

    it("renders welcome message on initial load", () => {
        render(<ChatInterface {...defaultProps} />);

        expect(screen.getByText("Welcome to Test Bot!")).toBeInTheDocument();
        expect(
            screen.getByPlaceholderText("Ask a question...")
        ).toBeInTheDocument();
    });

    it("displays user message after send", async () => {

        vi.mocked(chatHook.useChat).mockReturnValue({
            messages: [
                {
                    id: "1",
                    role: "user",
                    content: "Hello",
                    timestamp: Date.now(),
                },
            ],
            loading: false,
            streaming: false,
            error: null,
            sendMessage: mockSendMessage,
            clearHistory: mockClearHistory,
            retryLastMessage: mockRetryLastMessage,
        });

        render(<ChatInterface {...defaultProps} />);

        // The message should be visible
        expect(screen.getByText("Hello")).toBeInTheDocument();
    });

    it("shows typing indicator during streaming", () => {
        vi.mocked(chatHook.useChat).mockReturnValue({
            messages: [
                {
                    id: "1",
                    role: "user",
                    content: "Test question",
                    timestamp: Date.now(),
                },
            ],
            loading: true,
            streaming: true,
            error: null,
            sendMessage: mockSendMessage,
            clearHistory: mockClearHistory,
            retryLastMessage: mockRetryLastMessage,
        });

        render(<ChatInterface {...defaultProps} />);

        expect(screen.getByText("Typing...")).toBeInTheDocument();
    });

    it("displays error message with retry button", () => {
        vi.mocked(chatHook.useChat).mockReturnValue({
            messages: [],
            loading: false,
            streaming: false,
            error: "Connection failed",
            sendMessage: mockSendMessage,
            clearHistory: mockClearHistory,
            retryLastMessage: mockRetryLastMessage,
        });

        render(<ChatInterface {...defaultProps} />);

        expect(screen.getByText("Connection failed")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    });

    it("clears history when clear button clicked", async () => {
        const user = userEvent.setup();

        vi.mocked(chatHook.useChat).mockReturnValue({
            messages: [
                {
                    id: "1",
                    role: "user",
                    content: "Test",
                    timestamp: Date.now(),
                },
            ],
            loading: false,
            streaming: false,
            error: null,
            sendMessage: mockSendMessage,
            clearHistory: mockClearHistory,
            retryLastMessage: mockRetryLastMessage,
        });

        render(<ChatInterface {...defaultProps} />);

        const clearButton = screen.getByTitle("Start new conversation");
        await user.click(clearButton);

        // Confirmation dialog should appear
        await waitFor(() => {
            expect(screen.getByText("Start New Conversation?")).toBeInTheDocument();
        });

        // Click the confirm button
        const confirmButton = screen.getByText("Clear History");
        await user.click(confirmButton);

        await waitFor(() => {
            expect(mockClearHistory).toHaveBeenCalledOnce();
        });
    });

    it("sends message when Enter key pressed", async () => {
        const user = userEvent.setup();

        render(<ChatInterface {...defaultProps} />);

        const input = screen.getByPlaceholderText("Ask a question...");
        await user.type(input, "Test message{Enter}");

        await waitFor(() => {
            expect(mockSendMessage).toHaveBeenCalledWith("Test message");
        });
    });

    it("adds newline when Shift+Enter pressed", async () => {
        const user = userEvent.setup();

        render(<ChatInterface {...defaultProps} />);

        const input = screen.getByPlaceholderText(
            "Ask a question..."
        ) as HTMLTextAreaElement;
        await user.type(input, "Line 1{Shift>}{Enter}{/Shift}Line 2");

        expect(input.value).toContain("\n");
        expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it("disables send button when input is empty", () => {
        render(<ChatInterface {...defaultProps} />);

        const sendButton = screen.getByRole("button", {
            name: /send/i,
        });
        expect(sendButton).toBeDisabled();
    });

    it("disables input during loading", () => {
        vi.mocked(chatHook.useChat).mockReturnValue({
            messages: [],
            loading: true,
            streaming: false,
            error: null,
            sendMessage: mockSendMessage,
            clearHistory: mockClearHistory,
            retryLastMessage: mockRetryLastMessage,
        });

        render(<ChatInterface {...defaultProps} />);

        const input = screen.getByPlaceholderText("Ask a question...");
        expect(input).toBeDisabled();
    });

    it("shows 'Bot is not available' when not public", () => {
        render(<ChatInterface {...defaultProps} isPublic={false} />);

        expect(
            screen.getByText("This bot is not available")
        ).toBeInTheDocument();
    });
});

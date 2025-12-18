import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ContextSummary from "@/components/chat/ContextSummary";
import { ChatMessage } from "@/types/chat";

describe("ContextSummary", () => {
    const createMessage = (id: number, role: "user" | "assistant", content: string): ChatMessage => ({
        id: `msg-${id}`,
        role,
        content,
        timestamp: Date.now() + id,
    });

    it("should not render when messages are within context window", () => {
        const messages = [
            createMessage(1, "user", "Question 1"),
            createMessage(2, "assistant", "Answer 1"),
            createMessage(3, "user", "Question 2"),
        ];

        const { container } = render(
            <ContextSummary messages={messages} contextWindowSize={10} />
        );

        expect(container.firstChild).toBeNull();
    });

    it("should not render when messages equal context window size", () => {
        const messages = Array.from({ length: 10 }, (_, i) =>
            createMessage(i, i % 2 === 0 ? "user" : "assistant", `Message ${i}`)
        );

        const { container } = render(
            <ContextSummary messages={messages} contextWindowSize={10} />
        );

        expect(container.firstChild).toBeNull();
    });

    it("should render when messages exceed context window", () => {
        const messages = Array.from({ length: 15 }, (_, i) =>
            createMessage(i, i % 2 === 0 ? "user" : "assistant", `Message ${i}`)
        );

        render(<ContextSummary messages={messages} contextWindowSize={10} />);

        expect(screen.getByText(/Previous Context/)).toBeInTheDocument();
        expect(screen.getByText(/5 older messages/)).toBeInTheDocument();
    });

    it("should be collapsed by default", () => {
        const messages = Array.from({ length: 15 }, (_, i) =>
            createMessage(i, i % 2 === 0 ? "user" : "assistant", `Message ${i}`)
        );

        render(<ContextSummary messages={messages} contextWindowSize={10} />);

        // Summary text should not be visible when collapsed
        const summaryText = screen.queryByText(/You asked about/);
        expect(summaryText).not.toBeInTheDocument();
    });

    it("should expand when toggle button is clicked", () => {
        const messages = [
            createMessage(1, "user", "What is refund policy"),
            createMessage(2, "assistant", "30-day refund"),
            createMessage(3, "user", "What about shipping"),
            createMessage(4, "assistant", "Free shipping"),
            ...Array.from({ length: 10 }, (_, i) =>
                createMessage(i + 5, i % 2 === 0 ? "user" : "assistant", `Recent message ${i}`)
            ),
        ];

        render(<ContextSummary messages={messages} contextWindowSize={10} />);

        // Find and click toggle button
        const toggleButton = screen.getByRole("button");
        fireEvent.click(toggleButton);

        // Summary should now be visible
        expect(screen.getByText(/You asked about/)).toBeInTheDocument();
    });

    it("should collapse when toggle button is clicked again", () => {
        const messages = Array.from({ length: 15 }, (_, i) =>
            createMessage(i, i % 2 === 0 ? "user" : "assistant", `Message ${i}`)
        );

        render(<ContextSummary messages={messages} contextWindowSize={10} />);

        const toggleButton = screen.getByRole("button");

        // Expand
        fireEvent.click(toggleButton);
        expect(screen.getByText(/You asked about/)).toBeInTheDocument();

        // Collapse
        fireEvent.click(toggleButton);
        expect(screen.queryByText(/You asked about/)).not.toBeInTheDocument();
    });

    it("should display correct number of older messages", () => {
        const messages = Array.from({ length: 25 }, (_, i) =>
            createMessage(i, i % 2 === 0 ? "user" : "assistant", `Message ${i}`)
        );

        render(<ContextSummary messages={messages} contextWindowSize={10} />);

        expect(screen.getByText(/15 older messages/)).toBeInTheDocument();
    });

    it("should generate summary with user question topics", () => {
        const messages = [
            createMessage(1, "user", "What is your refund policy for electronics"),
            createMessage(2, "assistant", "30-day refund"),
            createMessage(3, "user", "Do you ship internationally"),
            createMessage(4, "assistant", "Yes we do"),
            ...Array.from({ length: 10 }, (_, i) =>
                createMessage(i + 5, i % 2 === 0 ? "user" : "assistant", `Recent ${i}`)
            ),
        ];

        render(<ContextSummary messages={messages} contextWindowSize={10} />);

        const toggleButton = screen.getByRole("button");
        fireEvent.click(toggleButton);

        // Check that summary mentions topics from user questions
        const summary = screen.getByText(/You asked about/);
        expect(summary.textContent).toContain("What is your");
        expect(summary.textContent).toContain("response");
    });

    it("should respect custom isCollapsed prop", () => {
        const messages = Array.from({ length: 15 }, (_, i) =>
            createMessage(i, i % 2 === 0 ? "user" : "assistant", `Message ${i}`)
        );

        render(
            <ContextSummary
                messages={messages}
                contextWindowSize={10}
                isCollapsed={false}
            />
        );

        // Summary should be visible initially
        expect(screen.getByText(/You asked about/)).toBeInTheDocument();
    });
});

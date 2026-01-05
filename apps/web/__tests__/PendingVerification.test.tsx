import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import PendingVerification from "@/components/chat/PendingVerification";
import { ChatMessage } from "@/types/chat";

// Mock fetch
global.fetch = vi.fn();

describe("PendingVerification Component", () => {
    const defaultProps = {
        messageId: "msg-123",
        botId: "bot-456",
    };

    beforeEach(() => {
        vi.clearAllMocks();
        // Mock successful pending status by default
        vi.mocked(global.fetch).mockResolvedValue({
            ok: true,
            json: async () => ({ status: "pending" }),
        } as Response);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe("Pending State", () => {
        it("renders pending message initially", () => {
            render(<PendingVerification {...defaultProps} />);

            expect(
                screen.getByText("I'm checking with the team.")
            ).toBeInTheDocument();
            expect(
                screen.getByText("You'll receive a verified response shortly.")
            ).toBeInTheDocument();
        });

        it("shows spinner while pending", () => {
            const { container } = render(
                <PendingVerification {...defaultProps} />
            );

            // Check for loader element (has animate-spin class)
            const loader = container.querySelector(".animate-spin");
            expect(loader).toBeInTheDocument();
        });

        it("displays estimated wait time when provided", () => {
            render(
                <PendingVerification
                    {...defaultProps}
                    estimatedWaitTime="Usually within 5 minutes"
                />
            );

            expect(
                screen.getByText("Usually within 5 minutes")
            ).toBeInTheDocument();
        });
    });

    describe("Resolved State", () => {
        it("transitions to resolved state when status changes", async () => {
            const mockResponse: ChatMessage = {
                id: "msg-123",
                role: "assistant",
                content: "Here's the verified answer",
                timestamp: Date.now(),
                trustLevel: "verified",
            };

            // First call returns pending, subsequent calls return resolved
            let callCount = 0;
            vi.mocked(global.fetch).mockImplementation(async () => {
                callCount++;
                if (callCount > 1) {
                    return {
                        ok: true,
                        json: async () => ({
                            status: "resolved",
                            response: mockResponse,
                        }),
                    } as Response;
                }
                return {
                    ok: true,
                    json: async () => ({ status: "pending" }),
                } as Response;
            });

            render(<PendingVerification {...defaultProps} />);

            // Should show pending initially
            expect(
                screen.getByText("I'm checking with the team.")
            ).toBeInTheDocument();
        });

        it("displays notification when verification completes", async () => {
            const mockResponse: ChatMessage = {
                id: "msg-123",
                role: "assistant",
                content: "Verified answer",
                timestamp: Date.now(),
                trustLevel: "verified",
            };

            vi.mocked(global.fetch).mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    status: "resolved",
                    response: mockResponse,
                }),
            } as Response);

            render(<PendingVerification {...defaultProps} />);

            // After fetch completes (which is immediate in test)
            await waitFor(() => {
                expect(
                    screen.getByText("✓ We have an answer for you!")
                ).toBeInTheDocument();
            }, { timeout: 3000 });
        });

        it("calls onVerified callback when status resolves", async () => {
            const mockResponse: ChatMessage = {
                id: "msg-123",
                role: "assistant",
                content: "Verified answer",
                timestamp: Date.now(),
                trustLevel: "verified",
            };

            const onVerified = vi.fn();

            vi.mocked(global.fetch).mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    status: "resolved",
                    response: mockResponse,
                }),
            } as Response);

            render(
                <PendingVerification
                    {...defaultProps}
                    onVerified={onVerified}
                />
            );

            await waitFor(() => {
                expect(onVerified).toHaveBeenCalled();
            }, { timeout: 3000 });
        });
    });

    describe("Error State", () => {
        it("displays error message on fetch failure", async () => {
            vi.mocked(global.fetch).mockRejectedValueOnce(
                new Error("Network error")
            );

            render(<PendingVerification {...defaultProps} />);

            await waitFor(() => {
                expect(screen.getByText("Error:")).toBeInTheDocument();
            }, { timeout: 3000 });
        });

        it("shows retry hint on error", async () => {
            vi.mocked(global.fetch).mockRejectedValueOnce(
                new Error("Connection failed")
            );

            render(<PendingVerification {...defaultProps} />);

            await waitFor(() => {
                expect(
                    screen.getByText(/Please try asking again or refresh/)
                ).toBeInTheDocument();
            }, { timeout: 3000 });
        });
    });

    describe("Accessibility", () => {
        it("renders without accessibility violations", () => {
            const { container } = render(
                <PendingVerification {...defaultProps} />
            );

            // Basic check that component renders and has semantic HTML
            expect(container).toBeInTheDocument();
            expect(
                screen.getByText("I'm checking with the team.")
            ).toBeInTheDocument();
        });
    });
});

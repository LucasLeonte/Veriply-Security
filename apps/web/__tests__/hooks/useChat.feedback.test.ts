import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useChat } from "@/hooks/useChat";
import * as feedbackApi from "@/lib/api/feedback";
import * as authLib from "@/lib/auth";

vi.mock("@/lib/api/feedback");
vi.mock("@/lib/auth");
vi.mock("@/lib/api/chat", () => ({
    streamChatQuery: vi.fn(),
    loadChatHistory: vi.fn().mockResolvedValue([]),
    saveChatHistory: vi.fn(),
    clearChatHistory: vi.fn(),
}));

describe("useChat - Feedback Functionality", () => {
    const mockBotId = "bot-123";
    const mockToken = "mock-jwt-token";

    // Helper to render hook and wait for initialization
    const renderChatHook = async () => {
        const hookResult = renderHook(() => useChat(mockBotId));
        await waitFor(() => {
            expect(hookResult.result.current.submitFeedbackForMessage).toBeDefined();
        });
        return hookResult;
    };

    beforeEach(() => {
        vi.clearAllMocks();
        sessionStorage.clear();
        vi.mocked(authLib.getAccessToken).mockReturnValue(mockToken);
        vi.mocked(feedbackApi.submitFeedback).mockResolvedValue({
            feedback_id: "feedback-123",
            success: true,
            message: "Feedback recorded",
        });
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    // TC1: submitFeedbackForMessage function is available
    it("provides submitFeedbackForMessage function", async () => {
        const { result } = await renderChatHook();
        
        expect(result.current.submitFeedbackForMessage).toBeDefined();
        expect(typeof result.current.submitFeedbackForMessage).toBe("function");
    });

    // TC2: Successfully submits positive feedback
    it("submits positive feedback successfully", async () => {
        const { result } = await renderChatHook();
        
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(response).toEqual({ success: true, retriesUsed: 0 });
        expect(feedbackApi.submitFeedback).toHaveBeenCalledWith(mockBotId, {
            answer_id: "ans-1",
            message_id: "msg-1",
            type: "positive",
            reason: undefined,
            additional_notes: undefined,
            session_id: expect.any(String),
        });
    });

    // TC3: Successfully submits negative feedback with reason
    it("submits negative feedback with reason successfully", async () => {
        const { result } = await renderChatHook();
        
        await waitFor(() => {
            expect(result.current.submitFeedbackForMessage).toBeDefined();
        });
        
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-2",
                answerId: "ans-2",
                type: "negative",
                reason: "not_helpful",
            });
        });
        
        expect(response).toEqual({ success: true, retriesUsed: 0 });
        expect(feedbackApi.submitFeedback).toHaveBeenCalledWith(mockBotId, {
            answer_id: "ans-2",
            message_id: "msg-2",
            type: "negative",
            reason: "not_helpful",
            additional_notes: undefined,
            session_id: expect.any(String),
        });
    });

    // TC4: Submits feedback with additional notes
    it("submits feedback with additional notes for Other reason", async () => {
        const { result } = await renderChatHook();
        
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "negative",
                reason: "other",
                notes: "The response was too generic",
            });
        });
        
        expect(feedbackApi.submitFeedback).toHaveBeenCalledWith(mockBotId, expect.objectContaining({
            additional_notes: "The response was too generic",
        }));
    });

    // TC5: Updates feedbackState after successful submission
    it("updates feedbackState after successful submission", async () => {
        const { result } = await renderChatHook();
        
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        await waitFor(() => {
            expect(result.current.feedbackState["msg-1"]).toEqual({
                type: "positive",
                reason: undefined,
                status: "sent",
                timestamp: expect.any(Number),
            });
        });
    });

    // TC6: Sets pending status during submission
    it("sets pending status during feedback submission", async () => {
        let resolveFeedback: any;
        vi.mocked(feedbackApi.submitFeedback).mockReturnValue(
            new Promise((resolve) => { resolveFeedback = resolve; })
        );
        
        const { result } = await renderChatHook();
        
        act(() => {
            result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        await waitFor(() => {
            expect(result.current.feedbackState["msg-1"]?.status).toBe("pending");
        });
        
        act(() => {
            resolveFeedback({ feedback_id: "fb-1", success: true, message: "OK" });
        });
    });

    // TC7: Handles missing answerId
    it("returns error when answerId is missing", async () => {
        const { result } = await renderChatHook();
        
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                type: "positive",
            });
        });
        
        expect(response).toEqual({
            success: false,
            error: "Missing answer identifier for feedback",
        });
        expect(feedbackApi.submitFeedback).not.toHaveBeenCalled();
    });

    // TC8: Handles unauthenticated user (no token)
    it("returns error when user is not authenticated", async () => {
        vi.mocked(authLib.getAccessToken).mockReturnValue(null);
        
        const { result } = await renderChatHook();
        
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(response).toEqual({
            success: false,
            error: "Please log in to provide feedback",
        });
        expect(feedbackApi.submitFeedback).not.toHaveBeenCalled();
    });

    // TC9: Enforces rate limiting (20 per 5 minutes)
    it("enforces client-side rate limiting at 20 submissions", async () => {
        const { result } = await renderChatHook();
        
        // Submit 20 feedback items
        for (let i = 0; i < 20; i++) {
            await act(async () => {
                await result.current.submitFeedbackForMessage({
                    messageId: `msg-${i}`,
                    answerId: `ans-${i}`,
                    type: "positive",
                });
            });
        }
        
        // 21st should be rate limited
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-21",
                answerId: "ans-21",
                type: "positive",
            });
        });
        
        expect(response).toEqual({
            success: false,
            rateLimited: true,
        });
        expect(result.current.feedbackState["msg-21"]?.status).toBe("cooldown");
    });

    // TC10: Rate limit window expires after 5 minutes
    it("allows feedback after rate limit window expires", async () => {
        const { result } = await renderChatHook();
        vi.useFakeTimers();
        
        // Submit 20 feedback items
        for (let i = 0; i < 20; i++) {
            await act(async () => {
                await result.current.submitFeedbackForMessage({
                    messageId: `msg-${i}`,
                    answerId: `ans-${i}`,
                    type: "positive",
                });
            });
        }
        
        // Advance time by 5 minutes + 1ms
        act(() => {
            vi.advanceTimersByTime(5 * 60 * 1000 + 1);
        });
        
        // Should allow new feedback
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-new",
                answerId: "ans-new",
                type: "positive",
            });
        });
        
        expect(response?.success).toBe(true);
    });

    // TC11: Sets cooldown status for 1 minute after rate limit
    it("sets cooldown with cooldownUntil timestamp", async () => {
        const { result } = await renderChatHook();
        
        // Hit rate limit
        for (let i = 0; i < 20; i++) {
            await act(async () => {
                await result.current.submitFeedbackForMessage({
                    messageId: `msg-${i}`,
                    answerId: `ans-${i}`,
                    type: "positive",
                });
            });
        }
        
        const beforeTime = Date.now();
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-21",
                answerId: "ans-21",
                type: "positive",
            });
        });
        const afterTime = Date.now();
        
        const state = result.current.feedbackState["msg-21"];
        expect(state?.cooldownUntil).toBeGreaterThanOrEqual(beforeTime + 60 * 1000);
        expect(state?.cooldownUntil).toBeLessThanOrEqual(afterTime + 60 * 1000);
    });

    // TC12: Handles 401 authentication error from API
    it("handles 401 error with authentication message", async () => {
        const error: any = new Error("Unauthorized");
        error.status = 401;
        vi.mocked(feedbackApi.submitFeedback).mockRejectedValue(error);
        
        const { result } = await renderChatHook();
        
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(response).toEqual({
            success: false,
            error: "Please log in to provide feedback",
        });
        expect(result.current.feedbackState["msg-1"]?.status).toBe("error");
    });

    // TC13: Handles 429 rate limit error from API
    it("handles 429 rate limit error from API", async () => {
        const error: any = new Error("Too Many Requests");
        error.status = 429;
        vi.mocked(feedbackApi.submitFeedback).mockRejectedValue(error);
        
        const { result } = await renderChatHook();
        
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(response?.success).toBe(false);
        expect(result.current.feedbackState["msg-1"]?.status).toBe("cooldown");
        expect(result.current.feedbackState["msg-1"]?.cooldownUntil).toBeDefined();
    });

    // TC14: Handles generic network error
    it("handles generic network error", async () => {
        const error = new Error("Network error");
        vi.mocked(feedbackApi.submitFeedback).mockRejectedValue(error);
        
        const { result } = await renderChatHook();
        
        let response;
        await act(async () => {
            response = await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(response).toEqual({
            success: false,
            error: "Network error",
            retriesExhausted: true,
        });
        expect(result.current.feedbackState["msg-1"]?.status).toBe("error");
    });

    // TC15: Persists feedbackState to sessionStorage
    it("persists feedbackState to sessionStorage", async () => {
        const { result } = await renderChatHook();
        
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        const sessionId = result.current.sessionId;
        const key = `feedback_state_${mockBotId}_${sessionId}`;
        const stored = sessionStorage.getItem(key);
        
        expect(stored).toBeTruthy();
        const parsed = JSON.parse(stored!);
        expect(parsed["msg-1"]).toBeDefined();
        expect(parsed["msg-1"].type).toBe("positive");
    });

    // TC16: Loads feedbackState from sessionStorage on resume
    it("loads feedbackState from sessionStorage on session resume", async () => {
        const sessionId = "existing-session";
        const mockState = {
            "msg-old": {
                type: "positive",
                status: "sent",
                timestamp: Date.now(),
            },
        };
        
        const key = `feedback_state_${mockBotId}_${sessionId}`;
        sessionStorage.setItem(key, JSON.stringify(mockState));
        sessionStorage.setItem(`chat_session_${mockBotId}`, sessionId);
        
        const { result } = await renderChatHook();
        
        act(() => {
            result.current.resumeSession(sessionId);
        });
        
        expect(result.current.feedbackState["msg-old"]).toEqual(mockState["msg-old"]);
    });

    // TC17: Sets feedbackError state on errors
    it("sets feedbackError state when error occurs", async () => {
        vi.mocked(authLib.getAccessToken).mockReturnValue(null);
        
        const { result } = await renderChatHook();
        
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(result.current.feedbackError).toBe("Please log in to provide feedback");
    });

    // TC18: Clears feedbackError on successful submission
    it("clears feedbackError on successful submission", async () => {
        const { result } = await renderChatHook();
        
        // Set initial error
        vi.mocked(authLib.getAccessToken).mockReturnValue(null);
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(result.current.feedbackError).toBeTruthy();
        
        // Now succeed
        vi.mocked(authLib.getAccessToken).mockReturnValue(mockToken);
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-2",
                answerId: "ans-2",
                type: "positive",
            });
        });
        
        expect(result.current.feedbackError).toBeNull();
    });

    // TC19: Allows changing feedback (replacing old feedback)
    it("allows changing feedback for same message", async () => {
        const { result } = await renderChatHook();
        
        // First feedback
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(result.current.feedbackState["msg-1"]?.type).toBe("positive");
        
        // Change to negative
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "negative",
                reason: "not_helpful",
            });
        });
        
        expect(result.current.feedbackState["msg-1"]?.type).toBe("negative");
        expect(result.current.feedbackState["msg-1"]?.reason).toBe("not_helpful");
    });

    // TC20: Includes session_id in API request
    it("includes session_id in feedback API request", async () => {
        const { result } = await renderChatHook();
        
        const sessionId = result.current.sessionId;
        
        await act(async () => {
            await result.current.submitFeedbackForMessage({
                messageId: "msg-1",
                answerId: "ans-1",
                type: "positive",
            });
        });
        
        expect(feedbackApi.submitFeedback).toHaveBeenCalledWith(
            mockBotId,
            expect.objectContaining({
                session_id: sessionId,
            })
        );
    });
});

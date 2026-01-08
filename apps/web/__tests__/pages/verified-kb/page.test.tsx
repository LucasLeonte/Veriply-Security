import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import VerifiedKBPage from "@/app/dashboard/verified-kb/page";

const mockGroupContext = {
    currentGroup: { id: "group-1" },
};

vi.mock("@/contexts/GroupContext", () => ({
    useGroup: () => mockGroupContext,
}));

vi.mock("@/components", () => ({
    DashboardLayout: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="layout">{children}</div>
    ),
}));

vi.mock("@/components/verified-kb/EditDialog", () => ({
    EditDialog: () => <div>EditDialog</div>,
}));

vi.mock("@/components/verified-kb/DeleteConfirmationDialog", () => ({
    DeleteConfirmationDialog: () => <div>DeleteDialog</div>,
}));

type VerifiedQAApiResponse = {
    items: Array<{
        id: string;
        tenant_id: string;
        group_id: string;
        bot_id: string | null;
        question_text: string;
        answer_text: string;
        source_citations: Record<string, unknown> | null;
        approved_by_user_id: string | null;
        approved_at: string;
        updated_by_user_id: string | null;
        deleted_at: string | null;
        created_at: string;
        updated_at: string;
    }>;
    total: number;
    page: number;
    limit: number;
    total_pages: number;
};

const makeEntry = (id: string): VerifiedQAApiResponse["items"][number] => ({
    id,
    tenant_id: "tenant-1",
    group_id: "group-1",
    bot_id: null,
    question_text: `Question ${id}`,
    answer_text: `Answer ${id}`,
    source_citations: null,
    approved_by_user_id: null,
    approved_at: "2024-01-01T00:00:00.000Z",
    updated_by_user_id: null,
    deleted_at: null,
    created_at: "2024-01-01T00:00:00.000Z",
    updated_at: "2024-01-01T00:00:00.000Z",
});

const mockResponse = (data: VerifiedQAApiResponse) => ({
    ok: true,
    json: async () => data,
});

describe("VerifiedKBPage", () => {
    const fetchMock = vi.fn();

    beforeEach(() => {
        fetchMock.mockReset();
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        global.fetch = fetchMock as any;
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    it("resets to page 1 when filters change from a later page", async () => {
        fetchMock.mockResolvedValueOnce(
            mockResponse({
                items: [makeEntry("1")],
                total: 30,
                page: 1,
                limit: 20,
                total_pages: 2,
            })
        );

        fetchMock.mockResolvedValueOnce(
            mockResponse({
                items: [makeEntry("2")],
                total: 30,
                page: 2,
                limit: 20,
                total_pages: 2,
            })
        );

        fetchMock.mockResolvedValueOnce(
            mockResponse({
                items: [makeEntry("3")],
                total: 5,
                page: 1,
                limit: 20,
                total_pages: 1,
            })
        );

        render(<VerifiedKBPage />);

        const firstSummary = await screen.findByText(/Showing/i);
        expect(firstSummary.textContent?.replace(/\s+/g, " ").trim()).toContain(
            "Showing 1 to 20 of 30 entries"
        );

        fireEvent.click(screen.getByText("Next"));

        const secondSummary = await screen.findByText(/Showing/i);
        expect(secondSummary.textContent?.replace(/\s+/g, " ").trim()).toContain(
            "Showing 21 to 30 of 30 entries"
        );

        fireEvent.change(
            screen.getByPlaceholderText("Search by question or answer..."),
            { target: { value: "payment" } }
        );

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledTimes(3);
        });

        const thirdCallUrl = String(fetchMock.mock.calls[2][0]);
        expect(thirdCallUrl).toContain("page=1");
        expect(thirdCallUrl).toContain("search=payment");
    });

    it("aborts in-flight requests on unmount", async () => {
        let capturedSignal: AbortSignal | undefined;

        fetchMock.mockImplementation((_url, options: RequestInit) => {
            capturedSignal = options?.signal as AbortSignal | undefined;
            return new Promise((_, reject) => {
                capturedSignal?.addEventListener("abort", () => {
                    reject(new DOMException("Aborted", "AbortError"));
                });
            });
        });

        const { unmount } = render(<VerifiedKBPage />);

        await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

        unmount();

        await waitFor(() => {
            expect(capturedSignal?.aborted).toBe(true);
        });
    });
});

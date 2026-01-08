import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import VerifiedKBPage from "@/app/dashboard/verified-kb/page";

const mockGroupContext = { currentGroup: { id: "group-1" } };

vi.mock("@/contexts/GroupContext", () => ({ useGroup: () => mockGroupContext }));
vi.mock("@/components", () => ({ DashboardLayout: ({ children }: { children: React.ReactNode }) => (<div>{children}</div>) }));
vi.mock("@/components/verified-kb/EditDialog", () => ({ EditDialog: () => <div /> }));
vi.mock("@/components/verified-kb/DeleteConfirmationDialog", () => ({ DeleteConfirmationDialog: () => <div /> }));

const makeEntry = (id: string) => ({
  id,
  tenant_id: "t",
  group_id: "group-1",
  bot_id: null,
  question_text: `Q${id}`,
  answer_text: `A${id}`,
  source_citations: null,
  approved_by_user_id: "user-1234",
  approved_at: "2024-01-01T00:00:00.000Z",
  deleted_at: null,
  created_at: "2024-01-01T00:00:00.000Z",
  updated_at: "2024-01-01T00:00:00.000Z",
});

const mockResponse = (data: any) => ({ ok: true, json: async () => data });

describe("VerifiedKBPage filters", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    global.fetch = fetchMock as any;
    fetchMock.mockResolvedValue(mockResponse({ items: [makeEntry("1")], total: 1, page: 1, limit: 20, total_pages: 1 }));
  });

  it("debounces search input to avoid extra fetches", async () => {
    render(<VerifiedKBPage />);

    const input = screen.getByPlaceholderText("Search by question or answer...");
    fireEvent.change(input, { target: { value: "pay" } });
    fireEvent.change(input, { target: { value: "payment" } });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    const url = String(fetchMock.mock.calls[1][0]);
    expect(url).toContain("search=payment");
  });

  it("includes creator_id when filtering by creator", async () => {
    render(<VerifiedKBPage />);

    const creatorInput = screen.getByPlaceholderText("Filter by creator UUID");
    fireEvent.change(creatorInput, { target: { value: "user-uuid" } });

    await waitFor(() => {
      const lastCall = fetchMock.mock.calls.at(-1);
      expect(String(lastCall?.[0])).toContain("creator_id=user-uuid");
    });
  });
});

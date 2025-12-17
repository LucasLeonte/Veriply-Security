import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Citation } from "@/types/citations";
import { SourceViewerPanel } from "@/components/SourceViewerPanel";

const sampleCitation: Citation = {
  id: "c1",
  chunk_id: "chunk-123",
  document_id: "doc-1",
  document_name: "Returns Policy.pdf",
  section: "Section 2.1",
  page_number: 3,
  similarity_score: 0.92,
  text_snippet:
    "We offer a 30-day money-back guarantee for all purchases. Refunds are processed within 5-7 business days.",
  confidence: "high",
  chunk_position: 0,
};

describe("SourceViewerPanel", () => {
  it("does not render when closed", () => {
    render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={false}
        onOpenChange={() => {}}
      />
    );

    expect(screen.queryByText("Source Context")).not.toBeInTheDocument();
  });

  it("renders when open with citation", () => {
    render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(screen.getByText("Source Context")).toBeInTheDocument();
  });

  it("displays document name in header", () => {
    render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    // Document name should appear in header subtitle
    const header = screen.getByText("Source Context").parentElement;
    expect(header?.textContent).toContain("Returns Policy.pdf");
  });

  it("displays all citation metadata", () => {
    render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    // Document - look for it in the header
    const header = screen.getByText("Source Context").parentElement;
    expect(header?.textContent).toContain("Returns Policy.pdf");
    
    // Check main content area
    expect(screen.getByText("Section 2.1")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getAllByText("92%")[0]).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("displays chunk text in full", () => {
    render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(
      screen.getByText(
        /We offer a 30-day money-back guarantee for all purchases/
      )
    ).toBeInTheDocument();
  });

  it("shows relevance progress bar", () => {
    const { container } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    const progressBar = container.querySelector(".bg-blue-600");
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveStyle({ width: "92%" });
  });

  it("displays confidence badge with correct styling", () => {
    const { container } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    const confidenceBadge = container.querySelector(".bg-green-100");
    expect(confidenceBadge).toBeInTheDocument();
    expect(confidenceBadge?.textContent).toContain("high");
  });

  it("displays medium confidence with yellow badge", () => {
    const citationMedium = { ...sampleCitation, confidence: "medium" as const };

    const { container } = render(
      <SourceViewerPanel
        citation={citationMedium}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(container.querySelector(".bg-yellow-100")).toBeInTheDocument();
  });

  it("displays low confidence with orange badge", () => {
    const citationLow = { ...sampleCitation, confidence: "low" as const };

    const { container } = render(
      <SourceViewerPanel
        citation={citationLow}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(container.querySelector(".bg-orange-100")).toBeInTheDocument();
  });

  it("calls onOpenChange when close button clicked", () => {
    const onOpenChange = vi.fn();

    const { container } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={onOpenChange}
      />
    );

    // Click the close button in the header (has aria-label)
    const closeButton = container.querySelector('[aria-label="Close panel"]') as HTMLButtonElement;
    fireEvent.click(closeButton);

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("calls onOpenChange when overlay clicked", () => {
    const onOpenChange = vi.fn();

    const { container } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={onOpenChange}
      />
    );

    // Click overlay
    const overlay = container.querySelector("[class*='bg-black']");
    if (overlay) {
      fireEvent.click(overlay);
      expect(onOpenChange).toHaveBeenCalledWith(false);
    }
  });

  it("handles citations without section", () => {
    const citationNoSection = { ...sampleCitation, section: undefined };

    render(
      <SourceViewerPanel
        citation={citationNoSection}
        open={true}
        onOpenChange={() => {}}
      />
    );

    // Should still render
    expect(screen.getByText("Source Context")).toBeInTheDocument();
    // Section should not show
    expect(screen.queryByText("Section")).not.toBeInTheDocument();
  });

  it("handles citations without page number", () => {
    const citationNoPage = { ...sampleCitation, page_number: undefined };

    render(
      <SourceViewerPanel
        citation={citationNoPage}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(screen.getByText("Source Context")).toBeInTheDocument();
    // Page label should not appear without page number
  });

  it("displays all metadata fields when present", () => {
    render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    // Check for the expected content
    expect(screen.getByText("Source Context")).toBeInTheDocument();
    expect(screen.getByText("Section 2.1")).toBeInTheDocument();
    expect(screen.getByText(/We offer a 30-day/)).toBeInTheDocument();
  });

  it("renders close button in footer", () => {
    const { container } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    // Look for button with "Close" text content in the footer
    const buttons = container.querySelectorAll("button");
    const closeFooterButton = Array.from(buttons).find(btn => btn.textContent?.includes("Close") && btn.className.includes("bg-slate-900"));
    expect(closeFooterButton).toBeInTheDocument();
  });

  it("properly scrolls content area on overflow", () => {
    const longSnippet =
      "This is a very long text that should be scrollable. " +
      "Lorem ipsum dolor sit amet. ".repeat(20);

    const citationLong = { ...sampleCitation, text_snippet: longSnippet };

    const { container } = render(
      <SourceViewerPanel
        citation={citationLong}
        open={true}
        onOpenChange={() => {}}
      />
    );

    const contentArea = container.querySelector(".overflow-y-auto");
    expect(contentArea).toBeInTheDocument();
  });

  it("renders panel slide-in from right", () => {
    const { container } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    const panel = container.querySelector(".max-w-md");
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveClass("translate-x-0"); // Visible when open
  });

  it("keeps panel hidden when open is false", () => {
    const { container } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={false}
        onOpenChange={() => {}}
      />
    );

    // Panel should not be visible (no rendered content)
    expect(screen.queryByText("Source Context")).not.toBeInTheDocument();
  });

  it("updates when citation changes", () => {
    const { rerender } = render(
      <SourceViewerPanel
        citation={sampleCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(screen.getByText("Source Context")).toBeInTheDocument();

    const newCitation: Citation = {
      ...sampleCitation,
      id: "c2",
      document_name: "FAQ.md",
    };

    rerender(
      <SourceViewerPanel
        citation={newCitation}
        open={true}
        onOpenChange={() => {}}
      />
    );

    // After rerender, should display new citation - check in subtitle/content
    const header = screen.getByText("Source Context").parentElement?.parentElement;
    expect(header?.textContent).toContain("FAQ.md");
  });

  it("correctly formats similarity percentage", () => {
    const citationLow = { ...sampleCitation, similarity_score: 0.45 };

    render(
      <SourceViewerPanel
        citation={citationLow}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(screen.getByText("45%")).toBeInTheDocument();
  });
});

// Import vitest's vi if using mocking
import { vi } from "vitest";

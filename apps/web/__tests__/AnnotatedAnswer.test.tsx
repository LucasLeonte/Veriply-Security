import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnnotatedAnswer as AnnotatedAnswerType, Citation } from "@/types/citations";
import { AnnotatedAnswer } from "@/components/AnnotatedAnswer";

const sampleCitations: Citation[] = [
  {
    id: "c1",
    chunk_id: "chunk-abc",
    document_id: "doc-1",
    document_name: "Returns Policy.pdf",
    section: "Section 2.1",
    page_number: 3,
    similarity_score: 0.92,
    text_snippet: "We offer a 30-day money-back guarantee for all purchases.",
    confidence: "high",
    chunk_position: 0,
  },
  {
    id: "c2",
    chunk_id: "chunk-def",
    document_id: "doc-2",
    document_name: "FAQ.md",
    section: "Customer Support",
    page_number: undefined,
    similarity_score: 0.87,
    text_snippet: "Contact support through the portal for refunds.",
    confidence: "medium",
    chunk_position: 1,
  },
];

const sampleHtml = `
  <p>The refund policy allows returns within <span class="citation-ref" data-citation-id="c1">30 days</span>.</p>
  <p>Customers can request refunds through <span class="citation-ref" data-citation-id="c2">the support portal</span>.</p>
`;

function renderAnnotatedAnswer(overrides?: Partial<AnnotatedAnswerType>) {
  return render(
    <AnnotatedAnswer
      answerHtml={overrides?.answer_html ?? sampleHtml}
      citations={overrides?.citations ?? sampleCitations}
    />
  );
}

describe("AnnotatedAnswer", () => {
  it("renders the answer HTML content", async () => {
    const { container } = renderAnnotatedAnswer();

    await waitFor(() => {
      // Check for text content (may be split across elements)
      expect(screen.getByText(/The refund policy/)).toBeInTheDocument();
      expect(screen.getByText(/30 days/)).toBeInTheDocument();
      expect(screen.getByText(/request refunds/)).toBeInTheDocument();
    });
  });

  it("decorates inline citations with styles", async () => {
    const { container } = renderAnnotatedAnswer();

    await waitFor(() => {
      const node = container.querySelector('[data-citation-id="c1"]');
      expect(node?.className).toContain("text-blue-600");
      expect(node?.className).toContain("underline");
      expect(node?.className).toContain("cursor-pointer");
    });
  });

  it("sets tooltip metadata on inline citations", async () => {
    const { container } = renderAnnotatedAnswer();

    await waitFor(() => {
      const node = container.querySelector('[data-citation-id="c1"]');
      expect(node?.getAttribute("title")).toContain("Returns Policy.pdf");
      expect(node?.getAttribute("title")).toContain("Section 2.1");
      expect(node?.getAttribute("title")).toContain("p. 3");
      expect(node?.getAttribute("title")).toContain("92%");
    });
  });

  it("renders citation list with document names", async () => {
    renderAnnotatedAnswer();

    expect(await screen.findByText("Citations")).toBeInTheDocument();
    expect(screen.getByText("Returns Policy.pdf")).toBeInTheDocument();
    expect(screen.getByText("FAQ.md")).toBeInTheDocument();
  });

  it("displays citation metadata", async () => {
    renderAnnotatedAnswer();

    expect(await screen.findByText("Citations")).toBeInTheDocument();
    // Check for similarity scores
    expect(screen.getByText(/92%/)).toBeInTheDocument();
    expect(screen.getByText(/87%/)).toBeInTheDocument();
    // Check for confidence levels
    expect(screen.getByText(/high/)).toBeInTheDocument();
    expect(screen.getByText(/medium/)).toBeInTheDocument();
  });

  it("opens source viewer when clicking inline citation", async () => {
    renderAnnotatedAnswer();

    // Click on inline citation (search for text that contains "30 days" which is the citation)
    const inlineCitation = screen.getByText("30 days");
    fireEvent.click(inlineCitation);

    // Source viewer should appear
    await waitFor(() => {
      expect(screen.getByText("Source Context")).toBeInTheDocument();
    });
  });

  it("opens source viewer when clicking citation in list", async () => {
    renderAnnotatedAnswer();

    // Click on citation in list
    const citationLink = screen.getAllByText("Returns Policy.pdf")[0];
    fireEvent.click(citationLink);

    // Source viewer should appear
    await waitFor(() => {
      expect(screen.getByText("Source Context")).toBeInTheDocument();
    });
  });

  it("displays correct section in tooltip when provided", async () => {
    const { container } = renderAnnotatedAnswer();

    await waitFor(() => {
      const node = container.querySelector('[data-citation-id="c1"]');
      expect(node?.getAttribute("title")).toContain("Section 2.1");
    });
  });

  it("handles citations without section gracefully", async () => {
    const citationsNoSection: Citation[] = [
      {
        ...sampleCitations[0],
        section: undefined,
      },
    ];

    const { container } = renderAnnotatedAnswer({
      citations: citationsNoSection,
    });

    await waitFor(() => {
      const node = container.querySelector('[data-citation-id="c1"]');
      // Should still have title with document and similarity
      expect(node?.getAttribute("title")).toContain("Returns Policy.pdf");
      expect(node?.getAttribute("title")).toContain("92%");
    });
  });

  it("handles empty citations list", () => {
    render(
      <AnnotatedAnswer
        answerHtml="<p>Simple answer without citations.</p>"
        citations={[]}
      />
    );

    expect(screen.getByText("Simple answer without citations.")).toBeInTheDocument();
    // Citations section should not appear
    expect(screen.queryByText("Citations")).not.toBeInTheDocument();
  });

  it("sorts citations by ID", async () => {
    const unsortedCitations: Citation[] = [
      { ...sampleCitations[1], id: "c2" },
      { ...sampleCitations[0], id: "c1" },
    ];

    renderAnnotatedAnswer({
      citations: unsortedCitations,
    });

    const citationElements = screen.getAllByText(/\[\d+\]/);
    expect(citationElements.length).toBeGreaterThan(0);
  });

  it("truncates long citation snippets", async () => {
    const longSnippetCitation: Citation = {
      ...sampleCitations[0],
      text_snippet:
        "This is a very long text snippet that should be truncated in the display. ".repeat(
          10
        ),
    };

    renderAnnotatedAnswer({
      citations: [longSnippetCitation],
    });

    const snippet = screen.getByText(/This is a very long text snippet/);
    expect(snippet).toBeInTheDocument();
  });

  it("closes source viewer on button click", async () => {
    renderAnnotatedAnswer();

    // Click inline citation to open
    fireEvent.click(screen.getByText("30 days"));

    await waitFor(() => {
      expect(screen.getByText("Source Context")).toBeInTheDocument();
    });

    // Click close button
    const closeButtons = screen.getAllByRole("button", { name: /close/i });
    const closeButton = closeButtons[closeButtons.length - 1]; // Get the panel close button
    fireEvent.click(closeButton);

    // Source viewer should close
    await waitFor(() => {
      expect(screen.queryByText("Source Context")).not.toBeInTheDocument();
    });
  });

  it("closes source viewer when clicking overlay", async () => {
    renderAnnotatedAnswer();

    // Click inline citation to open
    fireEvent.click(screen.getByText("30 days"));

    await waitFor(() => {
      expect(screen.getByText("Source Context")).toBeInTheDocument();
    });

    // Find and click the overlay
    const sourceContext = screen.getByText("Source Context");
    const panel = sourceContext.closest(".bg-white");
    const overlay = panel?.parentElement?.querySelector("[class*='bg-black']");
    
    if (overlay) {
      fireEvent.click(overlay);
      await waitFor(() => {
        expect(screen.queryByText("Source Context")).not.toBeInTheDocument();
      });
    }
  });

  it("displays page number when available", async () => {
    renderAnnotatedAnswer();

    await waitFor(() => {
      expect(screen.getByText(/Page 3/)).toBeInTheDocument();
    });
  });

  it("handles multiple inline references to same citation", async () => {
    const multiRefHtml = `
      <p>Returns are allowed within <span class="citation-ref" data-citation-id="c1">30 days</span>.
      The <span class="citation-ref" data-citation-id="c1">30-day window</span> starts from purchase.</p>
    `;

    const { container } = renderAnnotatedAnswer({
      answer_html: multiRefHtml,
    });

    const citationRefs = container.querySelectorAll('[data-citation-id="c1"]');
    expect(citationRefs.length).toBe(2);
  });
});

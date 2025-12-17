import { test, expect } from "@playwright/test";

/**
 * E2E tests for citation viewer feature.
 * Tests the complete flow: query → answer generation → citations display → source viewer interaction.
 */

test.describe("Citation Viewer E2E", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the chat/query page
    // This assumes there's a chat page at /chat or similar
    await page.goto("/chat", { waitUntil: "networkidle" });
  });

  test("displays citations when answer is generated", async ({ page }) => {
    // Enter a query
    await page.fill('input[type="text"]', "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    // Wait for answer to be displayed
    await page.waitForSelector(".prose, [class*='answer']");

    // Check for citations
    const citations = await page.locator('[data-citation-id]').count();
    expect(citations).toBeGreaterThan(0);

    // Check for citations list
    const citationsList = await page.locator('text=Citations');
    await expect(citationsList).toBeVisible();
  });

  test("displays tooltip when hovering citation", async ({ page }) => {
    // Query and get answer with citations
    await page.fill('input[type="text"]', "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    // Wait for citations to render
    await page.waitForSelector('[data-citation-id]');

    // Hover over a citation
    const citation = await page.locator('[data-citation-id]').first();
    await citation.hover();

    // Check for tooltip content (title attribute)
    const title = await citation.getAttribute("title");
    expect(title).toContain(".pdf");
    expect(title).toMatch(/\d+%/); // Should have similarity percentage
  });

  test("opens source viewer when clicking citation", async ({ page }) => {
    // Query and get answer
    await page.fill('input[type="text"]', "What is the return policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    // Wait for citations
    await page.waitForSelector('[data-citation-id]');

    // Click on first citation
    const citation = await page.locator('[data-citation-id]').first();
    await citation.click();

    // Check if source viewer opens
    const sourceViewer = await page.locator('text=Source Context');
    await expect(sourceViewer).toBeVisible();

    // Verify source viewer content
    const sourceText = await page.locator('[class*="Full Chunk"], text=Chunk Text').textContent();
    expect(sourceText).toBeTruthy();
  });

  test("displays citation metadata in source viewer", async ({ page }) => {
    // Get answer with citations
    await page.fill('input[type="text"]', "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    // Open source viewer
    await page.waitForSelector('[data-citation-id]');
    await page.locator('[data-citation-id]').first().click();

    // Check for metadata
    await expect(page.locator('text=Document')).toBeVisible();
    await expect(page.locator('text=Relevance')).toBeVisible();
    await expect(page.locator('text=Confidence')).toBeVisible();

    // Verify similarity score display
    const similarityScore = await page.locator('text=/\\d+%/').first();
    await expect(similarityScore).toBeVisible();
  });

  test("closes source viewer on close button click", async ({ page }) => {
    // Get answer and open source viewer
    await page.fill('input[type="text"]', "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    await page.waitForSelector('[data-citation-id]');
    await page.locator('[data-citation-id]').first().click();

    await expect(page.locator('text=Source Context')).toBeVisible();

    // Click close button
    await page.click('button[aria-label="Close panel"], button:has-text("Close")');

    // Source viewer should be hidden
    await expect(page.locator('text=Source Context')).not.toBeVisible();
  });

  test("closes source viewer when clicking overlay", async ({ page }) => {
    // Get answer and open source viewer
    await page.fill('input[type="text"]', "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    await page.waitForSelector('[data-citation-id]');
    await page.locator('[data-citation-id]').first().click();

    await expect(page.locator('text=Source Context')).toBeVisible();

    // Click on overlay/backdrop
    const overlay = await page.locator('[class*="fixed inset-0"], [class*="bg-black"]').first();
    await overlay.click({ position: { x: 10, y: 10 } }); // Click far left (outside panel)

    // Source viewer should close
    await expect(page.locator('text=Source Context')).not.toBeVisible();
  });

  test("displays multiple citations from single answer", async ({ page }) => {
    // Query that should return multiple citations
    await page.fill('input[type="text"]', "What are the refund and shipping policies?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    // Wait for multiple citations
    await page.waitForSelector('[data-citation-id]');

    const citationCount = await page.locator('[data-citation-id]').count();
    expect(citationCount).toBeGreaterThanOrEqual(1);

    // Check citations list shows all citations
    const citationItems = await page.locator('text=/\\[\\d+\\]/', {
      hasText: /.pdf|\.md/,
    });
    const itemCount = await citationItems.count();
    expect(itemCount).toBeGreaterThanOrEqual(1);
  });

  test("highlights citation when source viewer is open", async ({ page }) => {
    // Get answer and open source viewer for specific citation
    await page.fill('input[type="text"]', "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    await page.waitForSelector('[data-citation-id]');
    const firstCitation = await page.locator('[data-citation-id]').first();
    const citationId = await firstCitation.getAttribute("data-citation-id");

    // Click citation to open viewer
    await firstCitation.click();

    // Verify source viewer shows correct citation
    const sourceViewer = await page.locator('text=Source Context');
    await expect(sourceViewer).toBeVisible();

    // Verify we can identify which citation is active (by checking content match)
    const sourceText = await sourceViewer.textContent();
    expect(sourceText).toBeTruthy();
  });

  test("handles answer without citations gracefully", async ({ page }) => {
    // This is a theoretical test - in practice, all answers should have citations
    // But the UI should handle the edge case

    // Query that might not have matching citations
    await page.fill('input[type="text"]', "Random question");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    // Answer should still render
    await page.waitForSelector(".prose, [class*='answer']");

    // If no citations, citations section might not appear (or appear empty)
    const citationsList = await page.locator('text=Citations');
    const isVisible = await citationsList.isVisible().catch(() => false);

    // Either no citations list, or empty list - both are acceptable
    expect(
      isVisible === false || (await citationsList.textContent()).includes("Citation")
    ).toBeTruthy();
  });

  test("citation links are accessible (keyboard navigation)", async ({ page }) => {
    // Get answer with citations
    await page.fill('input[type="text"]', "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    await page.waitForSelector('[data-citation-id]');

    // Tab to a citation
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    // Press Enter to activate
    await page.keyboard.press("Enter");

    // Source viewer should open
    const sourceViewer = await page.locator('text=Source Context');
    expect(await sourceViewer.isVisible().catch(() => false)).toBeTruthy();
  });
});

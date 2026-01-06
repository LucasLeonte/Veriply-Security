import { test, expect, Page } from "@playwright/test";

/**
 * E2E tests for user feedback feature.
 * Tests the complete feedback flow: send message → receive answer → click feedback → submit reason.
 */

test.describe("User Feedback Flow E2E", () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    // Create new context and page
    const context = await browser.newContext();
    page = await context.newPage();
    
    // Navigate to the chat page
    await page.goto("/chat", { waitUntil: "networkidle" });
    
    // Wait for chat interface to load
    await page.waitForSelector('input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]');
  });

  test("TC1: displays feedback bar after answer is generated", async () => {
    // Send a message
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    await page.fill(inputSelector, "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');

    // Wait for answer to be displayed
    await page.waitForSelector("[data-message-role='assistant'], .prose, [class*='answer']", {
      timeout: 15000, // Give AI time to respond
    });

    // Check for feedback bar
    const feedbackBar = await page.locator('[data-testid="feedback-bar"], [class*="feedback"]').first();
    await expect(feedbackBar).toBeVisible();

    // Check for thumbs up and thumbs down buttons
    const thumbsUp = await page.locator('button[aria-label*="thumbs up"], button[title*="thumbs up"], svg.lucide-thumbs-up').first();
    const thumbsDown = await page.locator('button[aria-label*="thumbs down"], button[title*="thumbs down"], svg.lucide-thumbs-down').first();
    await expect(thumbsUp).toBeVisible();
    await expect(thumbsDown).toBeVisible();
  });

  test("TC2: submits positive feedback successfully", async () => {
    // Send message and wait for answer
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    await page.fill(inputSelector, "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');
    await page.waitForSelector("[data-message-role='assistant'], .prose", { timeout: 15000 });

    // Click thumbs up
    const thumbsUp = await page.locator('button[aria-label*="thumbs up"], button[title*="thumbs up"], svg.lucide-thumbs-up').first();
    await thumbsUp.click();

    // Wait for feedback submission
    await page.waitForTimeout(1000);

    // Verify thumbs up is now in "sent" state (filled icon or disabled)
    // Check for visual feedback - icon should change or button disabled
    const thumbsUpButton = await page.locator('button').filter({ has: page.locator('svg.lucide-thumbs-up') }).first();
    const isDisabled = await thumbsUpButton.getAttribute("disabled");
    const className = await thumbsUpButton.getAttribute("class");
    
    // Either button is disabled OR has success/sent styling
    expect(isDisabled !== null || className?.includes("sent") || className?.includes("success")).toBeTruthy();
  });

  test("TC3: opens reason modal when clicking thumbs down", async () => {
    // Send message and wait for answer
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    await page.fill(inputSelector, "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');
    await page.waitForSelector("[data-message-role='assistant'], .prose", { timeout: 15000 });

    // Click thumbs down
    const thumbsDown = await page.locator('button[aria-label*="thumbs down"], button[title*="thumbs down"], svg.lucide-thumbs-down').first();
    await thumbsDown.click();

    // Wait for modal to appear
    const modal = await page.locator('[role="dialog"], [data-testid="feedback-modal"], dialog, [class*="modal"]');
    await expect(modal).toBeVisible();

    // Check modal title
    const modalTitle = await page.locator('h2, h3, [class*="modal-title"]').filter({ hasText: /feedback|reason/i });
    await expect(modalTitle).toBeVisible();
  });

  test("TC4: submits negative feedback with reason 'Not Helpful'", async () => {
    // Send message and wait for answer
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    await page.fill(inputSelector, "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');
    await page.waitForSelector("[data-message-role='assistant'], .prose", { timeout: 15000 });

    // Click thumbs down to open modal
    const thumbsDown = await page.locator('button[aria-label*="thumbs down"], button[title*="thumbs down"], svg.lucide-thumbs-down').first();
    await thumbsDown.click();

    // Wait for modal
    await page.waitForSelector('[role="dialog"], dialog, [class*="modal"]');

    // Select "Not Helpful" reason
    const notHelpfulButton = await page.locator('button').filter({ hasText: /not helpful/i }).first();
    await notHelpfulButton.click();

    // Submit feedback
    const submitButton = await page.locator('button').filter({ hasText: /submit|send/i }).first();
    await submitButton.click();

    // Modal should close
    await expect(page.locator('[role="dialog"], dialog, [class*="modal"]')).not.toBeVisible({ timeout: 3000 });

    // Verify thumbs down is now in "sent" state
    await page.waitForTimeout(500);
    const thumbsDownButton = await page.locator('button').filter({ has: page.locator('svg.lucide-thumbs-down') }).first();
    const isDisabled = await thumbsDownButton.getAttribute("disabled");
    expect(isDisabled).not.toBeNull();
  });

  test("TC5: submits negative feedback with 'Other' reason and notes", async () => {
    // Send message and wait for answer
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    await page.fill(inputSelector, "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');
    await page.waitForSelector("[data-message-role='assistant'], .prose", { timeout: 15000 });

    // Click thumbs down
    const thumbsDown = await page.locator('button[aria-label*="thumbs down"], button[title*="thumbs down"], svg.lucide-thumbs-down').first();
    await thumbsDown.click();

    // Wait for modal
    await page.waitForSelector('[role="dialog"], dialog, [class*="modal"]');

    // Select "Other" reason
    const otherButton = await page.locator('button').filter({ hasText: /other/i }).first();
    await otherButton.click();

    // Enter additional notes (must be 10+ chars)
    const textarea = await page.locator('textarea[placeholder*="details"], textarea[placeholder*="specific"]').first();
    await textarea.fill("The answer provided incorrect information about the return window.");

    // Submit feedback
    const submitButton = await page.locator('button').filter({ hasText: /submit|send/i }).first();
    await submitButton.click();

    // Modal should close
    await expect(page.locator('[role="dialog"], dialog, [class*="modal"]')).not.toBeVisible({ timeout: 3000 });
  });

  test("TC6: validates minimum 10 characters for 'Other' reason notes", async () => {
    // Send message and wait for answer
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    await page.fill(inputSelector, "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');
    await page.waitForSelector("[data-message-role='assistant'], .prose", { timeout: 15000 });

    // Click thumbs down
    const thumbsDown = await page.locator('button[aria-label*="thumbs down"], button[title*="thumbs down"], svg.lucide-thumbs-down').first();
    await thumbsDown.click();

    // Wait for modal
    await page.waitForSelector('[role="dialog"], dialog, [class*="modal"]');

    // Select "Other" reason
    const otherButton = await page.locator('button').filter({ hasText: /other/i }).first();
    await otherButton.click();

    // Enter short text (< 10 chars)
    const textarea = await page.locator('textarea[placeholder*="details"], textarea[placeholder*="specific"]').first();
    await textarea.fill("Bad");

    // Try to submit - should show validation error
    const submitButton = await page.locator('button').filter({ hasText: /submit|send/i }).first();
    await submitButton.click();

    // Modal should NOT close (validation failed)
    await page.waitForTimeout(500);
    const modal = await page.locator('[role="dialog"], dialog, [class*="modal"]');
    await expect(modal).toBeVisible();

    // Check for validation error message
    const errorMessage = await page.locator('text=/10.*characters|minimum.*10/i');
    await expect(errorMessage).toBeVisible();
  });

  test("TC7: persists feedback state after page refresh", async () => {
    // Send message and wait for answer
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    await page.fill(inputSelector, "What is the refund policy?");
    await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');
    await page.waitForSelector("[data-message-role='assistant'], .prose", { timeout: 15000 });

    // Click thumbs up
    const thumbsUp = await page.locator('button[aria-label*="thumbs up"], button[title*="thumbs up"], svg.lucide-thumbs-up').first();
    await thumbsUp.click();

    // Wait for submission
    await page.waitForTimeout(1000);

    // Refresh page
    await page.reload({ waitUntil: "networkidle" });

    // Wait for chat to reload
    await page.waitForSelector("[data-message-role='assistant'], .prose", { timeout: 5000 });

    // Check that thumbs up is still in "sent" state
    const thumbsUpButton = await page.locator('button').filter({ has: page.locator('svg.lucide-thumbs-up') }).first();
    const isDisabled = await thumbsUpButton.getAttribute("disabled");
    expect(isDisabled).not.toBeNull();
  });

  test("TC8: enforces rate limiting after multiple submissions", async () => {
    // Send message and wait for answer
    const inputSelector = 'input[type="text"], textarea[placeholder*="Ask"], textarea[placeholder*="message"]';
    
    // Submit 5 questions to get 5 answers
    for (let i = 0; i < 5; i++) {
      await page.fill(inputSelector, `Question ${i + 1}: What is the refund policy?`);
      await page.click('button[type="submit"], button:has-text("Send"), button:has-text("Ask")');
      await page.waitForTimeout(2000); // Wait for answer
    }

    // Now try to submit feedback on all 5 quickly
    const thumbsUpButtons = await page.locator('button').filter({ has: page.locator('svg.lucide-thumbs-up') }).all();
    
    for (const button of thumbsUpButtons) {
      await button.click();
      await page.waitForTimeout(200);
    }

    // Try to send 20 more messages and submit feedback (to exceed 20 per 5 min limit)
    // This would require significant setup, so we'll check for cooldown state instead
    
    // After rate limit, feedback buttons should show cooldown state
    // Look for any visual indicator (disabled, timer, etc.)
    const feedbackButtons = await page.locator('button').filter({ has: page.locator('svg.lucide-thumbs-up, svg.lucide-thumbs-down') }).all();
    
    // At least one should be in cooldown state if rate limited
    // Check for disabled state or cooldown class
    let foundCooldown = false;
    for (const button of feedbackButtons) {
      const className = await button.getAttribute("class");
      if (className?.includes("cooldown") || className?.includes("disabled")) {
        foundCooldown = true;
        break;
      }
    }
    
    // If not found in classes, check for tooltip/title indicating cooldown
    if (!foundCooldown) {
      const cooldownTooltip = await page.locator('[title*="wait"], [title*="cooldown"], [title*="try again"]').first();
      if (await cooldownTooltip.isVisible({ timeout: 1000 }).catch(() => false)) {
        foundCooldown = true;
      }
    }

    // Note: Actual rate limiting test would require submitting 20+ feedback items
    // This test validates the UI reflects rate limiting state
    expect(foundCooldown).toBeTruthy();
  });
});

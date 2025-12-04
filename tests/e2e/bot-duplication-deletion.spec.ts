/**
 * E2E Tests for Bot Duplication and Deletion
 * Requires Playwright to be installed and configured
 * Run with: npm run test:e2e
 */

import { test, expect, Page } from "@playwright/test";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const APP_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:3000";

// Helper to login
async function login(page: Page, email: string = "test@example.com") {
    await page.goto(`${APP_URL}/auth/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', "password123");
    await page.click('button[type="submit"]');
    await page.waitForURL(`${APP_URL}/dashboard/bots`);
}

test.describe("Bot Duplication and Deletion E2E", () => {
    test("should duplicate a bot successfully", async ({ page }) => {
        // Login
        await login(page);

        // Create a bot
        await page.click("button:has-text('Create Bot')");
        await page.fill('input[placeholder*="Name"]', "Test Bot Original");
        await page.fill(
            'textarea[placeholder*="Description"]',
            "Original test bot"
        );
        await page.click('button:has-text("Create Bot")');

        // Wait for bot to appear in list
        await page.waitForSelector("text=Test Bot Original");

        // Open bot menu
        const botCard = page.locator("text=Test Bot Original").locator("..");
        await botCard.locator("button:has-text('⋮')").click();

        // Click duplicate
        await page.click("text=Duplicate");

        // Modal should open with default name
        await expect(
            page.locator("text=Test Bot Original (Copy)")
        ).toBeVisible();

        // Submit
        await page.click('button:has-text("Duplicate Bot")');

        // Wait for success
        await page.waitForSelector("text=Bot duplicated");
        await expect(
            page.locator("text=Test Bot Original (Copy)")
        ).toBeVisible();
    });

    test("should duplicate with custom name", async ({ page }) => {
        await login(page);

        // Create a bot
        await page.click("button:has-text('Create Bot')");
        await page.fill('input[placeholder*="Name"]', "Custom Bot");
        await page.click('button:has-text("Create Bot")');

        await page.waitForSelector("text=Custom Bot");

        // Duplicate with custom name
        const botCard = page.locator("text=Custom Bot").locator("..");
        await botCard.locator("button:has-text('⋮')").click();
        await page.click("text=Duplicate");

        // Clear default and type custom name
        const nameInput = page.locator('input[placeholder*="e.g., HR Bot"]');
        await nameInput.clear();
        await nameInput.fill("My Custom Copy");

        await page.click('button:has-text("Duplicate Bot")');

        await page.waitForSelector("text=Bot duplicated");
        await expect(page.locator("text=My Custom Copy")).toBeVisible();
    });

    test("should show error when duplicate name already exists", async ({
        page,
    }) => {
        await login(page);

        // Create a bot
        await page.click("button:has-text('Create Bot')");
        await page.fill('input[placeholder*="Name"]', "Duplicate Test");
        await page.click('button:has-text("Create Bot")');

        await page.waitForSelector("text=Duplicate Test");

        // First duplication succeeds
        const botCard = page.locator("text=Duplicate Test").locator("..");
        await botCard.locator("button:has-text('⋮')").click();
        await page.click("text=Duplicate");
        await page.click('button:has-text("Duplicate Bot")');
        await page.waitForSelector("text=Bot duplicated");

        // Second duplication with same name should fail
        await botCard.locator("button:has-text('⋮')").click();
        await page.click("text=Duplicate");

        const nameInput = page.locator('input[placeholder*="e.g., HR Bot"]');
        await nameInput.clear();
        await nameInput.fill("Duplicate Test (Copy)");
        await page.click('button:has-text("Duplicate Bot")');

        // Should show error
        await expect(
            page.locator("text=Bot name already exists in your organization")
        ).toBeVisible();
    });

    test("should delete a bot with confirmation", async ({ page }) => {
        await login(page);

        // Create a bot to delete
        await page.click("button:has-text('Create Bot')");
        await page.fill('input[placeholder*="Name"]', "Bot to Delete");
        await page.click('button:has-text("Create Bot")');

        await page.waitForSelector("text=Bot to Delete");

        // Open delete modal
        const botCard = page.locator("text=Bot to Delete").locator("..");
        await botCard.locator("button:has-text('⋮')").click();
        await page.click("text=Delete");

        // Type confirmation
        const confirmInput = page.locator(
            "input[placeholder*='Bot to Delete']"
        );
        await confirmInput.fill("Bot to Delete");

        // Delete
        await page.click('button:has-text("Delete Bot")');

        // Wait for success and bot to disappear
        await page.waitForSelector("text=Bot deleted successfully");
        await expect(page.locator("text=Bot to Delete")).not.toBeVisible();
    });

    test("should not delete without exact name confirmation", async ({
        page,
    }) => {
        await login(page);

        // Create a bot
        await page.click("button:has-text('Create Bot')");
        await page.fill('input[placeholder*="Name"]', "Protection Test");
        await page.click('button:has-text("Create Bot")');

        await page.waitForSelector("text=Protection Test");

        // Open delete modal
        const botCard = page.locator("text=Protection Test").locator("..");
        await botCard.locator("button:has-text('⋮')").click();
        await page.click("text=Delete");

        // Type wrong name
        const confirmInput = page.locator(
            "input[placeholder*='Protection Test']"
        );
        await confirmInput.fill("protection test");

        // Delete button should be disabled
        const deleteButton = page.locator('button:has-text("Delete Bot")');
        await expect(deleteButton).toBeDisabled();

        // Type correct name
        await confirmInput.clear();
        await confirmInput.fill("Protection Test");

        // Now delete button should be enabled
        await expect(deleteButton).not.toBeDisabled();
    });

    test("should show warning with document count in delete modal", async ({
        page,
    }) => {
        await login(page);

        // Create a bot
        await page.click("button:has-text('Create Bot')");
        await page.fill('input[placeholder*="Name"]', "Bot with Docs");
        await page.click('button:has-text("Create Bot")');

        await page.waitForSelector("text=Bot with Docs");

        // Navigate to bot and add documents (simulate)
        // For now, just check the modal structure
        const botCard = page.locator("text=Bot with Docs").locator("..");
        await botCard.locator("button:has-text('⋮')").click();
        await page.click("text=Delete");

        // Check warning text
        await expect(
            page.locator("text=Warning: Permanent Deletion")
        ).toBeVisible();
        await expect(
            page.locator("text=All associated documents will be removed")
        ).toBeVisible();
        await expect(
            page.locator("text=All embeddings will be deleted")
        ).toBeVisible();
    });

    test("should allow duplicate then delete flow", async ({ page }) => {
        await login(page);

        // Create original bot
        await page.click("button:has-text('Create Bot')");
        await page.fill('input[placeholder*="Name"]', "Original Flow Bot");
        await page.fill('textarea[placeholder*="Description"]', "Testing flow");
        await page.click('button:has-text("Create Bot")');

        await page.waitForSelector("text=Original Flow Bot");

        // Duplicate it
        const botCard = page.locator("text=Original Flow Bot").locator("..");
        await botCard.locator("button:has-text('⋮')").click();
        await page.click("text=Duplicate");
        await page.click('button:has-text("Duplicate Bot")');

        await page.waitForSelector("text=Original Flow Bot (Copy)");

        // Delete the duplicate
        const duplicateCard = page
            .locator("text=Original Flow Bot (Copy)")
            .locator("..");
        await duplicateCard.locator("button:has-text('⋮')").click();
        await page.click("text=Delete");

        const confirmInput = page.locator(
            "input[placeholder*='Original Flow Bot']"
        );
        await confirmInput.fill("Original Flow Bot (Copy)");
        await page.click('button:has-text("Delete Bot")');

        await page.waitForSelector("text=Bot deleted successfully");
        await expect(
            page.locator("text=Original Flow Bot (Copy)")
        ).not.toBeVisible();

        // Original should still exist
        await expect(page.locator("text=Original Flow Bot")).toBeVisible();
    });
});

import { test, expect } from '@playwright/test';

test.describe('HITL Review Interface', () => {
    test.beforeEach(async ({ page }) => {
        // Mock authentication
        await page.route('**/api/auth/**', route => route.fulfill({
            status: 200,
            body: JSON.stringify({ user: { id: '1', email: 'test@example.com' } }),
        }));
        
        // Mock HITL queue list
        await page.route('**/api/hitl/queue', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                items: [
                    {
                        id: 'item-1',
                        type: 'chat',
                        timestamp: new Date().toISOString(),
                        userQuestion: 'What is the return policy?',
                        aiDraft: 'Our return policy allows returns within 30 days.',
                        botName: 'Support Bot',
                        confidence: 0.65,
                        citations: [
                            { source: 'Return Policy.pdf', relevance: 0.85 },
                        ],
                        status: 'pending',
                        source: 'chatbot',
                    },
                ],
                stats: {
                    total: 1,
                    pending: 1,
                    chat: 1,
                    email: 0,
                },
            }),
        }));
    });

    test('should display split view with query on left and draft on right', async ({ page }) => {
        // Mock detailed item endpoint
        await page.route('**/api/hitl/queue/item-1', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'item-1',
                type: 'chat',
                timestamp: new Date().toISOString(),
                userQuestion: 'What is the return policy?',
                aiDraft: 'Our return policy allows returns within 30 days of purchase. [Source: Return Policy.pdf]',
                botName: 'Support Bot',
                confidence: 0.65,
                timeInQueue: '15m',
                citations: [
                    { source: 'Return Policy.pdf', relevance: 0.85 },
                ],
                contextChunks: [
                    {
                        chunk_id: 'chunk-1',
                        document_id: 'doc-1',
                        document_name: 'Return Policy.pdf',
                        section: 'Standard Returns',
                        text: 'Customers may return items within 30 days of purchase.',
                        similarity: 0.85,
                        page_number: 1,
                    },
                ],
                status: 'pending',
                source: 'chatbot',
            }),
        }));

        await page.goto('/inbox/item-1');

        // Wait for content to load
        await page.waitForLoadState('networkidle');

        // Check left panel (query and context)
        await expect(page.locator('text=Customer Question')).toBeVisible();
        await expect(page.locator('text=What is the return policy?')).toBeVisible();
        await expect(page.locator('text=Retrieved Context')).toBeVisible();

        // Check right panel (draft)
        await expect(page.locator('text=AI Draft Response')).toBeVisible();
        await expect(page.locator('textarea')).toBeVisible();
        const textarea = page.locator('textarea');
        await expect(textarea).toHaveValue(/return policy allows returns within 30 days/);

        // Check top bar
        await expect(page.locator('text=65% Confidence')).toBeVisible();
        await expect(page.locator('text=Support Bot')).toBeVisible();
        await expect(page.locator('text=15m in queue')).toBeVisible();
    });

    test('should allow expanding and collapsing context chunks', async ({ page }) => {
        await page.route('**/api/hitl/queue/item-1', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'item-1',
                type: 'chat',
                timestamp: new Date().toISOString(),
                userQuestion: 'What is the return policy?',
                aiDraft: 'Our return policy allows returns within 30 days.',
                botName: 'Support Bot',
                confidence: 0.65,
                timeInQueue: '15m',
                citations: [],
                contextChunks: [
                    {
                        chunk_id: 'chunk-1',
                        document_id: 'doc-1',
                        document_name: 'Return Policy.pdf',
                        section: 'Standard Returns',
                        text: 'Customers may return items within 30 days of purchase for a full refund.',
                        similarity: 0.85,
                        page_number: 1,
                    },
                ],
                status: 'pending',
                source: 'chatbot',
            }),
        }));

        await page.goto('/inbox/item-1');
        await page.waitForLoadState('networkidle');

        // Initially, chunk content should not be visible (collapsed)
        await expect(page.locator('text=Customers may return items within 30 days')).not.toBeVisible();

        // Click to expand chunk
        await page.locator('text=Return Policy.pdf').first().click();

        // Now chunk content should be visible
        await expect(page.locator('text=Customers may return items within 30 days')).toBeVisible();

        // Click again to collapse
        await page.locator('text=Return Policy.pdf').first().click();

        // Content should be hidden again
        await expect(page.locator('text=Customers may return items within 30 days')).not.toBeVisible();
    });

    test('should show clickable source document links', async ({ page }) => {
        await page.route('**/api/hitl/queue/item-1', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'item-1',
                type: 'chat',
                timestamp: new Date().toISOString(),
                userQuestion: 'Test question',
                aiDraft: 'Test draft',
                botName: 'Support Bot',
                confidence: 0.65,
                timeInQueue: '5m',
                citations: [],
                contextChunks: [
                    {
                        chunk_id: 'chunk-1',
                        document_id: 'doc-123',
                        document_name: 'Return Policy.pdf',
                        section: 'Returns',
                        text: 'Test content',
                        similarity: 0.85,
                        page_number: 1,
                    },
                ],
                status: 'pending',
                source: 'chatbot',
            }),
        }));

        await page.goto('/inbox/item-1');
        await page.waitForLoadState('networkidle');

        // Find the external link icon in the context chunk
        const externalLink = page.locator('a[href*="/knowledge-base/documents/doc-123"]');
        await expect(externalLink).toBeVisible();
        
        // Verify it has target="_blank" (opens in new tab)
        await expect(externalLink).toHaveAttribute('target', '_blank');
    });

    test('should highlight citation syntax in draft', async ({ page }) => {
        await page.route('**/api/hitl/queue/item-1', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'item-1',
                type: 'chat',
                timestamp: new Date().toISOString(),
                userQuestion: 'Test question',
                aiDraft: 'Our policy is clear. [Source: Policy.pdf] Additional info available. [Source: FAQ.pdf]',
                botName: 'Support Bot',
                confidence: 0.65,
                timeInQueue: '5m',
                citations: [],
                contextChunks: [],
                status: 'pending',
                source: 'chatbot',
            }),
        }));

        await page.goto('/inbox/item-1');
        await page.waitForLoadState('networkidle');

        // Check for citation preview section
        await expect(page.locator('text=Citations Found (2)')).toBeVisible();
        await expect(page.locator('text=[Source: Policy.pdf]')).toBeVisible();
        await expect(page.locator('text=[Source: FAQ.pdf]')).toBeVisible();
    });

    test('should allow editing draft and mark as modified', async ({ page }) => {
        await page.route('**/api/hitl/queue/item-1', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'item-1',
                type: 'chat',
                timestamp: new Date().toISOString(),
                userQuestion: 'Test question',
                aiDraft: 'Original draft',
                botName: 'Support Bot',
                confidence: 0.65,
                timeInQueue: '5m',
                citations: [],
                contextChunks: [],
                status: 'pending',
                source: 'chatbot',
            }),
        }));

        await page.goto('/inbox/item-1');
        await page.waitForLoadState('networkidle');

        // Initially no "Modified" badge
        await expect(page.locator('text=Modified')).not.toBeVisible();

        // Edit the draft
        const textarea = page.locator('textarea');
        await textarea.fill('Edited draft with corrections');

        // Now "Modified" badge should appear
        await expect(page.locator('text=Modified')).toBeVisible();

        // Approve button text should change
        await expect(page.locator('button', { hasText: 'Approve with Edits' })).toBeVisible();
    });

    test('should submit approval with edits', async ({ page }) => {
        await page.route('**/api/hitl/queue/item-1', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'item-1',
                type: 'chat',
                timestamp: new Date().toISOString(),
                userQuestion: 'Test question',
                aiDraft: 'Original draft',
                botName: 'Support Bot',
                confidence: 0.65,
                timeInQueue: '5m',
                citations: [],
                contextChunks: [],
                status: 'pending',
                source: 'chatbot',
            }),
        }));

        let approvalRequest: any = null;
        await page.route('**/api/hitl/queue/item-1/approve', route => {
            approvalRequest = route.request().postDataJSON();
            route.fulfill({
                status: 200,
                body: JSON.stringify({
                    status: 'approved',
                    item_id: 'item-1',
                    resolved_answer: 'Edited draft',
                }),
            });
        });

        await page.goto('/inbox/item-1');
        await page.waitForLoadState('networkidle');

        // Edit draft
        await page.locator('textarea').fill('Edited draft');

        // Click approve
        await page.locator('button', { hasText: 'Approve with Edits' }).click();

        // Wait for navigation
        await page.waitForURL('**/inbox');

        // Verify request was sent with edits
        expect(approvalRequest).toBeTruthy();
        expect(approvalRequest.edits).toBe('Edited draft');
    });

    test('should navigate back to queue on back button click', async ({ page }) => {
        await page.route('**/api/hitl/queue/item-1', route => route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: 'item-1',
                type: 'chat',
                timestamp: new Date().toISOString(),
                userQuestion: 'Test question',
                aiDraft: 'Test draft',
                botName: 'Support Bot',
                confidence: 0.65,
                timeInQueue: '5m',
                citations: [],
                contextChunks: [],
                status: 'pending',
                source: 'chatbot',
            }),
        }));

        await page.goto('/inbox/item-1');
        await page.waitForLoadState('networkidle');

        // Click back button
        await page.locator('button', { hasText: 'Back to Queue' }).click();

        // Should navigate to inbox
        await expect(page).toHaveURL(/\/inbox$/);
    });
});

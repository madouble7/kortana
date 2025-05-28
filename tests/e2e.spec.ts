import { expect, test } from '@playwright/test';

test('kor\'tana end-to-end chat', async ({ page }) => {
    // Add a longer delay to ensure server is ready
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log('Navigating to frontend...');
    // 1️⃣ Frontend loads - go to root with increased timeout
    await page.goto('http://localhost:3010/', { timeout: 60000 });

    console.log('Waiting for page content...');
    // Take a screenshot of the initial page state
    await page.screenshot({ path: 'initial-page.png' });

    // Wait for any content to load
    await page.waitForSelector('body', { timeout: 60000 });
    console.log('Body loaded');

    // Wait for the main chat interface to load with increased timeout
    console.log('Waiting for main chat interface...');
    await expect(page.locator('[data-test="lobechat-main"]')).toBeVisible({ timeout: 60000 });

    // Wait for loading state to complete
    console.log('Waiting for loading state to complete...');
    await page.waitForSelector('.lobe-brand-loading', { state: 'hidden', timeout: 60000 });
    await page.waitForTimeout(2000); // Give extra time for UI to stabilize

    // Take a screenshot after loading
    await page.screenshot({ path: 'after-loading.png' });

    // 2️⃣ Open provider dropdown
    console.log('Opening provider dropdown...');
    await page.click('[data-test="provider-dropdown"]');

    // Wait for the dropdown menu to be visible
    const dropdown = await page.locator('.ant-dropdown');
    await dropdown.waitFor({ state: 'visible', timeout: 10000 });

    // Take a screenshot of the dropdown
    await page.screenshot({ path: 'dropdown-open.png' });

    // Log the dropdown contents
    console.log('Dropdown HTML:', await dropdown.innerHTML());

    // Find and click the Kor'tana option by role and text content
    const kortanaOption = await page.getByRole('menuitem').filter({ hasText: /kor'tana/i });
    await kortanaOption.waitFor({ state: 'visible', timeout: 10000 });
    await kortanaOption.click();

    // 3️⃣ Send a message
    console.log('Sending a test message...');
    const chatInput = await page.locator('[data-test="chat-input"]');
    await chatInput.fill('Hello, this is a test message');
    await chatInput.press('Enter');

    // Wait for response
    await page.waitForTimeout(5000);
}); 
#!/usr/bin/env node

/**
 * Unseal Kor'tana Runtime
 * Auto-enters "I AM" elevation phrase to unlock Cloud Run instance
 */

const puppeteer = require("puppeteer");

async function unsealKortana() {
    const deployUrl =
        "https://kor-tana-780422883904.us-west1.run.app";
    const elevationPhrase = "I AM";

    try {
        console.log("🔓 Unsealing Kor'tana runtime...");
        console.log(`   Target: ${deployUrl}`);

        const browser = await puppeteer.launch({
            headless: "new",
            args: ["--disable-setuid-sandbox", "--disable-gpu"],
        });

        const page = await browser.newPage();
        await page.goto(deployUrl, { waitUntil: "networkidle2" });

        console.log("✓ Page loaded");

        // Wait for elevation input
        await page.waitForSelector("input[name='phrase'], input[placeholder*='phrase'], input[placeholder*='I AM']", {
            timeout: 5000,
        });

        console.log("✓ Found elevation input");

        // Type the phrase
        await page.type(
            "input[name='phrase'], input[placeholder*='phrase'], input[placeholder*='I AM']",
            elevationPhrase
        );

        console.log(`✓ Entered phrase: "${elevationPhrase}"`);

        // Click submit button
        await page.click(
            "button[data-action='unseal'], button[type='submit'], button:contains('Unseal')"
        );

        console.log("✓ Submitted elevation request");

        // Wait for success
        await page.waitForNavigation({ timeout: 3000 }).catch(() => { });

        console.log("✓ Runtime unsealed successfully!");
        console.log("   Kor'tana is now online and accessible.");

        await browser.close();
        process.exit(0);
    } catch (error) {
        console.error(
            "✗ Failed to unseal runtime:",
            error.message
        );
        process.exit(1);
    }
}

unsealKortana();

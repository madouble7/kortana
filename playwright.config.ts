import { defineConfig } from '@playwright/test';

export default defineConfig({
    // ... existing config ...
    projects: [
        {
            name: 'e2e',
            testMatch: /tests\/e2e.spec.ts$/,
        },
    ],
    // ... existing code ...
}); 
export default defineConfig({
    test: {
        include: ['src/**/*.test.mts'],
        environment: 'jsdom',
    },
}); 
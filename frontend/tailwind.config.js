/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        kor: {
          deep: '#0f0f1e',
          accent: '#00d4ff',
          surface: '#1a1a2e',
        }
      }
    },
  },
  plugins: [],
}

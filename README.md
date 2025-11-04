# Kor'tana - GitHub Issue Analyzer

A modern, dark-themed React application that connects to GitHub and analyzes repository issues.

![Kor'tana UI](https://github.com/user-attachments/assets/e91ed7e9-64d4-4fa4-8dac-7c9d223350bd)

## Features

- 🔍 **Fetch GitHub Issues**: Enter any GitHub repository URL (e.g., `owner/repo` or `https://github.com/owner/repo`) to fetch the 15 most recent open issues
- 📊 **Issue Display**: View issues with their title, number, author, creation date, and labels
- 🎨 **Modern Dark Theme**: Beautiful dark-themed UI built with Tailwind CSS
- 🤖 **Kor'tana Integration**: Each issue has an "Analyze with Kor'tana" button ready for Gemini API integration
- 🚀 **Fast & Responsive**: Built with React, TypeScript, and Vite for optimal performance

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Next-generation frontend tooling
- **GitHub REST API** - For fetching repository issues

## Getting Started

### Prerequisites

- Node.js 16+ and npm

### Installation

1. Clone the repository:
```bash
git clone https://github.com/KOR-TANA/kortana.git
cd kortana
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm run preview` - Preview the production build
- `npm run lint` - Run ESLint to check code quality

## Usage

1. Enter a GitHub repository in the format `owner/repo` (e.g., `facebook/react`) or paste a full GitHub URL
2. Click "Fetch Issues" to retrieve the latest open issues
3. Browse through the issues displayed with their details
4. Click "Analyze with Kor'tana" on any issue to trigger analysis (Gemini API integration placeholder)
5. Click "View on GitHub" to open the issue directly on GitHub

## Architecture

### Component Structure

```
src/
├── App.tsx                           # Main application component
├── components/
│   └── GitHubIssueAnalyzer.tsx      # GitHub issue fetcher and analyzer
├── index.tsx                         # Application entry point
└── index.css                         # Global styles with Tailwind
```

### Key Features Implementation

- **GitHub API Integration**: Uses the official GitHub REST API to fetch issues without authentication (public repositories only)
- **Error Handling**: Displays user-friendly error messages for various scenarios (repo not found, rate limits, etc.)
- **Responsive Design**: Fully responsive layout that works on desktop and mobile devices
- **Loading States**: Visual feedback during API calls with loading spinners
- **Label Styling**: Dynamic label colors using GitHub's label color scheme

## Future Enhancements

- [ ] Integrate with Google Gemini API for issue analysis
- [ ] Add authentication for private repositories
- [ ] Implement issue filtering and sorting
- [ ] Add issue search functionality
- [ ] Cache issues locally for offline viewing
- [ ] Export issues to various formats (CSV, JSON)
- [ ] Add pagination for repositories with many issues
- [ ] Implement issue comments viewer

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## About

Kor'tana is a GitHub issue analyzer that helps developers understand and triage repository issues more effectively.

import GitHubIssueAnalyzer from './components/GitHubIssueAnalyzer'

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-600 text-transparent bg-clip-text">
            Kor'tana
          </h1>
          <p className="text-gray-400 text-lg">GitHub Issue Analyzer</p>
        </header>
        <main>
          <GitHubIssueAnalyzer />
        </main>
      </div>
    </div>
  )
}

export default App

import { FractalDashboard } from './components/FractalDashboard';
import GitHubIssueAnalyzer from './components/GitHubIssueAnalyzer';

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col md:flex-row">
      {/* Primary Left Pane: Existing App */}
      <div className="container mx-auto px-4 py-8 flex-1">
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-600 text-transparent bg-clip-text">
            Kor'tana API & Task Analyzer
          </h1>
          <p className="text-gray-400 text-lg">Phase 10: Vanguard Manifestation</p>
        </header>
        <main>
          <GitHubIssueAnalyzer />
        </main>
      </div>

      {/* Secondary Right Pane: Fractal Swarm Dashboard */}
      <div className="w-full md:w-[400px] lg:w-[500px] border-t md:border-t-0 md:border-l border-gray-800">
        <FractalDashboard />
      </div>
    </div>
  );
}

export default App;

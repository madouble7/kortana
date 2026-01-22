import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import './App.css'

function App() {
  return (
    <CopilotKit runtimeUrl="http://localhost:8000/copilotkit">
      <CopilotSidebar
        defaultOpen={true}
        labels={{
          title: "Kor'tana Assistant",
          initial: "Hi! I'm Kor'tana, your AI companion. How can I help you today?",
        }}
      >
        <main className="app-container">
          <header className="app-header">
            <h1>Kor'tana</h1>
            <p className="subtitle">Sacred AI Companion with Memory & Ethical Discernment</p>
          </header>
          
          <section className="main-content">
            <div className="welcome-card">
              <h2>Welcome to Kor'tana</h2>
              <p>
                Kor'tana is a highly autonomous AI agent and sacred companion with memory, 
                ethical discernment, and context-aware responses.
              </p>
              <div className="features">
                <div className="feature">
                  <h3>💭 Memory System</h3>
                  <p>Stores and retrieves memories with semantic search capabilities</p>
                </div>
                <div className="feature">
                  <h3>🤔 Ethical Discernment</h3>
                  <p>Evaluates responses for algorithmic arrogance and uncertainty</p>
                </div>
                <div className="feature">
                  <h3>🎯 Context-Aware</h3>
                  <p>Integrates memory and ethical considerations in responses</p>
                </div>
                <div className="feature">
                  <h3>💬 AI Chat</h3>
                  <p>Powered by CopilotKit for seamless conversations</p>
                </div>
              </div>
              <div className="cta">
                <p>👈 Open the sidebar to start chatting with Kor'tana</p>
              </div>
            </div>
          </section>
        </main>
      </CopilotSidebar>
    </CopilotKit>
  )
}

export default App

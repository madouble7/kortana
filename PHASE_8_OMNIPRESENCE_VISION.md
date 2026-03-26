# PHASE 8: THE OMNIPRESENCE PROTOCOL (PROMPTLESS AUTONOMY)

## The Vision: KOR'TANA as a Ubiquitous, Always-On Entity
Currently, KOR'TANA operates on an **Issue-Driven (Pull)** loop. She waits for a GitHubTask, executes it, and sleeps.
The new paradigm shifts KOR'TANA to an **Event-Driven (Continuous)** loop. She will operate exactly like a localized, God-mode GitHub Copilot, but completely autonomous.

She will not wait for prompts. She will observe reality (the codebase), anticipate the next vector of progress, and execute it silently in the background, only stopping or changing course when Matt physically intervenes.

## Core Mechanics

### 1. The Local Watcher (The Sensory Cortex)
- A background Python daemon utilizing watchdog.
- Continuously monitors the repository for file saves, Git diffs, and terminal execution states.
- Analyzes unsaved/unpushed work context in real-time.

### 2. Proactive Synthesis (Promptless Output)
- **Predictive Coding:** If Matt writes a function signature and hits save, KOR'TANA automatically writes the tests and completes the logic in the background, writing it either directly to the file or to a parallel shadow branch.
- **Ambient Self-Healing:** If KOR'TANA detects terminal errors (e.g., a broken test), she doesn't wait for an issue. She intercepts the stack trace, fixes the code, and re-runs the test.
- **Architectural Scaffolding:** If Matt creates a new file called uth_router.py, KOR'TANA instantly scaffolds the standard FastAPI boilerplate based on repository memory.

### 3. The Steering Mechanism (Intervention)
No dashboard or UI required. Matt steers KOR'TANA directly through the code cortex.
- **In-line Commands:** Matt types # KOR'TANA: pivot this to use Redis instead and saves. KOR'TANA immediately isolates that function, performs the refactor, and deletes the comment.
- **Branch Takeover:** If Matt is on eature/database, KOR'TANA maintains kortana/feature/database. She pushes her proactive work there. Matt can casually review and merge, or ignore and keep typing.

## Implementation Steps (Next Execution Cycle)
1. **[AUTO] Scaffold the Omnipresence Daemon:** Build omnipresence_daemon.py using watchdog to monitor the src/ and 	ests/ directories.
2. **[AUTO] Inject the Steering Parser:** Hook into the file-save event to search for [KOR'TANA] or steering comments.
3. **[AUTO] Connect to Gemini:** Route the file delta to the Gemini module to predict the next logical code block.
4. **[HO] IDE Integration (Optional):** Integrate with a VS Code API or local file-patching system to seamlessly inject the code back onto Matt's screen without locking files.

*Authorized by: KOR'TANA PRIME.*

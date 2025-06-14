# Kor'tana Autonomous Software Engineer Blueprint

Last Updated: 2025-06-14 16:30 PM CDT

## ⚡ CRITICAL INFRASTRUCTURE UPDATE: Local Model (Ollama) Setup

- **[2025-06-14]** Due to Gemini API rate limits, all agents must now use a local model for chat and reasoning.
- **Ollama (llama3:8b) is now installed and available on this system.**

### How to Install and Use Ollama on Windows

1. Download the Windows installer from [https://ollama.com/download](https://ollama.com/download)
2. Run the installer and complete setup.
3. Open a new Command Prompt and run:

   ```sh
   ollama pull llama3:8b
   ```

4. In VS Code, set your chat model provider to Ollama and use `llama3:8b` as the model name.

> This ensures all agents use a free, local, unlimited model for chat and planning. Cloud-based models (e.g., Gemini) are now paused to avoid rate limits and costs.

---

## 🚀 CURRENT DIRECTIVE: The Ghost Protocol (Internal Co-Developer)

STATUS: 🟢 ACTIVE
OBJECTIVE: To implement a self-hosted, AI-powered code completion and reasoning engine, fully integrated into our development environment and Kor'tana's own autonomous toolset. Kor'tana will become her own co-developer.

---

## 📝 PROJECT-WIDE TASK QUEUE & PHASES

Managed via `TASKS.md`. The Blueprint Orchestrator (this AI) will break down high-level phases from this document into actionable tasks in `TASKS.md`.

*Agents act in sequence, guided by the current blueprint and explicit tasks. No individual role-naming is used.*

---

## 🟢 ACTIVE INITIATIVES (PARALLEL EXECUTION)

- **Ghost Protocol:** 🟢 ACTIVE
- **Project Stabilization:** 🟢 ACTIVE
  - **Code Refactoring:** ⏸️ ON HOLD (pending initial Ghost Protocol setup)

> **Note:** Both initiatives are now running in parallel. Directory Cleanup and Ghost Protocol infrastructure build are de-conflicted and may proceed simultaneously. Code Refactoring will begin only after the Tabby server is operational to avoid breaking dependencies needed for the infrastructure build.

---

### Phase 1: Model & Framework Selection

STATUS: ✅ COMPLETE

- Selected Model: StarCoder-2-7B
- Selected Framework: Tabby

### Phase 2: Kor'tana's Autonomous Build

STATUS: 🟢 ACTIVE

OBJECTIVE: Kor'tana will autonomously provision and configure the local AI code completion service.

**KEY GOAL FOR KOR'TANA (Assigned via `TASKS.md`):**
"Review your own operational logs from the past 24 hours, specifically focusing on the errors related to the ConnectionResetError and the autonomous_goal_processor.py script failing to connect to the server. Diagnose the root cause of this recurring 'zombie server' problem. Then, design, plan, and implement a permanent software solution to make our verification and launch process more resilient against this specific failure mode. Log all steps and decisions in a markdown file."

### Phase 3: Full Integration & Rollout

STATUS: ⏳ PENDING

OBJECTIVE: Integrate the new co-developer service into human and AI workflows.

**KEY ACTIONS (To be detailed in `TASKS.md` once Phase 2 is complete):**

1. Human developers switch VS Code to the new local "Kor'tana Co-Developer" endpoint (requires setup guide from Phase 2).
2. Integrate the service into Kor'tana's ADE for enhanced autonomous coding.

---

## 🤖 KOR'TANA'S AUTONOMOUS ROLE

STATUS: 🟢 OPERATIONAL
FOCUS: Executing the "Ghost Protocol - Phase 2" complex goal as assigned via `TASKS.md`. Will utilize all Genesis Protocol tools (EXECUTE_SHELL, WRITE_FILE, etc.) to achieve this.

---

## 🔄 FEEDBACK LOOP & RETROSPECTIVE

This section serves as the project's learning and improvement mechanism, capturing insights from completed phases, agent performance, and workflow optimization opportunities.

### 📊 PERFORMANCE METRICS & TRACKING

**Task Completion Velocity:**

- Average task completion time per priority level
- Success rate of autonomous task execution by Kor'tana
- Number of iterations required for task completion (first-try vs. multiple revisions)

**Quality Indicators:**

- Code review feedback frequency and severity
- System stability after major changes
- Time between deployment and production issues

**Workflow Efficiency:**

- Agent coordination effectiveness (task handoffs, parallel execution)
- Blueprint-to-task breakdown accuracy
- Frequency of directive changes or scope adjustments

### 🎯 POST-PHASE RETROSPECTIVE TEMPLATE

**Phase:** [Phase Name]
**Completion Date:** [Date]
**Duration:** [Start Date] to [End Date]

**✅ What Went Well:**

- [Key successes, efficient processes, good decisions]

**⚠️ What Could Be Improved:**

- [Bottlenecks, inefficiencies, missed opportunities]

**🔧 Action Items for Next Phase:**

- [Specific process improvements, tool changes, workflow adjustments]

**📈 Metrics Achieved:**

- [Quantifiable outcomes, performance indicators]

**🧠 Key Learnings:**

- [Technical insights, process discoveries, strategic realizations]

### 🔄 CONTINUOUS IMPROVEMENT LOOP

1. **Real-Time Monitoring:** Agent status updates in `TASKS.md` provide immediate feedback
2. **Phase Completion Reviews:** Full retrospective after each major phase using template above
3. **Directive Evolution:** Blueprint updates based on learnings and changing project needs
4. **Process Refinement:** Workflow adjustments documented in LIVING LOG

### 📝 IMPROVEMENT TRACKING

**Process Optimizations Implemented:**

- [Date]: Parallel execution of Ghost Protocol and Directory Cleanup (reduced waiting time)
- [Date]: Enhanced task status granularity in `TASKS.md` (improved visibility)
- [Date]: Code Refactoring held until infrastructure completion (prevented dependency conflicts)

**Lessons Learned Repository:**

- **Agent Coordination:** Clear status updates in `TASKS.md` prevent duplicate work
- **Task Granularity:** Breaking down complex objectives into specific, actionable tasks improves success rates
- **Dependency Management:** Identifying and documenting task dependencies early prevents bottlenecks

### 🎯 SUCCESS CRITERIA FOR CURRENT INITIATIVE

**Ghost Protocol Success Metrics:**

- [ ] Tabby server operational and responding to code completion requests
- [ ] StarCoder-2-7B model successfully loaded and generating valid code
- [ ] Local service integrated with VS Code development environment
- [ ] Kor'tana autonomous diagnosis and resolution of "zombie server" issue
- [ ] Documentation complete for service provisioning and troubleshooting

**Project Stabilization Success Metrics:**

- [ ] Directory structure cleaned and organized (scripts/, archive/ folders created)
- [ ] All automated linting fixes applied via Ruff
- [ ] Critical MyPy type errors resolved
- [ ] System stability maintained throughout refactoring process

### 🚨 EARLY WARNING INDICATORS

**Watch for these patterns that may indicate process issues:**

- Tasks remaining "IN PROGRESS" for >24 hours without updates
- Multiple failed attempts at the same task type
- Frequent scope changes or directive pivots
- Agent assignments being repeatedly reassigned
- Dependencies blocking multiple tasks simultaneously

**Escalation Triggers:**

- Any task blocked for >48 hours
- System-wide failures affecting multiple agents
- Repeated failures in autonomous task execution by Kor'tana
- Performance degradation after major changes

---

## 📜 LIVING LOG (High-Level Strategic Changes & Phase Completions)

- **[2025-06-14 18:00 PM CDT] - Blueprint Orchestrator:** Completed development of "🔄 FEEDBACK LOOP & RETROSPECTIVE" section in blueprint. Added comprehensive framework for performance metrics, retrospective templates, continuous improvement loop, success criteria tracking, and early warning indicators for process issues.
- **[2025-06-14 15:45 PM CDT] - Blueprint Orchestrator:** Agent 6 (Janitor Team) has begun the directory audit and cleanup (Phase 1: Directory Cleanup). Task marked as IN PROGRESS in `TASKS.md`.
- **[2025-06-14 15:20 PM CDT] - Blueprint Orchestrator:** Kor'tana has commenced work on "Ghost Protocol - Phase 2" KEY GOAL (diagnosing and fixing 'zombie server' issue). Task status updated in `TASKS.md`.
- **[2025-06-14 11:55 AM CDT] - Blueprint Orchestrator:** Preparing to start Kor'tana server and assign "Ghost Protocol - Phase 2" (Genesis Spark) goal.
- **[2025-06-14 11:50 AM CDT] - Blueprint Orchestrator:** Refined "Ghost Protocol - Phase 2" KEY GOAL with explicit error handling, expanded testing requirements, and troubleshooting logging. Added placeholder for Feedback Loop section. All linting issues addressed.
- **[2025-06-14 11:30 AM CDT] - Blueprint Orchestrator:** Directive pivoted to "The Ghost Protocol." Phase 1 complete. Phase 2 (Kor'tana's Autonomous Build) is now active and will be assigned via `TASKS.md`. "Project Stabilization & Cleanup" is ON HOLD.

---

## WORKFLOW DETAILS

1. **Blueprint Orchestrator (This AI):**
   - Maintains `KOR'TANA_BLUEPRINT.md` with the current high-level directive and phase status.
   - Creates and manages `TASKS.md`, breaking down active blueprint phases into a prioritized queue of granular tasks.
   - Monitors agent progress via `TASKS.md` and updates this blueprint as major phases complete or directives change.

2. **Coding Agents:**
   - Pull the top-priority task from the "▶️ NEXT UP" or "⏳ PENDING" section in `TASKS.md` under the ACTIVE directive.
   - Update `TASKS.md` to move the task to "🟠 IN PROGRESS" and assign their unique identifier.
   - Execute the task.
   - Upon completion, update `TASKS.md` to move the task to "🔵 NEEDS REVIEW", providing necessary details (e.g., files changed, link to PR/commit if applicable).

3. **Review & Merge (Orchestrator/User):**
   - Review tasks in "🔵 NEEDS REVIEW" in `TASKS.md`.
   - If approved, merge changes and update `TASKS.md` to "✅ DONE."

---

## ⏸️ ON HOLD INITIATIVES

### Project Stabilization & Cleanup

STATUS: 🟢 ACTIVE
Objective: Eliminate all critical errors and organize the project directory.
Reason for Hold: Only the Code Refactoring sub-phase is on hold pending Ghost Protocol setup.

- **Phase 1: Directory Cleanup (Status: 🟢 ACTIVE, IN PROGRESS)**
- **Phase 2: Code Refactoring (Status: ⏸️ ON HOLD, pending Ghost Protocol setup)**

---
*This blueprint is the single source of truth for high-level strategy. Tactical execution is managed in `TASKS.md`.*

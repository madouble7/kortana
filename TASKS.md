# Kor'tana - Active Task Queue

*Last Updated: 2025-06-14 19:45 PM CDT*

---

> **Note:** "The Ghost Protocol" and "Project Stabilization & Cleanup" are running in parallel. The Refactor Team will now begin systematic code quality improvements.

## 🚀 ACTIVE DIRECTIVE: The Ghost Protocol (Internal Co-Developer)

### **Phase 1: Model & Framework Selection**

STATUS: ✅ COMPLETE

| Priority | Task Description                                     | Status    | Agent      | Notes / PR Link |
| :------- | :--------------------------------------------------- | :-------- | :--------- | :-------------- |
| 1        | Research & Decide on LLM for Code Completion         | ✅ DONE   | Orchestrator | StarCoder-2-7B  |
| 2        | Research & Decide on Self-Hosting Framework        | ✅ DONE   | Orchestrator | Tabby           |

### **Phase 2: Kor'tana's Autonomous Build**

STATUS: 🟢 ACTIVE

| Priority | Task Description                                                                                                                                                                                                                                                                                                                                                                                       | Status           | Agent     | Notes / PR Link |
| :------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------- | :-------- | :-------------- |
| 0        | Start Kor'tana Server (Prerequisite for Goal Assignment)                                                                                                                                                                                                                                                                                                                                                        | ✅ DONE          | Orchestrator | Server started successfully. |
| 1        | **ASSIGN TO KOR'TANA:** "Review your own operational logs from the past 24 hours, specifically focusing on the errors related to the ConnectionResetError and the autonomous_goal_processor.py script failing to connect to the server. Diagnose the root cause of this recurring 'zombie server' problem. Then, design, plan, and implement a permanent software solution to make our verification and launch process more resilient against this specific failure mode. Log all steps and decisions in a markdown file." | 🟠 IN PROGRESS | Kor'tana   |                 |
| 2        | **Ghost Protocol - Phase 2 Infrastructure Build:** "Provision a new local service for AI code completion using the Tabby framework and StarCoder-2-7B model. Set up the infrastructure, download the model, and create all required config files. Document the process and ensure the service is operational. Do not modify existing Python source code at this stage." | 🟠 IN PROGRESS | Agent 5   | Infrastructure build running in parallel with Directory Cleanup. |
| 3        | **ASSIGN TO KOR'TANA:** "Provision a new local service for AI code completion. The service must use the Tabby framework to host the StarCoder-2-7B model. Configure the service to run locally. Document the entire process, including all commands, configurations, and troubleshooting steps, in a dedicated markdown file. Identify and log any errors encountered during setup; attempt self-correction and document all resolutions. For validation, confirm the service is operational by using it to generate a simple function (e.g., `def add(a, b): return a + b`) and a multi-line code block (e.g., a class definition with a method) in a test file. Ensure the generated code is functional." | ⏳ PENDING      | Kor'tana   | Aligns with Phase 2 Objective |

### **Phase 3: Full Integration & Rollout**

STATUS: ⏳ PENDING (Activates after Phase 2 is complete)

| Priority | Task Description                                                                 | Status    | Agent     | Notes / PR Link |
| :------- | :------------------------------------------------------------------------------- | :-------- | :-------- | :-------------- |
| 1        | Human developers switch VS Code to the new local "Kor'tana Co-Developer" endpoint. | ⏳ PENDING | N/A       |                 |
| 2        | Integrate the service into Kor'tana's ADE for enhanced autonomous coding.        | ⏳ PENDING | Kor'tana  |                 |

---

## 🧹 ACTIVE DIRECTIVE: Project Stabilization & Cleanup

### **Phase 1: Directory Cleanup**

STATUS: 🟢 ACTIVE

| Priority | Task Description                                                                                                | Status        | Agent      | Notes / PR Link |
| :------- | :-------------------------------------------------------------------------------------------------------------- | :------------ | :--------- | :-------------- |
| 1        | Consolidate remaining markdown, batch, and command files from project root into `scripts/` or `archive/` as appropriate. | 🟠 IN PROGRESS | Agent 6    |                 |
| 2        | Update `README.md` with a clear description of the new `scripts/` and `archive/` directory structure.         | ⏸️ ON HOLD    |            |                 |
| 3        | Perform a final scan of the project root to ensure all specified items are moved. Report completion of Phase 1. | ⏸️ ON HOLD    |            |                 |

### **Phase 2: Code Refactoring**

STATUS: 🟢 ACTIVE

| Priority | Task Description                                                                 | Status        | Agent          | Notes / PR Link |
| :------- | :------------------------------------------------------------------------------- | :------------ | :------------- | :-------------- |
| 1        | Unify KortanaConfig schema in `src/kortana/config/schema.py`.                    | ✅ DONE       | Lead Dev       | Consolidated root and src schemas. |
| 2        | Consolidate PlanningAgent and CovenantEnforcer logic in `src/kortana/`.          | ✅ DONE       | Lead Dev       | Merged duplicate agents and enforcers. |
| 3        | Update `main.py` entry point to use unified ChatEngine and Config.              | ✅ DONE       | Lead Dev       | Root API now uses consolidated brain. |
| 4        | Synchronize dependencies in `requirements.txt`.                                  | ✅ DONE       | Lead Dev       | Synced with pyproject.toml info. |
| 5        | Address missing `dev_agent_instance` parameter in `PlanningAgent`.              | ✅ DONE       | Lead Dev       | Handled via getattr in autonomous_agents.py |
| 6        | Fix KortanaConfig type issue with `**raw_config` in `brain.py`.                 | ✅ DONE       | Lead Dev       | Fixed via unified schema and load_kortana_config. |
| 7        | Run `poetry install` to ensure consistent development environment.               | ⏸️ ON HOLD    |                | |
| 8        | Execute `poetry run ruff check . --fix` for automated linting fixes.             | ⏸️ ON HOLD    |                | |

---

## 🌀 PROCESS IMPROVEMENT & ORCHESTRATION TASKS

| Priority | Task Description                                                                                                | Status        | Agent      | Notes / PR Link |
| :------- | :-------------------------------------------------------------------------------------------------------------- | :------------ | :--------- | :-------------- |
| 1        | Develop the "🔄 FEEDBACK LOOP & RETROSPECTIVE" section in `KOR'TANA_BLUEPRINT.md` to improve project learning. | ✅ DONE       | Orchestrator | Added comprehensive retrospective framework with lessons learned, success metrics, and forward-looking improvements |

---

**Agent Instructions:**

1. Pick the highest priority "▶️ NEXT UP" or "⏳ PENDING" task from an **ACTIVE DIRECTIVE**.
2. Update its status to "🟠 IN PROGRESS" and add your identifier (e.g., "Agent-Alpha", "Kor'tana-Core") in the "Agent" column.
3. Execute the task.
4. Upon completion, change status to "🔵 NEEDS REVIEW" and add notes/PR link.
5. Once reviewed and merged, the Orchestrator/User will mark as "✅ DONE".

**Key:**

* **NEXT UP**: Task is ready to be picked up.
* **IN PROGRESS**: Task is currently being worked on.
* **NEEDS REVIEW**: Task is complete and awaiting review/merge.
* **DONE**: Task is completed and merged.
* **PENDING**: Task is blocked or waiting for prerequisites.
* **ON HOLD**: Task is part of a paused initiative or phase.

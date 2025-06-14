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
STATUS: ⏸️ ON HOLD (pending Tabby server setup)

| Priority | Task Description                                                                 | Status        | Agent          | Notes / PR Link |
| :------- | :------------------------------------------------------------------------------- | :------------ | :------------- | :-------------- |
| 1        | Fix missing `get_memory_manager` function in import chain for `brain.py`.        | ⏸️ ON HOLD    |                | Error identified but fix waiting for infrastructure completion |
| 2        | Fix `ChatEngine` class missing attributes in `brain.py` (project_memory, pinecone_memory, json_memory).  | ⏸️ ON HOLD    |                | Missing attributes identified and documented |
| 3        | Address missing `dev_agent_instance` parameter in `PlanningAgent`.              | ⏸️ ON HOLD    |                | Parameter requirement identified |
| 4        | Fix KortanaConfig type issue with `**raw_config` in `brain.py`.                 | ⏸️ ON HOLD    |                | Type error identified on line 726 |
| 5        | Run `poetry install` to ensure consistent development environment.               | ⏸️ ON HOLD    |                | Will resume after infrastructure setup |
| 6        | Execute `poetry run ruff check . --fix` for automated linting fixes.             | ⏸️ ON HOLD    |                | Will resume after infrastructure setup |
| 7        | Run `poetry run ruff check .` and save output to `ruff_issues.txt`.              | ⏸️ ON HOLD    |                | Will resume after infrastructure setup |
| 8        | Run `poetry run mypy .` and save output to `mypy_issues.txt`.                    | ⏸️ ON HOLD    |                | Will resume after infrastructure setup |
| 9        | Systematically address remaining Ruff and MyPy errors, module by module.         | ⏸️ ON HOLD    |                | Will resume after infrastructure setup |

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

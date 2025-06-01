# Kor'tana Agent Relay & Torch System

This system manages agent registration, status reporting, and logs 'torch pass' handoff events between agents. It's designed to provide visibility into multi-agent interactions and state transitions, with a special emphasis on capturing detailed contextual and "soulful" information during handoffs via Torch Packages.

## Features

*   **Agent Status Tracking**: In-memory tracking of registered agents, including their ID, status (currently always 'active'), version, and the timestamp of their last handoff event.
*   **Detailed Handoff Logging**: Comprehensive logging of "torch passes" (handoffs) between agents. Each handoff event records basic information initially, which is then updated with a summary from the detailed Torch Package.
*   **Dual Logging System for Basic Handoffs**: Basic handoff details are logged to:
    *   A plain text file (`logs/torch_log.txt`) for easy human reading and tailing.
    *   An SQLite database (`logs/kortana.db`, in the `torch_passes` table) for structured querying and persistence.
*   **Detailed Torch Package Protocol**: Interactive prompting during handoff for a comprehensive 'Torch Package', capturing detailed context, agent identity, and reflections on Kor'tana (see `relays/torch_template.py` for structure). These packages are saved as JSON files and linked in the database.
*   **Command-Line Interface (CLI)**: Scripts provide CLI options to view current agent statuses and the history of torch passes, indicating which passes have detailed packages.

## Project Structure

```
.
├── logs/
│   ├── kortana.db      # SQLite database for torch passes
│   └── torch_log.txt   # Plain text log for basic torch pass info
├── relays/
│   ├── __init__.py     # Makes 'relays' a package
│   ├── handoff.py      # Logic for performing and logging handoffs, including Torch Package creation
│   ├── relay.py        # Agent registration, status, and CLI for viewing logs/status
│   └── torch_template.py # Defines the structure of a detailed Torch Package
├── state/
│   └── # Directory for storing saved Torch Package JSON files
└── tests/
    ├── __init__.py     # Makes 'tests' a package
    ├── test_handoff.py # Unit tests for handoff.py
    └── test_relay.py   # Unit tests for relay.py
```

## Usage

All commands should typically be run from the root directory of the project.

### Agent Status

To view the current status of all registered agents (active in memory):

```bash
python relays/relay.py --status
```

The output will typically look like this for each agent:

`Agent ID: <agent_id>, Status: <status>, Version: <version>, Last Handoff: <timestamp>`

*Example:*
`Agent ID: Agent001, Status: active, Version: 1.1, Last Handoff: 2023-10-27 10:00:00.123456`

### Torch Handoff Log

To view the chronological log of all torch pass events from the database:

```bash
python relays/relay.py --torch-log
```

Each log entry will be displayed in a format similar to:

`[<Timestamp>] <Outgoing Agent> -> <Incoming Agent> (v<Version>): <Summary> | Tokens: <Token Count> | Msg: <Message to Successor>`

Entries in this log that have an associated detailed Torch Package will be marked with `[+package]` at the end of the line.

*Example with package:*
`[2023-10-27 10:00:00.123456] Agent001 -> Agent002 (v1.1): Regular handoff | Tokens: 1500 | Msg: Keep up the good work! [+package]`

*(A future update may allow viewing the full package directly via a command.)*

## Detailed Torch Package Protocol

During each handoff initiated by `python -m relays.handoff`, the system now prompts the user (simulating the outgoing agent) to fill out a detailed Torch Package. This package is designed to capture not just operational context but also 'soulful' information, agent identity, lessons learned, and reflections on Kor'tana's development.

The user is guided through an interactive CLI process to fill various fields. Default values (pre-filled where possible from the initial handoff parameters) can be accepted by pressing Enter. For list fields, items are entered comma-separated; an empty space clears the list.

The full structure of this package, defining all expected fields, is located in `relays/torch_template.py`.

## Logging Details

Handoff events and Torch Packages are logged in multiple places:

*   **SQLite Database (`logs/kortana.db`)**:
    *   **`torch_passes` table**: Stores basic information about each handoff. The `summary` and `message_to_successor` fields are updated with information from the detailed Torch Package once it's completed.
        *   Schema: `id` (PK), `timestamp`, `outgoing_agent_name`, `incoming_agent_name`, `incoming_agent_version`, `summary`, `token_count_at_handoff`, `message_to_successor`.
    *   **`torch_packages` table**: Stores the complete JSON content of each detailed Torch Package, linked to the corresponding `torch_passes` entry via `torch_pass_id`, along with the filepath to the saved JSON file.
        *   Schema: `id` (PK), `torch_pass_id` (FK), `package_json` (TEXT), `filepath` (TEXT), `created_at`.
*   **Text File (`logs/torch_log.txt`)**:
    *   Each line represents a basic handoff event in a human-readable format. This log captures the initial state of the handoff.
*   **State Directory (`state/`)**:
    *   This directory stores the detailed Torch Package JSON files, named like `torch_<agent_name>_<timestamp>.json`. These files contain the full, rich context provided during the interactive handoff process.

## Running Handoffs (for testing/simulation)

The system includes a script to simulate a handoff event, which now includes the detailed Torch Package creation process.

To trigger a sample handoff:

```bash
python -m relays.handoff
```

This script executes a predefined test scenario located in its `if __name__ == '__main__':` block. This will:
1.  Register sample agents.
2.  Perform a handoff, logging basic details.
3.  Initiate the interactive CLI to fill the detailed Torch Package (in a non-interactive environment like automated testing, it will use defaults or pre-filled values).
4.  Save the completed Torch Package to a JSON file in `state/` and record its details in the `torch_packages` database table.
5.  Update the original `torch_passes` database entry with key information from the detailed package.
6.  Print information about these operations to the console.

## Running Tests

Unit tests are provided in the `tests/` directory.

To run the tests:

```bash
# For tests related to relay.py (agent status, log viewing)
python -m unittest tests.test_relay

# For tests related to handoff.py (handoff execution, Torch Package creation, logging)
python -m unittest tests.test_handoff
```

Make sure you are in the project's root directory. Tests will interact with the `logs/` and `state/` directories.

---
*This README provides an overview of the Kor'tana Agent Relay & Torch System. Refer to the source code for detailed implementation.*

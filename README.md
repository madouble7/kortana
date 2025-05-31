# Kor'tana Agent Relay & Torch System

This system manages agent registration, status reporting, and logs 'torch pass' handoff events between agents. It's designed to provide visibility into multi-agent interactions and state transitions.

## Features

*   **Agent Status Tracking**: In-memory tracking of registered agents, including their ID, status (currently always 'active'), version, and the timestamp of their last handoff event.
*   **Detailed Handoff Logging**: Comprehensive logging of "torch passes" (handoffs) between agents. Each handoff event records:
    *   Timestamp
    *   Outgoing agent's name
    *   Incoming agent's name
    *   Incoming agent's version
    *   A summary of the handoff
    *   Token count at the point of handoff
    *   An optional message to the successor agent
*   **Dual Logging System**: Handoffs are logged to:
    *   A plain text file (`logs/torch_log.txt`) for easy human reading and tailing.
    *   An SQLite database (`logs/kortana.db`, in the `torch_passes` table) for structured querying and persistence.
*   **Command-Line Interface (CLI)**: Scripts provide CLI options to view current agent statuses and the history of torch passes.

## Project Structure

```
.
├── logs/
│   ├── kortana.db      # SQLite database for torch passes
│   └── torch_log.txt   # Plain text log for torch passes
├── relays/
│   ├── __init__.py     # Makes 'relays' a package
│   ├── handoff.py      # Logic for performing and logging handoffs
│   └── relay.py        # Agent registration, status, and CLI for viewing logs/status
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

*Example:*
`[2023-10-27 10:00:00.123456] Agent001 -> Agent002 (v1.1): Regular handoff | Tokens: 1500 | Msg: Keep up the good work!`

## Logging Details

Handoff events are logged in two places:

*   **SQLite Database**: `logs/kortana.db`
    *   Table name: `torch_passes`
    *   Schema: `id` (PK), `timestamp`, `outgoing_agent_name`, `incoming_agent_name`, `incoming_agent_version`, `summary`, `token_count_at_handoff`, `message_to_successor`.
*   **Text File**: `logs/torch_log.txt`
    *   Each line represents a handoff event in a human-readable format.

## Running Handoffs (for testing/simulation)

The system includes a script to simulate a handoff event. This is useful for populating the logs for testing or demonstration.

To trigger a sample handoff:

```bash
python -m relays.handoff
```

This script executes a predefined test scenario located in its `if __name__ == '__main__':` block, which will:
1.  Register a sample outgoing agent.
2.  Perform a handoff to a sample incoming agent.
3.  Log this event to both the database and the text file.
4.  Print details of the handoff and the final state of registered agents to the console.

## Running Tests

Unit tests are provided in the `tests/` directory to ensure the core functionalities of agent registration, status updates, handoff logic, and logging work as expected.

To run the tests:

```bash
# For tests related to relay.py (agent status, log viewing)
python -m unittest tests.test_relay

# For tests related to handoff.py (handoff execution, logging)
python -m unittest tests.test_handoff
```

Make sure you are in the project's root directory when running these commands. The tests will create/clear log files and database entries in the `logs/` directory as part of their execution.

---
*This README provides an overview of the Kor'tana Agent Relay & Torch System. Refer to the source code for detailed implementation.*

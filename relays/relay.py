import argparse
import datetime
import time
import sqlite3
import os

AGENTS = {}
# Ensure paths are absolute from the script's location for robustness
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DB_PATH = os.path.join(REPO_ROOT, 'logs', 'kortana.db')


def register_agent(agent_id, version='1.0'):
  """Registers a new agent or updates an existing one. Updates last_handoff_time on each call."""
  AGENTS[agent_id] = {
    'status': 'active',
    'last_handoff_time': datetime.datetime.now(),
    'version': version
  }

def update_agent_handoff_time(agent_id, handoff_time):
  """Updates the last handoff time for a given agent."""
  if agent_id in AGENTS:
    AGENTS[agent_id]['last_handoff_time'] = handoff_time
  else:
    # This case should ideally not be hit if agents are registered before handoff
    print(f"Agent {agent_id} not found for handoff time update.")

def get_agent_status(agent_id):
  """Returns the status information for a specific agent."""
  return AGENTS.get(agent_id, None)

def get_all_agents_status():
  """Returns a formatted string representing the status of all registered agents."""
  if not AGENTS:
    return "No agents registered."

  status_report = []
  for agent_id, info in AGENTS.items():
    status_report.append(
      f"Agent ID: {agent_id}, Status: {info['status']}, Version: {info['version']}, Last Handoff: {info['last_handoff_time']}"
    )
  return "\n".join(status_report)

def get_torch_log_from_db():
  """
  Retrieves all torch handoff log entries from the database,
  including an indicator if a detailed torch package exists.
  Returns rows with: tp.id, tp.timestamp, tp.outgoing_agent_name,
  tp.incoming_agent_name, tp.incoming_agent_version, tp.summary,
  tp.token_count_at_handoff, tp.message_to_successor, has_detailed_package.
  """
  log_entries = []
  if not os.path.exists(DB_PATH):
    print(f"Database file not found at {DB_PATH}")
    return log_entries
  try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()
    query = """
    SELECT
        tp.id,
        tp.timestamp,
        tp.outgoing_agent_name,
        tp.incoming_agent_name,
        tp.incoming_agent_version,
        tp.summary,
        tp.token_count_at_handoff,
        tp.message_to_successor,
        CASE WHEN t_pkg.id IS NOT NULL THEN 1 ELSE 0 END AS has_detailed_package
    FROM
        torch_passes tp
    LEFT JOIN
        torch_packages t_pkg ON tp.id = t_pkg.torch_pass_id
    ORDER BY
        tp.timestamp
    """
    cursor.execute(query)
    log_entries = cursor.fetchall()
  except sqlite3.Error as e:
    print(f"Database error while fetching torch log: {e}")
  finally:
    if conn:
      conn.close()
  return log_entries

def display_torch_log(log_entries):
  """
  Prints the torch handoff log entries in a user-friendly format.
  Indicates if a detailed package is available.
  """
  if not log_entries:
    print("No torch handoff events found.")
    return

  print("\n--- Torch Handoff Log ---")
  for entry in log_entries:
    # Access by index or key based on conn.row_factory setting in get_torch_log_from_db
    # Since using sqlite3.Row, keys are 'timestamp', 'outgoing_agent_name', etc.
    # and 'has_detailed_package'

    ts = entry['timestamp']
    outgoing = entry['outgoing_agent_name']
    incoming = entry['incoming_agent_name']
    version = entry['incoming_agent_version']
    summary_val = entry['summary'] # Renamed to avoid conflict with summary module if imported
    tokens = entry['token_count_at_handoff']
    msg = entry['message_to_successor']
    has_pkg = entry['has_detailed_package']

    msg_str = f" | Msg: {msg}" if msg else ""
    pkg_indicator = " [+package]" if has_pkg == 1 else ""

    print(
      f"[{ts}] {outgoing} -> {incoming} (v{version}): "
      f"{summary_val} | Tokens: {tokens}{msg_str}{pkg_indicator}"
    )
  print("--- End of Log ---")

if __name__ == "__main__":
  # Sample agent registrations for testing --status
  if not AGENTS: # Avoid re-registering if script is imported elsewhere or run multiple times in a session
    register_agent("Agent001", version="1.1")
    time.sleep(0.1) # Simulate a slight delay for different timestamp
    register_agent("Agent002", version="1.0")

  parser = argparse.ArgumentParser(description="Relay agent status and torch log viewer.")
  parser.add_argument('--status', action='store_true', help='Display status of all registered agents.')
  parser.add_argument('--torch-log', action='store_true', help='Display all torch handoff log events from the database.')

  args = parser.parse_args()

  if args.status:
    print(get_all_agents_status())
  elif args.torch_log:
    log_entries = get_torch_log_from_db()
    display_torch_log(log_entries)
  else:
    # Default behavior: print help if no relevant arguments are passed.
    # parser.print_help()
    # For now, let's stick to no output if no specific command,
    # as per original behavior for --status.
    # If both --status and --torch-log are somehow passed, status takes precedence.
    # If only --torch-log is passed, it will be handled.
    # If neither, it will do nothing specific here.
    pass

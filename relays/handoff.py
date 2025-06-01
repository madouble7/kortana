from datetime import datetime, timezone
from relays.relay import register_agent, update_agent_handoff_time, AGENTS
from relays.torch_template import TORCH_PACKAGE_TEMPLATE
import sqlite3
import uuid
import copy
import os
import json # For pretty printing

# Define paths for database and log file
# Ensure paths are absolute from the script's location for robustness
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

DB_PATH = os.path.join(REPO_ROOT, 'logs', 'kortana.db')
LOG_FILE_PATH = os.path.join(REPO_ROOT, 'logs', 'torch_log.txt')
STATE_DIR = os.path.join(REPO_ROOT, 'state')


def prefill_torch_template(outgoing_agent_name, incoming_agent_name, incoming_agent_version, basic_torch_pass_summary, basic_torch_pass_tokens):
  """
  Pre-fills the TORCH_PACKAGE_TEMPLATE with initial data from a handoff event.
  Many fields are left blank for the user/agent to fill in detail.
  """
  package = copy.deepcopy(TORCH_PACKAGE_TEMPLATE)
  now_iso = datetime.now(timezone.utc).isoformat()

  package["task_id"] = str(uuid.uuid4())
  package["task_title"] = "Automated Handoff - Needs Detail" # Placeholder
  package["summary"] = basic_torch_pass_summary
  package["handoff_reason"] = "Routine Handoff - Needs Detail" # Placeholder
  # history_summary, system_prompt, code, issues, commit_ref left blank for user

  package["tokens"] = basic_torch_pass_tokens
  package["timestamp"] = now_iso

  # Agent Profile (Outgoing Agent's perspective)
  package["agent_profile"]["agent_name"] = outgoing_agent_name
  if outgoing_agent_name in AGENTS and 'version' in AGENTS[outgoing_agent_name]:
      package["agent_profile"]["agent_version"] = AGENTS[outgoing_agent_name]['version']
  else:
      package["agent_profile"]["agent_version"] = ""

  return package

def prompt_for_torch_package_details(package_data_param):
    """
    Interactively prompts the user to fill or update details for a Torch Package.
    The subtask environment might not support `input()` calls well.
    """
    package_data = copy.deepcopy(package_data_param)

    print("\n--- Detailed Torch Pass Report ---")
    print("Please fill out the following details for the Torch Pass.")
    print("Reflect on your experiences and be thorough in the 'soulful' sections.")
    print("This is a vital record for your successor and for Kor'tana's lineage.")
    print("Press Enter to accept the current value (shown in brackets []), or type your new value.")
    print("For list fields (e.g., issues, strengths), enter items separated by commas. To clear the list, enter an empty space then enter. To keep current, just press Enter.")
    print("-------------------------------------\n")

    def _prompt_recursive(current_data_level, path_prefix=""):
        for key, value in list(current_data_level.items()): # Use list() for safe iteration if modifying dict
            full_key_path = path_prefix + key

            if isinstance(value, dict):
                print(f"\n--- Editing section: {key} ---")
                _prompt_recursive(value, full_key_path + ".")
            elif isinstance(value, list):
                try:
                    user_input_str = input(f"Enter comma-separated items for '{full_key_path}' (current: {json.dumps(value)}): ")
                    if user_input_str: # If user provided any input
                        if user_input_str.strip() == "": # User entered whitespace, meaning clear the list
                            current_data_level[key] = []
                        else:
                            current_data_level[key] = [item.strip() for item in user_input_str.split(',') if item.strip()]
                    # Else: User pressed Enter, keep current (pass)
                except EOFError: # Handle non-interactive environment for testing
                    print(f"EOFError encountered for key '{full_key_path}'. Keeping current value: {json.dumps(value)}")
            else: # Strings, Integers, (Booleans not handled separately for now)
                try:
                    user_input_val = input(f"Enter value for '{full_key_path}' (current: [{value}]): ")
                    if user_input_val: # If user provided any input
                        if isinstance(value, int):
                            try:
                                current_data_level[key] = int(user_input_val)
                            except ValueError:
                                print(f"Invalid input for integer field '{full_key_path}'. Keeping current value: {value}")
                        else: # String
                            current_data_level[key] = user_input_val
                    # Else: User pressed Enter, keep current (pass)
                except EOFError: # Handle non-interactive environment for testing
                     print(f"EOFError encountered for key '{full_key_path}'. Keeping current value: {value}")

    _prompt_recursive(package_data)
    return package_data

def log_handoff_to_db(timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor=None):
  """Logs the handoff event to the SQLite database and returns the ID of the new row."""
  last_id = None
  try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
      INSERT INTO torch_passes (timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor))
    conn.commit()
    last_id = cursor.lastrowid
  except sqlite3.Error as e:
    print(f"Database error during initial log: {e}")
  finally:
    if conn:
      conn.close()
  return last_id

def log_handoff_to_file(timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor=None):
  """Logs the basic handoff event details to a text file."""
  try:
    with open(LOG_FILE_PATH, 'a') as f:
      log_entry = f"{timestamp} | OUT: {outgoing_agent_name} | IN: {incoming_agent_name} (v{incoming_agent_version}) | SUMMARY: {summary} | TOKENS: {token_count_at_handoff} | MSG: {message_to_successor if message_to_successor else ''}\n"
      f.write(log_entry)
  except IOError as e:
    print(f"File I/O error: {e}")

def perform_handoff(outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor=None):
  """
  Simulates a handoff, including detailed Torch Package creation and storage.
  The 'summary', 'token_count_at_handoff', and 'message_to_successor' parameters
  are for the initial basic log. The detailed package will refine these.
  """
  current_time_agents = datetime.now() # For agent status updates, non-UTC as before

  # 1. Update agent statuses and registration
  if outgoing_agent_name in AGENTS:
    update_agent_handoff_time(outgoing_agent_name, current_time_agents)
  else:
    # Register if not known, then update time
    register_agent(outgoing_agent_name, version="unknown")
    update_agent_handoff_time(outgoing_agent_name, current_time_agents)

  register_agent(incoming_agent_name, version=incoming_agent_version) # Sets its handoff time

  # 2. Initial basic logging to torch_passes table (and get its ID)
  # Using a potentially different timestamp for logging to reflect actual event time more closely if needed
  # For now, using the same current_time_agents for simplicity with existing log functions
  torch_pass_id = log_handoff_to_db(
      current_time_agents, outgoing_agent_name, incoming_agent_name,
      incoming_agent_version, summary, token_count_at_handoff, message_to_successor
  )

  # Also log basic info to text file
  log_handoff_to_file(
      current_time_agents, outgoing_agent_name, incoming_agent_name,
      incoming_agent_version, summary, token_count_at_handoff, message_to_successor
  )

  if torch_pass_id is None:
    print("Error: Failed to log initial torch pass to database. Aborting detailed package creation.")
    return False

  print(f"\nInitial torch pass logged with ID: {torch_pass_id}")
  print("Proceeding with detailed Torch Package creation...")

  # 3. Detailed Torch Package Handling
  prefilled_package = prefill_torch_template(
      outgoing_agent_name, incoming_agent_name, incoming_agent_version,
      summary, token_count_at_handoff # Use initial summary and tokens for prefill
  )

  # In a real scenario, this is interactive. In testing, it will use defaults.
  completed_package_data = prompt_for_torch_package_details(prefilled_package)

  final_summary = completed_package_data.get('summary', summary) # Use package's summary if available
  final_message_to_successor = completed_package_data.get('agent_profile', {}).get('message_to_successor', message_to_successor if message_to_successor is not None else '')


  # 4. Save detailed package to JSON file
  try:
    os.makedirs(STATE_DIR, exist_ok=True)
    # Use timestamp from the completed package for filename consistency
    package_timestamp_iso = completed_package_data.get('timestamp', datetime.now(timezone.utc).isoformat())
    # Convert ISO timestamp to a more filename-friendly format
    dt_object = datetime.fromisoformat(package_timestamp_iso.replace("Z", "+00:00"))
    timestamp_str = dt_object.strftime("%Y%m%d_%H%M%S")

    safe_agent_name = "".join(c if c.isalnum() else "_" for c in outgoing_agent_name)
    package_filename = f"torch_{safe_agent_name}_{timestamp_str}.json"
    package_filepath = os.path.join(STATE_DIR, package_filename)

    with open(package_filepath, 'w') as f:
      json.dump(completed_package_data, f, indent=2)
    print(f"Detailed Torch Package saved to: {package_filepath}")
  except Exception as e:
    print(f"Error saving Torch Package JSON to file: {e}")
    # Continue to DB logging if file save fails? Or return False? For now, continue.

  # 5. Save detailed package info to torch_packages table
  try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO torch_packages (torch_pass_id, package_json, filepath)
        VALUES (?, ?, ?)
    """, (torch_pass_id, json.dumps(completed_package_data), package_filepath if 'package_filepath' in locals() else None))
    conn.commit()
    print("Detailed Torch Package info saved to database.")
  except sqlite3.Error as e:
    print(f"Database error saving Torch Package info: {e}")
  finally:
    if conn:
      conn.close()

  # 6. Update original torch_passes entry with refined summary and message
  try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE torch_passes
        SET summary = ?, message_to_successor = ?
        WHERE id = ?
    """, (final_summary, final_message_to_successor, torch_pass_id))
    conn.commit()
    print(f"Torch pass entry {torch_pass_id} updated with final summary and message.")
  except sqlite3.Error as e:
    print(f"Database error updating torch_passes entry: {e}")
  finally:
    if conn:
      conn.close()

  print(f"\n--- Full Handoff Process Complete for {outgoing_agent_name} -> {incoming_agent_name} ---")
  print(f"  Original basic log ID: {torch_pass_id}")
  print(f"  Final Summary: {final_summary}")
  if final_message_to_successor:
    print(f"  Final Message to Successor: {final_message_to_successor}")
  print(f"  Token count (from prefill): {completed_package_data.get('tokens')}")

  return True

if __name__ == "__main__":
  logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
  if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
    print(f"Created directory: {logs_dir}")

  print("Initial AGENTS state:", AGENTS)

  if "Agent001" not in AGENTS: # For the main handoff simulation
    register_agent("Agent001", version="1.0")

  # For the prefill test section, ensure TestAgent001 is in AGENTS for version lookup
  if "TestAgent001" not in AGENTS:
      register_agent("TestAgent001", version="testing_v0.1")
  print("AGENTS state after initial registrations:", AGENTS)

  print("\n--- Main Handoff Simulation with Full Torch Package ---")
  handoff_successful = perform_handoff(
    outgoing_agent_name="AgentAlpha", # Changed for clarity in test
    incoming_agent_name="AgentBeta",
    incoming_agent_version="1.0",
    summary="Main test: Initial summary for Alpha to Beta handoff", # This will be used for prefill
    token_count_at_handoff=2500, # Used for prefill
    message_to_successor="Main test: Initial message from Alpha to Beta" # Used for initial log, might be overridden
  )

  if handoff_successful:
    print("\n--- Verification post-handoff ---")
    # Verify file logging (last line of basic log)
    try:
      with open(LOG_FILE_PATH, 'r') as f:
        lines = f.readlines()
        if lines:
          print("\nLast basic log entry from file (torch_log.txt):")
          print(lines[-1].strip())
    except Exception as e:
      print(f"\nError reading basic log file: {e}")

    # Verify DB logging (last torch_passes and torch_packages entries)
    conn = None
    try:
      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()

      print("\nLast entry from torch_passes (should reflect final summary/message if updated):")
      cursor.execute("SELECT * FROM torch_passes ORDER BY id DESC LIMIT 1")
      last_pass_entry = cursor.fetchone()
      if last_pass_entry:
        cols_pass = [desc[0] for desc in cursor.description]
        print(dict(zip(cols_pass, last_pass_entry)))
      else:
        print("No entries found in torch_passes.")

      print("\nLast entry from torch_packages:")
      cursor.execute("SELECT id, torch_pass_id, filepath, created_at FROM torch_packages ORDER BY id DESC LIMIT 1") # Avoid printing full JSON
      last_package_entry = cursor.fetchone()
      if last_package_entry:
        cols_pkg = [desc[0] for desc in cursor.description]
        package_info = dict(zip(cols_pkg, last_package_entry))
        print(package_info)
        if package_info.get('filepath') and os.path.exists(package_info['filepath']):
            print(f"Verified: JSON file exists at {package_info['filepath']}")
            # Optionally print part of the JSON content for deeper verification
            # with open(package_info['filepath'], 'r') as f_json:
            #   pkg_content_sample = json.load(f_json)
            #   print(f"  File content sample (task_id): {pkg_content_sample.get('task_id')}")
        elif package_info.get('filepath'):
            print(f"Warning: JSON file path recorded but not found at {package_info['filepath']}")
        else:
            print("No filepath recorded for the last torch_package.")

      else:
        print("No entries found in torch_packages.")

    except sqlite3.Error as e:
      print(f"\nDatabase error during verification: {e}")
    finally:
      if conn:
        conn.close()
  else:
    print("Main Handoff simulation failed.")

  print("\nFinal AGENTS state (end of script):", AGENTS)

  # The prefill and direct prompt test is now part of perform_handoff,
  # so the separate test block for those is removed to avoid confusion.
  # The main perform_handoff call above will exercise them.

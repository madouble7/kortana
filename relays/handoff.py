from datetime import datetime
from relays.relay import register_agent, update_agent_handoff_time, AGENTS
import sqlite3
import os

# Define paths for database and log file
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'kortana.db')
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'torch_log.txt')

def log_handoff_to_db(timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor=None):
  """Logs the handoff event to the SQLite database."""
  try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
      INSERT INTO torch_passes (timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor))
    conn.commit()
  except sqlite3.Error as e:
    print(f"Database error: {e}")
  finally:
    if conn:
      conn.close()

def log_handoff_to_file(timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor=None):
  """Logs the handoff event to a text file."""
  try:
    with open(LOG_FILE_PATH, 'a') as f:
      log_entry = f"{timestamp} | OUT: {outgoing_agent_name} | IN: {incoming_agent_name} (v{incoming_agent_version}) | SUMMARY: {summary} | TOKENS: {token_count_at_handoff} | MSG: {message_to_successor if message_to_successor else ''}\n"
      f.write(log_entry)
  except IOError as e:
    print(f"File I/O error: {e}")

def perform_handoff(outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor=None):
  """
  Simulates a handoff between two agents, updating their statuses and handoff times,
  and logs the event to the database and a file.
  """
  current_time = datetime.now()

  # Update outgoing agent's last handoff time
  if outgoing_agent_name in AGENTS: # Ensure outgoing agent exists before updating
    update_agent_handoff_time(outgoing_agent_name, current_time)
  else:
    # If the outgoing agent isn't registered, we might want to register it or handle as an error
    # For now, let's register it so the handoff can proceed.
    register_agent(outgoing_agent_name, version="unknown") # Or some default/unknown version
    update_agent_handoff_time(outgoing_agent_name, current_time)


  # Register incoming agent (this will set/update its handoff time)
  register_agent(incoming_agent_name, version=incoming_agent_version)

  # Log handoff to database
  log_handoff_to_db(current_time, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor)

  # Log handoff to file
  log_handoff_to_file(current_time, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor)

  print(f"Handoff complete: {outgoing_agent_name} -> {incoming_agent_name} at {current_time}")
  print(f"  Summary: {summary}")
  if message_to_successor:
    print(f"  Message to successor: {message_to_successor}")
  print(f"  Token count at handoff: {token_count_at_handoff}")

  return True

if __name__ == "__main__":
  # Ensure logs directory exists
  logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
  if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
    print(f"Created directory: {logs_dir}")

  # Ensure the database file exists, if not, the DB logging will create it.
  # We might need to initialize the table if the DB is newly created by log_handoff_to_db
  # For this test, we assume kortana.db and the torch_passes table were created in a previous step.
  # If not, log_handoff_to_db might fail if the table doesn't exist.
  # A robust setup would initialize the DB schema if DB_PATH doesn't exist.

  print("Initial AGENTS state:", AGENTS)

  # Register a sample outgoing agent for the test scenario
  register_agent("Agent001", version="1.0")
  print("AGENTS state after registering Agent001:", AGENTS)

  # Perform a sample handoff
  handoff_successful = perform_handoff(
    outgoing_agent_name="Agent001",
    incoming_agent_name="Agent003",
    incoming_agent_version="1.0",
    summary="Initial handoff to new agent Agent003",
    token_count_at_handoff=1000,
    message_to_successor="Welcome, Agent003!"
  )

  if handoff_successful:
    print("Handoff simulation was successful. Logs should have been written.")

    # Verify file logging
    try:
      with open(LOG_FILE_PATH, 'r') as f:
        lines = f.readlines()
        if lines:
          print("\nLast log entry from file:")
          print(lines[-1].strip())
    except FileNotFoundError:
      print(f"\nLog file {LOG_FILE_PATH} not found.")
    except Exception as e:
      print(f"\nError reading log file: {e}")

    # Verify DB logging
    try:
      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM torch_passes ORDER BY id DESC LIMIT 1")
      last_db_entry = cursor.fetchone()
      if last_db_entry:
        print("\nLast log entry from database:")
        # Print with column names for clarity
        cols = [desc[0] for desc in cursor.description]
        print(dict(zip(cols, last_db_entry)))

    except sqlite3.Error as e:
      print(f"\nDatabase error when verifying: {e}")
    finally:
      if conn:
        conn.close()
  else:
    print("Handoff simulation failed.")

  print("\nFinal AGENTS state:", AGENTS)

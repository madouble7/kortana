"""
Run Kor'tana and Capture Output

This script runs the Kor'tana system and captures the output to a log file
for analysis. It also sends input to test basic functionality.
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def main():
    """Run the setup and main Kor'tana system, capturing output."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Set up log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(f"logs/kortana_run_{timestamp}.log")

    print(f"Running Kor'tana and capturing output to {log_file}")

    # Prepare commands to run
    commands = [
        ["python", "src/setup_directories.py"],
        ["python", "src/check_dependencies.py"],
        ["python", "-m", "src.kortana.core.brain"],
    ]

    # Open log file
    with open(log_file, "w") as f:
        # Run setup commands
        for i, cmd in enumerate(commands[:-1]):
            f.write(f"\n\n{'='*80}\n")
            f.write(f"Running: {' '.join(cmd)}\n")
            f.write(f"{'='*80}\n\n")

            # Run command and capture output
            process = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            # Write output to log file
            f.write(process.stdout)

            if process.returncode != 0:
                f.write(f"\nCommand failed with exit code {process.returncode}\n")
                return

        # Run main command with interactive input
        cmd = commands[-1]
        f.write(f"\n\n{'='*80}\n")
        f.write(f"Running: {' '.join(cmd)}\n")
        f.write(f"{'='*80}\n\n")

        try:
            # Start process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Function to read output until a specific pattern is seen
            def read_until_prompt(prompt="matt: "):
                output = ""
                while True:
                    char = process.stdout.read(1)
                    if not char:
                        break
                    output += char
                    f.write(char)
                    f.flush()
                    if output.endswith(prompt):
                        break
                return output

            # Wait for initial startup and first prompt
            startup_output = read_until_prompt()

            # Test messages to send
            test_messages = [
                "hello kortana",
                "what can you help me with?",
                "tell me about warchief",
                "bye",
            ]

            # Send test messages
            for msg in test_messages:
                # Write message to stdin
                process.stdin.write(msg + "\n")
                process.stdin.flush()
                f.write(f"[SENT] {msg}\n")

                # Read response
                response = read_until_prompt()

                # If bye was sent, we're done
                if msg == "bye":
                    break

                # Wait a bit between messages
                time.sleep(1)

            # Make sure process is terminated
            process.terminate()
            process.wait(timeout=5)

        except Exception as e:
            f.write(f"\nError during interactive session: {e}\n")

    print(f"Run completed. Output saved to {log_file}")

    # Print the first part of the output
    with open(log_file, "r") as f:
        content = f.read()
        print("\n" + "=" * 40 + " OUTPUT PREVIEW " + "=" * 40)
        print(content[:1000] + "...\n")
        print(f"(Full output in {log_file})")

    return 0


if __name__ == "__main__":
    sys.exit(main())

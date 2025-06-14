#!/usr/bin/env python3
"""
Kor'tana Task Scheduler Setup
============================
Sets up Windows Task Scheduler for autonomous operation
"""

import os
import subprocess
import sys
from pathlib import Path


def create_scheduled_task(task_name, script_path, interval_minutes=5, description=""):
    """Create a Windows scheduled task"""

    # Convert to absolute path
    script_path = Path(script_path).absolute()
    working_dir = script_path.parent

    # Task XML template
    task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{description}</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT{interval_minutes}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2024-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT5M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>/c "{script_path}"</Arguments>
      <WorkingDirectory>{working_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    # Save XML to temp file
    xml_file = f"{task_name}.xml"
    with open(xml_file, "w", encoding="utf-16") as f:
        f.write(task_xml)

    try:
        # Create the task
        cmd = f'schtasks /create /tn "{task_name}" /xml "{xml_file}" /f'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[OK] Created task: {task_name}")
            return True
        else:
            print(f"[ERROR] Failed to create task: {result.stderr}")
            return False
    finally:
        # Clean up XML file
        if os.path.exists(xml_file):
            os.remove(xml_file)


def setup_automation_tasks():
    """Set up all automation tasks"""
    print("=====================================")
    print(" KOR'TANA TASK SCHEDULER SETUP")
    print("=====================================")

    base_dir = Path(__file__).parent

    # Task configurations
    tasks = [
        {
            "name": "KorTana_Relay_5min",
            "script": base_dir / "relays" / "run_relay.bat",
            "interval": 5,
            "description": "Kor'tana main relay system - runs every 5 minutes",
        },
        {
            "name": "KorTana_Handoff_10min",
            "script": base_dir / "relays" / "handoff.bat",
            "interval": 10,
            "description": "Kor'tana agent handoff monitoring - runs every 10 minutes",
        },
    ]

    success_count = 0
    for task in tasks:
        if create_scheduled_task(
            task["name"], task["script"], task["interval"], task["description"]
        ):
            success_count += 1

    print(f"\n[RESULT] Created {success_count}/{len(tasks)} scheduled tasks")

    if success_count == len(tasks):
        print("\n[OK] Hands-off automation configured successfully!")
        print("\nTo start automation:")
        print("  schtasks /run /tn KorTana_Relay_5min")
        print("  schtasks /run /tn KorTana_Handoff_10min")
        print("\nTo stop automation:")
        print("  schtasks /end /tn KorTana_Relay_5min")
        print("  schtasks /end /tn KorTana_Handoff_10min")
        print("\nTo remove tasks:")
        print("  schtasks /delete /tn KorTana_Relay_5min /f")
        print("  schtasks /delete /tn KorTana_Handoff_10min /f")
    else:
        print("\n[WARNING] Some tasks failed to create")
        print("Run as Administrator if permissions are required")


def check_existing_tasks():
    """Check if tasks already exist"""
    try:
        result = subprocess.run(
            "schtasks /query /fo csv", shell=True, capture_output=True, text=True
        )
        if "KorTana" in result.stdout:
            print("\n[INFO] Existing Kor'tana tasks found:")
            lines = result.stdout.split("\n")
            for line in lines:
                if "KorTana" in line:
                    parts = line.split(",")
                    if len(parts) > 0:
                        task_name = parts[0].strip('"')
                        print(f"  - {task_name}")
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    print("Checking for existing tasks...")
    if check_existing_tasks():
        response = input("\nExisting tasks found. Recreate them? (y/n): ")
        if response.lower() != "y":
            print("Setup cancelled.")
            sys.exit(0)

    setup_automation_tasks()

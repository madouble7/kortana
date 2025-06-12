from pathlib import Path

# Direct path construction and check
direct_path = Path("c:/project-kortana/tools/codex/tasks/test_brain_utils.json")
print(f"Direct path: '{str(direct_path)}'")
print(f"Direct path exists: {direct_path.exists()}")

# Directory path construction and check
dir_path = Path("c:/project-kortana/tools/codex/tasks/")
print(f"Directory path: '{str(dir_path)}'")
print(f"Directory exists: {dir_path.exists()}")

# Reconstruct path as in codex_runner.py
# Assuming project_root is correctly determined as c:\project-kortana
project_root_sim = Path("c:/project-kortana")
codex_dir_sim = project_root_sim / "tools" / "codex"
tasks_dir_sim = codex_dir_sim / "tasks"  # This is the critical line
task_name_sim = "test_brain_utils"
task_file_sim = tasks_dir_sim / f"{task_name_sim}.json"

print(f"Simulated codex_dir_sim: '{str(codex_dir_sim)}'")
print(f"Simulated tasks_dir_sim: '{str(tasks_dir_sim)}'")  # Check this output carefully
print(f"Simulated task_file_sim: '{str(task_file_sim)}'")
print(f"Simulated task_file_sim exists: {task_file_sim.exists()}")

# Check the type of the "tasks" string used in codex_runner
# In codex_runner.py: self.tasks_dir = self.codex_dir / "tasks"
# Let's see if "tasks" itself is somehow misinterpreted
problem_segment = "tasks"
print(f"Type of 'tasks' string: {type(problem_segment)}")
reconstructed_tasks_dir = (project_root_sim / "tools" / "codex") / problem_segment
print(f"Reconstructed tasks_dir with string variable: '{str(reconstructed_tasks_dir)}'")

# Check if an explicit cast to string for each part changes anything
codex_dir_explicit_str = project_root_sim / "tools" / "codex"
tasks_dir_explicit_str = codex_dir_explicit_str / "tasks"
task_file_explicit_str = tasks_dir_explicit_str / f"{str(task_name_sim)}.json"
print(f"Explicit str tasks_dir_explicit_str: '{str(tasks_dir_explicit_str)}'")
print(f"Explicit str task_file_explicit_str: '{str(task_file_explicit_str)}'")
print(f"Explicit str task_file_explicit_str exists: {task_file_explicit_str.exists()}")

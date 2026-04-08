import subprocess
import os
import sys

def execute(cmd):
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def main():
    repo_dir = "C:/kortana"
    os.chdir(repo_dir)

    print("--- KOR'TANA KILL SWITCH ENGAGED ---")
    # Identify the last commit by kor'tana
    log_cmd = 'git log -1 --author="kor\'tana" --oneline --format="%H"'
    last_commit_hash = execute(log_cmd)

    if not last_commit_hash or not last_commit_hash.strip():
        print("No recent autonomous commit found to revert.")
        sys.exit(0)

    commit_hash = last_commit_hash.strip()
    print(f"Found autonomous commit: {commit_hash}. Initiating revert...")

    execute(f"git revert --no-edit {commit_hash}")
    # execute("git push origin HEAD") # Leaving out auto-push for safety in early testing

    print(f"Successfully reverted {commit_hash}. Kor'tana is now locked.")

if __name__ == '__main__':
    main()
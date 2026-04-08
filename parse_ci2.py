import json

path = r"c:\Users\madou\AppData\Roaming\Code\User\workspaceStorage\454a91c31900fb43fa6b6f7a115a5535\GitHub.copilot-chat\chat-session-resources\b7bb51b6-c969-4221-bac4-2f973a4c14ed\toolu_bdrk_01MpJSuq9GmGTPgjnoq8xMtJ__vscode-1775502449337\content.json"

with open(path, encoding="utf-8") as f:
    d = json.load(f)

checks = d.get("statusChecks", [])

for c in checks:
    state = c.get("state", "")
    if state.lower() != "failure":
        continue

    name = c.get("context", c.get("name", "?"))
    target = c.get("targetUrl", "")
    logs = c.get("logs", "")

    # The logs have literal \n as newline chars already decoded from JSON
    lines = logs.split("\n")

    print(f"\n{'=' * 80}")
    print(f"CHECK: {name} ({len(lines)} lines, {len(logs)} chars)")
    print(f"URL: {target}")

    # Find lines with error keywords
    error_indices = []
    keywords = [
        "FAILED",
        "Error",
        "error:",
        "##[error]",
        "AssertionError",
        "ModuleNotFoundError",
        "ImportError",
        "exit code 1",
        "ERRORS",
        "failures=",
        "failed",
        "traceback",
        "no module",
        "cannot find",
        "not found",
    ]

    for i, line in enumerate(lines):
        if any(k.lower() in line.lower() for k in keywords):
            error_indices.append(i)

    if error_indices:
        printed = set()
        for idx in error_indices:
            start = max(0, idx - 5)
            end = min(len(lines), idx + 6)
            for j in range(start, end):
                if j not in printed:
                    line = lines[j]
                    # Strip timestamp
                    if "Z " in line and line[:4] == "2026":
                        line = line[line.index("Z ") + 2 :]
                    if line.strip():
                        marker = ">>>" if j in error_indices else "   "
                        print(f"  {marker} L{j:5d}: {line[:250]}")
                    printed.add(j)
            if end < len(lines):
                print("  --- (gap) ---")
    else:
        print("  (No error keywords found - last 15 lines)")
        for line in lines[-15:]:
            if "Z " in line and line[:4] == "2026":
                line = line[line.index("Z ") + 2 :]
            if line.strip():
                print(f"  {line[:200]}")

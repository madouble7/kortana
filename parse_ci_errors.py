import json

path = r"c:\Users\madou\AppData\Roaming\Code\User\workspaceStorage\454a91c31900fb43fa6b6f7a115a5535\GitHub.copilot-chat\chat-session-resources\b7bb51b6-c969-4221-bac4-2f973a4c14ed\toolu_bdrk_01MpJSuq9GmGTPgjnoq8xMtJ__vscode-1775502449337\content.json"

with open(path, encoding="utf-8") as f:
    d = json.load(f)

checks = d.get("statusChecks", [])

# Find all failures and extract error lines from their logs
for c in checks:
    state = c.get("state", "")
    if state.lower() != "failure":
        continue

    name = c.get("context", c.get("name", "?"))
    target = c.get("targetUrl", "")
    logs = c.get("logs", "")

    print(f"\n{'=' * 80}")
    print(f"CHECK: {name}")
    print(f"URL: {target}")
    print(f"LOG LENGTH: {len(logs)} chars")

    # Split logs into lines and find error-related ones
    lines = logs.split("\\n")
    error_lines = []
    for i, line in enumerate(lines):
        # Look for error indicators
        lowline = line.lower()
        if any(
            k in lowline
            for k in [
                "error",
                "failed",
                "failure",
                "assert",
                "traceback",
                "exit code",
                "fatal",
                "cannot",
                "not found",
                "no module",
            ]
        ):
            # Get context: 3 lines before, the error line, 3 lines after
            start = max(0, i - 3)
            end = min(len(lines), i + 4)
            error_lines.append((i, start, end))

    if error_lines:
        # Merge overlapping ranges
        printed = set()
        for idx, start, end in error_lines:
            for j in range(start, end):
                if j not in printed and j < len(lines):
                    line = lines[j].strip()
                    # Remove timestamp prefix for readability
                    if "Z " in line:
                        line = line[line.index("Z ") + 2 :]
                    if line:
                        print(f"  L{j:4d}: {line[:200]}")
                    printed.add(j)
    else:
        # Show last 20 lines
        print("  (No error keywords found - showing last 20 lines)")
        for line in lines[-20:]:
            line = line.strip()
            if "Z " in line:
                line = line[line.index("Z ") + 2 :]
            if line:
                print(f"  {line[:200]}")

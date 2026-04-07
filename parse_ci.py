import json

path = r"c:\Users\madou\AppData\Roaming\Code\User\workspaceStorage\454a91c31900fb43fa6b6f7a115a5535\GitHub.copilot-chat\chat-session-resources\b7bb51b6-c969-4221-bac4-2f973a4c14ed\toolu_bdrk_01MpJSuq9GmGTPgjnoq8xMtJ__vscode-1775502449337\content.json"

with open(path, encoding="utf-8") as f:
    d = json.load(f)

checks = d.get("statusChecks", [])
print(f"Total checks: {len(checks)}")
print()

for c in checks:
    state = c.get("state", "?")
    name = c.get("context", c.get("name", "?"))
    desc = (c.get("description") or "")[:100]
    conclusion = c.get("conclusion", "")
    print(f"{state:12} | {conclusion:12} | {name} | {desc}")

# Find failures and print details
print("\n=== FAILURES ===")
for c in checks:
    state = c.get("state", "")
    conclusion = c.get("conclusion", "")
    if state.lower() in ("failure", "error") or conclusion.lower() in (
        "failure",
        "error",
    ):
        print(json.dumps(c, indent=2, default=str)[:3000])

import subprocess, sys
msg = """feat: voice mode, revelation surfacing, insight commands, chat context

- voice_mode flag: 120 token cap, 1-2 sentence constraint, skips revelation context
- _load_recent_revelations(): injects top 3 revelations into chat system prompt (non-voice)
- _run_revelation_engine(): runs every 10 autonomy cycles
- _write_reflection() enriched with most recent revelation title+content
- voice_daemon: startup revelation 2s post-greeting, 30-min proactive surfacing
- voice_daemon: insight command routing (what have you noticed?, any insights?)
- voice_daemon: current_focus.json VS Code context, history depth 30/40, trim 600->350
- voice_daemon: voice_mode: True in all backend payloads

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"""
result = subprocess.run(
    ["git", "commit", "-m", msg],
    cwd="c:/kortana",
    capture_output=True, text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)

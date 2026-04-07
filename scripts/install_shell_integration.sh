#!/usr/bin/env bash
# Helper to add VS Code shell integration to ~/.bashrc (Git Bash / WSL / Linux)
set -euo pipefail

if ! command -v code &>/dev/null; then
  echo "'code' command not found in PATH. Open VS Code and run 'Shell Command: Install 'code' command in PATH' from the Command Palette." >&2
  exit 2
fi

# Locate the integration script path
SCRIPT_PATH=$(code --locate-shell-integration-path bash || true)
if [ -z "$SCRIPT_PATH" ]; then
  echo "Could not locate shell integration path for bash. Ensure VS Code is up-to-date and supports shell integration." >&2
  exit 1
fi

PROFILE="$HOME/.bashrc"
SOURCE_LINE='[[ "$TERM_PROGRAM" == "vscode" ]] && . "'"$SCRIPT_PATH"'"'

# Create profile if missing
if [ ! -f "$PROFILE" ]; then
  touch "$PROFILE"
fi

# Add idempotent entry
if ! grep -Fq "$SOURCE_LINE" "$PROFILE"; then
  echo "# VS Code Shell Integration - added by install_shell_integration.sh" >> "$PROFILE"
  echo "$SOURCE_LINE" >> "$PROFILE"
  echo "Inserted shell integration line into $PROFILE"
else
  echo "Profile already contains shell integration line. No changes made."
fi

echo "Done. Restart your shell (or open a new terminal in VS Code) to test. Hover the terminal tab to see shell integration quality."
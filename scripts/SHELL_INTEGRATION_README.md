Shell Integration Setup for VS Code (Git Bash & PowerShell)

Overview
--------
This repo provides two helper scripts to install VS Code's shell integration for Git Bash (or WSL/bash) and PowerShell:

- `scripts/install_shell_integration.sh` — adds the required line to `~/.bashrc` (Git Bash/Linux/WSL)
- `scripts/install_shell_integration.ps1` — adds the required line to your PowerShell profile (`$PROFILE`)

Usage
-----
1. Ensure `code` is on your PATH. In VS Code, open Command Palette and run `Shell Command: Install 'code' command in PATH`.
2. Run the appropriate script:

- Git Bash / WSL / Linux:
  - `bash scripts/install_shell_integration.sh`
- Windows PowerShell:
  - Open PowerShell and run: `.\	ools\install_shell_integration.ps1` (or `.\	asks\install_shell_integration.ps1` depending on your location)

Notes
-----
- The scripts add the injection lines idempotently and will not duplicate entries.
- For lower startup latency, inline the path: run `code --locate-shell-integration-path <shell>` then paste the script path directly into your profile.
- If you set `terminal.integrated.shellIntegration.enabled` to `false` in `.vscode/settings.json`, the automatic injection will be suppressed (useful when you inline the script manually).

Verification
------------
- Open a new integrated terminal in VS Code and hover the terminal tab to see the shell integration quality. You should see `Rich` or `Basic`.
- Run a failing command (e.g., `false` in bash) and check for a red decoration in the gutter.
- Try terminal IntelliSense (type `git checkout ` and press `Ctrl+Space`).

Troubleshooting
---------------
- If `code` is not on PATH, the scripts will fail and explain how to fix it.
- If the integration quality is `None`, double-check your shell rc file and ensure the added line is present and can be sourced.

If you'd like, I can run the scripts here (for Git Bash / PowerShell shells inside this environment) or update the scripts to support other shells (zsh, fish).

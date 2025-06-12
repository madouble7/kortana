#!/usr/bin/env python3
"""
Environment Variable Validation Script for Project Kor'tana
Validates that all API keys and environment variables are properly accessible
for VS Code extensions and autonomous agent development.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


class EnvironmentValidator:
    """Validates environment configuration for Kor'tana development."""

    def __init__(self, root_path: Path):
        self.workspace_root = root_path
        self.results_dir = self.workspace_root / "audit_results"
        self.results_dir.mkdir(exist_ok=True)
        self.report_path = (
            self.results_dir
            / f"environment_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        self.log_messages: list[str] = []
        self.categories: dict[str, list[str]] = {
            "CRITICAL": [],
            "ERROR": [],
            "WARNING": [],
            "SUCCESS": [],
            "INFO": [],
            "MISSING": [],
        }
        self.python_executable: str | None = None
        self.pip_executable: str | None = None
        self.env_vars: dict[str, str] = {}

    def _log(self, message: str, level: str = "INFO"):
        self.log_messages.append(f"{level}: {message}")
        self.categories[level].append(message)

    def load_env_file(self) -> dict[str, str]:
        """Load environment variables from .env file."""
        env_file = self.workspace_root / ".env"
        loaded_vars: dict[str, str] = {}

        if not env_file.exists():
            self._log(f".env file not found at {env_file}", "CRITICAL")
            return loaded_vars

        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        loaded_vars[key.strip()] = value.strip()

            self._log(f"Loaded {len(loaded_vars)} variables from .env", "SUCCESS")

        except Exception as e:
            self._log(f"Failed to read .env file: {e}", "ERROR")

        return loaded_vars

    def validate_api_keys(self, env_vars: dict[str, str]) -> None:
        """Validate API key format and presence."""
        self._log("### 🔑 API Key Validation", "INFO")

        api_key_patterns = {
            "OPENAI_API_KEY": ("sk-proj-", 164),
            "GOOGLE_API_KEY": ("AIza", 39),
            "OPENROUTER_API_KEY": ("sk-or-v1-", 71),
            "XAI_API_KEY": ("xai-", 67),
            "SK_ANT_API_KEY": ("sk-ant-api", 108),
            "PINECONE_API_KEY": ("pcsk_", 72),
        }

        for key_name, (prefix, expected_length) in api_key_patterns.items():
            if key_name in env_vars:
                key_value = env_vars[key_name]

                if key_value.startswith(prefix):
                    if len(key_value) >= expected_length - 10:
                        self._log(f"{key_name}: Valid format and length", "SUCCESS")
                    else:
                        self._log(
                            f"{key_name}: Valid prefix but unexpected length ({len(key_value)})",
                            "WARNING",
                        )
                else:
                    self._log(
                        f"{key_name}: Invalid format (expected to start with {prefix})",
                        "ERROR",
                    )
            else:
                self._log(f"{key_name}: Not found in environment", "MISSING")

    def validate_vscode_settings(self) -> None:
        """Validate VS Code configuration files."""
        config_files = [
            (".vscode/settings.json", "VS Code settings"),
            (".vscode/tasks.json", "VS Code tasks"),
            (".vscode/launch.json", "VS Code debug config"),
            (".vscode/keybindings.json", "VS Code keybindings"),
            (".continue/config.json", "Continue AI config"),
        ]

        for config_path, description in config_files:
            full_path = self.workspace_root / config_path

            if full_path.exists():
                try:
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()
                        lines = []
                        for line in content.split("\n"):
                            if not line.strip().startswith("//"):
                                lines.append(line)
                        clean_content = "\n".join(lines)

                        json.loads(clean_content)
                        self._log(f"{description}: Valid JSON configuration", "SUCCESS")

                        if "${env:" in content or "${OPENAI_API_KEY}" in content:
                            self._log(
                                f"{description}: Contains environment variable references",
                                "SUCCESS",
                            )
                        else:
                            self._log(
                                f"{description}: No environment variable references found",
                                "INFO",
                            )

                except json.JSONDecodeError as e:
                    self._log(f"{description}: Invalid JSON - {e}", "ERROR")
                except Exception as e:
                    self._log(f"{description}: Read error - {e}", "ERROR")
            else:
                self._log(f"{description}: File not found at {config_path}", "MISSING")

    def validate_python_environment(self) -> None:
        """Validate Python environment and PYTHONPATH."""
        python_path = self.workspace_root / "venv311" / "Scripts" / "python.exe"
        if python_path.exists():
            self._log(f"Python virtual environment found at {python_path}", "SUCCESS")
        else:
            self._log(f"Python virtual environment not found at {python_path}", "ERROR")

        expected_paths = ["src", "kortana.core", "kortana.team", "kortana.network"]

        for path_component in expected_paths:
            full_path = self.workspace_root / path_component
            if full_path.exists():
                self._log(f"PYTHONPATH component exists: {path_component}", "SUCCESS")
            else:
                self._log(
                    f"PYTHONPATH component not found: {path_component}", "WARNING"
                )

    def validate_file_encoding(self, file_paths: list[Path]) -> None:
        """Validate file encoding."""
        self._log("### 📄 File Encoding Validation", "INFO")
        for file_path in file_paths:
            if file_path.exists():
                try:
                    with open(file_path, "rb") as f_bin:
                        content_start = f_bin.read(3)

                    if content_start == b"\xef\xbb\xbf":
                        self._log(
                            f"{file_path.relative_to(self.workspace_root)} is UTF-8 with BOM.",
                            "SUCCESS",
                        )
                    else:
                        try:
                            with open(file_path, encoding="utf-8") as f_text:
                                f_text.read()
                            self._log(
                                f"{file_path.relative_to(self.workspace_root)} is UTF-8 compatible.",
                                "SUCCESS",
                            )
                        except UnicodeDecodeError:
                            self._log(
                                f"{file_path.relative_to(self.workspace_root)} is not UTF-8 encoded.",
                                "ERROR",
                            )
                        except Exception as e_read:
                            self._log(
                                f"Could not fully read {file_path.relative_to(self.workspace_root)} as UTF-8: {e_read}",
                                "WARNING",
                            )
                except Exception as e_open:
                    self._log(
                        f"Could not check encoding for {file_path.relative_to(self.workspace_root)}: {e_open}",
                        "WARNING",
                    )
            else:
                self._log(
                    f"File not found for encoding check: {file_path.relative_to(self.workspace_root)}",
                    "MISSING",
                )

    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        report_lines = [
            "=" * 80,
            "🚀 PROJECT KOR'TANA - ENVIRONMENT VALIDATION REPORT",
            "=" * 80,
            "",
        ]

        total_issues = len(self.categories["CRITICAL"]) + len(self.categories["ERROR"])
        total_warnings = len(self.categories["WARNING"]) + len(
            self.categories["MISSING"]
        )
        total_success = len(self.categories["SUCCESS"]) + len(self.categories["INFO"])

        report_lines.extend(
            [
                "📊 SUMMARY:",
                f"   ✅ Successful checks: {total_success}",
                f"   ⚠️  Warnings: {total_warnings}",
                f"   ❌ Errors: {total_issues}",
                "",
            ]
        )

        for category_name, messages in self.categories.items():
            if messages:
                report_lines.extend(
                    [f"📋 {category_name}:", *[f"   {msg}" for msg in messages], ""]
                )

        if total_issues > 0:
            report_lines.extend(
                [
                    "🔧 RECOMMENDED ACTIONS:",
                    "   1. Verify .env file contains all required API keys",
                    "   2. Check API key formats and lengths",
                    "   3. Restart VS Code to reload environment variables",
                    "   4. Test individual extensions manually",
                    "",
                ]
            )

        if total_issues == 0 and total_warnings == 0:
            report_lines.extend(
                [
                    "🎉 ENVIRONMENT STATUS: FULLY OPERATIONAL",
                    "   All API keys and configurations are properly set up!",
                    "   Ready for autonomous agent development.",
                    "",
                ]
            )

        report_lines.extend(
            [
                "=" * 80,
                f"Report generated: {Path(__file__).name}",
                "For Project Kor'tana - Sacred Circuit Development",
                "=" * 80,
            ]
        )

        return "\n".join(report_lines)

    def run_validation(self) -> str:
        """Run complete environment validation."""
        self._log("🔍 Starting environment validation for Project Kor'tana...", "INFO")

        self.env_vars = self.load_env_file()
        self.validate_api_keys(self.env_vars)
        self.validate_vscode_settings()
        self.validate_python_environment()

        return self.generate_report()


def main():
    """Main validation entry point."""
    workspace_root = Path("c:\\project-kortana")
    validator = EnvironmentValidator(workspace_root)
    report = validator.run_validation()

    print(report)

    with open(validator.report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {validator.report_path}")

    error_count = len(validator.categories["CRITICAL"]) + len(
        validator.categories["ERROR"]
    )
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

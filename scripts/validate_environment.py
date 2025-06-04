#!/usr/bin/env python3
"""
Environment Variable Validation Script for Project Kor'tana
Validates that all API keys and environment variables are properly accessible
for VS Code extensions and autonomous agent development.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict


class EnvironmentValidator:
    """Validates environment configuration for Kor'tana development."""

    def __init__(self):
        self.workspace_root = Path("c:/kortana")
        self.required_env_vars = [
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "OPENROUTER_API_KEY",
            "XAI_API_KEY",
            "SK_ANT_API_KEY",
            "PINECONE_API_KEY",
            "VECTOR_STORE",
        ]

        self.optional_env_vars = ["GCP_SERVICE_ACCOUNT_KEY_PATH", "PYTHONPATH"]

        self.results = []

    def load_env_file(self) -> Dict[str, str]:
        """Load environment variables from .env file."""
        env_file = self.workspace_root / ".env"
        env_vars = {}

        if not env_file.exists():
            self.results.append(
                ("❌", "CRITICAL", f".env file not found at {env_file}")
            )
            return env_vars

        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

            self.results.append(
                ("✅", "SUCCESS", f"Loaded {len(env_vars)} variables from .env")
            )

        except Exception as e:
            self.results.append(("❌", "ERROR", f"Failed to read .env file: {e}"))

        return env_vars

    def validate_api_keys(self, env_vars: Dict[str, str]) -> None:
        """Validate API key format and presence."""

        api_key_patterns = {
            "OPENAI_API_KEY": ("sk-proj-", 164),  # OpenAI project keys
            "GOOGLE_API_KEY": ("AIza", 39),  # Google API keys
            "OPENROUTER_API_KEY": ("sk-or-v1-", 71),  # OpenRouter keys
            "XAI_API_KEY": ("xai-", 67),  # xAI keys
            "SK_ANT_API_KEY": ("sk-ant-api", 108),  # Anthropic keys
            "PINECONE_API_KEY": ("pcsk_", 72),  # Pinecone keys
        }

        for key_name, (prefix, expected_length) in api_key_patterns.items():
            if key_name in env_vars:
                key_value = env_vars[key_name]

                if key_value.startswith(prefix):
                    if len(key_value) >= expected_length - 10:  # Allow some variance
                        self.results.append(
                            ("✅", "SUCCESS", f"{key_name}: Valid format and length")
                        )
                    else:
                        self.results.append(
                            (
                                "⚠️",
                                "WARNING",
                                f"{key_name}: Valid prefix but unexpected length ({len(key_value)})",
                            )
                        )
                else:
                    self.results.append(
                        (
                            "❌",
                            "ERROR",
                            f"{key_name}: Invalid format (expected to start with {prefix})",
                        )
                    )
            else:
                self.results.append(
                    ("❌", "MISSING", f"{key_name}: Not found in environment")
                )

    def validate_vscode_config(self) -> None:
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
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Remove comments for JSON parsing
                        lines = []
                        for line in content.split("\n"):
                            if not line.strip().startswith("//"):
                                lines.append(line)
                        clean_content = "\n".join(lines)

                        # Try to parse as JSON
                        json.loads(clean_content)
                        self.results.append(
                            (
                                "✅",
                                "SUCCESS",
                                f"{description}: Valid JSON configuration",
                            )
                        )

                        # Check for environment variable references
                        if "${env:" in content or "${OPENAI_API_KEY}" in content:
                            self.results.append(
                                (
                                    "✅",
                                    "SUCCESS",
                                    f"{description}: Contains environment variable references",
                                )
                            )
                        else:
                            self.results.append(
                                (
                                    "⚠️",
                                    "INFO",
                                    f"{description}: No environment variable references found",
                                )
                            )

                except json.JSONDecodeError as e:
                    self.results.append(
                        ("❌", "ERROR", f"{description}: Invalid JSON - {e}")
                    )
                except Exception as e:
                    self.results.append(
                        ("❌", "ERROR", f"{description}: Read error - {e}")
                    )
            else:
                self.results.append(
                    ("❌", "MISSING", f"{description}: File not found at {config_path}")
                )

    def validate_python_environment(self) -> None:
        """Validate Python environment and PYTHONPATH."""

        # Check Python executable
        python_path = self.workspace_root / "venv311" / "Scripts" / "python.exe"
        if python_path.exists():
            self.results.append(
                ("✅", "SUCCESS", f"Python virtual environment found at {python_path}")
            )
        else:
            self.results.append(
                (
                    "❌",
                    "ERROR",
                    f"Python virtual environment not found at {python_path}",
                )
            )

        # Check PYTHONPATH components
        expected_paths = ["src", "kortana.core", "kortana.team", "kortana.network"]

        for path_component in expected_paths:
            full_path = self.workspace_root / path_component
            if full_path.exists():
                self.results.append(
                    ("✅", "SUCCESS", f"PYTHONPATH component exists: {path_component}")
                )
            else:
                self.results.append(
                    (
                        "⚠️",
                        "WARNING",
                        f"PYTHONPATH component not found: {path_component}",
                    )
                )

    def test_environment_access(self) -> None:
        """Test if environment variables are accessible from Python."""

        for var_name in self.required_env_vars:
            value = os.getenv(var_name)
            if value:
                # Mask sensitive data
                display_value = (
                    f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                )
                self.results.append(
                    (
                        "✅",
                        "SUCCESS",
                        f"Environment access: {var_name} = {display_value}",
                    )
                )
            else:
                self.results.append(
                    ("❌", "ERROR", f"Environment access: {var_name} not accessible")
                )

    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""

        report_lines = [
            "=" * 80,
            "🚀 PROJECT KOR'TANA - ENVIRONMENT VALIDATION REPORT",
            "=" * 80,
            "",
        ]

        # Group results by category
        categories = {
            "CRITICAL": [],
            "ERROR": [],
            "WARNING": [],
            "SUCCESS": [],
            "INFO": [],
            "MISSING": [],
        }

        for emoji, category, message in self.results:
            categories[category].append(f"{emoji} {message}")

        # Add summary
        total_issues = len(categories["CRITICAL"]) + len(categories["ERROR"])
        total_warnings = len(categories["WARNING"]) + len(categories["MISSING"])
        total_success = len(categories["SUCCESS"]) + len(categories["INFO"])

        report_lines.extend(
            [
                "📊 SUMMARY:",
                f"   ✅ Successful checks: {total_success}",
                f"   ⚠️  Warnings: {total_warnings}",
                f"   ❌ Errors: {total_issues}",
                "",
            ]
        )

        # Add detailed results
        for category_name, messages in categories.items():
            if messages:
                report_lines.extend(
                    [f"📋 {category_name}:", *[f"   {msg}" for msg in messages], ""]
                )

        # Add recommendations
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

        print("🔍 Starting environment validation for Project Kor'tana...")

        # Load environment variables
        env_vars = self.load_env_file()

        # Run all validation checks
        self.validate_api_keys(env_vars)
        self.validate_vscode_config()
        self.validate_python_environment()
        self.test_environment_access()

        # Generate and return report
        return self.generate_report()


def main():
    """Main validation entry point."""

    validator = EnvironmentValidator()
    report = validator.run_validation()

    print(report)

    # Save report to file
    report_file = Path("c:/kortana/logs/environment_validation_report.txt")
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    # Return appropriate exit code
    error_count = len([r for r in validator.results if r[1] in ["CRITICAL", "ERROR"]])
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

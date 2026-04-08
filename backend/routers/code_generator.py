"""
Code generation module for Kor'tana autonomous development
Parses AI-generated plans and creates actual code/file changes
"""

import json
import re
from pathlib import Path
from typing import Any


class CodeGenerationError(Exception):
    """Raised when code generation fails"""

    pass


class CodeGenerator:
    """Generates code from AI-generated plans"""

    def __init__(self, repo_path: str = "."):
        """Initialize code generator with repository path"""
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise CodeGenerationError(f"Repository path does not exist: {repo_path}")

    def parse_plan(self, plan_text: str) -> dict[str, Any]:
        """
        Parse Gemini-generated plan into structured format

        Expected format:
        ```
        FILE_CHANGES:
        - file: path/to/file.py
          action: create|modify|delete
          content: |
            code content here
        ```
        """
        try:
            # Try to extract JSON if present
            json_match = re.search(r"```json\n(.*?)\n```", plan_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass  # Fall through to YAML-like parser

            # Parse file changes section
            parsed = {
                "files": [],
                "commands": [],
                "tests": [],
                "description": plan_text[:500],  # First 500 chars as description
            }

            # Extract file changes
            file_pattern = r"FILE_CHANGES:.*?(?=COMMANDS:|$)"
            file_section = re.search(file_pattern, plan_text, re.DOTALL)
            if file_section:
                file_matches = re.finditer(
                    r"- file: (.+?)\n\s+action: (.+?)\n\s+content: \|\n(.*?)(?=- file:|COMMANDS:|$)",
                    file_section.group(),
                    re.DOTALL,
                )
                for match in file_matches:
                    parsed["files"].append(
                        {
                            "path": match.group(1).strip(),
                            "action": match.group(2).strip(),
                            "content": match.group(3).strip(),
                        }
                    )

            # Extract commands
            cmd_pattern = r"COMMANDS:.*?(?=TESTS:|$)"
            cmd_section = re.search(cmd_pattern, plan_text, re.DOTALL)
            if cmd_section:
                cmd_matches = re.finditer(
                    r"- (.*?)(?=\n-|\nTESTS:|$)", cmd_section.group(), re.DOTALL
                )
                for match in cmd_matches:
                    parsed["commands"].append(match.group(1).strip())

            return parsed
        except Exception as e:
            raise CodeGenerationError(f"Failed to parse plan: {str(e)}")

    def validate_plan(self, parsed_plan: dict[str, Any]) -> bool:
        """Validate parsed plan structure"""
        if not isinstance(parsed_plan, dict):
            return False

        if "files" in parsed_plan:
            for file_change in parsed_plan["files"]:
                if not all(k in file_change for k in ["path", "action", "content"]):
                    return False
                if file_change["action"] not in ["create", "modify", "delete"]:
                    return False
                # Prevent path traversal
                if ".." in file_change["path"]:
                    raise CodeGenerationError(
                        f"Invalid path (contains ..): {file_change['path']}"
                    )

        return True

    def generate_files(
        self, parsed_plan: dict[str, Any], dry_run: bool = True
    ) -> dict[str, Any]:
        """
        Generate files from parsed plan

        Args:
            parsed_plan: Parsed plan from parse_plan()
            dry_run: If True, don't actually write files (just return what would be created)

        Returns:
            Dict with created/modified/deleted file paths
        """
        if not self.validate_plan(parsed_plan):
            raise CodeGenerationError("Invalid plan structure")

        results = {"created": [], "modified": [], "deleted": [], "errors": []}

        for file_change in parsed_plan.get("files", []):
            try:
                file_path = self.repo_path / file_change["path"]

                # Security check: ensure path is within repo
                if not str(file_path.resolve()).startswith(
                    str(self.repo_path.resolve())
                ):
                    raise CodeGenerationError(
                        f"Path escape attempt: {file_change['path']}"
                    )

                action = file_change["action"]

                if action == "create":
                    if not dry_run:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, "w") as f:
                            f.write(file_change["content"])
                    results["created"].append(str(file_path))

                elif action == "modify":
                    if not file_path.exists():
                        raise CodeGenerationError(
                            f"File not found for modification: {file_change['path']}"
                        )
                    if not dry_run:
                        with open(file_path, "w") as f:
                            f.write(file_change["content"])
                    results["modified"].append(str(file_path))

                elif action == "delete":
                    if not file_path.exists():
                        raise CodeGenerationError(
                            f"File not found for deletion: {file_change['path']}"
                        )
                    if not dry_run:
                        file_path.unlink()
                    results["deleted"].append(str(file_path))

            except Exception as e:
                results["errors"].append(
                    {"file": file_change.get("path", "unknown"), "error": str(e)}
                )

        return results

    def format_code(self, content: str, file_type: str) -> str:
        """
        Format generated code based on file type

        Args:
            content: Raw code content
            file_type: File extension (py, js, md, etc.)

        Returns:
            Formatted code
        """
        try:
            if file_type == "py":
                # Basic Python formatting
                lines = content.split("\n")
                formatted = []
                for line in lines:
                    # Remove trailing whitespace but preserve indentation
                    formatted.append(line.rstrip())
                content = "\n".join(formatted)
                # Remove multiple blank lines
                content = re.sub(r"\n\n\n+", "\n\n", content)

            return content
        except Exception:
            # Return original if formatting fails
            return content

    def validate_python_syntax(self, file_path: str) -> bool:
        """Validate Python file syntax"""
        try:
            with open(file_path) as f:
                code = f.read()
            compile(code, file_path, "exec")
            return True
        except SyntaxError as e:
            raise CodeGenerationError(f"Syntax error in {file_path}: {str(e)}")

    def generate_from_gemini_plan(
        self,
        gemini_plan: str,
        repo_path: str = ".",
        dry_run: bool = True,
        validate_syntax: bool = True,
    ) -> dict[str, Any]:
        """
        End-to-end code generation from Gemini plan

        Args:
            gemini_plan: Raw text from Gemini analysis
            repo_path: Repository root path
            dry_run: If True, don't write files
            validate_syntax: If True, validate Python file syntax

        Returns:
            Generation results including created/modified/deleted files
        """
        self.repo_path = Path(repo_path)

        # Parse the plan
        parsed = self.parse_plan(gemini_plan)

        # Generate files
        results = self.generate_files(parsed, dry_run=dry_run)

        # Validate syntax if requested
        if validate_syntax and not dry_run:
            for py_file in results.get("created", []) + results.get("modified", []):
                if py_file.endswith(".py"):
                    try:
                        self.validate_python_syntax(py_file)
                    except CodeGenerationError as e:
                        results["errors"].append({"file": py_file, "error": str(e)})

        results["parsed_plan"] = parsed
        return results

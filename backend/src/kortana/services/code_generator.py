"""
Code generation module for Kor'tana autonomous development
Parses AI-generated plans and creates actual code/file changes

Phase 7 Enhancement: Atomic multi-file transactions with rollback capability
and dependency tracking for recursive self-optimization cycles.
"""

import json
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class CodeGenerationError(Exception):
    """Raised when code generation fails"""

    pass


@dataclass
class FileChange:
    """Represents a single file change with metadata"""

    path: str
    action: str  # create, modify, delete
    content: str = ""
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0

    def __post_init__(self):
        if self.action not in ["create", "modify", "delete"]:
            raise CodeGenerationError(f"Invalid action: {self.action}")


@dataclass
class AtomicTransaction:
    """Handles atomic multi-file changes with rollback capability"""

    files: list[FileChange] = field(default_factory=list)
    repo_path: Path = None
    backup_dir: Path = None
    executed: bool = False
    error: str = None

    def add_file_change(self, change: FileChange):
        """Add a file change to the transaction"""
        self.files.append(change)

    def validate_dependencies(self) -> tuple[bool, str]:
        """
        Validate that file dependencies are satisfied
        Returns: (is_valid, error_message)
        """
        # Build dependency graph
        all_files = {f.path for f in self.files}

        for file_change in self.files:
            for dep in file_change.dependencies:
                if dep not in all_files:
                    return (
                        False,
                        f"Dependency not in transaction: {dep} (required by {file_change.path})",
                    )

        # Check for cycles
        visited = set()
        rec_stack = set()

        def has_cycle(node: str, graph: dict) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, graph):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        graph = defaultdict(list)
        for file_change in self.files:
            for dep in file_change.dependencies:
                graph[dep].append(file_change.path)

        for node in graph:
            if node not in visited:
                if has_cycle(node, graph):
                    return False, "Circular dependency detected in transaction"

        return True, None

    def get_execution_order(self) -> list[FileChange]:
        """Return files ordered by dependencies (topological sort)"""
        is_valid, error = self.validate_dependencies()
        if not is_valid:
            raise CodeGenerationError(f"Invalid dependencies: {error}")

        # Topological sort with priority
        sorted_files = []
        visited = set()

        def visit(file_path: str):
            if file_path in visited:
                return
            visited.add(file_path)

            # Find file_change for this path
            file_change = next((f for f in self.files if f.path == file_path), None)
            if file_change:
                for dep in file_change.dependencies:
                    visit(dep)
                sorted_files.append(file_change)

        for file_change in sorted(self.files, key=lambda f: -f.priority):
            visit(file_change.path)

        return sorted_files

    def create_backup(self):
        """Create backup of files that will be modified"""
        if not self.repo_path.exists():
            raise CodeGenerationError(
                f"Repository path does not exist: {self.repo_path}"
            )

        self.backup_dir = self.repo_path / ".backup" / "atomic_transaction"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        for file_change in self.files:
            file_path = self.repo_path / file_change.path

            if file_change.action in ["modify", "delete"] and file_path.exists():
                # Create backup
                backup_path = self.backup_dir / file_change.path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)

    def execute(self, repo_path: str | Path) -> dict[str, Any]:
        """
        Execute all file changes in order with rollback on error
        Returns execution results
        """
        self.repo_path = Path(repo_path)
        results = {"created": [], "modified": [], "deleted": [], "errors": []}

        if self.executed:
            raise CodeGenerationError("Transaction already executed")

        try:
            # Validate dependencies
            is_valid, error = self.validate_dependencies()
            if not is_valid:
                raise CodeGenerationError(f"Transaction validation failed: {error}")

            # Create backups before executing
            self.create_backup()

            # Execute in dependency order
            ordered_files = self.get_execution_order()

            for file_change in ordered_files:
                file_path = self.repo_path / file_change.path

                # Security check: ensure path is within repo
                if not str(file_path.resolve()).startswith(
                    str(self.repo_path.resolve())
                ):
                    raise CodeGenerationError(
                        f"Path escape attempt: {file_change.path}"
                    )

                try:
                    if file_change.action == "create":
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, "w") as f:
                            f.write(file_change.content)
                        results["created"].append(str(file_path))

                    elif file_change.action == "modify":
                        if not file_path.exists():
                            raise CodeGenerationError(
                                f"File not found: {file_change.path}"
                            )
                        with open(file_path, "w") as f:
                            f.write(file_change.content)
                        results["modified"].append(str(file_path))

                    elif file_change.action == "delete":
                        if not file_path.exists():
                            raise CodeGenerationError(
                                f"File not found: {file_change.path}"
                            )
                        file_path.unlink()
                        results["deleted"].append(str(file_path))

                except Exception as e:
                    # Rollback on first error
                    self.rollback()
                    raise CodeGenerationError(
                        f"Failed to execute file change {file_change.path}: {str(e)}"
                    )

            self.executed = True
            return results

        except Exception as e:
            self.error = str(e)
            results["error"] = str(e)
            return results

    def rollback(self):
        """Rollback transaction to pre-execution state"""
        if not self.backup_dir or not self.backup_dir.exists():
            raise CodeGenerationError("No backup available for rollback")

        # Restore from backup
        for backup_file in self.backup_dir.rglob("*"):
            if backup_file.is_file():
                relative_path = backup_file.relative_to(self.backup_dir)
                target_path = self.repo_path / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, target_path)

        # Clean up backup
        shutil.rmtree(self.backup_dir)
        self.backup_dir = None


class CodeGenerator:
    """Generates code from AI-generated plans with atomic transaction support"""

    def __init__(self, repo_path: str = "."):
        """Initialize code generator with repository path"""
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise CodeGenerationError(f"Repository path does not exist: {repo_path}")

    def _normalize_json_plan(self, parsed_json: dict[str, Any]) -> dict[str, Any]:
        """Normalize JSON plan variants into the internal parsed-plan shape."""
        if "files" in parsed_json and isinstance(parsed_json["files"], list):
            return parsed_json

        normalized = {
            "files": [],
            "commands": parsed_json.get("COMMANDS", []),
            "tests": parsed_json.get("TESTS", []),
            "description": (
                parsed_json.get("description") or json.dumps(parsed_json)[:500]
            ),
        }

        for file_change in parsed_json.get("FILE_CHANGES", []):
            if not isinstance(file_change, dict):
                continue

            normalized["files"].append(
                {
                    "path": (
                        file_change.get("path")
                        or file_change.get("file")
                        or file_change.get("filename")
                        or ""
                    ),
                    "action": file_change.get("action", "modify"),
                    "dependencies": file_change.get("dependencies", []),
                    "priority": int(file_change.get("priority", 0) or 0),
                    "content": file_change.get("content", ""),
                }
            )

        return normalized

    def parse_plan(self, plan_text: str) -> dict[str, Any]:
        """
        Parse Gemini-generated plan into structured format

        Expected format:
        ```
        FILE_CHANGES:
        - file: path/to/file.py
          action: create|modify|delete
          dependencies: [path/to/file1.py, path/to/file2.py]  # Optional
          priority: 0  # Optional, higher = earlier
          content: |
            code content here
        ```
        """
        try:
            stripped_plan = plan_text.strip()

            # Accept raw JSON plans stored directly in the database.
            if stripped_plan.startswith("{"):
                try:
                    parsed_json = json.loads(stripped_plan)
                    if isinstance(parsed_json, dict):
                        return self._normalize_json_plan(parsed_json)
                except json.JSONDecodeError:
                    pass  # Fall through to fenced JSON / YAML-like parser

            # Try to extract JSON if present
            json_match = re.search(r"```json\n(.*?)\n```", plan_text, re.DOTALL)
            if json_match:
                try:
                    parsed_json = json.loads(json_match.group(1))
                    if isinstance(parsed_json, dict):
                        return self._normalize_json_plan(parsed_json)
                except json.JSONDecodeError:
                    pass  # Fall through to YAML-like parser

            # Parse file changes section
            parsed = {
                "files": [],
                "commands": [],
                "tests": [],
                "description": plan_text[:500],  # First 500 chars as description
            }

            # Extract file changes (enhanced with dependencies)
            # Accept FILE_CHANGES with or without colon, optional markdown fencing
            file_pattern = r"(?:```\s*)?FILE_CHANGES:?.*?(?=COMMANDS:|```\s*$|$)"
            file_section = re.search(file_pattern, plan_text, re.DOTALL)
            if file_section:
                file_matches = re.finditer(
                    r"- file: (.+?)\n\s+action: (.+?)(?:\n\s+dependencies: \[(.*?)\])?(?:\n\s+priority: (\d+))?(?:\n\s+content: \|\n(.*?))?(?=- file:|COMMANDS:|$)",
                    file_section.group(),
                    re.DOTALL,
                )
                for match in file_matches:
                    deps = []
                    if match.group(3):  # dependencies group
                        deps = [
                            d.strip().strip("'\"") for d in match.group(3).split(",")
                        ]

                    priority = int(match.group(4)) if match.group(4) else 0

                    parsed["files"].append(
                        {
                            "path": match.group(1).strip(),
                            "action": match.group(2).strip(),
                            "dependencies": deps,
                            "priority": priority,
                            "content": (match.group(5) or "").strip(),
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
        """Validate parsed plan structure including dependencies"""
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

                # Validate dependencies
                if "dependencies" in file_change:
                    if not isinstance(file_change["dependencies"], list):
                        return False
                    for dep in file_change["dependencies"]:
                        if not isinstance(dep, str):
                            return False

        return True

    def generate_files_atomic(
        self, parsed_plan: dict[str, Any], dry_run: bool = True
    ) -> dict[str, Any]:
        """
        Generate files using atomic transaction pattern

        Args:
            parsed_plan: Parsed plan from parse_plan()
            dry_run: If True, validate but don't write files

        Returns:
            Dict with execution results
        """
        if not self.validate_plan(parsed_plan):
            raise CodeGenerationError("Invalid plan structure")

        results = {"created": [], "modified": [], "deleted": [], "errors": []}

        # Validate security for all file changes first
        for file_change in parsed_plan.get("files", []):
            file_path = self.repo_path / file_change["path"]

            # Security check: ensure path is within repo
            if not str(file_path.resolve()).startswith(str(self.repo_path.resolve())):
                raise CodeGenerationError(f"Path escape attempt: {file_change['path']}")

        # Create transaction from plan
        transaction = AtomicTransaction(repo_path=self.repo_path)

        for file_change_dict in parsed_plan.get("files", []):
            change = FileChange(
                path=file_change_dict["path"],
                action=file_change_dict["action"],
                content=file_change_dict.get("content", ""),
                dependencies=file_change_dict.get("dependencies", []),
                priority=file_change_dict.get("priority", 0),
            )
            transaction.add_file_change(change)

        # Validate transaction
        is_valid, error = transaction.validate_dependencies()
        if not is_valid:
            raise CodeGenerationError(f"Transaction validation failed: {error}")

        # Execute transaction (or dry-run)
        if dry_run:
            # Validate without executing
            results = {
                "created": [f.path for f in transaction.files if f.action == "create"],
                "modified": [f.path for f in transaction.files if f.action == "modify"],
                "deleted": [f.path for f in transaction.files if f.action == "delete"],
                "errors": [],
                "dry_run": True,
            }
        else:
            results = transaction.execute(str(self.repo_path))
            results["dry_run"] = False

        results["transaction_verified"] = True
        return results

        return True

    def generate_files(
        self, parsed_plan: dict[str, Any], dry_run: bool = True
    ) -> dict[str, Any]:
        """
        Legacy method - delegates to atomic transaction system

        Kept for backward compatibility but uses new atomic patterns internally
        """
        return self.generate_files_atomic(parsed_plan, dry_run=dry_run)

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
        use_atomic_transactions: bool = True,
    ) -> dict[str, Any]:
        """
        End-to-end code generation from Gemini plan with optional atomic transactions

        Phase 7 Enhancement: Supports atomic multi-file transactions with rollback

        Args:
            gemini_plan: Raw text from Gemini analysis
            repo_path: Repository root path
            dry_run: If True, don't write files
            validate_syntax: If True, validate Python file syntax
            use_atomic_transactions: If True, use atomic transaction pattern (Phase 7 default)

        Returns:
            Generation results including created/modified/deleted files
        """
        self.repo_path = Path(repo_path)

        # Parse the plan
        parsed = self.parse_plan(gemini_plan)

        # Generate files using selected strategy
        if use_atomic_transactions:
            results = self.generate_files_atomic(parsed, dry_run=dry_run)
        else:
            results = self.generate_files(parsed, dry_run=dry_run)

        # Validate syntax if requested
        if validate_syntax and not dry_run:
            py_files = results.get("created", []) + results.get("modified", [])
            errors = []
            for py_file in py_files:
                if str(py_file).endswith(".py"):
                    try:
                        self.validate_python_syntax(py_file)
                    except CodeGenerationError as e:
                        errors.append({"file": py_file, "error": str(e)})

            if errors:
                results["syntax_errors"] = errors

        results["parsed_plan"] = parsed
        results["atomic_transactions_enabled"] = use_atomic_transactions
        return results

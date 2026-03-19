#!/usr/bin/env python3
"""
KOR'TANA Autonomous Execution System
=====================================

Core autonomy engine for KOR'TANA. Executes all automatable steps without approval,
only interrupting for human-exclusive actions (credential creation).

Philosophy: Maximum autonomy with minimal human interaction.
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import argparse
import shutil
from getpass import getpass

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
ENV_FILE = BACKEND_DIR / ".env"
ENV_EXAMPLE = BACKEND_DIR / ".env.example"
LOG_FILE = PROJECT_ROOT / "AUTONOMY_EXECUTION.log"

# Database configuration
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "kortana_db"

# Server configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_command(cmd: str, shell: bool = True, check: bool = True) -> Tuple[int, str, str]:
    """Execute a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return 1, "", str(e)

def check_file_exists(path: Path, name: str) -> bool:
    """Check if a file exists and log result."""
    if path.exists():
        logger.info(f"[OK] {name} found: {path}")
        return True
    else:
        logger.error(f"[FAIL] {name} not found: {path}")
        return False

def check_postgres_available() -> bool:
    """Check if PostgreSQL is available."""
    code, _, _ = run_command("psql --version")
    return code == 0

def get_secure_input(prompt: str, mask: bool = True) -> str:
    """Get input from user, optionally masked."""
    if mask:
        return getpass(prompt)
    else:
        return input(prompt)

def read_env_template() -> Dict[str, str]:
    """Read environment template and extract field names."""
    template_vars = {}
    if ENV_EXAMPLE.exists():
        with open(ENV_EXAMPLE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _ = line.split('=', 1)
                    template_vars[key.strip()] = ""
    return template_vars

def write_env_file(env_vars: Dict[str, str]) -> bool:
    """Write environment variables to .env file."""
    try:
        with open(ENV_FILE, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        logger.info(f"✓ .env file created: {ENV_FILE}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to write .env file: {e}")
        return False

# ============================================================================
# HUMAN-ONLY STEPS (Require user input)
# ============================================================================

def ho_1_github_token() -> Optional[str]:
    """HO-1: Get GitHub token from user."""
    print("\n" + "="*70)
    print("HO-1: GitHub Token")
    print("="*70)
    print("""
CREATE GITHUB TOKEN:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token"
3. Name: KOR-TANA-PRODUCTION
4. Select scopes: repo, workflow, admin:repo_hook
5. Generate and copy token

Token format: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    """)
    
    token = get_secure_input("Paste your GitHub token: ", mask=True)
    if token and len(token) > 10:
        logger.info("✓ GitHub token received")
        return token
    else:
        logger.error("✗ Invalid GitHub token")
        return None

def ho_2_gemini_key() -> Optional[str]:
    """HO-2: Get Gemini API key from user."""
    print("\n" + "="*70)
    print("HO-2: Gemini API Key")
    print("="*70)
    print("""
CREATE GEMINI API KEY:
1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the generated key

Key format: AIzaSy_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
    """)
    
    key = get_secure_input("Paste your Gemini API key: ", mask=True)
    if key and len(key) > 10:
        logger.info("✓ Gemini API key received")
        return key
    else:
        logger.error("✗ Invalid Gemini API key")
        return None

# ============================================================================
# AUTOMATABLE STEPS (No approval needed)
# ============================================================================

def ho_3_create_database(db_password: Optional[str] = None) -> bool:
    """HO-3: Create PostgreSQL database."""
    logger.info("Starting HO-3: Create Database...")
    
    if not check_postgres_available():
        logger.error("✗ PostgreSQL not available")
        return False
    
    # Try to create database
    if db_password:
        cmd = f'psql -U {DB_USER} -h {DB_HOST} -c "CREATE DATABASE {DB_NAME};"'
    else:
        cmd = f'psql -U {DB_USER} -c "CREATE DATABASE {DB_NAME};"'
    
    code, stdout, stderr = run_command(cmd)
    
    if code == 0 or "already exists" in stderr:
        logger.info(f"✓ HO-3 Complete: Database ready ({DB_NAME})")
        return True
    else:
        logger.error(f"✗ HO-3 Failed: {stderr}")
        return False

def ho_4_populate_env(github_token: str, gemini_key: str) -> bool:
    """HO-4: Populate .env file with credentials."""
    logger.info("Starting HO-4: Populate .env...")
    
    if not check_file_exists(ENV_EXAMPLE, ".env.example"):
        return False
    
    try:
        # Read template
        env_vars = {}
        with open(ENV_EXAMPLE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, default_value = line.split('=', 1)
                    key = key.strip()
                    default_value = default_value.strip()
                    
                    # Inject credentials
                    if key == "GITHUB_TOKEN":
                        env_vars[key] = github_token
                    elif key == "GEMINI_API_KEY":
                        env_vars[key] = gemini_key
                    elif key == "DATABASE_URL":
                        env_vars[key] = f"postgresql://{DB_USER}:password@{DB_HOST}:{DB_PORT}/{DB_NAME}"
                    else:
                        env_vars[key] = default_value
        
        # Write .env
        if write_env_file(env_vars):
            logger.info("✓ HO-4 Complete: .env file populated")
            return True
        else:
            return False
            
    except Exception as e:
        logger.error(f"✗ HO-4 Failed: {e}")
        return False

def ho_5_run_migration() -> bool:
    """HO-5: Run database migration."""
    logger.info("Starting HO-5: Run Migration...")
    
    cmd = "alembic upgrade head"
    code, stdout, stderr = run_command(cmd)
    
    if code == 0:
        logger.info("✓ HO-5 Complete: Migration successful")
        return True
    else:
        logger.error(f"✗ HO-5 Failed: {stderr}")
        logger.info("Hint: Try 'alembic downgrade base' then 'alembic upgrade head'")
        return False

def ho_6_install_dependencies() -> bool:
    """HO-6: Install Python dependencies."""
    logger.info("Starting HO-6: Install Dependencies...")
    
    requirements_file = BACKEND_DIR / "requirements.txt"
    if not check_file_exists(requirements_file, "requirements.txt"):
        return False
    
    cmd = f"pip install -r {requirements_file}"
    code, stdout, stderr = run_command(cmd)
    
    if code == 0:
        logger.info("✓ HO-6 Complete: Dependencies installed")
        return True
    else:
        logger.error(f"✗ HO-6 Failed: {stderr}")
        return False

def ho_7_start_server(background: bool = False) -> bool:
    """HO-7: Start the server."""
    logger.info("Starting HO-7: Start Server...")
    
    cmd = f"python -m uvicorn backend.main:app --reload --host {SERVER_HOST} --port {SERVER_PORT}"
    
    if background:
        logger.info(f"✓ HO-7: Server starting in background at http://localhost:{SERVER_PORT}")
        # Use Popen for background execution
        try:
            subprocess.Popen(cmd, shell=True, cwd=PROJECT_ROOT)
            return True
        except Exception as e:
            logger.error(f"✗ Failed to start server: {e}")
            return False
    else:
        logger.info(f"Server running at http://localhost:{SERVER_PORT}")
        logger.info("Press Ctrl+C to stop")
        code, _, _ = run_command(cmd, check=False)
        return code == 0

def ho_8_verify_health() -> bool:
    """HO-8: Verify health endpoints."""
    logger.info("Starting HO-8: Verify Health...")
    
    import time
    import urllib.request
    
    # Wait for server to be ready
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = urllib.request.urlopen(f"http://localhost:{SERVER_PORT}/health")
            if response.status == 200:
                logger.info("✓ HO-8 Complete: Health endpoints verified")
                return True
        except:
            if attempt < max_attempts - 1:
                logger.info(f"  Waiting for server... ({attempt + 1}/{max_attempts})")
                time.sleep(1)
    
    logger.error("✗ HO-8 Failed: Server not responding")
    return False

# ============================================================================
# ORCHESTRATION
# ============================================================================

def print_banner():
    """Print startup banner."""
    print("\n" + "="*70)
    print("KOR'TANA AUTONOMOUS EXECUTION SYSTEM")
    print("="*70)
    print(f"Project: {PROJECT_ROOT}")
    print(f"Log file: {LOG_FILE}")
    print("="*70 + "\n")

def run_prerequisites_check() -> bool:
    """Check all prerequisites."""
    logger.info("Running prerequisite checks...")
    
    checks = [
        (check_file_exists(PROJECT_ROOT, "Project root"), "Project directory"),
        (check_file_exists(BACKEND_DIR, "Backend directory"), "Backend directory"),
        # (check_postgres_available(), "PostgreSQL availability"),  # Skip for demo
    ]
    
    all_passed = all(check[0] for check in checks)
    
    if all_passed:
        logger.info("✓ All prerequisites passed")
    else:
        logger.error("✗ Some prerequisites failed")
    
    return all_passed

def run_full_autonomy_sequence(github_token: str, gemini_key: str, dry_run: bool = False) -> bool:
    """Execute all automatable steps."""
    logger.info(f"Running full autonomy sequence (dry_run={dry_run})")
    
    steps = [
        ("HO-3", lambda: ho_3_create_database()),
        ("HO-4", lambda: ho_4_populate_env(github_token, gemini_key)),
        ("HO-5", lambda: ho_5_run_migration()),
        ("HO-6", lambda: ho_6_install_dependencies()),
        ("HO-7", lambda: ho_7_start_server(background=True)),
        ("HO-8", lambda: ho_8_verify_health()),
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        print(f"\n{'='*70}")
        print(f"Executing: {step_name}")
        print(f"{'='*70}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would execute: {step_name}")
            results[step_name] = True
        else:
            try:
                success = step_func()
                results[step_name] = success
                if not success:
                    logger.warning(f"Step {step_name} failed, continuing...")
            except Exception as e:
                logger.error(f"Step {step_name} crashed: {e}")
                results[step_name] = False
    
    # Summary
    print(f"\n{'='*70}")
    print("EXECUTION SUMMARY")
    print(f"{'='*70}")
    for step, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {step}")
    
    all_passed = all(results.values())
    if all_passed:
        print(f"\nALL STEPS COMPLETED!")
        print(f"Server should be running at: http://localhost:{SERVER_PORT}")
        print(f"API Docs at: http://localhost:{SERVER_PORT}/docs")
    
    return all_passed

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="KOR'TANA Autonomous Execution System"
    )
    
    parser.add_argument("--all", action="store_true", 
                       help="Execute all automatable steps (HO-3 through HO-8)")
    parser.add_argument("--create-db", action="store_true", 
                       help="Execute HO-3: Create database")
    parser.add_argument("--populate-env", action="store_true", 
                       help="Execute HO-4: Populate .env")
    parser.add_argument("--run-migration", action="store_true", 
                       help="Execute HO-5: Run migration")
    parser.add_argument("--install-deps", action="store_true", 
                       help="Execute HO-6: Install dependencies")
    parser.add_argument("--start-server", action="store_true", 
                       help="Execute HO-7: Start server")
    parser.add_argument("--verify-health", action="store_true", 
                       help="Execute HO-8: Verify health")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run in interactive mode (confirm each step)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would execute without running")
    parser.add_argument("--github-token", type=str, 
                       help="Provide GitHub token directly (not recommended)")
    parser.add_argument("--gemini-key", type=str, 
                       help="Provide Gemini key directly (not recommended)")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Prerequisites check
    if not run_prerequisites_check():
        logger.error("Prerequisites check failed. Aborting.")
        sys.exit(1)
    
    # Determine if we need credentials
    github_token = args.github_token
    gemini_key = args.gemini_key
    
    # Get credentials if running full sequence
    if args.all or args.populate_env:
        if not github_token:
            github_token = ho_1_github_token()
            if not github_token:
                logger.error("GitHub token required. Aborting.")
                sys.exit(1)
        
        if not gemini_key:
            gemini_key = ho_2_gemini_key()
            if not gemini_key:
                logger.error("Gemini API key required. Aborting.")
                sys.exit(1)
    
    # Execute requested steps
    if args.all:
        success = run_full_autonomy_sequence(github_token, gemini_key, args.dry_run)
        sys.exit(0 if success else 1)
    
    # Individual step execution
    steps = {
        "create_db": (ho_3_create_database, ()),
        "populate_env": (ho_4_populate_env, (github_token, gemini_key)),
        "run_migration": (ho_5_run_migration, ()),
        "install_deps": (ho_6_install_dependencies, ()),
        "start_server": (ho_7_start_server, ()),
        "verify_health": (ho_8_verify_health, ()),
    }
    
    any_executed = False
    for arg_name, (func, args) in steps.items():
        if getattr(args, arg_name):
            if args.dry_run:
                logger.info(f"[DRY RUN] Would execute: {arg_name}")
            else:
                logger.info(f"Executing: {arg_name}")
                func(*args)
            any_executed = True
    
    if not any_executed:
        parser.print_help()
        logger.info("Use --all to execute all automatable steps")

if __name__ == "__main__":
    main()

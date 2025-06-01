"""
Automated validation script for Google GenAI setup
"""

import logging
import os
import subprocess
import sys

# Configure logging with Windows-compatible formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("genai_validation.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def check_environment():
    """Verify environment setup"""
    logger.info("[INFO] Checking environment setup...")

    # Check Python version
    logger.info(f"Python version: {sys.version}")

    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("[ERROR] GOOGLE_API_KEY not found in environment")
        return False
    logger.info("[SUCCESS] GOOGLE_API_KEY found in environment")

    return True


def install_dependencies():
    """Install required packages"""
    logger.info("[INFO] Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        logger.info("[SUCCESS] Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"[ERROR] Failed to install dependencies: {e}")
        return False


def run_tests():
    """Execute test suite"""
    logger.info("[INFO] Running tests...")
    try:
        result = subprocess.run(
            [sys.executable, "test_autonomous_consciousness.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        logger.info("Test output:")
        logger.info(result.stdout)

        if result.returncode != 0:
            logger.error(f"[ERROR] Tests failed with error:\n{result.stderr}")
            return False

        logger.info("[SUCCESS] Tests completed successfully")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Error running tests: {e}")
        return False


def main():
    """Main validation process"""
    logger.info("[START] Starting GenAI validation process...")

    # Check environment
    if not check_environment():
        logger.error("[ERROR] Environment validation failed")
        return False

    # Install dependencies
    if not install_dependencies():
        logger.error("[ERROR] Dependency installation failed")
        return False

    # Run tests
    if not run_tests():
        logger.error("[ERROR] Test execution failed")
        return False

    logger.info("[SUCCESS] GenAI validation process completed successfully")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

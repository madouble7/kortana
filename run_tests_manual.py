import os
import sys

import pytest

# Add src to sys.path
sys.path.insert(0, os.path.abspath("src"))

# Run pytest
if __name__ == "__main__":
    retcode = pytest.main(["tests/test_model_router.py", "tests/test_brain.py", "-v"])
    sys.exit(retcode)

#!/usr/bin/env python
"""
Very simple diagnostic test
"""

import os
import sys

print("=" * 50)
print("VERY SIMPLE DIAGNOSTIC TEST")
print("=" * 50)
print("\nThis should print normally.")
print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("This script is at:", __file__)
print("Done!")

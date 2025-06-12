#!/usr/bin/env python3
"""
Analyze Ruff static analysis results
"""

import json
from collections import defaultdict


def analyze_ruff_results():
    try:
        with open("ruff_analysis.json") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading ruff_analysis.json: {e}")
        return

    print("=== RUFF ANALYSIS SUMMARY ===")
    print(f"Total Issues Found: {len(data)}")

    # Group by error codes
    codes = defaultdict(list)
    severity_counts = defaultdict(int)

    for item in data:
        code = item["code"]
        filename = item["filename"].split("\\")[-1]  # Get just filename
        codes[code].append(filename)

        # Categorize severity
        if code.startswith("E"):
            severity_counts["Error"] += 1
        elif code.startswith("W"):
            severity_counts["Warning"] += 1
        elif code.startswith("F"):
            severity_counts["Flake8"] += 1
        else:
            severity_counts["Other"] += 1

    print("\nSeverity Breakdown:")
    for severity, count in severity_counts.items():
        print(f"  {severity}: {count} issues")

    print("\nIssue Breakdown by Code:")
    for code, files in sorted(codes.items()):
        unique_files = list(set(files))
        print(f"  {code}: {len(files)} instances across {len(unique_files)} file(s)")

        if len(unique_files) <= 3:
            for f in unique_files:
                print(f"    - {f}")
        else:
            for f in unique_files[:2]:
                print(f"    - {f}")
            print(f"    - ... and {len(unique_files) - 2} more files")

    # Identify worst files
    file_counts = defaultdict(int)
    for item in data:
        filename = item["filename"].split("\\")[-1]
        file_counts[filename] += 1

    print("\nWorst Files (most issues):")
    sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
    for filename, count in sorted_files[:5]:
        print(f"  {filename}: {count} issues")


if __name__ == "__main__":
    analyze_ruff_results()

#!/usr/bin/env python3
"""
Pinecone Dependency Diagnostic Tool
"""

import sys

sys.path.insert(0, '.')

def diagnose_pinecone():
    """Diagnose the exact Pinecone import issue."""
    print("=== Pinecone Dependency Diagnostic ===")

    try:
        import pinecone
        print("SUCCESS: Pinecone imported successfully")
        print(f"Version: {getattr(pinecone, '__version__', 'Unknown')}")

        # Check for common attributes
        attrs = [attr for attr in dir(pinecone) if not attr.startswith('_')]
        print(f"Available attributes: {attrs[:10]}...")

        # Check for the problematic 'Pinecone' class
        if hasattr(pinecone, 'Pinecone'):
            print("SUCCESS: pinecone.Pinecone class found")
        else:
            print("ISSUE: pinecone.Pinecone class NOT found")
            print("This suggests an older version or different API structure")

            # Check for alternative initialization methods
            alternatives = ['init', 'Client', 'PineconeClient', 'connect']
            found_alternatives = [alt for alt in alternatives if hasattr(pinecone, alt)]
            print(f"Available alternatives: {found_alternatives}")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        print("Pinecone is not installed or not accessible")

    except Exception as e:
        print(f"OTHER ERROR: {e}")

def find_pinecone_usage():
    """Find where Pinecone is being used in the codebase."""
    print("\n=== Finding Pinecone Usage ===")

    import glob

    # Search for pinecone imports in Python files
    python_files = glob.glob("**/*.py", recursive=True)
    pinecone_files = []

    for file_path in python_files:
        try:
            with open(file_path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'pinecone' in content.lower():
                    pinecone_files.append(file_path)
        except:
            continue

    print(f"Files mentioning 'pinecone': {len(pinecone_files)}")
    for file_path in pinecone_files[:5]:  # Show first 5
        print(f"  - {file_path}")

def main():
    """Run the diagnostic."""
    diagnose_pinecone()
    find_pinecone_usage()

    print("\n=== Recommendation ===")
    print("Based on the results above, we can:")
    print("1. Update Pinecone to the latest version")
    print("2. Fix the import/initialization code")
    print("3. Mock Pinecone for testing purposes")

if __name__ == "__main__":
    main()

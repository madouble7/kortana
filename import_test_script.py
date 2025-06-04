import sys

print("--- sys.path ---")
for p in sys.path:
    print(p)
print("--- end sys.path ---")

try:
    print("\nSuccessfully imported load_config from kortana.config")
except Exception as e:
    print(f"\nError: {e}")

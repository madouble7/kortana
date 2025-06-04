# c:\kortana\check_covenant_rules.py
print("--- Starting check_covenant_rules.py ---")
try:
    # Attempt to make 'src' importable if 'python check_covenant_rules.py' is run from c:\kortana
    import os
    import sys

    if os.getcwd() not in sys.path:  # If CWD is not in sys.path
        if os.path.join(os.getcwd(), "src") not in sys.path:  # and src is not
            sys.path.insert(
                0, os.getcwd()
            )  # then add CWD which should make 'src.config' findable

    from config import (
        load_config,  # Or use 'from src.config import load_config' if that's correct for your structure
    )

    print("Successfully imported load_config from config module.")

    settings = load_config()
    print(f"load_config() executed. Type of settings object: {type(settings)}")

    print("\n--- Checking for covenant_rules attribute ---")
    if hasattr(settings, "covenant_rules"):
        print("SUCCESS: Attribute 'covenant_rules' EXISTS on the settings object.")
        print(f"Type of settings.covenant_rules: {type(settings.covenant_rules)}")
        print("Content of settings.covenant_rules:")
        # Pretty print if it's a dict or list, otherwise just print
        if isinstance(settings.covenant_rules, (dict, list)):
            import json

            print(json.dumps(settings.covenant_rules, indent=2))
        else:
            print(settings.covenant_rules)
    else:
        print(
            "FAILURE: Attribute 'covenant_rules' DOES NOT EXIST on the settings object."
        )
        print("\nAll attributes on settings object:")
        import inspect

        for name, value in inspect.getmembers(settings):
            if not name.startswith("_") and not inspect.ismethod(value):
                print(f"  {name}: {type(value)}")

except ImportError as e:
    print(
        f"ImportError: {e}. Could not import 'load_config'. Check PYTHONPATH and package structure."
    )
    print("Current sys.path:")
    for pth in sys.path:
        print(f"  - {pth}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback

    print("Traceback:")
    print(traceback.format_exc())

print("--- End of check_covenant_rules.py ---")

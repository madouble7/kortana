# C:\project-kortana\verify_brain_init.py
import traceback

print("--- Starting verify_brain_init.py ---")  # ASCII output
output_lines = []
final_outcome_message = "Test script did not complete as expected."  # Default

try:
    output_lines.append("Attempting to import load_config from kortana.config...")
    from kortana.config import (
        load_config,  # Assuming src is on PYTHONPATH for 'kortana' package
    )

    output_lines.append("SUCCESS: Imported load_config from kortana.config.")

    output_lines.append("\nAttempting to call load_config()...")
    settings = load_config()
    output_lines.append(
        f"SUCCESS: Called load_config(), type of settings: {type(settings)}"
    )

    # We can optionally log a part of settings here if needed for debugging, keeping it concise
    # output_lines.append(f"DEBUG: settings.app.name (example): {getattr(getattr(settings, 'app', {}), 'name', 'Not found')}")

    output_lines.append(
        "\nAttempting to import ChatEngine and Brain from kortana.core.brain..."
    )
    from kortana.core.brain import (  # Assuming Brain alias exists in brain.py
        Brain,
        ChatEngine,
    )

    output_lines.append("SUCCESS: Imported ChatEngine and Brain.")

    output_lines.append("\nAttempting to instantiate ChatEngine(settings=settings)...")
    engine = ChatEngine(settings=settings)
    output_lines.append("SUCCESS: Instantiated ChatEngine.")
    output_lines.append(f"  Instance type: {type(engine)}")

    output_lines.append("\nAttempting to instantiate Brain(settings=settings)...")
    brain_alias_instance = Brain(settings=settings)
    output_lines.append("SUCCESS: Instantiated Brain alias.")
    output_lines.append(f"  Instance type: {type(brain_alias_instance)}")

    final_outcome_message = (
        "OVERALL_SUCCESS: All core imports and instantiations successful."
    )

except ImportError as ie:
    output_lines.append(f"\nIMPORT_ERROR: {ie}")
    output_lines.append("Traceback:")
    output_lines.append(traceback.format_exc())
    final_outcome_message = f"FAILURE: Encountered ImportError - {ie}"
except Exception as e:
    output_lines.append(f"\nGENERAL_ERROR: {e}")
    output_lines.append("Traceback:")
    output_lines.append(traceback.format_exc())
    final_outcome_message = f"FAILURE: Encountered Exception - {e}"

# Write detailed output to a log file
output_file_path = r"C:\project-kortana\verify_brain_init_output.txt"
header = "--- Output of verify_brain_init.py ---\n"

# Ensure output_lines always has some content before writing
if not output_lines:
    output_lines.append(
        "No specific diagnostic lines were generated before file write attempt."
    )

try:
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(header)
        for line_content in output_lines:  # Renamed variable to avoid conflict
            f.write(line_content + "\n")
    # This message below will go to standard output when the script is run
    print(
        f"VERIFY_BRAIN_INIT_MSG: Diagnostic output written to {output_file_path}. Final outcome: {final_outcome_message}"
    )
except Exception as e_file:
    # This message below will go to standard output (or standard error) if an exception occurs
    print(
        f"VERIFY_BRAIN_INIT_ERROR: Failed to write to {output_file_path}. Error: {e_file}. Final outcome: {final_outcome_message}"
    )

print("--- End of verify_brain_init.py ---")  # ASCII output

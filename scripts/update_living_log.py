import re
import sys
from datetime import datetime

BLUEPRINT_PATH = "KOR'TANA_BLUEPRINT.md"
LIVING_LOG_HEADER = "Living Log / Agent Updates"


def append_living_log_entry(message: str):
    try:
        with open(BLUEPRINT_PATH, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[ERROR] {BLUEPRINT_PATH} not found.")
        sys.exit(1)

    # Find the Living Log section
    pattern = rf"(#+\s*{re.escape(LIVING_LOG_HEADER)}.*?)(\n#+ |\Z)"  # Section until next header or EOF
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if not match:
        print(f"[ERROR] '{LIVING_LOG_HEADER}' section not found in {BLUEPRINT_PATH}.")
        sys.exit(1)

    section_start, section_end = match.start(1), match.end(1)
    log_section = content[section_start:section_end]

    # Prepare new entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n- [{timestamp}] {message}"

    # Insert entry before the next section header or EOF
    new_log_section = log_section.rstrip() + entry + "\n"
    new_content = content[:section_start] + new_log_section + content[section_end:]

    with open(BLUEPRINT_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("[INFO] Entry added to Living Log.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_living_log.py <message>")
        sys.exit(1)
    message = " ".join(sys.argv[1:])
    append_living_log_entry(message)


if __name__ == "__main__":
    main()

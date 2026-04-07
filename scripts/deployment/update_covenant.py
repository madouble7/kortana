#!/usr/bin/env python3
"""
Update COVENANT_INDEX.md with latest sync timestamp
"""

import re
from datetime import datetime
from pathlib import Path


def update_covenant():
    """Update COVENANT_INDEX.md with latest sync time"""
    covenant_file = Path("COVENANT_INDEX.md")

    if not covenant_file.exists():
        return

    content = covenant_file.read_text()
    now = datetime.now().isoformat()

    # Update last_sync timestamp
    pattern = r"last_sync: .*"
    replacement = f"last_sync: {now}"

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
    else:
        # Add to front matter if not exists
        if content.startswith("---"):
            end_marker = content.find("---", 3)
            if end_marker > 0:
                front_matter_end = end_marker + 3
                content = (
                    content[:front_matter_end]
                    + f"\nlast_sync: {now}"
                    + content[front_matter_end:]
                )

    covenant_file.write_text(content)
    print(f"✓ COVENANT_INDEX.md updated with timestamp: {now}")


if __name__ == "__main__":
    update_covenant()

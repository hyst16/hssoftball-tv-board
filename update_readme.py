#!/usr/bin/env python3
"""Generate the README office mappings from teams.json."""

import json
import re
from pathlib import Path

REPO_OWNER = "hyst16"
REPO_NAME = "hssoftball-tv-board"
TEAMS_FILE = Path("teams.json")
README_FILE = Path("README.md")


def generate_office_section(teams_data):
    if not teams_data:
        return "<!-- offices-start -->\n\nNo office mappings found.\n\n<!-- offices-end -->"

    lines = [
        "<!-- offices-start -->\n",
        "## Office URL mappings\n",
        "Use the links to open each office directly:\n",
    ]
    for office_key in sorted(teams_data):
        lines.append(
            f"\n- [{office_key}](https://{REPO_OWNER}.github.io/"
            f"{REPO_NAME}/?office={office_key})\n"
        )
        lines.extend(f"  - {team}\n" for team in teams_data[office_key])
    lines.append("\n<!-- offices-end -->")
    return "".join(lines)


def main():
    teams_data = json.loads(TEAMS_FILE.read_text(encoding="utf-8"))
    readme = README_FILE.read_text(encoding="utf-8")
    updated = re.sub(
        r"<!-- offices-start -->.*?<!-- offices-end -->",
        generate_office_section(teams_data),
        readme,
        flags=re.DOTALL,
    )
    if updated == readme:
        print("No README changes needed.")
        return

    README_FILE.write_text(updated, encoding="utf-8")
    print("Updated README.md")


if __name__ == "__main__":
    main()

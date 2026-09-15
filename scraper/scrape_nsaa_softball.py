#!/usr/bin/env python3
"""Download NSAA softball schedules and write data/softball.json."""

import csv
import json
import re
import time
from datetime import datetime
from io import StringIO
from pathlib import Path

import requests

CLASSES = ("A", "B", "C")
EXPORT_URL = "https://secure.nsaahome.org/wildcards/schedules/export.php"
OUTFILE = Path(__file__).resolve().parents[1] / "data" / "softball.json"


def normalize_team(name):
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def convert_date(value):
    value = value.strip()
    try:
        return datetime.strptime(
            f"{value} {datetime.now().year}", "%a %d %b %Y"
        ).strftime("%m/%d/%y")
    except ValueError:
        return value


def parse_result(score):
    score = score.replace("&ndash;", "-").replace("–", "-").strip()
    match = re.match(r"(\d+)-(\d+)", score)
    if not match:
        return "", score or "-"

    left, right = (int(value) for value in match.groups())
    if left > right:
        return "W", score
    if left < right:
        return "L", score
    return "T", score


def download_class(class_name):
    response = requests.get(
        EXPORT_URL,
        params={"sport": "sb", "class": class_name},
        timeout=60,
    )
    response.raise_for_status()
    return response.text


def main():
    by_team = {}

    for class_name in CLASSES:
        print(f"Downloading class {class_name}")
        reader = csv.DictReader(StringIO(download_class(class_name)))

        for row in reader:
            school = row.get("School", "").strip()
            if not school:
                continue

            score = row.get("Score", "").strip()
            result, score = parse_result(score)
            wins = row.get("Wins", "").strip()
            losses = row.get("Losses", "").strip()

            game = {
                "Date": convert_date(row.get("Date", "")),
                "Opponent": row.get("Opponent", "").strip(),
                "Class": row.get("Class", "").strip(),
                "W-L": f"{wins}-{losses}" if wins and losses else "-",
                "Div": row.get("Division", "").strip() or "-",
                "W/L": result,
                "Score": score,
                "Tournament Name": row.get("Tournament", "").strip(),
                "Tournament Location": row.get("Tournament Location", "").strip(),
                "_team": school,
                "_team_display": school,
                "_class": class_name,
            }
            by_team.setdefault(normalize_team(school), []).append(game)

    payload = {"updated": int(time.time()), "by_team": by_team}
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTFILE} for {len(by_team)} teams")


if __name__ == "__main__":
    main()

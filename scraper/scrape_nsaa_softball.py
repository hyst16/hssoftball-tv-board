#!/usr/bin/env python3
"""
Scrape NSAA softball class pages (A/B/C) and build data/softball.json.
Keeps Tournament Name/Location and handles pages without <caption>.
"""

import json, time, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

CLASS_URLS = {
    "A": "https://nsaa-static.s3.amazonaws.com/calculate/showclasssbA.html",
    "B": "https://nsaa-static.s3.amazonaws.com/calculate/showclasssbB.html",
    "C": "https://nsaa-static.s3.amazonaws.com/calculate/showclasssbC.html",
}

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "softball.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Columns we preserve
KEEP_COLS = [
    "Date", "Opponent", "Class", "W-L", "W/L", "Score",
    "Tournament Name", "Tournament Location", "Site", "Time", "Home/Away",
]

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

def strip_record(name_with_record: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", clean(name_with_record))

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

TEAM_PAT = re.compile(r"([A-Za-z][A-Za-z0-9 .@&'’/-]+)\s*\(\d+-\d+\)")

def extract_team_name_for_table(table):
    """Return (team_without_record, full_text_with_record) or (None, None)."""
    # 1) <caption>Team (x-y)</caption>
    cap = table.find("caption")
    if cap:
        full = clean(cap.get_text())
        return strip_record(full), full

    # 2) Nearby text like "Adams Central (1-4)"
    steps = 0
    node = table
    while node and steps < 80:
        node = node.previous_element
        steps += 1
        if not node:
            break
        text = None
        if hasattr(node, "get_text"):
            text = clean(node.get_text())
        elif isinstance(node, str):
            text = clean(node)
        if not text:
            continue
        m = TEAM_PAT.search(text)
        if m:
            full = m.group(0)
            return strip_record(full), full

    # 3) Excel link like "Click Here for Excel Export (Adams Central)"
    a = table.find_previous("a", string=re.compile(r"Click Here for Excel Export", re.I))
    if a:
        t = clean(a.get_text())
        m = re.search(r"\(([^)]+)\)", t)
        if m:
            full = m.group(1)
            return strip_record(full), full

    return None, None

def parse_class_page(html: str, cls_code: str):
    soup = BeautifulSoup(html, "html.parser")
    by_team = {}

    for table in soup.find_all("table"):
        team, team_display = extract_team_name_for_table(table)
        if not team:
            continue
        key = norm(team)

        # Find the header row
        hdr_tr = None
        headers = []
        for tr in table.find_all("tr"):
            cells = [clean(td.get_text()) for td in tr.find_all(["td", "th"])]
            if not cells:
                continue
            if "Date" in cells and any(x in cells for x in ["Opponent", "Opponents", "Opponents:", "Tournament Name"]):
                hdr_tr = tr
                headers = cells
                break
        if not hdr_tr:
            continue

        rows = []
        for tr in hdr_tr.find_next_siblings("tr"):
            text_line = tr.get_text(" ", strip=True)

            # End-of-table guard
            if "Total Points:" in text_line:
                break

            # Many NSAA tables put an <hr> row immediately after the header.
            # Don't stop here—just skip it.
            if tr.find("hr"):
                continue

            tds = tr.find_all(["td", "th"])
            if not tds:
                continue
            cells = [clean(td.get_text()) for td in tds]
            if not cells:
                continue

            # Skip repeated headers and the "Opponents:" section header
            if cells[0] == "Date":
                continue
            if cells[0] and cells[0].lower().startswith("opponents"):
                continue

            row = {}
            for i in range(min(len(headers), len(cells))):
                h = headers[i]
                v = cells[i]
                if h in KEEP_COLS:
                    row[h] = v

            if not row:
                continue

            row["_team"] = team
            row["_team_display"] = team_display
            row["_class"] = cls_code
            rows.append(row)

        if rows:
            by_team.setdefault(key, []).extend(rows)

    return by_team

def main():
    all_teams = {}
    for cls, url in CLASS_URLS.items():
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = parse_class_page(r.text, cls)
        for k, rows in data.items():
            all_teams.setdefault(k, []).extend(rows)

    payload = {"updated": int(time.time()), "by_team": all_teams}
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {OUT_PATH} (teams: {len(all_teams)})")

if __name__ == "__main__":
    main()

import json, time, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# NSAA softball class pages
CLASS_URLS = {
    "A": "https://nsaa-static.s3.amazonaws.com/calculate/showclasssbA.html",
    "B": "https://nsaa-static.s3.amazonaws.com/calculate/showclasssbB.html",
    "C": "https://nsaa-static.s3.amazonaws.com/calculate/showclasssbC.html",
}

# Output path
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "softball.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Only keep the columns we actually display
KEEP_COLS = [
    "Date", "Opponent", "Class", "W-L", "W/L", "Score",
    "Tournament Name", "Tournament Location", "Site", "Time", "Home/Away"
]

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

def strip_record(name_with_record: str) -> str:
    # "Adams Central (1-4)" -> "Adams Central"
    return re.sub(r"\s*\([^)]*\)\s*$", "", clean(name_with_record))

def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

def has_totals_block(tr) -> bool:
    txt = tr.get_text(" ", strip=True)
    return "Total Points:" in txt or "Total" in txt and "Points" in txt

def parse_class_page(html: str, cls_code: str):
    soup = BeautifulSoup(html, "html.parser")
    by_team = {}

    for table in soup.find_all("table"):
        cap = table.find("caption")
        if not cap:
            continue
        team_display = clean(cap.get_text())          # e.g., "Adams Central (1-4)"
        team = strip_record(team_display)             # "Adams Central"
        key = norm(team)

        # headers row (find the row that contains "Date" and "Opponent")
        hdr_tr = None
        headers = []
        for tr in table.find_all("tr"):
            cells = [clean(td.get_text()) for td in tr.find_all("td")]
            if cells and "Date" in cells and ("Opponent" in cells or "Opponents:" in " ".join(cells)):
                hdr_tr = tr
                headers = cells
                break
        if not hdr_tr:
            continue

        # collect rows after header until totals block
        rows = []
        for tr in hdr_tr.find_next_siblings("tr"):
            # stop at totals/footer block
            if tr.find("hr") or has_totals_block(tr):
                break

            tds = tr.find_all("td")
            if not tds:
                continue
            cells = [clean(td.get_text()) for td in tds]
            if not cells:
                continue

            # Skip header-like repeater rows
            if cells[0] == "Date":
                continue

            # Map cells to headers; only keep whitelisted columns
            row = {}
            for i in range(min(len(headers), len(cells))):
                h = headers[i]
                v = cells[i]
                if h in KEEP_COLS:
                    row[h] = v

            if not row:
                continue

            # Some pages inject a section header "Opponents:" row—skip it
            opp = row.get("Opponent", "")
            if opp.lower().startswith("opponents"):
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

    payload = {
        "updated": int(time.time()),
        "by_team": all_teams
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {OUT_PATH} (teams: {len(all_teams)})")

if __name__ == "__main__":
    main()

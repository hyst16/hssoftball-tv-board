# HS Softball TV — Office URL Guide

This repository powers HS softball TV boards. Show a curated group of teams by
visiting a GitHub Pages URL with an office key.

## Quick start

- [Debug / Teams Builder](https://hyst16.github.io/hssoftball-tv-board/debug.html)
- Office URL format:
  `https://hyst16.github.io/hssoftball-tv-board/?office=<office-key>`
- Example:
  [Mead TV](https://hyst16.github.io/hssoftball-tv-board/?office=mead-office)

## Office URL mappings and teams

The section below is generated from `teams.json` during the scheduled update.

<!-- offices-start -->
## Office URL mappings
Use the links to open each office directly:

- [mead-office](https://hyst16.github.io/hssoftball-tv-board/?office=mead-office)
  - Bishop Neumann
  - Wahoo
  - Yutan/Mead

- [northbend-office](https://hyst16.github.io/hssoftball-tv-board/?office=northbend-office)
  - North Bend Central
  - Arlington
  - Logan View/Scribner-Snyder

- [tarnov-office](https://hyst16.github.io/hssoftball-tv-board/?office=tarnov-office)
  - Columbus
  - Columbus Lakeview
  - Twin River

- [yanka-office](https://hyst16.github.io/hssoftball-tv-board/?office=yanka-office)
  - Aquinas Catholic
  - Blue River

<!-- offices-end -->

## Editing teams

1. Use the Debug / Teams Builder page to select teams and preview `teams.json`.
2. Copy the JSON, then use its **Edit on GitHub** link.
3. Paste the JSON and commit it to `main`.

Team matching ignores case and punctuation. If a team is marked missing in the
debug page, choose the matching NSAA team name and save the updated mapping.

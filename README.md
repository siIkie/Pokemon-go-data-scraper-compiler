# Pokemon-go-data-scraper-compiler
Proactively scrapes and compiles pokemon go data for up to date LLM training. 

# Pokémon GO Event Library + Digest Toolkit

This gives you a **self-updating local library** of event posts and a **digest builder** you can run offline.

## Files
- `build_pogo_library.py` — Crawls and saves **all event posts** from Niantic News (RSS + archive pages) and Leek Duck (events + calendar). Produces HTML files and indexes (`index.json`).
- `digest_from_library.py` — Parses the saved HTML (no internet), outputs a consolidated **Excel digest** (and optional **ICS** calendar).

## Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Build Your Library
```bash
# One month
python build_pogo_library.py --month 2025-09 --out pogo_library

# Date range
python build_pogo_library.py --start 2024-06-01 --end 2025-09-30 --out pogo_library
```
This creates:
```
pogo_library/
  niantic/
    2025-09-10_community-day-xyz.html
    ...
    index.json
  leekduck/
    2025-09-01_events.html
    2025-09-01_calendar.html
    ...
    index.json
library_index.json
```

## Build the Digest (Offline)
```bash
python digest_from_library.py --lib pogo_library --out POGO_Digest.xlsx --ics POGO_Events.ics
```
Outputs:
- `POGO_Digest.xlsx` (Events + Sources sheets)
- `POGO_Events.ics` (optional calendar export)

## Tips
- Schedule monthly: `cron`/Task Scheduler to run on the 1st of each month.
- Add more sources (e.g., GO Hub) by copying the scraper pattern.
- If a site changes HTML, tweak selectors in `build_pogo_library.py` and `digest_from_library.py`.

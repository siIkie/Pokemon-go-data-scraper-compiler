
#!/usr/bin/env python3
"""
Build an Events digest (Excel + optional ICS) from a local library created by build_pogo_library.py.

Usage:
  python digest_from_library.py --lib pogo_library --out POGO_Digest.xlsx --ics POGO_Events.ics
"""

import argparse
import json
import os
import re
from datetime import datetime, date, timedelta

import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

def _norm_date(s):
    try:
        return dtparser.parse(s).date()
    except Exception:
        return None

def _parse_date_range(text):
    if not text:
        return None, None
    t = re.sub(r"[–—−]", "-", text)
    m = re.search(r"([A-Za-z]{3,9}\.?\s+\d{1,2})(?:\s*-\s*([A-Za-z]{3,9}\.?\s+\d{1,2}))?,?\s*(\d{4})", t)
    if m:
        p1, p2, y = m.groups()
        s = dtparser.parse(f"{p1} {y}", fuzzy=True).date()
        e = dtparser.parse(f"{p2 or p1} {y}", fuzzy=True).date()
        return s, e
    try:
        d = dtparser.parse(t, fuzzy=True).date()
        return d, d
    except Exception:
        return None, None

def parse_html_file(path, source_label):
    html = open(path, "r", encoding="utf-8", errors="ignore").read()
    soup = BeautifulSoup(html, "lxml")
    rows = []

    # Generic card/article parsing
    for art in soup.find_all(["article", "div", "li", "section"], class_=re.compile("(post|article|card|event|calendar|list)", re.I)):
        title_el = art.find(["h1", "h2", "h3"]) or art.select_one("[class*=title]")
        title = (title_el.get_text(" ", strip=True) if title_el else "").strip()
        if not title:
            continue
        date_text = ""
        t_el = art.find("time")
        if t_el:
            date_text = t_el.get_text(" ", strip=True)
        if not date_text:
            m = re.search(r"([A-Za-z]{3,9}\.? \d{1,2}(?:\s*-\s*[A-Za-z]{3,9}\.? \d{1,2})?,?\s*\d{4})", art.get_text(" ", strip=True))
            if m:
                date_text = m.group(1)
        s, e = _parse_date_range(date_text)

        # Category heuristics
        tl = title.lower()
        if "community day classic" in tl:
            cat = "CD Classic"
        elif "community day" in tl:
            cat = "Community Day"
        elif "shadow raid" in tl:
            cat = "Shadow Raid"
        elif "raid" in tl or "mega" in tl or "legendary" in tl:
            cat = "Raid/Mega"
        elif "spotlight hour" in tl:
            cat = "Spotlight"
        elif "research" in tl:
            cat = "Research"
        else:
            cat = "Event/News"

        rows.append({
            "Source": source_label,
            "Month": s.strftime("%Y-%m") if s else "",
            "Start Date": s.isoformat() if s else "",
            "End Date": e.isoformat() if e else "",
            "Event Name": title,
            "Category (CD / CD Classic / Raid / Mega / Shadow Raid / Spotlight / Research / Other)": cat,
            "Featured Pokémon": "",
            "Exclusive/Legacy Move (Yes/No)": "",
            "Move Name": "",
            "League/Use Impact (PvP/Raids)": "",
            "Bonuses (XP/Candy/Stardust/etc.)": "",
            "Shiny Released (Yes/No/Already in Game)": "",
            "Top Counters / Prep Notes": "",
            "Recommended Actions (e.g., Elite TM, Evolve Window)": "",
            "Source URL(s)": "",
            "Raw Summary": art.get_text(" ", strip=True)[:1200],
            "File": os.path.basename(path),
        })
    return rows

def write_ics(df, ics_path):
    def dtfmt(d):
        return datetime.strptime(d, "%Y-%m-%d").strftime("%Y%m%d")
    with open(ics_path, "w", encoding="utf-8") as f:
        f.write("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//POGO Digest//EN\r\n")
        for _, r in df.iterrows():
            if not r["Start Date"]:
                continue
            uid = f"{hash((r['Event Name'], r['Start Date']))}@pogo-digest"
            start = dtfmt(r["Start Date"])
            end = dtfmt(r["End Date"] or r["Start Date"])
            if end < start: end = start
            f.write("BEGIN:VEVENT\r\n")
            f.write(f"UID:{uid}\r\n")
            f.write(f"DTSTART;VALUE=DATE:{start}\r\n")
            f.write(f"DTEND;VALUE=DATE:{end}\r\n")
            f.write(f"SUMMARY:{r['Event Name']}\r\n")
            desc = (r.get('Category (CD / CD Classic / Raid / Mega / Shadow Raid / Spotlight / Research / Other)', '') or '')[:200]
            f.write(f"DESCRIPTION:{desc}\r\n")
            f.write("END:VEVENT\r\n")
        f.write("END:VCALENDAR\r\n")

def main():
    ap = argparse.ArgumentParser(description="Create Events digest from local library")
    ap.add_argument("--lib", required=True, help="Library folder produced by build_pogo_library.py")
    ap.add_argument("--out", default="POGO_Digest.xlsx", help="Output Excel path")
    ap.add_argument("--ics", help="Optional ICS path to export calendar")
    args = ap.parse_args()

    ni_idx = os.path.join(args.lib, "niantic", "index.json")
    ld_idx = os.path.join(args.lib, "leekduck", "index.json")
    rows = []

    if os.path.exists(ni_idx):
        ni = json.load(open(ni_idx, "r", encoding="utf-8"))
        for e in ni:
            path = os.path.join(args.lib, "niantic", e.get("file", ""))
            if os.path.exists(path):
                rows.extend(parse_html_file(path, "Niantic"))
    if os.path.exists(ld_idx):
        ld = json.load(open(ld_idx, "r", encoding="utf-8"))
        for e in ld:
            path = os.path.join(args.lib, "leekduck", e.get("file", ""))
            if os.path.exists(path):
                rows.extend(parse_html_file(path, "Leek Duck"))

    cols = [
        "Source",
        "Month",
        "Start Date",
        "End Date",
        "Event Name",
        "Category (CD / CD Classic / Raid / Mega / Shadow Raid / Spotlight / Research / Other)",
        "Featured Pokémon",
        "Exclusive/Legacy Move (Yes/No)",
        "Move Name",
        "League/Use Impact (PvP/Raids)",
        "Bonuses (XP/Candy/Stardust/etc.)",
        "Shiny Released (Yes/No/Already in Game)",
        "Top Counters / Prep Notes",
        "Recommended Actions (e.g., Elite TM, Evolve Window)",
        "Source URL(s)",
        "Raw Summary",
        "File",
    ]
    df = pd.DataFrame(rows, columns=cols).fillna("")
    # sort
    def to_dt(v):
        try:
            return datetime.strptime(v, "%Y-%m-%d")
        except Exception:
            return datetime.max
    if not df.empty:
        df["__k"] = df["Start Date"].apply(to_dt)
        df = df.sort_values(["__k", "Source"]).drop(columns="__k")

    # Sources sheet
    months = sorted(set(df["Month"]) - {""})
    sources_df = pd.DataFrame({
        "Month": months,
        "Niantic News URL": ["https://pokemongolive.com/news/" for _ in months],
        "Leek Duck URL": ["https://leekduck.com/events/" for _ in months],
        "Other source(s)": ["" for _ in months],
        "Notes": ["" for _ in months],
    })

    with pd.ExcelWriter(args.out, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Events")
        sources_df.to_excel(w, index=False, sheet_name="Sources")

    if args.ics:
        write_ics(df, args.ics)

    print(f"Wrote {args.out} with {len(df)} events")
    if args.ics:
        print(f"Wrote {args.ics} (calendar)")

if __name__ == "__main__":
    main()

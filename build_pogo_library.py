#!/usr/bin/env python3
"""
Build a local library of Pokémon GO event posts (HTML + index.json).

Sources:
- Niantic News (RSS + archive pagination)
- Leek Duck (Events + Calendar)

Creates a folder like:
  pogo_library/
    niantic/
      2025-09-10_community-day-solosis.html
      ...
      index.json
    leekduck/
      2025-09-01_events.html
      2025-09-01_calendar.html
      ...
      index.json
  library_index.json

Usage:
  python build_pogo_library.py --out pogo_library --month 2025-09
  python build_pogo_library.py --out pogo_library --start 2024-06-01 --end 2025-09-30

Requires: requests, beautifulsoup4, feedparser, python-dateutil, lxml
"""

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta, date
from urllib.parse import urljoin, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

NIANTIC_NEWS = "https://pokemongolive.com/news/"
NIANTIC_RSS = "https://pokemongolive.com/news/?format=rss"
LEEK_EVENTS = "https://leekduck.com/events/"
LEEK_CAL = "https://leekduck.com/calendar/"

UA = {"User-Agent": "Mozilla/5.0 (POGO-Library-Builder/1.0)"}


# ------------------------
# Utils
# ------------------------
def normalize_date(x):
    if isinstance(x, (datetime, date)):
        return x.date() if isinstance(x, datetime) else x
    try:
        return dtparser.parse(x).date()
    except Exception:
        return None


def safe_slug(text, maxlen=120):
    t = re.sub(r"\s+", "-", (text or "").strip().lower())
    t = re.sub(r"[^a-z0-9\-]+", "", t)
    return t[:maxlen] or "untitled"


def mkdirp(p):
    os.makedirs(p, exist_ok=True)


def fetch(url, timeout=25, sleep=0.8):
    time.sleep(sleep)  # be polite
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.text


def hash_content(html):
    return hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()


def write_json_atomic(path, obj):
    """Write JSON safely: tmp file then atomic replace."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ------------------------
# Discovery
# ------------------------
def discover_niantic_posts(start, end, max_pages=10):
    posts = []

    # 1) RSS (fastest / most reliable dates)
    try:
        rss = feedparser.parse(NIANTIC_RSS)
        for e in rss.entries:
            pub = None
            for k in ("published_parsed", "updated_parsed"):
                if getattr(e, k, None):
                    pub = datetime(*getattr(e, k)[:6]).date()
                    break
            if pub is None:
                pub = normalize_date(getattr(e, "published", None) or getattr(e, "updated", None))
            if not pub or pub < start or pub > end:
                continue
            title = (e.get("title") or "").strip()
            link = (e.get("link") or "").strip()
            if link:
                posts.append({"title": title, "date": pub.isoformat(), "url": link, "source": "niantic"})
    except Exception:
        pass

    # 2) News listing pages (fallback for anything RSS misses)
    try:
        for page in range(max_pages):
            url = NIANTIC_NEWS if page == 0 else f"{NIANTIC_NEWS}?page={page}"
            html = fetch(url)
            soup = BeautifulSoup(html, "lxml")

            cards = soup.find_all(["article", "div"], class_=re.compile("(post|article|card|list)", re.I))
            for art in cards:
                a = art.find("a", href=True)
                if not a:
                    continue
                link = urljoin(url, a["href"])
                title_el = art.find(["h2", "h3"]) or a
                title = (title_el.get_text(" ", strip=True) if title_el else "").strip()

                # attempt to find a date
                pub = None
                t = art.find("time")
                if t:
                    pub = normalize_date(t.get_text(" ", strip=True))
                if not pub:
                    # fallback: look for a date-like string in the card
                    m = re.search(r"(\w+\s+\d{1,2},\s*\d{4})", art.get_text(" ", strip=True))
                    if m:
                        pub = normalize_date(m.group(1))

                if not pub or pub < start or pub > end:
                    continue

                posts.append({"title": title, "date": pub.isoformat(), "url": link, "source": "niantic"})
    except Exception:
        pass

    # Deduplicate by URL
    uniq = {}
    for p in posts:
        if p.get("url"):
            uniq[p["url"]] = p
    return list(uniq.values())


def discover_leek_posts(start, end):
    posts = []
    for url in (LEEK_EVENTS, LEEK_CAL):
        try:
            html = fetch(url)
            soup = BeautifulSoup(html, "lxml")

            # Save hub pages too (they often expose month blocks)
            posts.append({"title": url.split("//")[-1], "date": start.isoformat(), "url": url, "source": "leekduck"})

            seen = set()
            # Crawl anchors; filter to event-like links on leekduck.com
            for a in soup.find_all("a", href=True):
                href = urljoin(url, a["href"])
                if href in seen:
                    continue
                seen.add(href)
                netloc = urlparse(href).netloc
                if netloc.endswith("leekduck.com"):
                    if any(k in href for k in ["/event/", "/events/", "/calendar", "/raid", "/community", "/research", "/hour"]):
                        posts.append({
                            "title": (a.get_text(" ", strip=True) or href),
                            "date": start.isoformat(),
                            "url": href,
                            "source": "leekduck"
                        })
        except Exception:
            continue

    # Deduplicate by URL
    uniq = {}
    for p in posts:
        if p.get("url"):
            uniq[p["url"]] = p
    return list(uniq.values())


# ------------------------
# Main
# ------------------------
def main():
    ap = argparse.ArgumentParser(description="Build local library of Pokémon GO event posts (HTML + index.json)")
    g = ap.add_mutually_exclusive_group(required=False)
    g.add_argument("--month", help="YYYY-MM")
    ap.add_argument("--start", help="YYYY-MM-DD")
    ap.add_argument("--end", help="YYYY-MM-DD")
    ap.add_argument("--out", default="pogo_library", help="Output folder")
    ap.add_argument("--max", type=int, default=500, help="Max pages to save per source")
    args = ap.parse_args()

    # Resolve date window
    if args.month:
        start = normalize_date(args.month + "-01")
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
    else:
        if not args.start or not args.end:
            raise SystemExit("Provide either --month YYYY-MM or --start/--end YYYY-MM-DD")
        start = normalize_date(args.start)
        end = normalize_date(args.end)
        if not start or not end or start > end:
            raise SystemExit("Invalid --start/--end dates")

    out = args.out
    ni_dir = os.path.join(out, "niantic")
    ld_dir = os.path.join(out, "leekduck")
    mkdirp(ni_dir)
    mkdirp(ld_dir)

    # Discover links
    ni_posts = discover_niantic_posts(start, end)[:args.max]
    ld_posts = discover_leek_posts(start, end)[:args.max]

    # Fetch & save helpers
    def save_posts(posts, target_dir):
        saved = []
        for p in posts:
            url = p.get("url")
            if not url:
                continue
            try:
                html = fetch(url)
            except Exception:
                # skip if fetch fails
                continue
            d = p.get("date") or datetime.utcnow().date().isoformat()
            slug = safe_slug(p.get("title") or url)
            fn = f"{d}_{slug}.html"
            path = os.path.join(target_dir, fn)
            with open(path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(html)
            p["file"] = fn
            p["sha256"] = hash_content(html)
            saved.append(p)
        return saved

    ni_saved = save_posts(ni_posts, ni_dir)
    ld_saved = save_posts(ld_posts, ld_dir)

    # Write per-source indexes atomically (never empty/partial)
    write_json_atomic(os.path.join(ni_dir, "index.json"), ni_saved)
    write_json_atomic(os.path.join(ld_dir, "index.json"), ld_saved)

    # Top-level index (also atomic)
    lib_index = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "counts": {"niantic": len(ni_saved), "leekduck": len(ld_saved)},
        "folders": {"niantic": ni_dir, "leekduck": ld_dir},
    }
    write_json_atomic(os.path.join(out, "library_index.json"), lib_index)

    # Human-friendly summary
    print(json.dumps(lib_index, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build a local library of Pokémon GO event posts (HTML + index.json).

Sources:
- Niantic News (RSS + archive pagination)
- Leek Duck Events + Calendar

This creates a folder like:
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
  python build_pogo_library.py --out pogo_library --start 2024-06-01 --end 2025-09-30
  python build_pogo_library.py --month 2025-09

Requires: requests, beautifulsoup4, feedparser, python-dateutil
"""

import argparse
import hashlib
import os
import re
import time
from datetime import datetime, timedelta, timezone, date
from urllib.parse import urljoin, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

NIANTIC_NEWS = "https://pokemongolive.com/news/"
NIANTIC_RSS = "https://pokemongolive.com/news/?format=rss"
LEEK_EVENTS = "https://leekduck.com/events/"
LEEK_CAL = "https://leekduck.com/calendar/"

UA = {"User-Agent": "Mozilla/5.0 (POGO-Library-Builder)"}

def normalize_date(x):
    if isinstance(x, (datetime, date)):
        return x.date() if isinstance(x, datetime) else x
    try:
        return dtparser.parse(x).date()
    except Exception:
        return None

def safe_slug(text, maxlen=120):
    t = re.sub(r"\s+", "-", text.strip().lower())
    t = re.sub(r"[^a-z0-9\-]+", "", t)
    return t[:maxlen] or "untitled"

def mkdirp(p):
    os.makedirs(p, exist_ok=True)

def fetch(url, timeout=25, sleep=0.8):
    time.sleep(sleep)
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.text

def save_file(path, content, mode="w", encoding="utf-8"):
    with open(path, mode, encoding=encoding, errors="ignore") as f:
        f.write(content)

def hash_content(html):
    return hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()

def discover_niantic_posts(start, end):
    posts = []
    # RSS first
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
            title = e.get("title", "").strip()
            link = e.get("link", "").strip()
            posts.append({"title": title, "date": pub.isoformat(), "url": link, "source": "niantic"})
    except Exception:
        pass

    # Also crawl the news listing pages (paginate by simple ?page=)
    try:
        for page in range(0, 10):  # adjust if needed
            url = NIANTIC_NEWS if page == 0 else f"{NIANTIC_NEWS}?page={page}"
            html = fetch(url)
            soup = BeautifulSoup(html, "lxml")
            for art in soup.find_all(["article", "div"], class_=re.compile("(post|article|card|list)", re.I)):
                a = art.find("a", href=True)
                if not a:
                    continue
                link = urljoin(url, a["href"])
                title_el = art.find(["h2", "h3"]) or a
                title = (title_el.get_text(" ", strip=True) if title_el else "").strip()
                # attempt to find date
                t = art.find("time")
                pub = None
                if t:
                    try:
                        pub = normalize_date(t.get_text(" ", strip=True))
                    except Exception:
                        pub = None
                if not pub:
                    # fallback: from link or text
                    m = re.search(r"(\w+\s+\d{1,2},\s*\d{4})", art.get_text(" ", strip=True))
                    if m:
                        pub = normalize_date(m.group(1))
                if not pub:
                    continue
                if pub < start or pub > end:
                    continue
                posts.append({"title": title, "date": pub.isoformat(), "url": link, "source": "niantic"})
    except Exception:
        pass

    # Dedup by URL
    uniq = {}
    for p in posts:
        uniq[p["url"]] = p
    return list(uniq.values())

def discover_leek_posts(start, end):
    posts = []
    # Main index pages
    for url in (LEEK_EVENTS, LEEK_CAL):
        try:
            html = fetch(url)
            soup = BeautifulSoup(html, "lxml")
            # Save the hub pages too (they often have month cards)
            posts.append({"title": url.split("//")[-1], "date": start.isoformat(), "url": url, "source": "leekduck"})
            cards = soup.select(".card, .event, .calendar-item, .ldCard, article a")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = urljoin(url, a["href"])
                if href in seen:
                    continue
                seen.add(href)
                # Filter to event-like pages
                if urlparse(href).netloc.endswith("leekduck.com"):
                    if any(k in href for k in ["/event/", "/events/", "/calendar", "/raid", "/community", "/research", "/hour"]):
                        posts.append({"title": a.get_text(" ", strip=True) or href, "date": start.isoformat(), "url": href, "source": "leekduck"})
        except Exception:
            continue
    # Dedup
    uniq = {}
    for p in posts:
        uniq[p["url"]] = p
    return list(uniq.values())

def main():
    ap = argparse.ArgumentParser(description="Build local library of Pokémon GO event posts (HTML + index.json)")
    g = ap.add_mutually_exclusive_group(required=False)
    g.add_argument("--month", help="YYYY-MM")
    ap.add_argument("--start", help="YYYY-MM-DD")
    ap.add_argument("--end", help="YYYY-MM-DD")
    ap.add_argument("--out", default="pogo_library", help="Output folder")
    ap.add_argument("--max", type=int, default=500, help="Max pages to save per source")
    args = ap.parse_args()

    if args.month:
        start = normalize_date(args.month + "-01")
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
    else:
        if not args.start or not args.end:
            raise SystemExit("Provide either --month YYYY-MM or --start/--end YYYY-MM-DD")
        start = normalize_date(args.start)
        end = normalize_date(args.end)
        if start > end:
            raise SystemExit("start must be <= end")

    out = args.out
    ni_dir = os.path.join(out, "niantic")
    ld_dir = os.path.join(out, "leekduck")
    os.makedirs(ni_dir, exist_ok=True)
    os.makedirs(ld_dir, exist_ok=True)

    # Discover links
    ni_posts = discover_niantic_posts(start, end)[:args.max]
    ld_posts = discover_leek_posts(start, end)[:args.max]

    # Fetch & save
    def save_posts(posts, target_dir):
        saved = []
        for p in posts:
            try:
                html = fetch(p["url"])
            except Exception as e:
                continue
            # Use date + slug as filename
            d = p.get("date") or datetime.utcnow().date().isoformat()
            slug = safe_slug(p.get("title") or p["url"])
            fn = f"{d}_{slug}.html"
            path = os.path.join(target_dir, fn)
            save_file(path, html)
            p["file"] = fn
            p["sha256"] = hash_content(html)
            saved.append(p)
        return saved

    ni_saved = save_posts(ni_posts, ni_dir)
    ld_saved = save_posts(ld_posts, ld_dir)

    # Write indexes
    with open(os.path.join(ni_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(ni_saved, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ld_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(ld_saved, f, ensure_ascii=False, indent=2)

    # Top-level index
    lib_index = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "counts": {"niantic": len(ni_saved), "leekduck": len(ld_saved)},
        "folders": {"niantic": ni_dir, "leekduck": ld_dir},
    }
    with open(os.path.join(out, "library_index.json"), "w", encoding="utf-8") as f:
        json.dump(lib_index, f, ensure_ascii=False, indent=2)

    print(json.dumps(lib_index, indent=2))

if __name__ == "__main__":
    main()

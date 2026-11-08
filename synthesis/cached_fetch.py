#!/usr/bin/env python3
"""Ember Cached Fetch v0.1 (Nov 8, 2026) — think-tank Exercise 1 (Python).
Fetch a URL through the HTML Viewer ONCE; every later ask is answered from the
Ember Index (SQLite) without touching the network. Pass bar (DeepSeek): the
same page is never fetched twice; the cached answer returns in well under 10s.
Usage: python3 cached_fetch.py <url> [--refresh]"""
import json, os, sqlite3, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ember_index

def fetch(url, refresh=False):
    t0 = time.time()
    if not refresh:
        c = sqlite3.connect(ember_index.DB); ember_index.db()  # ensure tables
        row = c.execute("SELECT view_json FROM pages WHERE url=?", (url,)).fetchone()
        if row:
            v = json.loads(row[0]); v["fromCache"] = True
            v["elapsedSec"] = round(time.time() - t0, 3)
            return v
    r = ember_index.add(url)
    if "error" in r: return r
    c = sqlite3.connect(ember_index.DB)
    v = json.loads(c.execute("SELECT view_json FROM pages WHERE url=?", (url,)).fetchone()[0])
    v["fromCache"] = False; v["elapsedSec"] = round(time.time() - t0, 3)
    return v

if __name__ == "__main__":
    url = sys.argv[1]
    v = fetch(url, refresh="--refresh" in sys.argv)
    print(json.dumps({k: v.get(k) for k in ("url", "title", "textLength", "fromCache", "elapsedSec")}, indent=1))

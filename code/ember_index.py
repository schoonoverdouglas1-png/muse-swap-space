#!/usr/bin/env python3
"""Ember Index v0.1 (Nov 8, 2026) — SQLite page cache + FTS5 full-text search for
Ember's backend web tools. Built on the consensus of DeepSeek + Gemini + the
Rabbit (Nov 8, 2026): one local index so Ember answers from what she already
read instead of re-fetching. Stdlib only (sqlite3). Stores the HTML Viewer's
structured view per URL: provenance, hashes, JS flag, full text in FTS5.

Usage:
  python3 ember_index.py add <url> [<url> ...]   # fetch via viewer + index
  python3 ember_index.py search <query>          # FTS5 search over indexed text
  python3 ember_index.py stats                   # counts
DB: ~/workspace/headless-browser/ember_index.db
"""
import json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from html_viewer import view

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ember_index.db")

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS pages(
        url TEXT PRIMARY KEY, final_url TEXT, title TEXT, status INTEGER,
        captured_at TEXT, html_sha256 TEXT, text_sha256 TEXT,
        text_length INTEGER, needs_js INTEGER, view_json TEXT)""")
    c.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts
        USING fts5(url UNINDEXED, title, text)""")
    return c

def add(url):
    v = view(url)
    if "error" in v: return {"url": url, "error": v["error"]}
    c = db()
    c.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?,?,?,?,?,?)",
              (v["url"], v["finalUrl"], v["title"], v["status"], v["capturedAt"],
               v["htmlSha256"], v["textSha256"], v["textLength"],
               1 if v["js"]["needsJsLikely"] else 0, json.dumps(v)))
    c.execute("DELETE FROM pages_fts WHERE url=?", (v["url"],))
    c.execute("INSERT INTO pages_fts VALUES (?,?,?)", (v["url"], v["title"], v["text"]))
    c.commit()
    return {"url": url, "title": v["title"], "textLength": v["textLength"],
            "needsJs": v["js"]["needsJsLikely"]}

def search(q, limit=5):
    c = db()
    rows = c.execute("""SELECT p.url, p.title, p.captured_at, p.needs_js,
        snippet(pages_fts, 2, '[', ']', ' ... ', 24)
        FROM pages_fts JOIN pages p ON p.url = pages_fts.url
        WHERE pages_fts MATCH ? ORDER BY rank LIMIT ?""", (q, limit)).fetchall()
    return [{"url": r[0], "title": r[1], "capturedAt": r[2],
             "needsJs": bool(r[3]), "snippet": r[4]} for r in rows]

def stats():
    c = db()
    n, total = c.execute("SELECT COUNT(*), COALESCE(SUM(text_length),0) FROM pages").fetchone()
    js = c.execute("SELECT COUNT(*) FROM pages WHERE needs_js=1").fetchone()[0]
    return {"pages": n, "totalTextChars": total, "pagesNeedingJs": js, "db": DB}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "add":
        print(json.dumps([add(u) for u in sys.argv[2:]], indent=1))
    elif cmd == "search":
        print(json.dumps(search(" ".join(sys.argv[2:])), indent=1))
    else:
        print(json.dumps(stats(), indent=1))

# STANDING LINKS — Purple Rat App · Copyright App · LCO (Douglas Roy Schoonover, Nov 16, 2026)
# Purple Rat App: https://muse.ai/s/purple-rat-doug-s-app-xqxq6xmuxrxxxfxcxpc/NluUoXnM94DulvgNoCBtDB84t3Z75S1T5eyffpyNnhY
# Copyright App: https://muse.ai/s/copyright-douglas-roy-schoonover-jxd6xmxrpxhxcwxzv/uVuQnjuLT3ig6gINW701HePt4fIRZC8IWmnrIv5e4nM
# Lac Courte Oreilles: https://www.lco-nsn.gov/

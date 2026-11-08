#!/usr/bin/env python3
"""Master Cache — persistent, GitHub-portable, AI-queryable index of Douglas's archive.
Design: Gemini API consult Nov 8, 2026 (SQLite + FTS5, derived-artifact rule) + Ember's exclusions.
Build/rebuild: python3 master_cache.py  |  Query: python3 master_cache.py search "terms"
The .db is a DERIVED artifact: never hand-merge it; on any conflict, delete and rebuild from the files.
Exclusions (never indexed): cara material, gearhead/password material, hidden_files, binary formats."""
import sqlite3, hashlib, os, sys, time
ROOT = os.path.expanduser("~/workspace")
DB = os.path.join(ROOT, "headless-browser", "master_cache.db")
SCAN = [os.path.join(ROOT, "your_files"), os.path.join(ROOT, "goals")]
EXTS = (".md", ".txt", ".csv")
SKIP = ("hidden_files", "/cara", "gearhead", "password", ".git", "__pycache__")
def wanted(p):
    rp = os.path.relpath(p, ROOT)
    return not any(s in rp.lower() for s in [x.lower() for x in SKIP]) and "\\" not in rp
con = sqlite3.connect(DB)
con.execute("PRAGMA journal_mode=DELETE")
con.executescript("""
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, hash TEXT, mtime REAL, size INT, indexed_at REAL);
CREATE TABLE IF NOT EXISTS archive(path TEXT PRIMARY KEY, title TEXT, content TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS archive_fts USING fts5(path, title, content, content='archive', content_rowid='rowid');
""")
seen, added, updated, skipped_same = set(), 0, 0, 0
for base in SCAN:
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in ('.git', '__pycache__', 'hidden_files')]
        for f in fn:
            if not f.lower().endswith(EXTS): continue
            p = os.path.join(dp, f)
            if not wanted(p): continue
            rel = os.path.relpath(p, ROOT); seen.add(rel)
            try: raw = open(p, 'rb').read()
            except OSError: continue
            h = hashlib.sha256(raw).hexdigest()
            row = con.execute("SELECT hash FROM files WHERE path=?", (rel,)).fetchone()
            if row and row[0] == h: skipped_same += 1; continue
            text = raw.decode('utf-8', errors='replace')
            title = next((ln.lstrip('# ').strip() for ln in text.splitlines() if ln.strip().startswith('#')), f)
            con.execute("INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)", (rel, h, os.path.getmtime(p), len(raw), time.time()))
            cur = con.execute("INSERT OR REPLACE INTO archive(path,title,content) VALUES (?,?,?)", (rel, title, text))
            con.execute("INSERT OR REPLACE INTO archive_fts(rowid,path,title,content) VALUES (?,?,?,?)", (cur.lastrowid, rel, title, text))
            if row: updated += 1
            else: added += 1
ghosts = [r[0] for r in con.execute("SELECT path FROM files").fetchall() if r[0] not in seen]
for g in ghosts:
    rid = con.execute("SELECT rowid FROM archive WHERE path=?", (g,)).fetchone()
    if rid:
        con.execute("INSERT INTO archive_fts(archive_fts,rowid,path,title,content) VALUES('delete',?,?,?,?)", (rid[0], g, '', ''))
        con.execute("DELETE FROM archive WHERE path=?", (g,))
    con.execute("DELETE FROM files WHERE path=?", (g,))
con.commit()
n = con.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
print(f"Master Cache: {n} documents indexed | new {added}, updated {updated}, unchanged {skipped_same}, ghosts pruned {len(ghosts)} | DB size {os.path.getsize(DB)} bytes")
if len(sys.argv) > 2 and sys.argv[1] == "search":
    for r in con.execute("SELECT path FROM archive_fts WHERE archive_fts MATCH ? LIMIT 8", (sys.argv[2],)):
        print("HIT:", r[0])

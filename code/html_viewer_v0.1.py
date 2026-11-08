#!/usr/bin/env python3
"""Ember HTML Viewer v0.1 (Nov 7, 2026) — backend page viewing for an AI, no browser.
Fetch (stdlib urllib, uses proxy env) -> parse (stdlib html.parser) -> structured view:
title, headings, tables, links, image alt text, clean text, truncation flags, provenance.
Zero installs. Output: JSON on stdout."""
import sys, json, urllib.request, urllib.error
from html.parser import HTMLParser
from datetime import datetime, timezone

MAX_TEXT = 60000
SKIP = {"script", "style", "noscript", "svg", "head"}

class View(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""; self._in_title = False
        self.headings = []; self._h = None
        self.links = []; self._a = None
        self.images = []
        self.tables = []; self._tbl = None; self._cell = None
        self.text_parts = []; self._skip = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP: self._skip += 1
        if tag == "title": self._in_title = True
        if tag in ("h1","h2","h3","h4"): self._h = [tag, ""]
        if tag == "a" and a.get("href"): self._a = [a["href"], ""]
        if tag == "img": self.images.append({"alt": a.get("alt",""), "src": a.get("src","")[:300]})
        if tag == "table": self._tbl = []
        if tag == "tr" and self._tbl is not None: self._tbl.append([])
        if tag in ("td","th") and self._tbl: self._cell = ""
    def handle_endtag(self, tag):
        if tag in SKIP and self._skip: self._skip -= 1
        if tag == "title": self._in_title = False
        if self._h and tag == self._h[0]:
            t = " ".join(self._h[1].split())
            if t: self.headings.append({"level": self._h[0], "text": t[:200]})
            self._h = None
        if tag == "a" and self._a:
            t = " ".join(self._a[1].split())[:120]
            if len(self.links) < 200: self.links.append({"text": t, "href": self._a[0]})
            self._a = None
        if tag in ("td","th") and self._cell is not None and self._tbl:
            self._tbl[-1].append(" ".join(self._cell.split())[:200]); self._cell = None
        if tag == "table" and self._tbl is not None:
            if self._tbl and len(self.tables) < 20: self.tables.append(self._tbl[:50])
            self._tbl = None
    def handle_data(self, d):
        if self._in_title: self.title += d
        if self._skip: return
        if self._h: self._h[1] += d
        if self._a: self._a[1] += d
        if self._cell is not None: self._cell += d
        self.text_parts.append(d)

def view(url):
    req = urllib.request.Request(url, headers={"User-Agent": "EmberHTMLViewer/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        final_url, status = r.geturl(), r.status
        raw = r.read(3_000_000)
        ctype = r.headers.get_content_charset() or "utf-8"
    html = raw.decode(ctype, errors="replace")
    v = View(); v.feed(html)
    text = "\n".join(" ".join(p.split()) for p in v.text_parts)
    lines = [ln for ln in (l.strip() for l in text.split("\n")) if ln]
    clean = "\n".join(lines)
    return {"schemaVersion": 1, "tool": "ember-html-viewer/0.1", "url": url, "finalUrl": final_url,
            "status": status, "capturedAt": datetime.now(timezone.utc).isoformat(),
            "title": " ".join(v.title.split()), "headings": v.headings[:100],
            "tables": v.tables, "links": v.links, "images": v.images[:100],
            "textLength": len(clean), "textTruncated": len(clean) > MAX_TEXT,
            "text": clean[:MAX_TEXT]}

if __name__ == "__main__":
    try:
        print(json.dumps(view(sys.argv[1]), indent=1)[:8000])
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"})); sys.exit(1)

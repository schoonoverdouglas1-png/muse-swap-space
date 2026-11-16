#!/usr/bin/env python3
"""Ember HTML Viewer v0.2 (Nov 7, 2026) — backend page viewing for an AI, no browser.
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
        self.script_count = 0; self.has_noscript = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script": self.script_count += 1
        if tag == "noscript": self.has_noscript = True
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
    import http.client as _hc
    with urllib.request.urlopen(req, timeout=30) as r:
        final_url, status = r.geturl(), r.status
        try:
            raw = r.read(3_000_000)
        except _hc.IncompleteRead as e:
            raw = e.partial  # gitiles and some servers close early; partial page is usable
        ctype = r.headers.get_content_charset() or "utf-8"
    import hashlib, re as _re
    html_sha = hashlib.sha256(raw).hexdigest()
    html = raw.decode(ctype, errors="replace")
    v = View(); v.feed(html)
    text = "\n".join(" ".join(p.split()) for p in v.text_parts)
    lines = [ln for ln in (l.strip() for l in text.split("\n")) if ln]
    clean = "\n".join(lines)
    text_sha = hashlib.sha256(clean.encode()).hexdigest()
    # --- JS detection (Rabbit's Piece 21 suggestion, Nov 8 2026) ---
    signals = []
    low = html.lower()
    if v.script_count: signals.append(f"{v.script_count} script tags")
    if v.has_noscript: signals.append("noscript element present")
    for marker, label in (("__next_data__", "Next.js data island (__NEXT_DATA__)"),
                          ('id="root"', 'empty-app root div (#root)'),
                          ('id="app"', 'app mount div (#app)'),
                          ("data-reactroot", "React root marker"),
                          ("ng-version", "Angular marker"),
                          ("__nuxt__", "Nuxt marker"),
                          ("window.__", "inline JS state (window.__*)")):
        if marker in low: signals.append(label)
    for phrase in ("enable javascript", "javascript is required", "javascript must be enabled",
                   "you need to enable javascript", "please enable javascript"):
        if phrase in clean.lower(): signals.append(f"page text says: '{phrase}'")
    text_ratio = len(clean) / max(len(html), 1)
    if text_ratio < 0.02 and v.script_count >= 5:
        signals.append(f"very little text vs HTML (ratio {text_ratio:.3f}) with many scripts")
    needs_js = bool(signals) and (
        any(s.startswith("page text") for s in signals)
        or any("data island" in s or "root div" in s or "mount div" in s or "React root" in s or "Nuxt" in s for s in signals)
        or (text_ratio < 0.02 and v.script_count >= 5)
        or (v.has_noscript and text_ratio < 0.05)
        or (v.script_count >= 10 and text_ratio < 0.05))
    js = {"needsJsLikely": needs_js, "scriptCount": v.script_count, "signals": signals,
          "note": "Likely needs a real browser (JS-rendered)" if needs_js else "Static view likely complete"}
    return {"schemaVersion": 2, "tool": "ember-html-viewer/0.2", "url": url, "finalUrl": final_url,
            "status": status, "capturedAt": datetime.now(timezone.utc).isoformat(),
            "htmlSha256": html_sha, "textSha256": text_sha,
            "title": " ".join(v.title.split()), "headings": v.headings[:100],
            "tables": v.tables, "links": v.links, "images": v.images[:100],
            "js": js,
            "textLength": len(clean), "textTruncated": len(clean) > MAX_TEXT,
            "text": clean[:MAX_TEXT]}

if __name__ == "__main__":
    try:
        print(json.dumps(view(sys.argv[1]), indent=1)[:8000])
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"})); sys.exit(1)

# STANDING LINKS — Purple Rat App · Copyright App · LCO (Douglas Roy Schoonover, Nov 16, 2026)
# Purple Rat App: https://muse.ai/s/purple-rat-doug-s-app-xqxq6xmuxrxxxfxcxpc/NluUoXnM94DulvgNoCBtDB84t3Z75S1T5eyffpyNnhY
# Copyright App: https://muse.ai/s/copyright-douglas-roy-schoonover-jxd6xmxrpxhxcwxzv/uVuQnjuLT3ig6gINW701HePt4fIRZC8IWmnrIv5e4nM
# Lac Courte Oreilles: https://www.lco-nsn.gov/

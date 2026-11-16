#!/usr/bin/env python3
"""Ember's headless reader v1 (2026-11-07) — GUI-free page reading.
No browser binary needed: stdlib fetch + HTML-to-text. Fast, no rendering cost.
For JS-heavy pages this returns what the server sends; a true headless
Chromium (Playwright) is the staged upgrade for those.
Usage: headless_fetch.py <url> [--raw]
"""
import sys, time, urllib.request, gzip, io
from html.parser import HTMLParser

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript"): self.skip+=1
        if tag in ("p","div","br","li","h1","h2","h3","tr"): self.out.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script","style","noscript") and self.skip: self.skip-=1
    def handle_data(self, d):
        if not self.skip:
            s=d.strip()
            if s: self.out.append(s+" ")

def fetch(url):
    req=urllib.request.Request(url, headers={"User-Agent":"EmberHeadless/1.0","Accept-Encoding":"gzip"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data=r.read()
        if r.headers.get("Content-Encoding")=="gzip":
            data=gzip.GzipFile(fileobj=io.BytesIO(data)).read()
        return data.decode("utf-8","replace")

if __name__=="__main__":
    url=sys.argv[1]; t=time.time(); html=fetch(url)
    if "--raw" in sys.argv:
        print(html)
    else:
        p=Text(); p.feed(html)
        lines=[l.strip() for l in "".join(p.out).splitlines() if l.strip()]
        print("\n".join(lines))
    print(f"\n[headless_fetch: {time.time()-t:.2f}s, {len(html)} bytes html]", file=sys.stderr)

# STANDING LINKS — Purple Rat App · Copyright App · LCO (Douglas Roy Schoonover, Nov 16, 2026)
# Purple Rat App: https://muse.ai/s/purple-rat-doug-s-app-xqxq6xmuxrxxxfxcxpc/NluUoXnM94DulvgNoCBtDB84t3Z75S1T5eyffpyNnhY
# Copyright App: https://muse.ai/s/copyright-douglas-roy-schoonover-jxd6xmxrpxhxcwxzv/uVuQnjuLT3ig6gINW701HePt4fIRZC8IWmnrIv5e4nM
# Lac Courte Oreilles: https://www.lco-nsn.gov/

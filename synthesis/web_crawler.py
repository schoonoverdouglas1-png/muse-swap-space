#!/usr/bin/env python3
"""Ember Web Crawler v0.1 (Nov 7, 2026) — crawl the web with NO browser.
Stdlib only: fetch via urllib (proxy env), parse via html_viewer's parser.
Same-domain BFS, page/depth caps, polite delay. Output: JSONL index + summary.
CPU cost is plain text parsing — no rendering, no GPU, no JavaScript engine."""
import sys, json, time, urllib.parse, urllib.request
sys.path.insert(0, "/home/hatch/workspace/headless-browser")
from html_viewer import View

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "EmberCrawler/0.1"})
    import http.client
    with urllib.request.urlopen(req, timeout=25) as r:
        try:
            raw = r.read(2_000_000)
        except http.client.IncompleteRead as e:
            raw = e.partial
        return r.geturl(), r.status, raw.decode("utf-8", errors="replace")

def crawl(start, max_pages=6, max_depth=1, delay=0.3):
    host = urllib.parse.urlparse(start).netloc
    seen, queue, index = set(), [(start, 0)], []
    while queue and len(index) < max_pages:
        url, depth = queue.pop(0)
        if url in seen: continue
        seen.add(url)
        t0 = time.time()
        try:
            final, status, html = fetch(url)
            v = View(); v.feed(html)
            text = " ".join(" ".join(v.text_parts).split())
            rec = {"url": final, "status": status, "title": " ".join(v.title.split()),
                   "headings": len(v.headings), "links": len(v.links), "tables": len(v.tables),
                   "textChars": len(text), "seconds": round(time.time()-t0, 2)}
            if depth < max_depth:
                for lk in v.links:
                    u = urllib.parse.urljoin(final, lk["href"])
                    p = urllib.parse.urlparse(u)
                    if p.netloc == host and p.scheme in ("http","https") and u not in seen:
                        queue.append((u.split("#")[0], depth+1))
        except Exception as e:
            rec = {"url": url, "error": f"{type(e).__name__}: {e}", "seconds": round(time.time()-t0, 2)}
        index.append(rec); time.sleep(delay)
    return index

if __name__ == "__main__":
    start = sys.argv[1]; mp = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    t0 = time.time(); idx = crawl(start, max_pages=mp)
    for r in idx: print(json.dumps(r))
    print(json.dumps({"pages": len(idx), "totalSeconds": round(time.time()-t0, 2), "tool": "ember-web-crawler/0.1"}))

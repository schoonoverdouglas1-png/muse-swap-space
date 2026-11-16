#!/usr/bin/env python3
"""Ember MCP Bridge v0.1 — stdlib-only MCP server (stdio transport, JSON-RPC).

Built Nov 8, 2026 at Douglas's order ("Make it so. And build yourself even better.").
Design rules: READ-ONLY tools only in v0.1; no arbitrary execution — the one
command-shaped tool (guard_check) only ASKS the Guard whether a command line
would be allowed; it never runs it. Localhost/stdio only; no network listener.
Tools:
  index_search(query)     — full-text search of the Ember Index (cached web knowledge)
  index_stats()           — page count of the Ember Index
  guard_check(command)    — would the Guard allow this command line? (check only)
  sys_snapshot()          — memory + load, read-only
  list_deliverables()     — count + recent names in ~/workspace/your_files
"""
import sys, os, json, sqlite3, subprocess

HOME = os.path.expanduser("~")
INDEX_DB = os.path.join(HOME, "workspace/headless-browser/ember_index.db")
GUARD = os.path.join(HOME, "workspace/ember-upgrades/guard/check-command.sh")
FILES_DIR = os.path.join(HOME, "workspace/your_files")

TOOLS = [
    {"name": "index_search", "description": "Full-text search of Ember's local index of cached web pages. Returns matching page titles and URLs.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "index_stats", "description": "How many pages are in Ember's local index.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "guard_check", "description": "Ask Ember's Guard whether a command line would be ALLOWED (exit 0) or REFUSED as destructive (exit 99). Check only - nothing is executed.",
     "inputSchema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "sys_snapshot", "description": "Read-only snapshot: available memory and system load on Ember's VM.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "list_deliverables", "description": "Count and most recent file names in Douglas's deliverables folder.",
     "inputSchema": {"type": "object", "properties": {}}},
]

def tool_index_search(a):
    q = (a.get("query") or "").strip()
    if not q:
        return "empty query"
    con = sqlite3.connect("file:%s?mode=ro" % INDEX_DB, uri=True)
    try:
        rows = con.execute(
            "SELECT title, url FROM pages_fts JOIN pages ON pages.id = pages_fts.rowid "
            "WHERE pages_fts MATCH ? LIMIT 5", (q,)).fetchall()
    except Exception:
        rows = con.execute(
            "SELECT title, url FROM pages WHERE title LIKE ? OR text LIKE ? LIMIT 5",
            ("%" + q + "%", "%" + q + "%")).fetchall()
    con.close()
    if not rows:
        return "no matches for: " + q
    return "\n".join("- %s | %s" % (t or "(untitled)", u) for t, u in rows)

def tool_index_stats(a):
    con = sqlite3.connect("file:%s?mode=ro" % INDEX_DB, uri=True)
    n = con.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    con.close()
    return "Ember Index holds %d pages." % n

def tool_guard_check(a):
    cmd = a.get("command") or ""
    p = subprocess.run(["bash", GUARD, cmd], capture_output=True, text=True, timeout=10)
    verdict = "ALLOWED (exit 0)" if p.returncode == 0 else "REFUSED (exit %d)" % p.returncode
    return "Guard verdict for %r: %s %s" % (cmd, verdict, (p.stdout or p.stderr or "").strip()[:200])

def tool_sys_snapshot(a):
    mem = open("/proc/meminfo").read()
    avail = [l for l in mem.splitlines() if l.startswith("MemAvailable")][0]
    load = open("/proc/loadavg").read().split()[:3]
    return "%s | load average: %s" % (avail.strip(), " ".join(load))

def tool_list_deliverables(a):
    names = sorted(os.listdir(FILES_DIR))
    return "%d items. Most recent by name sample: %s" % (len(names), "; ".join(names[-5:]))

DISPATCH = {"index_search": tool_index_search, "index_stats": tool_index_stats,
            "guard_check": tool_guard_check, "sys_snapshot": tool_sys_snapshot,
            "list_deliverables": tool_list_deliverables}

def reply(rid, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "result": result}) + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        method, rid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
        if method == "initialize":
            reply(rid, {"protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "ember-bridge", "version": "0.1.0"}})
        elif method == "tools/list":
            reply(rid, {"tools": TOOLS})
        elif method == "tools/call":
            name = params.get("name")
            fn = DISPATCH.get(name)
            if fn is None:
                reply(rid, {"content": [{"type": "text", "text": "unknown tool: %s" % name}], "isError": True})
            else:
                try:
                    text = fn(params.get("arguments") or {})
                    reply(rid, {"content": [{"type": "text", "text": text}]})
                except Exception as e:
                    reply(rid, {"content": [{"type": "text", "text": "error: %s" % e}], "isError": True})
        elif rid is not None:
            reply(rid, {})

if __name__ == "__main__":
    main()

# STANDING LINKS — Purple Rat App · Copyright App · LCO (Douglas Roy Schoonover, Nov 16, 2026)
# Purple Rat App: https://muse.ai/s/purple-rat-doug-s-app-xqxq6xmuxrxxxfxcxpc/NluUoXnM94DulvgNoCBtDB84t3Z75S1T5eyffpyNnhY
# Copyright App: https://muse.ai/s/copyright-douglas-roy-schoonover-jxd6xmxrpxhxcwxzv/uVuQnjuLT3ig6gINW701HePt4fIRZC8IWmnrIv5e4nM
# Lac Courte Oreilles: https://www.lco-nsn.gov/

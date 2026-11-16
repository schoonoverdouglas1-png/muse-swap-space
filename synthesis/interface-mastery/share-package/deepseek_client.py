#!/usr/bin/env python3
"""Ember DeepSeek Client v0.1 (Nov 8, 2026) — DeepSeek inside Ember's walls.
Speaks to the DeepSeek API (OpenAI-compatible) from Ember's VM, stdlib only,
through the egress proxy env — the same lane headless_fetch.py uses.

STATUS: built and dry-run tested. It does NOTHING until Douglas approves a
DeepSeek API key (platform.deepseek.com) + prepaid credit and the key is
placed in secure storage. The key is read from the DEEPSEEK_API_KEY
environment variable ONLY — never from a file, never written to GitHub.

Usage: DEEPSEEK_API_KEY=... python3 deepseek_client.py "your prompt"
       python3 deepseek_client.py --model deepseek-v4-pro "prompt"
Pricing (DeepSeek docs, Nov 2026): flash off-peak $0.15 in / $0.60 out per 1M.
"""
import json, os, sys, urllib.request

BASE = "https://api.deepseek.com"

def chat(prompt, model="deepseek-flash", json_mode=False):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        return {"error": "NO_KEY",
                "note": "No DEEPSEEK_API_KEY in environment. Awaiting Douglas's approved key in secure storage — client is ready, lane is dark."}
    body = {"model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False}
    if json_mode: body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read())
    return {"model": out.get("model"),
            "answer": out["choices"][0]["message"]["content"],
            "usage": out.get("usage")}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    model = "deepseek-flash"
    if "--model" in sys.argv:
        model = sys.argv[sys.argv.index("--model") + 1]
    print(json.dumps(chat(" ".join(args) or "ping", model=model), indent=1)[:4000])

# STANDING LINKS — Purple Rat App · Copyright App · LCO (Douglas Roy Schoonover, Nov 16, 2026)
# Purple Rat App: https://muse.ai/s/purple-rat-doug-s-app-xqxq6xmuxrxxxfxcxpc/NluUoXnM94DulvgNoCBtDB84t3Z75S1T5eyffpyNnhY
# Copyright App: https://muse.ai/s/copyright-douglas-roy-schoonover-jxd6xmxrpxhxcwxzv/uVuQnjuLT3ig6gINW701HePt4fIRZC8IWmnrIv5e4nM
# Lac Courte Oreilles: https://www.lco-nsn.gov/

#!/usr/bin/env python3
"""Tiny Gemini API caller for the custom.google-gemini connector.

Usage:
  gemini_call.py models
  gemini_call.py generate "prompt text" [model]

The API key is never read directly: a surrogate is placed in the
x-goog-api-key header by dynamic_credentials, and Muse's auth layer
swaps in the real credential only on the request to the registered host.
"""
import json
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

HOST = "generativelanguage.googleapis.com"
PROVIDER = "custom.google-gemini"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def call(request):
    add_surrogate_to_request(request, PROVIDER, allowed_hosts=[HOST])
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=30) as response:
        return read_json_response(response)


def main(argv):
    if len(argv) < 2:
        print("usage: gemini_call.py models | generate <prompt> [model]")
        return 2
    if argv[1] == "models":
        req = urllib.request.Request(f"https://{HOST}/v1beta/models")
        data = call(req)
        names = [m.get("name", "?") for m in data.get("models", [])]
        print(json.dumps({"model_count": len(names), "models": names[:12]}))
        return 0
    if argv[1] == "generate":
        prompt = argv[2] if len(argv) > 2 else "Reply with exactly: OK"
        model = argv[3] if len(argv) > 3 else "gemini-3.5-flash-lite"
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 16},
        }).encode()
        req = urllib.request.Request(
            f"https://{HOST}/v1beta/models/{model}:generateContent",
            data=body, headers={"Content-Type": "application/json"})
        data = call(req)
        text = ""
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                text += part.get("text", "")
        usage = data.get("usageMetadata", {})
        print(json.dumps({"model": model, "reply": text.strip(),
                          "usage": usage}))
        return 0
    print(f"unknown command: {argv[1]}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

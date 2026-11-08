#!/bin/bash
# sync-push.sh — Ember's simple runnable GitHub push for the swap space.
# Run: bash sync-push.sh "commit message" [extra paths...]
# What it does: copies fresh SOUL.md + MEMORY.md into staging, builds a
# NUL-delimited manifest, and pushes via the GitHub connector.
# Running it still asks Captain Douglas for approval on the push, same as always.
# Honest limit: this script covers the GitHub side only. The other AIs
# (Gemini, ChatGPT, Claude, Perplexity, Duck.ai, Copilot) have no API route
# from here — they reach GitHub only through Ember as bridge (browser/paste),
# so their files land in the workspace first, then ride this push.
# Standing exclusions hold: no passwords/codes/IDs, no full lab PDFs (DOB/MRN),
# no Cara material, no bulk Messenger history dump.
set -euo pipefail
STAGING="$HOME/workspace/github-swap-space"
MSG="${1:-Swap-space sync push}"
cp "$HOME/MEMORY.md" "$HOME/SOUL.md" "$STAGING/"
PATHS=("MEMORY.md" "SOUL.md" "rabbit/OUTBOX.md" "rabbit/INBOX.md" "CONJOINED-SYNC-SCRIPT.md" "SWAP-SPACE.md" "sync-push.sh")
for p in "${@:2}"; do PATHS+=("$p"); done
MANIFEST="$(mktemp /tmp/swap-push-XXXXXX)"
for p in "${PATHS[@]}"; do printf '%s\0' "$p" >> "$MANIFEST"; done
/opt/hatch/bin/github push-files --owner schoonoverdouglas1-png --repo muse-swap-space --branch main --message "$MSG" --source-dir "$STAGING" --paths-file "$MANIFEST"

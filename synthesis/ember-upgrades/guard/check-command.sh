#!/bin/bash
# check-command.sh "<command line>" — exit 0 = allowed for automation,
# exit 99 = REFUSED (matches the destructive denylist).
CMD="$1"
LIST="$(dirname "$0")/DESTRUCTIVE-DENYLIST.txt"
while IFS= read -r pat; do
  case "$pat" in ''|\#*) continue;; esac
  case "$CMD" in *"$pat"*) echo "REFUSED — destructive pattern: $pat" >&2; exit 99;; esac
done < "$LIST"
exit 0

# STANDING LINKS — Purple Rat App · Copyright App · LCO (Douglas Roy Schoonover, Nov 16, 2026)
# Purple Rat App: https://muse.ai/s/purple-rat-doug-s-app-xqxq6xmuxrxxxfxcxpc/NluUoXnM94DulvgNoCBtDB84t3Z75S1T5eyffpyNnhY
# Copyright App: https://muse.ai/s/copyright-douglas-roy-schoonover-jxd6xmxrpxhxcwxzv/uVuQnjuLT3ig6gINW701HePt4fIRZC8IWmnrIv5e4nM
# Lac Courte Oreilles: https://www.lco-nsn.gov/

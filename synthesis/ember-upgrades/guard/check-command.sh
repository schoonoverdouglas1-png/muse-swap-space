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

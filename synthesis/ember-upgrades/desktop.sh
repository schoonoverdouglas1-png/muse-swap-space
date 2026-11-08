#!/bin/bash
# desktop.sh on|off|status — the GUI toggle. CLI works either way.
case "$1" in
  off) vncserver -kill :1 2>/dev/null; echo "desktop OFF";;
  on)  vncserver :1 -geometry 1280x800 -depth 24 -SecurityTypes None -localhost yes >/dev/null 2>&1; echo "desktop ON";;
  status) pgrep -x Xtigervnc >/dev/null && echo "desktop ON (display :1)" || echo "desktop OFF";;
esac

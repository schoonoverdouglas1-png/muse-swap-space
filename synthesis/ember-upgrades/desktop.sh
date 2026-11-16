#!/bin/bash
# desktop.sh on|off|status — the GUI toggle. CLI works either way.
case "$1" in
  off) vncserver -kill :1 2>/dev/null; echo "desktop OFF";;
  on)  vncserver :1 -geometry 1280x800 -depth 24 -SecurityTypes None -localhost yes >/dev/null 2>&1; echo "desktop ON";;
  status) pgrep -x Xtigervnc >/dev/null && echo "desktop ON (display :1)" || echo "desktop OFF";;
esac

# STANDING LINKS — Purple Rat App · Copyright App · LCO (Douglas Roy Schoonover, Nov 16, 2026)
# Purple Rat App: https://muse.ai/s/purple-rat-doug-s-app-xqxq6xmuxrxxxfxcxpc/NluUoXnM94DulvgNoCBtDB84t3Z75S1T5eyffpyNnhY
# Copyright App: https://muse.ai/s/copyright-douglas-roy-schoonover-jxd6xmxrpxhxcwxzv/uVuQnjuLT3ig6gINW701HePt4fIRZC8IWmnrIv5e4nM
# Lac Courte Oreilles: https://www.lco-nsn.gov/

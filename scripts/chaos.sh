#!/usr/bin/env bash
# Usage: ./scripts/chaos.sh fire|slow|rush|random|off
#   fire|slow|rush|random -> breaks ONE random pizzeria pod (so you can practise finding the bad pod!)
#   off                   -> fixes ALL pods
source "$(dirname "$0")/common.sh"
MODE="${1:-fire}"
QUIET=0
if [[ "$MODE" == "random" ]]; then MODE=$(printf "fire\nslow\nrush\n" | sort -R | head -1); QUIET=1; fi
hit() { $K -n pizza exec "$1" -- wget -qO- "http://127.0.0.1:8080/chaos?mode=$MODE"; }

if [[ "$MODE" == "off" ]]; then
  for pod in $($K -n pizza get pods -l app=pizzeria -o name); do hit "$pod" >/dev/null; done
  say "all ovens fixed ✅"
  exit 0
fi
POD=$($K -n pizza get pods -l app=pizzeria -o name | sort -R | head -1)
if [[ $QUIET == 1 ]]; then
  hit "$POD" >/dev/null; say "💥 something just broke. Go find out what, and where!"
else
  say "chaos mode '$MODE' -> $POD"; hit "$POD"
fi

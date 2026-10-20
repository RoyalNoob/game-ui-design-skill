#!/usr/bin/env bash
# Usage: bash tests/validator/run.sh
set -u
cd "$(dirname "$0")"
V=../../plugins/game-gui/skills/game-gui-design/scripts/validate_ui.py
fail=0
expect() {  # name, registry, html, expected exit, expected error count, grep patterns...
  local name=$1 reg=$2 html=$3 want_exit=$4 want_err=$5; shift 5
  out=$(python3 "$V" "$reg" "$html"); code=$?
  errs=$(grep -c '^ERROR' <<<"$out")
  [[ $code == "$want_exit" && $errs == "$want_err" ]] || { echo "FAIL $name: exit=$code errors=$errs"; fail=1; }
  for p in "$@"; do grep -q -- "$p" <<<"$out" || { echo "FAIL $name: missing '$p'"; fail=1; }; done
}
expect good   good-registry.json   good.html   0 0 "Exception: PC-only"
expect bad    bad-registry.json    bad.html    1 8 "below the text floor" "needs visibility" "has no trigger" \
       "not in input_map" "no focus style" "hard-coded prompt 'Press A'" "longer than 500ms" "font-size:14px"
expect legacy legacy-registry.json legacy.html 1 7 "removed" "not in registry" "#shiny" "type-size-big" "#ff0000"
expect nav    nav-registry.json    good.html   1 3 "\[WARN\] equip-weapon .*presses 7/3" "\[ok  \] open-map .*presses 1/3" \
       "\[FAIL\] change-volume .*presses 7/6" "(set by user)" "budget 3 (default)" "'credits' cannot be reached" \
       "task 'view-credits' cannot be reached" "target 'quests' is not a screen"
G=../../plugins/game-gui/skills/game-gui-design/scripts/nav_graph.py
tmp=$(mktemp -d)
python3 "$G" nav-registry.json "$tmp/nav.svg" >/dev/null || { echo "FAIL nav_graph: exit code"; fail=1; }
for p in "<svg" "inventory" "unreachable" "stroke-dasharray" "FAIL" "WARN" "change-volume"; do
  grep -q -- "$p" "$tmp/nav.svg" || { echo "FAIL nav_graph: missing '$p'"; fail=1; }
done
python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" "$tmp/nav.svg" || { echo "FAIL nav_graph: invalid XML"; fail=1; }
python3 "$G" good-registry.json "$tmp/none.svg" >/dev/null && { echo "FAIL nav_graph: should refuse registry without navigation"; fail=1; }
[[ $fail == 0 ]] && echo "All validator tests passed."
exit $fail

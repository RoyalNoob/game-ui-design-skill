#!/usr/bin/env python3
"""Validate game UI mockups against ui-registry.json.

Usage: python3 validate_ui.py ui-registry.json mockup1.html [mockup2.html ...]
Exit code 0 = no errors, 1 = errors found.

Structure checks: IDs, components, tags, tokens, removed IDs.
Token checks: text size floor (XAG 101) for the brief platforms, motion durations.
Markup checks: focus style, hard-coded button prompts, @prompt actions, HUD visibility.
Navigation checks: cheapest gamepad path (presses, depth) from the start screen to each task,
against frequency budgets. Over a default budget = WARN. Over a user-set budget = ERROR.
"""
import json, re, sys
from html.parser import HTMLParser

ALLOWED_TAG_PATTERNS = [
    r"p[123]", r"interactive", r"readout", r"label", r"decor", r"icon", r"prompt",
    r"danger", r"warning", r"success", r"info", r"rarity-[a-z]+",
    r"gamepad-only", r"mouse-only", r"touch-only", r"loc",
]
RESERVED_VARS = {"motion-slow"}  # set by inspector.js for slow-motion preview
# XAG 101 minimum body text height at 1080p. Handheld uses the console value (assumption).
TEXT_FLOOR_1080 = {"console": 26, "handheld": 26, "pc": 18, "vr": 18, "mobile": 18}
VISIBILITY = {"hidden", "peek", "persistent", "expanded"}
MAX_UI_DURATION_MS = 500

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
VAR = re.compile(r"var\(--([a-z0-9-]+)")
FONT_SIZE_LITERAL = re.compile(r"font-size\s*:\s*[0-9.]+(px|pt|rem|em)\b")
OUTLINE_NONE = re.compile(r"outline\s*:\s*(none|0)\b")
FOCUS_RULE = re.compile(r":focus(-visible|-within)?\b|\.focus\b|\[data-focus|\.is-focus")
PROMPT_TEXT = re.compile(
    r"\b(press|hold|tap|push|hit)\s+\[?(A|B|X|Y|LB|RB|LT|RT|L1|R1|L2|R2|L3|R3|ZL|ZR|"
    r"Cross|Circle|Square|Triangle|Start|Select|Options|Space|Enter|Esc|Tab|Shift)\]?(?![a-z])",
    re.I)


def token_to_var(path):  # $color.accent.primary -> color-accent-primary
    return path.lstrip("$").replace(".", "-")


def strip_index(i):  # inventory.grid.slot[3] -> inventory.grid.slot[*]
    return re.sub(r"\[\d+\]", "[*]", i)


def to_px(value, rem=16):
    m = re.fullmatch(r"\s*([0-9.]+)\s*(px|rem|em|pt)?\s*", str(value))
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2) or "px"
    return n * {"px": 1, "rem": rem, "em": rem, "pt": 4 / 3}[unit]


def to_ms(value):
    m = re.fullmatch(r"\s*([0-9.]+)\s*(ms|s)?\s*", str(value))
    if not m:
        return None
    return float(m.group(1)) * (1000 if m.group(2) == "s" else 1)


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements, self.css, self.text = [], [], []
        self._skip = None  # inside <style> or <script>

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("style", "script"):
            self._skip = tag
        if "style" in a:
            self.css.append(("inline:" + a.get("data-id", tag), a["style"] or ""))
        if "data-id" in a:
            self.elements.append({
                "id": a["data-id"],
                "component": a.get("data-component", "") or "",
                "action": a.get("data-action", ""),
                "tags": (a.get("data-tags", "") or "").split(),
                "line": self.getpos()[0],
            })

    def handle_endtag(self, tag):
        if tag == self._skip:
            self._skip = None

    def handle_data(self, data):
        if self._skip == "style":
            self.css.append(("<style>", data))
        elif self._skip is None and data.strip():
            self.text.append((self.getpos()[0], data.strip()))


def css_outside_root(css):
    return re.sub(r":root[^{]*\{[^}]*\}", "", css)


def check_tokens(reg, errors, warnings):
    tokens = reg.get("tokens", {})
    brief = reg.get("brief", {})
    platforms = brief.get("platforms", [])
    ref_h = brief.get("reference_height", 1080)
    exceptions = reg.get("type_exceptions", {})
    if not platforms:
        warnings.append("registry: brief.platforms is empty. Text size floor not checked.")
    else:
        unknown = [p for p in platforms if p not in TEXT_FLOOR_1080]
        if unknown:
            errors.append(f"registry: unknown platform(s) {unknown}. Use {sorted(TEXT_FLOOR_1080)}.")
        known = [p for p in platforms if p in TEXT_FLOOR_1080]
        if known:
            floor = max(TEXT_FLOOR_1080[p] for p in known) * ref_h / 1080
            for path, value in tokens.items():
                if not path.startswith("$type.size."):
                    continue
                px = to_px(value)
                if px is None:
                    warnings.append(f"registry: {path} = {value!r} is not a size. Not checked.")
                elif px < floor:
                    msg = (f"registry: {path} = {value} is below the text floor {floor:g}px "
                           f"for {known} at {ref_h}p (XAG 101)")
                    if path in exceptions:
                        warnings.append(msg + f". Exception: {exceptions[path]}")
                    else:
                        errors.append(msg + ". Raise it, or add it to type_exceptions with a reason.")
    for path, value in tokens.items():
        if path.startswith("$motion.duration."):
            ms = to_ms(value)
            if ms is not None and ms > MAX_UI_DURATION_MS:
                warnings.append(f"registry: {path} = {value} is longer than {MAX_UI_DURATION_MS}ms. "
                                f"Check that it does not block input and has a reduced-motion version.")


def check_registry(reg, errors, warnings):
    actions = reg.get("input_map", {}).get("actions", {})
    hud_screens = reg.get("hud_screens", ["hud"])
    for screen, entries in reg.get("screens", {}).items():
        for path, entry in entries.items():
            if entry.get("status") == "removed":
                continue
            comp = (entry.get("component") or "").split(":")[0]
            if comp == "@prompt" and entry.get("action") not in actions:
                errors.append(f"registry: {path} is a @prompt with action {entry.get('action')!r}, "
                              f"which is not in input_map.actions")
            if screen in hud_screens and any(t in ("#p1", "#p2", "#p3") for t in entry.get("tags", [])):
                vis = entry.get("visibility")
                if vis not in VISIBILITY:
                    errors.append(f"registry: HUD element {path} needs visibility "
                                  f"({', '.join(sorted(VISIBILITY))})")
                elif vis != "persistent" and not entry.get("trigger"):
                    errors.append(f"registry: HUD element {path} is '{vis}' but has no trigger")


# ---------------------------------------------------------------- navigation

# Default budgets [heur]. Over a default budget = WARN. Over a user-set budget = ERROR.
DEFAULT_BUDGETS = {"high": {"presses": 3, "depth": 1},
                   "medium": {"presses": 6, "depth": 2},
                   "low": {"presses": 10, "depth": 3}}


def focus_moves(scr, a, b):
    """Directional presses to move focus from element a to element b on one screen."""
    order = scr.get("focus_order", [])
    i, j = order.index(a), order.index(b)
    n, wrap = len(order), scr.get("wrap", False)
    if scr.get("layout") == "grid":
        cols = max(1, int(scr.get("cols", 1)))
        rows = -(-n // cols)
        dr, dc = abs(i // cols - j // cols), abs(i % cols - j % cols)
        if wrap:
            dr, dc = min(dr, rows - dr), min(dc, cols - dc)
        return dr + dc
    d = abs(i - j)
    return min(d, n - d) if wrap else d


def analyze_navigation(reg):
    """Return (results, errors, warnings). results: one dict per task with the cheapest path."""
    nav = reg.get("navigation")
    errors, warnings, results = [], [], []
    if not nav:
        return results, errors, warnings
    start = nav.get("start", "hud")
    screens = nav.get("screens", {})
    actions = reg.get("input_map", {}).get("actions", {})
    user_budgets = nav.get("budgets", {})
    if start not in screens:
        errors.append(f"navigation: start screen '{start}' is not in navigation.screens")
        return results, errors, warnings
    for name, scr in screens.items():
        order = scr.get("focus_order", [])
        if len(set(order)) != len(order):
            errors.append(f"navigation: screen '{name}' has duplicate IDs in focus_order")
        if order and scr.get("default_focus", order[0]) not in order:
            errors.append(f"navigation: screen '{name}' default_focus is not in its focus_order")

    # Build edges: (from, to, cost, label)
    edges = []
    for k, link in enumerate(nav.get("links", [])):
        src, dst = link.get("from"), link.get("to")
        if src not in screens or dst not in screens:
            errors.append(f"navigation: link {k} {src} -> {dst} uses an unknown screen")
            continue
        if "via" in link:
            scr = screens[src]
            order = scr.get("focus_order", [])
            if link["via"] not in order:
                errors.append(f"navigation: link {src} -> {dst} via '{link['via']}', which is not in "
                              f"the focus_order of '{src}'")
                continue
            moves = focus_moves(scr, scr.get("default_focus", order[0]), link["via"])
            edges.append((src, dst, moves + 1, f"{moves} move(s) + confirm on {link['via']}"))
        elif "input" in link:
            if actions and link["input"] not in actions:
                warnings.append(f"navigation: link {src} -> {dst} uses input '{link['input']}', "
                                f"which is not in input_map.actions")
            edges.append((src, dst, int(link.get("presses", 1)), f"button '{link['input']}'"))
        else:
            errors.append(f"navigation: link {src} -> {dst} needs 'via' (menu item) or 'input' (button)")

    # Dijkstra on (presses, depth)
    import heapq
    best = {start: (0, 0, [])}
    heap = [(0, 0, start, [])]
    while heap:
        cost, depth, node, path = heapq.heappop(heap)
        if best.get(node, (1e9, 1e9))[:2] < (cost, depth):
            continue
        for src, dst, c, label in edges:
            if src != node:
                continue
            cand = (cost + c, depth + 1)
            if cand < best.get(dst, (1e9, 1e9, None))[:2]:
                best[dst] = (*cand, path + [(src, dst, c, label)])
                heapq.heappush(heap, (*cand, dst, path + [(src, dst, c, label)]))
    for name in screens:
        if name not in best:
            warnings.append(f"navigation: screen '{name}' cannot be reached from '{start}'")

    for task, spec in nav.get("tasks", {}).items():
        freq = spec.get("frequency", "medium")
        if freq not in DEFAULT_BUDGETS:
            errors.append(f"navigation: task '{task}' has unknown frequency '{freq}' (high, medium, low)")
            continue
        target = spec.get("target", "")
        if target in screens:
            tscreen, extra, extra_label = target, 0, ""
        else:
            tscreen = next((n for n, s in screens.items() if target in s.get("focus_order", [])), None)
            if tscreen is None:
                errors.append(f"navigation: task '{task}' target '{target}' is not a screen and not in any focus_order")
                continue
            scr = screens[tscreen]
            m = focus_moves(scr, scr.get("default_focus", scr["focus_order"][0]), target)
            extra, extra_label = m + 1, f"{m} move(s) + confirm on {target}"
        if tscreen not in best:
            errors.append(f"navigation: task '{task}' cannot be reached: no path from '{start}' to '{tscreen}'")
            continue
        presses, depth, path = best[tscreen]
        presses += extra
        steps = [label for *_, label in path] + ([extra_label] if extra_label else [])
        r = {"task": task, "frequency": freq, "target": target, "presses": presses, "depth": depth,
             "path": [start] + [dst for _, dst, _, _ in path], "steps": steps, "status": "ok", "edges": path}
        for dim, key in (("presses", "max_presses"), ("depth", "max_depth")):
            if key in spec:
                limit, user = spec[key], True
            elif dim in user_budgets.get(freq, {}):
                limit, user = user_budgets[freq][dim], True
            else:
                limit, user = DEFAULT_BUDGETS[freq][dim], False
            r[f"max_{dim}"] = limit
            if r[dim] > limit:
                msg = (f"navigation: task '{task}' ({freq}) needs {r[dim]} {dim}, budget {limit}"
                       f"{' (set by user)' if user else ' (default)'}. Path: {' > '.join(r['path'])}")
                (errors if user else warnings).append(msg)
                r["status"] = "error" if user else ("warn" if r["status"] != "error" else "error")
        results.append(r)
    return results, errors, warnings


def print_navigation(results):
    if not results:
        return
    print("NAVIGATION")
    for r in sorted(results, key=lambda r: ({"high": 0, "medium": 1, "low": 2}[r["frequency"]], r["task"])):
        mark = {"ok": "ok  ", "warn": "WARN", "error": "FAIL"}[r["status"]]
        print(f"  [{mark}] {r['task']:<24} {r['frequency']:<6} presses {r['presses']}/{r['max_presses']}  "
              f"depth {r['depth']}/{r['max_depth']}  {' > '.join(r['path'])}")
        if r["status"] != "ok":
            for s in r["steps"]:
                print(f"           - {s}")
    print()


def main(reg_path, html_paths):
    reg = json.load(open(reg_path, encoding="utf-8"))
    tokens = {token_to_var(t) for t in reg.get("tokens", {})}
    components = reg.get("components", {})
    screens = reg.get("screens", {})
    actions = reg.get("input_map", {}).get("actions", {})
    allowed = [re.compile("^" + p + "$") for p in ALLOWED_TAG_PATTERNS + reg.get("extra_tags", [])]
    errors, warnings = [], []

    check_tokens(reg, errors, warnings)
    check_registry(reg, errors, warnings)
    nav_results, nav_err, nav_warn = analyze_navigation(reg)
    errors += nav_err
    warnings += nav_warn

    for hp in html_paths:
        c = Collector()
        c.feed(open(hp, encoding="utf-8").read())
        seen = {}
        for e in c.elements:
            eid, key = e["id"], strip_index(e["id"])
            screen = eid.split(".")[0]
            where = f"{hp}:{e['line']} {eid}"
            if eid in seen and "[" not in eid:
                errors.append(f"{where}: duplicate data-id")
            seen[eid] = e
            if e["component"].split(":")[0] == "@prompt" and e["action"] not in actions:
                errors.append(f"{where}: @prompt needs data-action from input_map.actions, got {e['action']!r}")
            entry = screens.get(screen, {}).get(key)
            if entry is None:
                errors.append(f"{where}: not in registry")
                continue
            if entry.get("status") == "removed":
                errors.append(f"{where}: registry marks this ID as removed")
            want_comp = entry.get("component", "")
            if want_comp != e["component"]:
                errors.append(f"{where}: data-component '{e['component']}' != registry '{want_comp}'")
            if want_comp and want_comp.split(":")[0] not in components:
                errors.append(f"{where}: component '{want_comp}' not defined in registry")
            if sorted(entry.get("tags", [])) != sorted(e["tags"]):
                errors.append(f"{where}: tags {e['tags']} != registry {entry.get('tags', [])}")
            for t in e["tags"]:
                if not any(p.match(t.lstrip("#")) for p in allowed):
                    errors.append(f"{where}: tag '{t}' not in allowed set")

        html_screens = {e["id"].split(".")[0] for e in c.elements}
        seen_keys = {strip_index(i) for i in seen}
        for s in html_screens:
            for path, entry in screens.get(s, {}).items():
                if entry.get("status") != "removed" and path not in seen_keys:
                    errors.append(f"{hp}: registry element '{path}' missing from mockup")

        all_css = "\n".join(css for _, css in c.css)
        for src, css in c.css:
            for v in VAR.findall(css):
                if v not in tokens and v not in RESERVED_VARS:
                    errors.append(f"{hp} {src}: var(--{v}) has no registry token")
            body = css_outside_root(css)
            for h in HEX.findall(body):
                warnings.append(f"{hp} {src}: hard-coded color {h} (use a token)")
            for m in FONT_SIZE_LITERAL.finditer(body):
                warnings.append(f"{hp} {src}: hard-coded '{m.group(0)}' (use a $type.size token)")
        if OUTLINE_NONE.search(all_css) and not FOCUS_RULE.search(all_css):
            errors.append(f"{hp}: 'outline: none' is used, but there is no focus style. "
                          f"Gamepad and keyboard players cannot see focus.")

        for line, text in c.text:
            m = PROMPT_TEXT.search(text)
            if m:
                errors.append(f"{hp}:{line}: hard-coded prompt '{m.group(0)}'. "
                              f"Use a @prompt component with data-action.")

    print_navigation(nav_results)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2:]))

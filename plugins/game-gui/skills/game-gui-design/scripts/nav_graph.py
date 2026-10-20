#!/usr/bin/env python3
"""Draw the navigation graph in ui-registry.json as an SVG file.

Usage: python3 nav_graph.py ui-registry.json [output.svg]
Needs validate_ui.py in the same folder. The numbers come from the same analysis as the validator.

Columns = depth from the start screen. Arrows = links, labeled with the input and press cost.
Colored arrows = task paths: green OK, amber WARN (over a default budget), red FAIL (over a user budget).
The task table under the graph repeats the status in text, so color is not the only signal.
"""
import json, os, sys
from html import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_ui import analyze_navigation, focus_moves  # noqa: E402

C = {"bg": "#ffffff", "text": "#1f2329", "muted": "#5f6670", "node": "#f4f5f7", "stroke": "#b9bec6",
     "start": "#e8eefc", "edge": "#9aa0a8", "ok": "#2e7d32", "warn": "#b26a00", "error": "#c62828"}
RANK = {"ok": 0, "warn": 1, "error": 2}
NODE_W, NODE_H, COL_GAP, ROW_GAP, PAD = 170, 44, 120, 34, 32


def short(id_):
    return id_.split(".")[-1]


def build(reg):
    nav = reg["navigation"]
    screens, start = nav.get("screens", {}), nav.get("start", "hud")
    results, errors, warnings = analyze_navigation(reg)

    # Edges with cost and label
    edges = []
    for link in nav.get("links", []):
        s, d = link.get("from"), link.get("to")
        if s not in screens or d not in screens:
            continue
        if "via" in link:
            scr = screens[s]
            order = scr.get("focus_order", [])
            if link["via"] not in order:
                continue
            m = focus_moves(scr, scr.get("default_focus", order[0]), link["via"])
            edges.append({"s": s, "d": d, "cost": m + 1, "label": f"{short(link['via'])} ({m + 1})",
                          "key": f"{m} move(s) + confirm on {link['via']}", "status": None})
        elif "input" in link:
            c = int(link.get("presses", 1))
            edges.append({"s": s, "d": d, "cost": c, "label": f"[{link['input']}] ({c})",
                          "key": f"button '{link['input']}'", "status": None})

    # Mark edges used by task paths with the worst status of those tasks
    for r in results:
        for (s, d, _, label) in r["edges"]:
            for e in edges:
                if e["s"] == s and e["d"] == d and e["key"] == label:
                    if e["status"] is None or RANK[r["status"]] > RANK[e["status"]]:
                        e["status"] = r["status"]

    # Levels: shortest hop count from start (BFS). Unreachable screens go to the last column.
    level, frontier = {start: 0}, [start]
    while frontier:
        nxt = []
        for n in frontier:
            for e in edges:
                if e["s"] == n and e["d"] not in level:
                    level[e["d"]] = level[n] + 1
                    nxt.append(e["d"])
        frontier = nxt
    max_lv = max(level.values()) if level else 0
    unreachable = [n for n in screens if n not in level]
    for n in unreachable:
        level[n] = max_lv + 1

    cols = {}
    for n in screens:  # keep registry order inside a column
        cols.setdefault(level[n], []).append(n)
    pos = {}
    for lv, names in cols.items():
        for i, n in enumerate(names):
            pos[n] = (PAD + lv * (NODE_W + COL_GAP), PAD + 64 + i * (NODE_H + ROW_GAP))
    return screens, start, edges, pos, cols, unreachable, results, errors


def render(reg):
    screens, start, edges, pos, cols, unreachable, results, errors = build(reg)
    n_cols = max(cols) + 1 if cols else 1
    graph_h = max(len(v) for v in cols.values()) * (NODE_H + ROW_GAP) + 64 if cols else 100
    width = max(PAD * 2 + n_cols * NODE_W + (n_cols - 1) * COL_GAP, 760)
    table_y = PAD + graph_h + 24
    row_h = 22
    height = table_y + 40 + row_h * max(1, len(results)) + (row_h * (len(errors) + 1) if errors else 0) + PAD

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="system-ui, -apple-system, Segoe UI, sans-serif" font-size="13">',
           '<title>Navigation graph</title>',
           f'<rect width="100%" height="100%" fill="{C["bg"]}"/>',
           '<defs>']
    for k in ("edge", "ok", "warn", "error"):
        out.append(f'<marker id="a-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                   f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C[k]}"/></marker>')
    out.append('</defs>')

    # Column headers
    for lv in sorted(cols):
        x = PAD + lv * (NODE_W + COL_GAP)
        head = "unreachable" if unreachable and cols[lv] == unreachable and lv == max(cols) else f"depth {lv}"
        out.append(f'<text x="{x}" y="{PAD + 12}" fill="{C["muted"]}" font-size="12">{head}</text>')

    # Edges (draw before nodes). Forward edges: straight-ish curve. Back or same-column: arc.
    pair_count = {}
    for e in edges:
        (x1, y1), (x2, y2) = pos[e["s"]], pos[e["d"]]
        key = (e["s"], e["d"])
        k = pair_count.get(key, 0)
        pair_count[key] = k + 1
        color = C[e["status"]] if e["status"] else C["edge"]
        width_ = 2.4 if e["status"] else 1.4
        marker = f'url(#a-{e["status"] or "edge"})'
        if x2 > x1:
            sx, sy, ex, ey = x1 + NODE_W, y1 + NODE_H / 2 + k * 8, x2, y2 + NODE_H / 2 + k * 8
            mx = (sx + ex) / 2
            d = f"M{sx},{sy} C{mx},{sy} {mx},{ey} {ex},{ey}"
            lx, ly = mx, (sy + ey) / 2 - 6
        elif x2 == x1:  # same column: vertical link on the left side
            down = y2 > y1
            sx, ex = x1 + 24 + k * 10, x2 + 24 + k * 10
            sy, ey = (y1 + NODE_H, y2) if down else (y1, y2 + NODE_H)
            d = f"M{sx},{sy} L{ex},{ey}"
            lx, ly = sx + 8 + 3.5 * len(e["label"]), (sy + ey) / 2 + 4
        else:  # back link: dashed, from the left side of src to the right side of dst
            sx, sy = x1, y1 + NODE_H - 8 - k * 6
            ex, ey = x2 + NODE_W, y2 + NODE_H - 8 - k * 6
            mx = (sx + ex) / 2
            d = f"M{sx},{sy} C{mx},{sy} {mx},{ey} {ex},{ey}"
            lx, ly = mx, (sy + ey) / 2 + 14
        dash = ' stroke-dasharray="6 4"' if x2 < x1 else ""
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width_}"{dash} marker-end="{marker}"/>')
        label = escape(e["label"])
        tw = 7 * len(e["label"]) + 8
        out.append(f'<rect x="{lx - tw / 2}" y="{ly - 12}" width="{tw}" height="16" rx="3" fill="{C["bg"]}" opacity="0.9"/>')
        out.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" fill="{color}" font-size="11">{label}</text>')

    # Nodes
    for n, (x, y) in pos.items():
        fill = C["start"] if n == start else C["node"]
        dash = ' stroke-dasharray="5 4"' if n in unreachable else ""
        out.append(f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="6" fill="{fill}" '
                   f'stroke="{C["stroke"]}" stroke-width="1.2"{dash}/>')
        items = len(screens[n].get("focus_order", []))
        out.append(f'<text x="{x + 12}" y="{y + 19}" fill="{C["text"]}" font-weight="600">{escape(n)}'
                   f'{" (start)" if n == start else ""}</text>')
        sub = f'{items} focusable, {screens[n].get("layout", "list")}' if items else "no focus list"
        out.append(f'<text x="{x + 12}" y="{y + 35}" fill="{C["muted"]}" font-size="11">{escape(sub)}</text>')

    # Task table
    y = table_y
    out.append(f'<text x="{PAD}" y="{y}" fill="{C["text"]}" font-weight="600">Tasks (cheapest gamepad path from '
               f'{escape(start)})</text>')
    y += 22
    cols_x = [PAD, PAD + 70, PAD + 250, PAD + 330, PAD + 430, PAD + 520]
    for x, h in zip(cols_x, ["status", "task", "freq", "presses", "depth", "path"]):
        out.append(f'<text x="{x}" y="{y}" fill="{C["muted"]}" font-size="12">{h}</text>')
    order = {"high": 0, "medium": 1, "low": 2}
    for r in sorted(results, key=lambda r: (order[r["frequency"]], r["task"])):
        y += row_h
        st = {"ok": "OK", "warn": "WARN", "error": "FAIL"}[r["status"]]
        vals = [st, r["task"], r["frequency"], f'{r["presses"]} / {r["max_presses"]}',
                f'{r["depth"]} / {r["max_depth"]}', " > ".join(r["path"])]
        for i, (x, v) in enumerate(zip(cols_x, vals)):
            color = C[r["status"]] if i == 0 else C["text"]
            weight = ' font-weight="600"' if i == 0 else ""
            out.append(f'<text x="{x}" y="{y}" fill="{color}"{weight}>{escape(str(v))}</text>')
    if errors:
        y += row_h + 6
        out.append(f'<text x="{PAD}" y="{y}" fill="{C["error"]}" font-weight="600">Navigation errors</text>')
        for e in errors:
            y += row_h
            out.append(f'<text x="{PAD}" y="{y}" fill="{C["error"]}" font-size="12">'
                       f'{escape(e.replace("navigation: ", ""))}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    reg = json.load(open(sys.argv[1], encoding="utf-8"))
    if not reg.get("navigation"):
        print("ui-registry.json has no 'navigation' section. Nothing to draw.")
        sys.exit(1)
    out_path = sys.argv[2] if len(sys.argv) > 2 else "nav-graph.svg"
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(render(reg))
    print(f"Wrote {out_path}")

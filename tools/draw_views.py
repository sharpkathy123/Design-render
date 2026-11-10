"""A design's drawing sheet from its parts list (Design-render, 2026-11-10):
the front, the right side and the top, drawn to one scale and laid out as a
shop drawing has them (the top above the front, the side to its right),
the overall sizes and the model's own dimensions (kit.dim) on them, and the
cut list in the corner. Plain SVG, sharp at any zoom (Sketchup-tools'
docs/drawings.md: SVG for drawings).

    python3 tools/draw_views.py designs/<name>/parts.json [designs/<name>/<name>-drawing.svg]

parts.json is written by the model (tools/blender/kit.py write_parts()).
Nearer parts are drawn over farther ones, so what's behind is hidden; a
part with cuts in it is drawn as its outline.
"""
import json
import math
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgdraw import SvgDraw  # noqa: E402

INK = "#2a2724"
DIM = "#8a3b12"
DIM_OFF = 2.0
FILL = "#ffffff"
HIDDEN = 'fill="none" stroke="%s" stroke-width="0.8" stroke-dasharray="5 3"' % INK
SHADE = {"box": "#ffffff", "cyl": "#f1efe9", "prism": "#ffffff"}


def font(size):
    return type("Font", (), {"path": "sans.ttf", "size": size})


def frac(x, den=16):
    """Inches to the nearest 1/16, as a shop drawing writes it: 29 3/4"."""
    neg = x < 0
    n = int(round(abs(x) * den))
    whole, rest = divmod(n, den)
    g = math.gcd(rest, den) if rest else den
    s = ("%d" % whole if whole or not rest else "") + ((" " if whole else "") + "%d/%d" % (rest // g, den // g) if rest else "")
    return ("-" if neg else "") + s + '"'


# each view: (horizontal axis, its sign), (vertical axis), the depth axis, nearer = which way
VIEWS = {
    "front": dict(h=0, hs=1, v=2, depth=1, near=-1, title="FRONT"),
    "side": dict(h=1, hs=1, v=2, depth=0, near=1, title="RIGHT SIDE"),
    "top": dict(h=0, hs=1, v=1, depth=2, near=1, title="TOP"),
}


def shapes(part, view):
    """The part's outline in a view: ("rect", (h0, v0, h1, v1)), ("circle",
    (ch, cv, r)) or ("poly", [(h, v), ...]), in inches."""
    vw = VIEWS[view]
    h, vv, d = vw["h"], vw["v"], vw["depth"]
    lo, hi = part["lo"], part["hi"]
    rect = ("rect", (lo[h], lo[vv], hi[h], hi[vv]))
    if part["kind"] == "cyl" and "xyz".index(part["axis"]) == d:
        return ("circle", ((lo[h] + hi[h]) / 2, (lo[vv] + hi[vv]) / 2, part["r"]))
    if part["kind"] == "prism" and "xyz".index(part["axis"]) == d:
        others = [k for k in range(3) if k != d]
        pts = []
        for u, w in part["pts"]:
            c = {others[0]: u, others[1]: w}
            pts.append((c[h], c[vv]))
        return ("poly", pts)
    return rect


def order(parts, view):
    """Farthest first, so nearer parts cover them."""
    vw = VIEWS[view]
    d, near = vw["depth"], vw["near"]
    if near > 0:
        return sorted(parts, key=lambda p: (p["hi"][d], p["lo"][d]))
    return sorted(parts, key=lambda p: (-p["lo"][d], -p["hi"][d]))


def cut_list(data):
    """Rows (qty, names, material, T x W x L) of like parts together."""
    rows = OrderedDict()
    for p in data["parts"]:
        lo, hi = p["lo"], p["hi"]
        size = [hi[k] - lo[k] for k in range(3)]
        mat = data["materials"].get(p["key"], p["key"])
        if p["kind"] == "cyl":
            L = size["xyz".index(p["axis"])]
            desc = "%s dia. x %s" % (frac(2 * p["r"]), frac(L))
        else:
            g = "xyz".index(p.get("grain", "x"))
            L = size[g]
            t, w = sorted(size[k] for k in range(3) if k != g)
            desc = "%s x %s x %s" % (frac(t), frac(w), frac(L)) + (" (shaped)" if p["kind"] == "prism" else "")
        base = p["name"].rstrip("0123456789 ").rstrip(" -_") or p["name"]
        k = (base, mat, desc)
        rows[k] = rows.get(k, 0) + 1
    return [(n, base, mat, desc) for (base, mat, desc), n in rows.items()]


def draw(data, out):
    lo, hi = data["bounds"]
    W, D, H = (hi[k] - lo[k] for k in range(3))
    big = max(W, D, H)
    K = min(14.0, 900.0 / max(W + D, 1.0), 700.0 / max(H + D, 1.0))   # px per inch
    global DIM_OFF
    DIM_OFF = 2.2 * big / 40 + 1.5                                 # the overall dimensions' offset, inches
    M, GAP = 70.0, max(80.0, 0.25 * D * K)
    rows = cut_list(data)
    table_w = 620.0
    # where each view's (h, v) = lo corner lands on the sheet
    fx, fy = M + 40, M + 60 + D * K + GAP + H * K          # the front view's lower left (y down)
    origins = {"front": (fx, fy), "top": (fx, M + 60 + D * K), "side": (fx + W * K + GAP, fy)}
    sw = max(origins["side"][0] + D * K + M + 40, fx + W * K + GAP + table_w + M)
    sh = fy + DIM_OFF * K + 80 + 20 * len(data.get("notes", []))
    sh = max(sh, M + 60 + 30 * (len(rows) + 4))
    svg = SvgDraw((int(sw), int(sh)))

    def P(view, hv):
        ox, oy = origins[view]
        vw = VIEWS[view]
        return ox + (hv[0] - lo[vw["h"]]) * K, oy - (hv[1] - lo[vw["v"]]) * K

    for view in ("front", "side", "top"):
        for p in order(data["parts"], view):
            kind, s = shapes(p, view)
            fill = SHADE.get(p["kind"], FILL)
            if kind == "rect":
                (x0, y0), (x1, y1) = P(view, (s[0], s[3])), P(view, (s[2], s[1]))
                svg.rectangle([(x0, y0), (x1, y1)], fill=fill, outline=INK, width=1.2)
            elif kind == "circle":
                cx, cy = P(view, (s[0], s[1]))
                r = s[2] * K
                svg.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=fill, outline=INK, width=1.2)
            else:
                svg.polygon([P(view, q) for q in s], fill=fill, outline=INK, width=1.2)
        # every outline again, dashed and thin: over a visible edge it reads
        # as the solid line; where a nearer part covers one, as a hidden line
        for p in data["parts"]:
            kind, s = shapes(p, view)
            if kind == "rect":
                (x0, y0), (x1, y1) = P(view, (s[0], s[3])), P(view, (s[2], s[1]))
                svg.parts.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" %s/>' % (x0, y0, x1 - x0, y1 - y0, HIDDEN))
            elif kind == "circle":
                cx, cy = P(view, (s[0], s[1]))
                svg.parts.append('<circle cx="%.2f" cy="%.2f" r="%.2f" %s/>' % (cx, cy, s[2] * K, HIDDEN))
            else:
                svg.parts.append('<polygon points="%s" %s/>' % (" ".join("%.2f,%.2f" % P(view, q) for q in s), HIDDEN))
        vw = VIEWS[view]
        x0, y0 = P(view, (lo[vw["h"]], lo[vw["v"]]))
        x1, _ = P(view, (hi[vw["h"]], lo[vw["v"]]))
        below = 24 if view == "top" else 24 + DIM_OFF * K + 22
        svg.text(((x0 + x1) / 2, y0 + below), vw["title"], font=font(13), fill=INK, anchor="mt")

    def dimension(view, a, b, label, offset, along):
        """A dimension line in a view between two (h, v) points, `along`
        "h" or "v", offset in inches (+: up or right)."""
        pa, pb = P(view, a), P(view, b)
        if along == "h":
            y = min(pa[1], pb[1]) - offset * K if offset > 0 else max(pa[1], pb[1]) - offset * K
            for p in (pa, pb):
                svg.line([(p[0], p[1] + (-4 if offset > 0 else 4)), (p[0], y + (-5 if offset > 0 else 5))], fill=DIM, width=0.7)
            svg.line([(pa[0], y), (pb[0], y)], fill=DIM, width=0.9)
            for x in (pa[0], pb[0]):
                svg.line([(x - 4, y + 4), (x + 4, y - 4)], fill=DIM, width=1.2)
            svg.text(((pa[0] + pb[0]) / 2, y - 4), label, font=font(12), fill=DIM, anchor="md")
        else:
            x = max(pa[0], pb[0]) + offset * K if offset > 0 else min(pa[0], pb[0]) + offset * K
            for p in (pa, pb):
                svg.line([(p[0] + (4 if offset > 0 else -4), p[1]), (x + (5 if offset > 0 else -5), p[1])], fill=DIM, width=0.7)
            svg.line([(x, pa[1]), (x, pb[1])], fill=DIM, width=0.9)
            for y in (pa[1], pb[1]):
                svg.line([(x - 4, y + 4), (x + 4, y - 4)], fill=DIM, width=1.2)
            svg.text((x + (6 if offset > 0 else -6), (pa[1] + pb[1]) / 2), label, font=font(12), fill=DIM,
                     anchor="lm" if offset > 0 else "rm")

    # the overall sizes
    dimension("front", (lo[0], lo[2]), (hi[0], lo[2]), frac(W), -DIM_OFF, "h")
    dimension("front", (lo[0], lo[2]), (lo[0], hi[2]), frac(H), -DIM_OFF, "v")
    dimension("side", (lo[1], lo[2]), (hi[1], lo[2]), frac(D), -DIM_OFF, "h")
    # the model's own
    for dm in data.get("dims", []):
        vw = VIEWS[dm["view"]]
        a = (dm["a"][vw["h"]], dm["a"][vw["v"]])
        b = (dm["b"][vw["h"]], dm["b"][vw["v"]])
        along = "h" if abs(a[0] - b[0]) >= abs(a[1] - b[1]) else "v"
        if along == "h":
            b = (b[0], a[1])
        else:
            b = (a[0], b[1])
        dimension(dm["view"], a, b, dm["label"] or frac(abs((b[0] - a[0]) if along == "h" else (b[1] - a[1]))),
                  dm.get("offset", 2.0), along)

    # the title and the cut list, in the top right
    tx = origins["side"][0]
    ty = M
    svg.text((tx, ty), data.get("name") or "Design", font=font(22), fill=INK, anchor="la")
    svg.text((tx, ty + 30), "%s wide x %s deep x %s high, in inches" % (frac(W), frac(D), frac(H)),
             font=font(12), fill="#555", anchor="la")
    # a 12" scale bar, in 3" steps
    for i in range(4):
        svg.rectangle([(tx + i * 3 * K, ty + 48), (tx + (i + 1) * 3 * K, ty + 54)],
                      fill=INK if i % 2 == 0 else FILL, outline=INK, width=0.8)
    svg.text((tx + 12 * K + 8, ty + 51), '12"', font=font(11), fill="#555", anchor="lm")
    y = ty + 84
    svg.text((tx, y), "CUT LIST", font=font(13), fill=INK, anchor="la")
    y += 22
    cols = (0, 40, 230, 400)
    for i, head in enumerate(("Qty", "Part", "Material", "T x W x L")):
        svg.text((tx + cols[i], y), head, font=font(11), fill="#555", anchor="la")
    y += 16
    svg.line([(tx, y), (tx + table_w - 20, y)], fill="#aaa", width=0.7)
    y += 6
    for n, base, mat, desc in rows:
        for i, s in enumerate((str(n), base, mat, desc)):
            svg.text((tx + cols[i], y), s, font=font(12), fill=INK, anchor="la")
        y += 20
    for i, note in enumerate(data.get("notes", [])):
        svg.text((M, sh - 30 - 20 * (len(data["notes"]) - 1 - i)), note, font=font(12), fill="#555", anchor="la")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    svg.save(out)
    print("DRAWING %s" % out)


def main():
    src = sys.argv[1]
    data = json.load(open(src))
    name = os.path.basename(os.path.dirname(os.path.abspath(src)))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(src), name + "-drawing.svg")
    draw(data, out)


if __name__ == "__main__":
    main()

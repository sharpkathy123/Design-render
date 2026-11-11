"""The bed frame's joinery sheet: every mortise, tenon, peg and bolt hole,
dimensioned for marking out, from sizes.py (the same numbers the model is
built from).

    python3 designs/bed-frame/draw_joinery.py      # writes bed-frame-joinery.svg

Each detail is drawn to its own scale; work from the numbers. Distances on
the posts and legs are from the floor (their bottom ends), and from their
front faces (the faces toward the foot of the bed).
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sizes import *  # noqa: E402,F401,F403

INK, DIM, NOTE, HID = "#2a2724", "#8a3b12", "#555555", "#2a2724"
FONT = "Helvetica, Arial, sans-serif"
OUT = []


class Detail:
    """A drawing at (ox, oy) on the sheet, k px per inch, its own inches
    with y up from (ox, oy)."""

    def __init__(self, ox, oy, k, title, sub=""):
        self.ox, self.oy, self.k = ox, oy, k
        self.title, self.sub = title, sub

    def P(self, x, y):
        return self.ox + x * self.k, self.oy - y * self.k

    def rect(self, x0, y0, x1, y1, fill="#fff", dash=False, sw=1.2, color=INK):
        a, b = self.P(min(x0, x1), max(y0, y1))
        OUT.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="%s"%s/>'
                   % (a, b, abs(x1 - x0) * self.k, abs(y1 - y0) * self.k, fill, color, sw,
                      ' stroke-dasharray="5 3"' if dash else ""))

    def poly(self, pts, fill="#fff", dash=False, sw=1.2):
        OUT.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s"%s/>'
                   % (" ".join("%.1f,%.1f" % self.P(*p) for p in pts), fill, INK, sw,
                      ' stroke-dasharray="5 3"' if dash else ""))

    def line(self, pts, color=INK, sw=1.0, dash=False):
        OUT.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"%s/>'
                   % (" ".join("%.1f,%.1f" % self.P(*p) for p in pts), color, sw, ' stroke-dasharray="5 3"' if dash else ""))

    def circle(self, x, y, r, fill="#fff", dash=False):
        cx, cy = self.P(x, y)
        OUT.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="1"%s/>'
                   % (cx, cy, r * self.k, fill, INK, ' stroke-dasharray="4 2"' if dash else ""))

    def text(self, x, y, s, size=12, anchor="middle", color=INK, px=(0, 0), weight="normal"):
        a, b = self.P(x, y)
        OUT.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" fill="%s" text-anchor="%s" font-weight="%s">%s</text>'
                   % (a + px[0], b + px[1], FONT, size, color, anchor, weight, html.escape(s)))

    def dim(self, a, b, off, label=None, along=None):
        """A dimension from a to b (inches), offset off inches (+ up/right)."""
        along = along or ("h" if abs(b[0] - a[0]) >= abs(b[1] - a[1]) else "v")
        if along == "h":
            y = (max(a[1], b[1]) if off > 0 else min(a[1], b[1])) + off
            pa, pb = (a[0], y), (b[0], y)
            for p in (a, b):
                self.line([(p[0], p[1]), (p[0], y + (0.08 if off > 0 else -0.08) * 12 / self.k)], DIM, 0.6)
            v = abs(b[0] - a[0])
        else:
            x = (max(a[0], b[0]) if off > 0 else min(a[0], b[0])) + off
            pa, pb = (x, a[1]), (x, b[1])
            for p in (a, b):
                self.line([(p[0], p[1]), (x + (0.08 if off > 0 else -0.08) * 12 / self.k, p[1])], DIM, 0.6)
            v = abs(b[1] - a[1])
        self.line([pa, pb], DIM, 0.9)
        for p in (pa, pb):
            x, y = self.P(*p)
            OUT.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.2"/>' % (x - 4, y + 4, x + 4, y - 4, DIM))
        lab = label or frac(v)
        mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        if along == "h":
            self.text(mx, my, lab, 11, color=DIM, px=(0, -4))
        else:
            self.text(mx, my, lab, 11, "start" if off > 0 else "end", DIM, px=(5 if off > 0 else -5, 4))

    def heading(self, top):
        """The detail's title and notes, above its top (inches)."""
        x, y = self.P(0, top)
        sub = self.sub.split("\n") if self.sub else []
        y0 = y - 22 - 15 * len(sub)
        OUT.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="14" font-weight="bold" fill="%s">%s</text>'
                   % (x, y0, FONT, INK, html.escape(self.title)))
        for i, ln in enumerate(sub):
            OUT.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="11" fill="%s">%s</text>'
                       % (x, y0 + 16 + 15 * i, FONT, NOTE, html.escape(ln)))


# ---------------------------------------------------------------------------
TOP = POST_BODY + CAP_RISE
hb_mort_y = (HB_Y - (L - POST)) + (HB_RAIL_T - HB_TENON_T) / 2           # from the post's front face
ft_mort_y = (FOOT_IN - RAIL_T) + (RAIL_T - FOOT_TENON_T) / 2              # from the leg's front face
rails = (("top", HB_TOP), ("bottom", HB_BOTTOM))


def head_post(ox, oy):
    k = 9.0
    d = Detail(ox, oy, k, "A. HEAD POST (2)", "2 3/4\" square, %s long with its cap.\nLeft post shown; the right is its mirror." % frac(TOP))
    gap = 9.0
    # inside face: the through-mortises (seen on this face and on the outside face)
    d.rect(0, 0, POST, POST_BODY)
    d.poly([(0, POST_BODY), (POST, POST_BODY), (POST / 2 + CAP_FLAT / 2, TOP), (POST / 2 - CAP_FLAT / 2, TOP)])
    for nm, (z0, z1) in rails:
        d.rect(hb_mort_y, z0 + HB_SHOULDER, hb_mort_y + HB_TENON_T, z1 - HB_SHOULDER, fill="#e9e3d6")
        d.dim((POST, 0), (POST, z0 + HB_SHOULDER), 1.2 if nm == "bottom" else 2.6)
        d.dim((POST, z0 + HB_SHOULDER), (POST, z1 - HB_SHOULDER), 1.2)
    d.rect(0, STUB[3], STUB[2], STUB[3] + STUB[1], fill="#e9e3d6", dash=True)
    d.text(POST / 2, -1.2, "INSIDE FACE", 11, color=NOTE)
    d.text(-0.3, (HB_TOP[0] + HB_TOP[1]) / 2, "front", 10, "end", NOTE)
    # front face: the pegs, the side rail's stub mortise and bolt
    fx = POST + gap
    d.rect(fx, 0, fx + POST, POST_BODY)
    d.poly([(fx, POST_BODY), (fx + POST, POST_BODY), (fx + POST / 2 + CAP_FLAT / 2, TOP), (fx + POST / 2 - CAP_FLAT / 2, TOP)])
    for nm, (z0, z1) in rails:
        for zp in (z0 + HB_SHOULDER + PEG_IN, z1 - HB_SHOULDER - PEG_IN):
            d.rect(fx + POST / 2 - PEG / 2, zp - PEG / 2, fx + POST / 2 + PEG / 2, zp + PEG / 2, fill="#bba78a")
    d.rect(fx + (POST - RAIL_T) / 2, RAIL_Z[0], fx + (POST + RAIL_T) / 2, RAIL_Z[1], fill="none", dash=True)
    d.rect(fx + POST / 2 - STUB[0] / 2, STUB[3], fx + POST / 2 + STUB[0] / 2, STUB[3] + STUB[1], fill="#e9e3d6")
    d.circle(fx + POST / 2, BOLT_Z[0], 0.1875, fill="#e9e3d6")
    d.dim((fx, BOLT_Z[0]), (fx, 0), -1.0, along="v")
    d.dim((fx + POST, STUB[3]), (fx + POST, STUB[3] + STUB[1]), 1.3, along="v")
    d.text(fx + POST / 2, -1.2, "FRONT FACE", 11, color=NOTE)
    # notes
    notes = [
        "Through-mortises %s x %s and %s x %s, %s from the front face," % (frac(HB_TENON_T), frac(HB_TOP[1] - HB_TOP[0] - 2 * HB_SHOULDER),
                                                                          frac(HB_TENON_T), frac(HB_BOTTOM[1] - HB_BOTTOM[0] - 2 * HB_SHOULDER), frac(hb_mort_y)),
        "  cut halfway from the inside and outside faces so neither blows out.",
        "Pegs %s square, %s deep from the front face, centered across it, at" % (frac(PEG), frac(hb_mort_y + HB_TENON_T + 0.375)),
        "  " + ", ".join(frac(z) for nm, (z0, z1) in reversed(rails) for z in (z0 + HB_SHOULDER + PEG_IN, z1 - HB_SHOULDER - PEG_IN)) + " up.",
        "Stub mortise for the side rail: %s x %s x %s deep, centered, %s up." % (frac(STUB[0]), frac(STUB[1]), frac(STUB[2] + 1 / 16), frac(STUB[3])),
        "Bed bolt: %s hole through, front to back, %s up, centered;" % (frac(0.375), frac(BOLT_Z[0])),
        "  %s counterbore %s deep on the back face for the bolt head." % (frac(BOLT_COUNTERBORE[0]), frac(BOLT_COUNTERBORE[1])),
        "Pyramid cap: %s rise to a %s flat; plane or sand it before glue-up." % (frac(CAP_RISE), frac(CAP_FLAT)),
    ]
    for i, n in enumerate(notes):
        d.text(fx + POST + 4.5, TOP - 1.0 - i * 2.4, n, 11, "start", NOTE)
    d.heading(TOP + 1.0)


def rail_end(d, x0, y0, rail_h, tenon_h, shoulder, tenon_l, chamfer=0.125, label=""):
    """A rail's end seen from the front: the rail, its tenon, peg holes."""
    d.rect(x0, y0, x0 + 4.0, y0 + rail_h)
    d.poly([(x0, y0 + shoulder), (x0 - tenon_l + chamfer, y0 + shoulder), (x0 - tenon_l, y0 + shoulder + chamfer),
            (x0 - tenon_l, y0 + shoulder + tenon_h - chamfer), (x0 - tenon_l + chamfer, y0 + shoulder + tenon_h),
            (x0, y0 + shoulder + tenon_h)])
    d.line([(x0 - POST, y0 - 0.4), (x0 - POST, y0 + rail_h + 0.4)], NOTE, 0.6, dash=True)
    d.dim((x0 - tenon_l, y0 + shoulder + tenon_h), (x0, y0 + shoulder + tenon_h), 0.8)
    d.dim((x0 - tenon_l, y0 + shoulder), (x0 - tenon_l, y0 + shoulder + tenon_h), -0.6)
    d.dim((x0 + 4.0, y0), (x0 + 4.0, y0 + rail_h), 0.6)
    for zp in (shoulder + PEG_IN, shoulder + tenon_h - PEG_IN):
        d.rect(x0 - POST / 2 - PEG / 2, y0 + zp - PEG / 2, x0 - POST / 2 + PEG / 2, y0 + zp + PEG / 2, fill="#bba78a")
    d.text(x0 + 6.8, y0 + rail_h / 2, label, 11, "start", NOTE)


def headboard_rails(ox, oy):
    k = 18.0
    d = Detail(ox, oy, k, "B. HEADBOARD RAILS: THROUGH-TENONS",
               "%s thick tenons, centered on the %s rail; shoulders %s top and bottom." % (frac(HB_TENON_T), frac(HB_RAIL_T), frac(HB_SHOULDER)) +
               "\nThe dashed line is the post's outside face: the tenon stands %s proud, its end chamfered %s." % (frac(PROUD), frac(0.125)))
    tl = POST + PROUD
    rail_end(d, tl + 1.2, 0.0, HB_BOTTOM[1] - HB_BOTTOM[0], HB_BOTTOM[1] - HB_BOTTOM[0] - 2 * HB_SHOULDER, HB_SHOULDER, tl,
             label="bottom rail")
    rail_end(d, tl + 1.2, 7.0, HB_TOP[1] - HB_TOP[0], HB_TOP[1] - HB_TOP[0] - 2 * HB_SHOULDER, HB_SHOULDER, tl,
             label="top rail (edges rounded %s)" % frac(0.375))
    d.heading(7.0 + HB_TOP[1] - HB_TOP[0] + 1.5)


def slats(ox, oy):
    k = 9.0
    sw = HB_SLAT_W
    d = Detail(ox, oy, k, "C. HEADBOARD SLATS (7) AND THEIR MORTISES",
               "Slats %s x %s x %s with tenons (%s between the rails)." % (frac(SLAT_T), frac(sw), frac(HB_TOP[0] - HB_BOTTOM[1] + 2 * SLAT_TENON[1]), frac(HB_TOP[0] - HB_BOTTOM[1])) +
               "\nStub tenons %s thick x %s long, %s shoulders each side; flush with the rails' front faces." % (frac(SLAT_TENON[0]), frac(SLAT_TENON[1]), frac(SLAT_TENON[2])))
    # one slat's end
    d.rect(0, 0, sw, 3.0)
    d.rect(SLAT_TENON[2], 3.0, sw - SLAT_TENON[2], 3.0 + SLAT_TENON[1])
    d.dim((SLAT_TENON[2], 3.0 + SLAT_TENON[1]), (sw - SLAT_TENON[2], 3.0 + SLAT_TENON[1]), 0.6)
    d.dim((0, 0), (sw, 0), -0.8)
    d.dim((sw, 3.0), (sw, 3.0 + SLAT_TENON[1]), 0.6)
    d.text(sw / 2, 1.4, "slat, front", 11, color=NOTE)
    # the mortise layout along a rail
    rows = ["Mortises in both rails, %s wide x %s deep, %s from the rails' front faces;" % (frac(SLAT_TENON[0]), frac(SLAT_TENON[1] + 1 / 16), frac((SLAT_T - SLAT_TENON[0]) / 2)),
            "measured from the rail's shoulder (the post's inside face):"]
    for i in range(HB_SLATS):
        a = HB_GAP + i * (sw + HB_GAP) + SLAT_TENON[2]
        rows.append("  slat %d: %s to %s" % (i + 1, frac(a), frac(a + sw - 2 * SLAT_TENON[2])))
    for i, r in enumerate(rows):
        d.text(sw + 4.5, 5.5 - i * 1.65, r, 11, "start", NOTE)
    d.heading(6.5)


def foot(ox, oy):
    k = 9.0
    d = Detail(ox, oy, k, "D. FOOT LEGS (2) AND FOOT RAIL",
               "Legs %s square x %s with the cap; the rail %s thick, %s tall at its ends, its bottom arched %s." % (frac(POST), frac(FOOT_LEG + CAP_RISE), frac(RAIL_T), frac(FOOT_Z[1] - FOOT_Z[0]), frac(FOOT_ARCH)) +
               "\nLeft leg and the rail's left end shown; the right is the mirror.")
    # left leg, front face
    d.rect(0, 0, POST, FOOT_LEG)
    d.poly([(0, FOOT_LEG), (POST, FOOT_LEG), (POST / 2 + CAP_FLAT / 2, FOOT_LEG + CAP_RISE), (POST / 2 - CAP_FLAT / 2, FOOT_LEG + CAP_RISE)])
    d.dim((0, FOOT_Z[1]), (0, FOOT_LEG), -0.8, label=frac(FOOT_LEG - FOOT_Z[1]) + " above rail")
    for zp in (FOOT_TENON_Z[0] + PEG_IN, FOOT_TENON_Z[1] - PEG_IN):
        d.rect(POST / 2 - PEG / 2, zp - PEG / 2, POST / 2 + PEG / 2, zp + PEG / 2, fill="#bba78a")
    d.circle(POST / 2, BOLT_Z[0], BOLT_COUNTERBORE[0] / 2, fill="#f3e3b5")
    d.dim((0, 0), (0, BOLT_Z[0]), -1.0)
    d.text(POST / 2, -1.2, "LEG, FRONT FACE", 11, color=NOTE)
    # the rail's left end, with the leg's mortise in section
    rx = POST + 5.0
    d.rect(rx, FOOT_Z[0], rx + POST, FOOT_LEG, fill="#f6f3ec")
    d.rect(rx, FOOT_TENON_Z[0], rx + POST, FOOT_TENON_Z[1], fill="#e9e3d6")
    d.text(rx + POST / 2, FOOT_Z[0] - 2.6, "leg, in section", 10, color=NOTE)
    run = 26.0
    span = (HB_SPAN) - 2 * FOOT_FLAT
    r = (span ** 2 / 4 + FOOT_ARCH ** 2) / (2 * FOOT_ARCH)
    import math
    arch = []
    for i in range(0, 41):
        xx = FOOT_FLAT + (run - FOOT_FLAT) * i / 40
        dx = xx - HB_SPAN / 2
        arch.append((rx + POST + xx, FOOT_Z[0] + math.sqrt(max(0, r * r - dx * dx)) - (r - FOOT_ARCH)))
    d.line([(rx + POST, FOOT_Z[1]), (rx + POST + run, FOOT_Z[1])])
    d.line([(rx + POST, FOOT_Z[0]), (rx + POST + FOOT_FLAT, FOOT_Z[0])] + arch)
    d.line([(rx + POST + run, FOOT_Z[1] + 0.5), (rx + POST + run, arch[-1][1] - 0.5)], NOTE, 0.8, dash=True)
    d.poly([(rx + POST, FOOT_TENON_Z[0]), (rx - PROUD + 0.125, FOOT_TENON_Z[0]), (rx - PROUD, FOOT_TENON_Z[0] + 0.125),
            (rx - PROUD, FOOT_TENON_Z[1] - 0.125), (rx - PROUD + 0.125, FOOT_TENON_Z[1]), (rx + POST, FOOT_TENON_Z[1])],
           fill="none")
    d.dim((rx - PROUD, FOOT_Z[1]), (rx + POST, FOOT_Z[1]), 1.0, label=frac(POST + PROUD) + " tenon")
    d.dim((rx + POST, FOOT_Z[0]), (rx + POST + FOOT_FLAT, FOOT_Z[0]), -1.2)
    d.dim((rx + POST + run + 0.6, FOOT_Z[0]), (rx + POST + run + 0.6, FOOT_TENON_Z[0]), 0.4, along="v")
    d.dim((rx + POST + run + 0.6, FOOT_TENON_Z[0]), (rx + POST + run + 0.6, FOOT_TENON_Z[1]), 0.4, along="v")
    notes = [
        "Rail %s long between the legs, %s overall with its tenons." % (frac(HB_SPAN), frac(HB_SPAN + 2 * (POST + PROUD))),
        "Through-tenons %s thick, centered on the rail; mortises %s from the legs' front faces." % (frac(FOOT_TENON_T), frac(ft_mort_y)),
        "The arch: a fair curve from %s in from each leg, %s high at the middle (%s from the" % (frac(FOOT_FLAT), frac(FOOT_ARCH), frac(HB_SPAN / 2)),
        "  shoulder). Bend a thin batten through the three points and trace it.",
        "Bed bolt from the front face, %s up, %s counterbore %s deep, brass cover;" % (frac(BOLT_Z[0]), frac(BOLT_COUNTERBORE[0]), frac(BOLT_COUNTERBORE[1])),
        "  stub mortise for the side rail on the back face, as on the head posts.",
        "Pegs %s square through the front face, centered, at %s and %s up." % (frac(PEG), frac(FOOT_TENON_Z[0] + PEG_IN), frac(FOOT_TENON_Z[1] - PEG_IN)),
    ]
    for i, n in enumerate(notes):
        d.text(0, -4.0 - i * 1.75, n, 11, "start", NOTE)
    d.heading(FOOT_LEG + CAP_RISE + 2.0)


def side_rail(ox, oy):
    k = 12.0
    d = Detail(ox, oy, k, "E. SIDE RAILS (2): ENDS",
               "%s x %s, %s between the posts and legs, %s overall with the stub tenons." % (frac(RAIL_T), frac(RAIL_Z[1] - RAIL_Z[0]), frac(L - 2 * POST), frac(L - 2 * POST + 2 * STUB[2])) +
               "\nThe inside face shown (the end at a post: both ends the same).")
    h = RAIL_Z[1] - RAIL_Z[0]
    run = 9.0
    d.line([(0, 0), (run, 0)])
    d.line([(0, h), (run, h)])
    d.line([(run, -0.4), (run, h + 0.4)], NOTE, 0.8, dash=True)
    d.line([(0, 0), (0, h)])
    sb = STUB[3] - RAIL_Z[0]
    d.rect(-STUB[2], sb, 0, sb + STUB[1])
    bz = BOLT_Z[0] - RAIL_Z[0]
    d.line([(0, bz), (BOLT_LEN - (POST - BOLT_COUNTERBORE[1]) + 0.5, bz)], INK, 0.8, dash=True)
    d.circle(BOLT_NUT[0], bz, BOLT_NUT[1] / 2, fill="#e9e3d6")
    ct = CLEAT_TOP - RAIL_Z[0]
    d.rect(0.0, ct - CLEAT, run, ct, fill="#efe6cf")
    d.text(run / 2 - 0.5, ct - CLEAT / 2 - 0.15, "cleat (glued and screwed)", 10, color=NOTE)
    d.dim((0, bz), (BOLT_NUT[0], bz), -1.5 - bz, along="h")
    d.dim((-STUB[2], sb + STUB[1]), (0, sb + STUB[1]), h - sb - STUB[1] + 0.6)
    d.dim((-STUB[2], 0), (-STUB[2], bz), -0.6)
    d.dim((-STUB[2] - 1.4, sb), (-STUB[2] - 1.4, sb + STUB[1]), -0.1, along="v")
    d.dim((run, ct - CLEAT), (run, ct), 0.6)
    d.dim((run, 0), (run, ct - CLEAT), 1.6)
    notes = [
        "Bolt hole %s, %s deep into the end grain, %s up, centered." % (frac(0.375), frac(BOLT_LEN - (POST - BOLT_COUNTERBORE[1]) + 0.5), frac(BOLT_Z[0] - RAIL_Z[0])),
        "Nut hole %s Forstner from the inside face, %s deep, %s from the end:" % (frac(BOLT_NUT[1]), frac(BOLT_NUT[2]), frac(BOLT_NUT[0])),
        "  check it against the bolt before drilling.",
        "Stub tenon %s thick, %s tall, %s long, centered." % (frac(STUB[0]), frac(STUB[1]), frac(STUB[2])),
        "Cleats run the rail's full length, above the nut hole; each slat screwed to them",
        "  with one #8 x 1 1/4\" at each end, and to the center rail with one.",
    ]
    for i, n in enumerate(notes):
        d.text(-STUB[2], -2.4 - i * 1.4, n, 11, "start", NOTE)
    d.heading(RAIL_Z[1] - RAIL_Z[0] + 2.0)


def main():
    head_post(70, 780)
    headboard_rails(720, 400)
    slats(1130, 400)
    foot(620, 900)
    side_rail(1230, 960)
    W_, H_ = 1800, 1100
    OUT.insert(0, '<rect width="100%" height="100%" fill="#fff"/>')
    OUT.insert(1, '<text x="40" y="44" font-family="%s" font-size="22" fill="%s">Queen bed frame: joinery</text>' % (FONT, INK))
    OUT.insert(2, '<text x="40" y="66" font-family="%s" font-size="12" fill="%s">Inches. Heights from the floor; '
                  'post and leg positions from their front faces (toward the foot). Details drawn to different scales: '
                  'work from the numbers. Overall plan and cut list: bed-frame-drawing.svg.</text>' % (FONT, NOTE))
    svg = ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d">%s</svg>\n' % (W_, H_, W_, H_, "".join(OUT)))
    out = os.path.join(HERE, "bed-frame-joinery.svg")
    open(out, "w").write(svg)
    print("DRAWING " + out)


if __name__ == "__main__":
    main()

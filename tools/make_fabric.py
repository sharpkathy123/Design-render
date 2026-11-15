"""Original textile patterns for renders, drawn with numpy (Design-render,
2026-11-11). Our own designs in the manner of Arts & Crafts prints, so they
can go in a public repository (a shop's or designer's print can't).

    python3 tools/make_fabric.py OUT_DIR [kind ...]

Kinds (each a seamless tile, unless it's a whole piece):
  pomegranate  large orange and rust pomegranates on scrolling stems with
               teal and ochre leaves, on deep blue (a Morris-era manner);
               one tile is an 18" repeat
  blockprint   an indigo hand-block print: small pale-blue flowers and
               sprigs in a half-drop, on indigo; one tile is an 8" repeat
  kilim        a flat-woven throw's stripes, across its width: rust and
               orange bands, a stepped-diamond band, cream and brown
               guards; the whole 50" length of the throw, one tile wide
Writes OUT_DIR/<kind>.png.
"""
import os
import sys

import numpy as np
from PIL import Image


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def wrap(d):
    return (d + 0.5) % 1.0 - 0.5


class Canvas:
    def __init__(self, w, h, ground):
        self.w, self.h = w, h
        self.X, self.Y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
        self.rgb = np.broadcast_to(hexrgb(ground), (h, w, 3)).copy()

    def paint(self, mask, color, a=1.0):
        c = hexrgb(color) if isinstance(color, str) else color
        if mask.dtype == bool:
            self.rgb[mask] = self.rgb[mask] * (1 - a) + c * a
        else:                                   # a soft mask, 0..1
            m = (np.clip(mask, 0, 1) * a)[..., None]
            self.rgb = self.rgb * (1 - m) + c * m

    def ell(self, cx, cy, a, b, ang=0.0, tile=True):
        """(x/a)^2 + (y/b)^2 about a center, turned by ang, wrapping."""
        dx, dy = self.X - cx, self.Y - cy
        if tile:
            dx, dy = wrap(dx), wrap(dy)
        ca, sa = np.cos(ang), np.sin(ang)
        xr, yr = dx * ca + dy * sa, -dx * sa + dy * ca
        return (xr / a) ** 2 + (yr / b) ** 2

    def leaf(self, cx, cy, length, width, ang, color, vein=None):
        """A pointed leaf (a lens) from its base at (cx, cy), along ang."""
        mx, my = cx + np.cos(ang) * length / 2, cy + np.sin(ang) * length / 2
        dx, dy = wrap(self.X - mx), wrap(self.Y - my)
        ca, sa = np.cos(ang), np.sin(ang)
        u, v = (dx * ca + dy * sa) / (length / 2), (-dx * sa + dy * ca) / (width / 2)
        m = np.abs(v) < np.clip(1 - np.abs(u) ** 2, 0, 1) ** 1.2
        m &= np.abs(u) < 1
        self.paint(m, color)
        if vein:
            self.paint(m & (np.abs(v) < 0.09) & (np.abs(u) < 0.8), vein)

    def stem(self, pts, width, color):
        """A smooth stem through points (tile coordinates), as discs along it."""
        pts = np.array(pts)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(2, int(np.hypot(*(b - a)) / (width * 0.4)))
            for t in np.linspace(0, 1, n):
                p = a + (b - a) * t
                self.paint(self.ell(p[0], p[1], width, width) < 1, color)

    def texture(self, amount=0.05, seed=1):
        """A little weave and dye variation, so the print isn't flat."""
        rng = np.random.default_rng(seed)
        n = rng.normal(0, 1, (self.h, self.w))
        weave = 0.5 + 0.5 * np.sin(np.arange(self.w) * np.pi / 1.5)[None, :] * np.sin(np.arange(self.h) * np.pi / 1.5)[:, None]
        self.rgb *= (1 + amount * (0.6 * n + 0.4 * (weave - 0.5)))[..., None]

    def save(self, path):
        Image.fromarray((np.clip(self.rgb, 0, 1) * 255).astype(np.uint8)).save(path)


def pomegranate(path):
    c = Canvas(1024, 1024, "#17264a")                  # deep blue
    ORANGE, RUST, OCHRE, TEAL, CREAM, DARK = "#d9792b", "#a8421f", "#d6a443", "#3f7f78", "#efd9a8", "#0f1a33"
    # two scrolling stems in a half-drop, each carrying a fruit and leaves
    for (ox, oy, flip) in ((0.0, 0.0, 1), (0.5, 0.5, -1)):
        sx = lambda t: ox + 0.08 + 0.06 * np.sin(t * 2 * np.pi)      # the stem's x at height t
        pts = [(sx(t), oy + t) for t in np.linspace(-0.05, 1.05, 12)]
        c.stem(pts, 0.008, OCHRE)
        # big acanthus-like leaves curling off the stem
        for k, (t, side) in enumerate(((0.12, 1), (0.32, -1), (0.62, 1), (0.84, -1))):
            bx, by = sx(t), oy + t
            ang = (-0.5 if side > 0 else np.pi + 0.5) + (0.3 * flip)
            c.leaf(bx, by, 0.24, 0.09, ang, TEAL if k % 2 else OCHRE, vein=DARK)
            c.leaf(bx, by, 0.14, 0.05, ang + 0.6 * side, ORANGE if k % 2 else TEAL)
        # the pomegranate: a round fruit with a crown, its open face showing seeds
        fx, fy = ox + 0.3, oy + 0.45
        c.paint(c.ell(fx, fy, 0.105, 0.115) < 1, RUST)
        c.paint(c.ell(fx, fy + 0.01, 0.085, 0.095) < 1, ORANGE)
        c.paint(c.ell(fx, fy + 0.025, 0.055, 0.06) < 1, CREAM)
        for i in range(14):                               # seeds
            a = i * 2.4
            r = 0.012 + 0.003 * i
            c.paint(c.ell(fx + r * np.cos(a), fy + 0.025 + r * np.sin(a), 0.008, 0.01) < 1, RUST)
        for dx in (-0.03, 0.0, 0.03):                     # the crown
            c.leaf(fx + dx, fy - 0.1, 0.05, 0.022, -np.pi / 2 + dx * 6, RUST)
        c.stem([(fx, fy - 0.1), (sx(0.4), oy + 0.4)], 0.006, OCHRE)
        # small buds and flowers filling the ground
        for (bx, by, col) in ((0.4, 0.15, ORANGE), (0.2, 0.8, OCHRE), (0.42, 0.72, TEAL)):
            x, y = ox + bx, oy + by
            c.paint(c.ell(x, y, 0.025, 0.025) < 1, col)
            c.paint(c.ell(x, y, 0.01, 0.01) < 1, CREAM)
    # fine dots in the ground, as a print's filler
    for i in range(60):
        rng = np.random.default_rng(i)
        x, y = rng.random(2)
        c.paint(c.ell(x, y, 0.004, 0.004) < 1, "#2c3f6e")
    c.texture(0.06, 2)
    c.save(path)


def blockprint(path):
    c = Canvas(512, 512, "#1d3a6b")                      # indigo
    PALE, MID, DEEP, WHITE = "#9fbbe0", "#5f86c0", "#1d3866", "#dce8f5"
    for (ox, oy) in ((0.25, 0.25), (0.75, 0.75), (0.25, 0.75), (0.75, 0.25)):   # flower sprigs, close set
        c.stem([(ox, oy + 0.2), (ox + 0.02, oy + 0.05), (ox, oy - 0.05)], 0.008, MID)
        for ang, col in ((-2.4, PALE), (-0.7, PALE), (2.5, MID), (0.6, MID)):
            c.leaf(ox + 0.01, oy + 0.08, 0.13, 0.05, ang, col, vein=DEEP)
        rr, = (np.hypot(wrap(c.X - ox), wrap(c.Y - oy + 0.06)),)
        th = np.arctan2(wrap(c.Y - oy + 0.06), wrap(c.X - ox))
        c.paint(rr < 0.075 * (0.65 + 0.35 * np.abs(np.cos(3 * th))), WHITE)
        c.paint(rr < 0.03, MID)
        c.paint(rr < 0.012, DEEP)
    for (ox, oy) in ((0.5, 0.5), (0.0, 0.0), (0.5, 0.0), (0.0, 0.5)):          # small rosettes between
        rr = np.hypot(wrap(c.X - ox), wrap(c.Y - oy))
        th = np.arctan2(wrap(c.Y - oy), wrap(c.X - ox))
        c.paint(rr < 0.045 * (0.6 + 0.4 * np.abs(np.cos(2.5 * th))), PALE)
        c.paint(rr < 0.015, DEEP)
        for k in range(4):
            a = k * np.pi / 2 + np.pi / 4
            c.leaf(ox + 0.05 * np.cos(a), oy + 0.05 * np.sin(a), 0.06, 0.022, a, MID)
    # block-print irregularity: the pale ink a little uneven
    rng = np.random.default_rng(3)
    blot = rng.normal(0, 1, (64, 64))
    blot = np.array(Image.fromarray(((blot - blot.min()) / np.ptp(blot) * 255).astype(np.uint8)).resize((512, 512), Image.BICUBIC)) / 255.0
    c.rgb *= (0.94 + 0.12 * blot)[..., None]
    c.texture(0.05, 4)
    c.save(path)


def kilim(path):
    """Bands across the width (the image's height runs along the throw's 50")."""
    w, h = 256, 1600
    c = Canvas(w, h, "#b4471f")                          # rust
    ORANGE, CREAM, BROWN, GOLD, NAVY = "#e07a2e", "#ead7ad", "#4a2716", "#d9a441", "#22304f"
    y = c.Y

    def band(y0, y1, col):
        c.paint((y >= y0) & (y < y1), col)

    # a symmetric plan from each end to the middle
    plan = [(0.00, 0.03, CREAM), (0.03, 0.045, BROWN), (0.06, 0.11, ORANGE), (0.11, 0.12, CREAM),
            (0.12, 0.13, BROWN), (0.17, 0.19, GOLD), (0.19, 0.2, BROWN), (0.24, 0.26, CREAM),
            (0.3, 0.33, ORANGE), (0.33, 0.34, BROWN)]
    for y0, y1, col in plan:
        band(y0, y1, col)
        band(1 - y1, 1 - y0, col)
    # a stepped-diamond band in the middle, and smaller ones near each end
    for (yc, hh, col, inner) in ((0.5, 0.1, BROWN, ORANGE), (0.215, 0.025, NAVY, GOLD), (0.785, 0.025, NAVY, GOLD)):
        band(yc - hh, yc + hh, CREAM if hh > 0.05 else ORANGE)
        reps = 3 if hh > 0.05 else 6
        u = (c.X * reps) % 1.0 - 0.5
        v = (y - yc) / hh
        step = np.floor(np.abs(u) * 12) / 12 * 2 + np.floor(np.abs(v) * 6) / 6
        c.paint((step < 0.95) & (np.abs(v) < 1), col)
        c.paint((step < 0.55) & (np.abs(v) < 1), inner)
        c.paint((step < 0.2) & (np.abs(v) < 1), CREAM)
    # abrash: a flat-weave's dye changes from row to row
    rng = np.random.default_rng(7)
    rows = np.repeat(rng.normal(0, 1, h // 8), 8)[:h]
    c.rgb *= (1 + 0.035 * rows)[:, None, None]
    c.texture(0.06, 8)
    c.save(path)


def _sett(stripes, n):
    """A tartan sett as a row of n colors: stripes [(color, threads)], then
    mirrored, as a symmetric sett is woven."""
    row = []
    for col, k in stripes + stripes[::-1]:
        row += [hexrgb(col)] * k
    idx = (np.arange(n) * len(row) / n).astype(int)
    return np.array(row)[idx]


def plaid(path):
    """A wool blanket's plaid, our own: moss green and deep brown blocks
    with a rust and a cream overcheck, a 2/2 twill (half the threads warp,
    half weft). One tile is an 8" repeat."""
    n = 512
    sett = _sett([("#3d4a2a", 18), ("#2b2118", 6), ("#3d4a2a", 4), ("#2b2118", 14), ("#a4482a", 3),
                  ("#2b2118", 14), ("#3d4a2a", 22), ("#d8c9a0", 2)], n)
    warp = np.broadcast_to(sett[None, :, :], (n, n, 3))
    weft = np.broadcast_to(sett[:, None, :], (n, n, 3))
    yy, xx = np.mgrid[0:n, 0:n]
    twill = ((xx + yy) // 2) % 2 == 0
    rgb = np.where(twill[..., None], warp, weft) * 0.5 + (warp + weft) * 0.25
    c = Canvas(n, n, "#000000")
    c.rgb = rgb.copy()
    c.texture(0.05, 21)
    c.save(path)


def check(path):
    """A woven check for a small piece (the headboard's cover), our own:
    ochre and sage in a gingham weave, its crossings darker, on cream.
    One tile is a 4" repeat."""
    n = 256
    a = ((np.arange(n) // (n // 4)) % 2 == 0).astype(float)           # two bands each way per tile
    X, Y = np.meshgrid(a, a)
    c = Canvas(n, n, "#e8dcc0")
    c.paint(X * (1 - Y) > 0.5, "#b88a3c")
    c.paint(Y * (1 - X) > 0.5, "#8c9a6a")
    c.paint(X * Y > 0.5, "#5f5a32")
    c.texture(0.06, 22)
    c.save(path)


def quilt(path):
    """A pieced quilt, our own: ochre and sage squares with pale stitched
    seams. One tile is an 18" repeat, 3 by 3 squares."""
    n = 540
    c = Canvas(n, n, "#8a6a2a")
    sq = (np.floor(c.X * 3) + np.floor(c.Y * 3)) % 2 == 1
    c.paint(sq, "#4f5e3a")
    seam = (np.abs(((c.X * 3) % 1.0) - 0.5) > 0.49) | (np.abs(((c.Y * 3) % 1.0) - 0.5) > 0.49)
    c.paint(seam, "#a89466")
    c.texture(0.05, 23)
    c.save(path)


def percale(path):
    """Plain white cotton percale for sheets and pillowcases (client,
    2026-11-14: plain white everywhere, no band): white with only its
    weave. One tile is a 2" repeat."""
    c = Canvas(128, 128, "#f3f1ec")
    c.texture(0.025, 24)
    c.save(path)


def linen_blue(path):
    """A plain linen in light blue, the Strawberry Thief's leaf blue lightened
    (#9db0cc: its hue and saturation, picked from the print, client
    2026-11-15), for the headboard's cover beside the Morris coverlet: only
    its weave and a few slubs. One tile is a 3" repeat."""
    c = Canvas(192, 192, "#9db0cc")
    rng = np.random.default_rng(25)
    slub = np.repeat(rng.normal(0, 1, 192 // 3), 3)[:192]
    c.rgb *= (1 + 0.03 * slub)[:, None, None]
    c.texture(0.04, 26)
    c.save(path)


def star_quilt(path):
    """A pieced Ohio Star quilt in the Strawberry Thief's colors (client,
    2026-11-15: the headboard in a quilt pattern that goes with the
    coverlet), our own: 9" blocks of a 3 x 3 grid, the star's points
    quarter-square triangles, in two colorways alternating like a
    checkerboard (navy points on biscuit, a red center; light blue points on
    navy, a sage center), the leaf blue between each star's points, every patch's
    dye a little different, the seams stitched. One tile is 2 x 2 blocks,
    an 18" repeat."""
    NAVY, LEAF, LIGHT, SAGE, BISCUIT, BERRY = "#262b4a", "#5f6f9a", "#9db0cc", "#6f7f4a", "#d9c9a0", "#a8483a"
    ways = [dict(ground=BISCUIT, point=NAVY, point2=LEAF, center=BERRY, corner=BISCUIT),
            dict(ground=NAVY, point=LIGHT, point2=LEAF, center=SAGE, corner=NAVY)]
    n = 720
    c = Canvas(n, n, BISCUIT)
    rng = np.random.default_rng(27)
    bx, by = np.floor(c.X * 2).astype(int), np.floor(c.Y * 2).astype(int)        # which block
    u, v = (c.X * 2) % 1.0, (c.Y * 2) % 1.0                                       # within it, 0..1
    gx, gy = np.floor(u * 3).astype(int), np.floor(v * 3).astype(int)           # its 3 x 3 grid
    fu, fv = (u * 3) % 1.0, (v * 3) % 1.0                                         # within a unit
    for b in range(4):
        i, j = b % 2, b // 2
        w = ways[(i + j) % 2]
        blk = (bx == i) & (by == j)
        c.paint(blk, w["ground"])
        c.paint(blk & (gx == 1) & (gy == 1), w["center"])
        c.paint(blk & (gx != 1) & (gy != 1), w["corner"])
        # the side units: four triangles meeting in the middle; the two pointing in toward the
        # center are the star's points, the outer two the ground
        side = blk & ((gx == 1) ^ (gy == 1))
        du, dv = fu - 0.5, fv - 0.5
        toward = np.where(gx == 1, np.where(gy == 0, dv > np.abs(du), -dv > np.abs(du)),
                          np.where(gx == 0, du > np.abs(dv), -du > np.abs(dv)))
        across = np.abs(du) > np.abs(dv)
        across = np.where(gx == 1, across, ~across)
        c.paint(side & across, w["point"])
        c.paint(side & toward & ~across, w["point2"])
    # each patch's dye a little different (the patches: units, split along the triangles' diagonals)
    patch = (bx * 2 + by) * 100 + gx * 10 + gy
    for k in np.unique(patch):
        c.rgb[patch == k] *= 1 + 0.035 * rng.normal()
    # the seams, pressed and stitched: a pale line round every unit and down the triangles' diagonals
    d1, d2 = np.abs(fu - fv), np.abs(fu + fv - 1)
    seam = (np.minimum(fu, 1 - fu) < 0.012) | (np.minimum(fv, 1 - fv) < 0.012)
    seam |= ((gx == 1) ^ (gy == 1)) & ((d1 < 0.012) | (d2 < 0.012))
    c.rgb[seam] = c.rgb[seam] * 0.7 + hexrgb("#e8dcc0") * 0.3
    c.texture(0.05, 28)
    c.save(path)


KINDS = {"star-quilt": star_quilt, "linen-blue": linen_blue, "pomegranate": pomegranate, "blockprint": blockprint, "kilim": kilim, "plaid": plaid, "check": check,
         "quilt": quilt, "percale": percale}


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for k in sys.argv[2:] or KINDS:
        KINDS[k](os.path.join(out, k + ".png"))
        print("FABRIC " + os.path.join(out, k + ".png"))


if __name__ == "__main__":
    main()

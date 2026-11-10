"""An SVG that records the same calls as Pillow's ImageDraw, so a drawing made
with Pillow can be written as a sharp, zoomable SVG as well (client asked,
2026-10-17: plans anyone can zoom into).

    from svgdraw import SvgDraw, Tee
    svg = SvgDraw(size)
    d = Tee(ImageDraw.Draw(im), svg)     # draw once, into both
    ...
    svg.save("plan.svg")

Covers what the plan scripts use: rectangle, line, ellipse, arc, text and
multiline_text, with Pillow's anchors. The font (a TrueType file given to
ImageFont.truetype) is embedded, so the SVG looks the same anywhere, even
shown as an <img>.
"""
import base64
import os
import re
import html
import math


def _color(c):
    if c is None:
        return "none"
    if isinstance(c, tuple):
        return "#%02x%02x%02x" % c[:3]
    return c


SERIF = "Old Standard TT, Georgia, Times New Roman, serif"
SANS = "Source Sans 3, Helvetica, Arial, sans-serif"
MONO = "DejaVu Sans Mono, Menlo, Consolas, monospace"


def stack(path):
    """The font family list for a TrueType file's look."""
    n = os.path.basename(path or "").lower()
    if "mono" in n:
        return MONO
    if any(k in n for k in ("sans", "helvet", "arial", "inter", "roboto", "dejavusans")):
        return SANS
    return SERIF


def unembed(src):
    """An SVG written by an older svgdraw (embedded fonts named f0, f1...)
    rewritten to use font family lists, each embedded font's look kept by
    reading its name from the font data."""
    faces = dict(re.findall(r"@font-face\{font-family:(f\d+);src:url\(data:font/ttf;base64,([A-Za-z0-9+/=]+)\)\}", src))
    for name, b64 in faces.items():
        data = base64.b64decode(b64)
        low = data.replace(b"\x00", b"").lower()
        fam = MONO if b"mono" in low else SANS if (b"sans" in low or b"helvetica" in low) else SERIF
        src = src.replace('font-family="%s"' % name, 'font-family="%s"' % fam)
    src = re.sub(r"@font-face\{[^}]*\}", "", src)
    if not src.lstrip().startswith("<?xml"):
        src = '<?xml version="1.0" encoding="UTF-8"?>\n' + src
    return src


class SvgDraw:
    def __init__(self, size, background="white"):
        self.w, self.h = size
        self.parts = []
        self.fonts = {}
        if background:
            self.parts.append('<rect width="100%%" height="100%%" fill="%s"/>' % _color(background))

    def _font(self, font):
        """A font family list, not an embedded font (2026-10-29: the client saw
        a plan with no text at all; Safari and the Claude app can draw an SVG
        image's embedded-font text invisible while the font loads, and an image
        is never redrawn). The font's own name first, for anyone who has it."""
        path = getattr(font, "path", None)
        return stack(path), getattr(font, "size", 11)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        (x0, y0), (x1, y1) = _pts(xy)
        self.parts.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"%s/>'
                          % (x0, y0, x1 - x0, y1 - y0, _color(fill), _stroke(outline, width)))

    def line(self, xy, fill=None, width=1):
        pts = _pts(xy)
        self.parts.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"/>'
                          % (" ".join("%.2f,%.2f" % p for p in pts), _color(fill), width))

    def polygon(self, xy, fill=None, outline=None, width=1):
        pts = _pts(xy)
        self.parts.append('<polygon points="%s" fill="%s"%s/>'
                          % (" ".join("%.2f,%.2f" % p for p in pts), _color(fill), _stroke(outline, width)))

    def ellipse(self, xy, fill=None, outline=None, width=1):
        (x0, y0), (x1, y1) = _pts(xy)
        self.parts.append('<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" fill="%s"%s/>'
                          % ((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, _color(fill),
                             _stroke(outline, width)))

    def arc(self, xy, start, end, fill=None, width=1):
        # Pillow's angles: degrees clockwise from 3 o'clock, y down (as SVG's)
        (x0, y0), (x1, y1) = _pts(xy)
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        a, b = math.radians(start), math.radians(end)
        large = 1 if (end - start) % 360 > 180 else 0
        self.parts.append('<path d="M%.2f,%.2f A%.2f,%.2f 0 %d 1 %.2f,%.2f" fill="none" stroke="%s" stroke-width="%s"/>'
                          % (cx + rx * math.cos(a), cy + ry * math.sin(a), rx, ry, large,
                             cx + rx * math.cos(b), cy + ry * math.sin(b), _color(fill), width))

    def text(self, xy, s, font=None, fill="black", anchor="la", spacing=4, **kw):
        self.multiline_text(xy, s, font=font, fill=fill, anchor=anchor, spacing=spacing)

    def multiline_text(self, xy, s, font=None, fill="black", anchor="la", spacing=4, **kw):
        fam, size = self._font(font)
        anchor = anchor or "la"
        lines = str(s).split("\n")
        lh = size * 1.17 + spacing
        x, y = xy
        ta = {"l": "start", "m": "middle", "r": "end"}[anchor[0]]
        v = anchor[1]
        # the block's first baseline, from Pillow's vertical anchor
        asc = size * 0.92
        if v in "at":
            y0 = y + asc
        elif v == "m":
            y0 = y - (len(lines) - 1) * lh / 2 + size * 0.33
        elif v == "d":
            y0 = y - (len(lines) - 1) * lh - size * 0.25
        else:                              # "s": the baseline
            y0 = y
        for i, ln in enumerate(lines):
            self.parts.append('<text x="%.2f" y="%.2f" font-family="%s" font-size="%s" fill="%s" text-anchor="%s">%s</text>'
                              % (x, y0 + i * lh, fam, size, _color(fill), ta, html.escape(ln)))

    def svg(self):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
                '<style>text{white-space:pre}</style>%s</svg>\n'
                % (self.w, self.h, self.w, self.h, "".join(self.parts)))

    def save(self, path):
        open(path, "w").write(self.svg())


class Tee:
    """Sends every drawing call to several drawers (a Pillow ImageDraw and an SvgDraw)."""

    def __init__(self, *drawers):
        self.drawers = drawers

    def __getattr__(self, name):
        def call(*a, **kw):
            for d in self.drawers:
                getattr(d, name)(*a, **kw)
        return call


def _pts(xy):
    xy = list(xy)
    if xy and not isinstance(xy[0], (tuple, list)):
        xy = list(zip(xy[0::2], xy[1::2]))
    return [tuple(p) for p in xy]


def _stroke(c, width):
    return ' stroke="%s" stroke-width="%s"' % (_color(c), width) if c else ""

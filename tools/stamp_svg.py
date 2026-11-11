"""Every drawing we share shows the date it was updated (client, 2026-10-29:
"All of our documents that we share should show the date the document was
updated"; the PDFs had it since 2026-10-26, the SVG drawings didn't).

Adds a strip along the bottom of each SVG drawing with "Updated <date>" at
its right, drawn last so nothing covers it. The date is the day the
drawing's content last changed, not the day it was rebuilt: each drawing's
content (without the strip) is fingerprinted in site/svg_dates.json, and
the date moves only when the fingerprint does (a drawing first seen takes
its last commit's date, if it's unchanged since). Run after the drawings are made; idempotent.

    python3 tools/stamp_svg.py            # stamp every drawing
    python3 tools/stamp_svg.py --check    # list drawings with no date (check_docs.py runs this)
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATES = os.path.join(ROOT, "designs", "svg_dates.json")
STRIP = 22.0                      # the strip's height, in pixels
FONT = "Helvetica, Arial, sans-serif"
BLOCK = re.compile(r'<g id="updated">.*?</g>', re.S)


def drawings():
    """Every SVG drawing under designs/ (copied from Sketchup-tools,
    2026-11-10)."""
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "designs/*.svg"], cwd=ROOT,
                           capture_output=True, text=True).stdout.split()
    return sorted(set(files))


def strip(src):
    """The drawing without its date strip, its size as it was."""
    if 'id="updated"' not in src:
        return src
    src = BLOCK.sub("", src)
    m = re.search(r"<svg\b[^>]*>", src)
    root = m.group(0)
    h0 = re.search(r'data-h0="([^"]*)"', root)
    vh0 = re.search(r'data-vh0="([^"]*)"', root)
    new = root
    if h0:
        new = re.sub(r'\sheight="[^"]*"', ' height="%s"' % h0.group(1), new, count=1)
    if vh0:
        new = re.sub(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) [-\d.]+"',
                     lambda v: 'viewBox="%s %s %s %s"' % (v.group(1), v.group(2), v.group(3), vh0.group(1)), new, count=1)
    new = re.sub(r'\sdata-(h0|vh0)="[^"]*"', "", new)
    return src.replace(root, new, 1)


def num(s):
    return float(re.match(r"[-\d.]+", s).group(0))


def stamp(src, date):
    """src (unstamped) with the strip and "Updated <date>" added."""
    m = re.search(r"<svg\b[^>]*>", src)
    root = m.group(0)
    W = num(re.search(r'\swidth="([^"]*)"', root).group(1))
    H = num(re.search(r'\sheight="([^"]*)"', root).group(1))
    vb = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', root)
    vx, vy, vw, vh = (float(v) for v in vb.groups()) if vb else (0.0, 0.0, W, H)
    k = vh / H                                    # (user units per pixel)
    ext = STRIP * k
    new = re.sub(r'\sheight="[^"]*"', ' height="%g"' % (H + STRIP), root, count=1)
    new = new[:-1] + ' data-h0="%g"' % H + (' data-vh0="%g"' % vh if vb else "") + ">"
    if vb:
        new = new.replace(vb.group(0), 'viewBox="%g %g %g %g"' % (vx, vy, vw, vh + ext), 1)
    block = ('<g id="updated"><rect x="%g" y="%g" width="%g" height="%g" fill="#fff"/>'
             '<text x="%g" y="%g" font-family="%s" font-size="%g" fill="#666" text-anchor="end">Updated %s</text></g>'
             % (vx, vy + vh, vw, ext, vx + vw - 10 * k, vy + vh + ext - 7 * k, FONT, 12 * k, date))
    src = src.replace(root, new, 1)
    i = src.rfind("</svg>")
    return src[:i] + block + src[i:]


def human(d):
    return "%s %d, %d" % (d.strftime("%B"), d.day, d.year)


def committed_date(rel, body):
    """The file's last commit date, if its content then was this body."""
    old = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT, capture_output=True, text=True)
    if old.returncode or strip(old.stdout).strip() != body.strip():
        return None
    ts = subprocess.run(["git", "log", "-1", "--format=%ct", "--", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return datetime.date.fromtimestamp(int(ts)) if ts else None


def run(check=False):
    dates = json.load(open(DATES)) if os.path.exists(DATES) else {}
    missing, changed = [], 0
    for rel in drawings():
        path = os.path.join(ROOT, rel)
        src = open(path, encoding="utf-8").read()
        if check:
            if 'id="updated"' not in src:
                missing.append(rel)
            continue
        body = strip(src)
        fp = hashlib.sha1(body.encode()).hexdigest()
        rec = dates.get(rel)
        if not rec or rec["hash"] != fp:
            d = (rec is None and committed_date(rel, body)) or datetime.date.today()
            rec = dates[rel] = {"hash": fp, "date": d.isoformat()}
        out = stamp(body, human(datetime.date.fromisoformat(rec["date"])))
        if out != src:
            open(path, "w", encoding="utf-8").write(out)
            changed += 1
    if not check:
        json.dump(dates, open(DATES, "w"), indent=1, sort_keys=True)
        print("stamp_svg: %d drawings, %d restamped" % (len(drawings()), changed))
    return missing


if __name__ == "__main__":
    if "--check" in sys.argv:
        miss = run(check=True)
        for m in miss:
            print("PROBLEM %s: no date on the drawing (python3 tools/stamp_svg.py)" % m)
        sys.exit(1 if miss else 0)
    run()

"""Small labels on a render, nudged apart: tools/blender/kitchen.py's --open
pictures say what's in each cabinet (client, 2026-10-29).

    python3 tools/label_render.py picture.jpg labels.json

labels.json is [[text, u, v], ...], u and v the place in the picture from
its top left, 0 to 1.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def annotate(path, labels):
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    f = ImageFont.truetype(os.path.join(ROOT, "tools/fonts/OldStandard-Regular.ttf"), max(12, W // 62))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    placed = []
    for text, u, v in sorted(labels, key=lambda t: t[2]):
        x, y = u * W, v * H
        tw, th = d.textlength(text, font=f), f.size + 6
        bx = min(max(4, x - tw / 2 - 5), W - tw - 14)
        by = y - th / 2
        for _ in range(40):
            if all(abs(by - py) > th + 1 or bx + tw + 10 < px or px + pw < bx for px, py, pw in placed):
                break
            by += th * 0.6
        placed.append((bx, by, tw + 10))
        d.line([x, y, bx + tw / 2 + 5, by + th / 2], fill=(176, 48, 42, 200), width=1)
        d.rounded_rectangle([bx, by, bx + tw + 10, by + th], radius=4, fill=(255, 255, 255, 220),
                            outline=(90, 60, 40, 255))
        d.text((bx + 5, by + 3), text, font=f, fill=(40, 30, 25, 255))
        d.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill=(176, 48, 42, 255))
    Image.alpha_composite(im, ov).convert("RGB").save(path, quality=90)


if __name__ == "__main__":
    annotate(sys.argv[1], json.load(open(sys.argv[2])))

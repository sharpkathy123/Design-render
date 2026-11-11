"""Wrap an SVG drawing in a small web page, so the Claude app shows the
drawing (it shows an .svg file as its code: client, 2026-10-26) and it can
still be pinched and zoomed, sharp at any size. The SVG stays the drawing;
this page is only for looking at it in the chat.

Usage: python3 tools/svg_view.py <drawing.svg> [out.html]
(default out: the same name with .html, in the scratchpad folder given by
$SCRATCH if set, else beside the drawing)
"""
import html
import os
import re
import sys

src = sys.argv[1]
svg = open(src).read()
svg = re.sub(r"^<\?xml[^>]*>\s*", "", svg)
# (fill the page's width, keeping the drawing's proportions)
svg = re.sub(r'<svg([^>]*?) width="[^"]*" height="[^"]*"', r'<svg\1', svg, count=1)
name = os.path.splitext(os.path.basename(src))[0]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.environ.get("SCRATCH") or os.path.dirname(src), name + ".html")
page = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=10, user-scalable=yes">
<title>%s</title>
<style>body{margin:0;padding:12px;background:#fff} svg{display:block;width:100%%;height:auto}</style>
</head><body>
%s
</body></html>
""" % (html.escape(name), svg)
open(out, "w").write(page)
print(out)

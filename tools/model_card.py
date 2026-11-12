"""A design's 3D model, described for the repos that place it in their rooms
(Sketchup-tools' notes, 2026-11-12): from designs/<name>/model/exports.json
(written by tools/blender/deliver.py: every size measured from the saved
file, never typed), model/CHANGELOG.md and share.yaml's `model:` section,
writes

    designs/<name>/model/README.md      what's in each file, its size, placing it, SketchUp, rights
    designs/<name>/model/VERSION        the version, the change, every file's sha256
    designs/<name>/model/library.yaml   ready-to-paste records for Sketchup-tools' library/models/models.yaml
    designs/<name>/<name>-footprint.svg the top view to scale: the frame solid, the bedding's outline dashed

    python3 tools/model_card.py <name>      (deliver.export runs it after every export)
"""
import json
import math
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
REPO = "https://github.com/sharpkathy123/Design-render"
INK, DIM, SOFT = "#2a2724", "#8a3b12", "#555555"
DASHES = ["#2f5d8a", "#6b7f2a", "#8a2f6b"]


def frac(x, den=16):
    """Inches to the nearest 1/16, as a shop drawing writes it: 29 3/4"."""
    n = int(round(abs(x) * den))
    whole, rest = divmod(n, den)
    g = math.gcd(rest, den) if rest else den
    s = ("%d" % whole if whole or not rest else "") + ((" " if whole else "") + "%d/%d" % (rest // g, den // g) if rest else "")
    return ("-" if x < 0 else "") + s + '"'


def size3(s):
    return "%s x %s x %s" % tuple(frac(c) for c in s)


def load(name):
    d = os.path.join(ROOT, "designs", name)
    share = yaml.safe_load(open(os.path.join(d, "share.yaml")))
    cfg = share.get("model") or {}
    recs = json.load(open(os.path.join(d, "model", "exports.json")))
    order = [s for s in cfg.get("versions", {}) if s in recs] + sorted(s for s in recs if s not in cfg.get("versions", {}))
    return d, share, cfg, recs, order


def write(name):
    d, share, cfg, recs, order = load(name)
    md = os.path.join(d, "model")
    vers = {recs[s]["version"] for s in order}
    version = max(vers)
    change = next(recs[s]["change"] for s in order if recs[s]["version"] == version)
    prefix = recs[order[0]]["prefix"]
    if len(vers) > 1:
        print("model_card: WARNING %s's files are of different versions (%s): re-export them all"
              % (name, ", ".join(sorted(vers))), flush=True)

    # VERSION
    v = ["version: %s" % version, "change: %s" % change, "design: %s/tree/main/deliverables/%s" % (REPO, name), "sha256:"]
    for s in order:
        for f, h in sorted(recs[s]["sha256"].items()):
            v.append("  %s: %s" % (f, h))
    open(os.path.join(md, "VERSION"), "w").write("\n".join(v) + "\n")

    # library records, ready to paste
    lib = {}
    for s in order:
        r, c = recs[s], cfg.get("versions", {}).get(s, {})
        lib[s] = dict(use=c.get("use", share["title"]), name=c.get("name", share["title"]),
                      size_in=[round(x, 1) for x in r["size_in"]],
                      source="%s/tree/main/deliverables/%s" % (REPO, name),
                      version="Design-render %s (model/VERSION and CHANGELOG.md in the source)" % r["version"],
                      license=cfg.get("license", "our own design"),
                      file="library/models/%s/%s" % (s, r["file"]),
                      facing=cfg.get("rot_rule", "rot=0: its back to the room's +y"))
    hdr = ("# Ready-made records for Sketchup-tools' library/models/models.yaml (written by tools/model_card.py\n"
           "# from the exported files: paste them in, copy each .blend to the record's file, and the sizes,\n"
           "# version and facing are already right).\n")
    open(os.path.join(md, "library.yaml"), "w").write(hdr + yaml.safe_dump(lib, sort_keys=False, width=110))

    footprint(name, d, share, recs, order)
    open(os.path.join(md, "README.md"), "w").write(readme(name, share, cfg, recs, order, version, change, prefix, lib))
    print("MODEL CARD %s: %s (%s)" % (name, version, ", ".join(order)), flush=True)


def readme(name, share, cfg, recs, order, version, change, prefix, lib):
    L = ["<!-- Written by tools/model_card.py from exports.json, CHANGELOG.md and share.yaml: edit those. -->",
         "# %s as a 3D model, for rendering rooms\n" % share["title"],
         "**Version %s:** %s ([VERSION](VERSION) has every file's sha256; [CHANGELOG](CHANGELOG.md)). "
         "Every object in the files carries it too, as `o[\"design_render_version\"]`.\n" % (version, change),
         cfg.get("intro", "").strip() + "\n" if cfg.get("intro") else "",
         "## The files\n",
         "| Version | Blender 4.5 | glTF (meters) | SketchUp (inches) | Size over everything, W x D x H | Triangles (viewport / render) |",
         "|---|---|---|---|---|---|"]
    for s in order:
        r = recs[s]
        L.append("| **%s** | [%s](%s) | [%s.glb](%s.glb) | [sketchup/%s.dae](sketchup/%s.dae) | %s | %s / %s |" % (
            cfg.get("versions", {}).get(s, {}).get("name", s), r["file"], r["file"], s, s, s, s,
            size3(r["size_in"]), "{:,}".format(r["triangles"]), "{:,}".format(r["triangles_render"])))
    L.append("")
    for s in order:
        r, c = recs[s], cfg.get("versions", {}).get(s, {})
        L.append("- **%s**: %s Collections: %s." % (r["file"], (c.get("about") or r.get("about") or "").strip(),
                                                 "; ".join("`%s` (%d)" % (k, len(v)) for k, v in r["collections"].items())))
    r0 = recs[order[0]]
    L += ["", "The frame alone is %s (W x D x H), the same in every file. Sizes are measured from the saved files by "
          "the export's check, not typed." % size3(r0["frame_size_in"]), "",
          "## What's in them\n",
          "- Only meshes, and one empty: every object, mesh, material and image is named `%s ...`, so appending them "
          "into a room that has its own `oak` or `brass` neither merges them nor makes `.001` copies. Materials: %s." % (
              prefix, ", ".join("`%s`" % m for m in sorted({m for s in order for m in recs[s]["materials"]}))),
          "- Real size in Blender meters (the scene's display unit set to inches). The floor is at z = 0 and the "
          "frame's footprint is centered on the origin.",
          "- %s" % cfg.get("facing", "Its front faces -y, its back +y."),
          "- An empty, `%s`, at the middle of the front on the floor, its arrow pointing -y (out of the front); its "
          "`depth_in` property is how far behind it the back is. Place by the front or by the back without measuring." % r0["front"],
          "- Every transform applied, no parents: each mesh's matrix is the identity. (Blender doesn't save "
          "`matrix_world`: an object appended without `view_layer.update()` reads as the identity, so an object "
          "with a transform of its own lands in the wrong place; these can't.) Modifiers applied, except any "
          "smoothing (Subdivision), left at 0 in the viewport and on in renders; the triangle counts above are both "
          "ways. The empty is the one object with a transform: read it after an update.",
          "- Every image packed into the .blend.",
          "- Checked on every export (`tools/blender/check_export.py`): a fresh Blender appends every object into an "
          "empty scene without `view_layer.update()`, and the size, floor, centering, facing, names, version tags, "
          "packing and collections are asserted.", "",
          "## Placing it\n",
          "In Blender: File > Append, the file, `Object`, and select every `%s ...` object (or `Collection`, and the "
          "collections you want).\n" % prefix,
          "In a script, append the collections you want and move their objects together; the footprint is centered "
          "on (x, y), turn is degrees about z, skip names collections to leave out (a choice of bedding), and the "
          "last lines check the facing:\n",
          "```python",
          "import bpy, math",
          "from mathutils import Matrix, Vector",
          "",
          "def place(path, x, y, turn=0.0, skip=()):",
          "    with bpy.data.libraries.load(path, link=False) as (src, dst):",
          "        dst.collections = [c for c in src.collections if c not in skip]",
          "    parts = [o for c in dst.collections for o in c.objects]",
          "    for o in parts:",
          "        bpy.context.scene.collection.objects.link(o)",
          "    bpy.context.view_layer.update()",
          "    m = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(turn), 4, \"Z\")",
          "    for o in parts:",
          "        o.matrix_world = m @ o.matrix_world",
          "    bpy.context.view_layer.update()"]
    if r0.get("tall_in"):
        L += ["    # the facing: everything above %s\" (the back) is behind the turned front" % r0["tall_in"],
              "    back = Vector((-math.sin(math.radians(turn)), math.cos(math.radians(turn)), 0))",
              "    tall = [o.matrix_world @ v.co for o in parts if o.type == \"MESH\" for v in o.data.vertices",
              "            if (o.matrix_world @ v.co).z > %s * 0.0254]" % r0["tall_in"],
              "    assert all((p - Vector((x, y, 0))).dot(back) > 0 for p in tall), \"facing the wrong way\""]
    L += ["    return parts", "```", "",
          "Appending every object instead (`dst.objects = list(src.objects)`, as Sketchup-tools' `assets.place()` "
          "does) brings in the whole file: each file holds one choice of bedding, so that's always one bed.\n",
          "## In SketchUp\n",
          "File > Import, COLLADA (.dae), `sketchup/<file>.dae`: it's in inches, Z up, the same facing; keep the "
          "images beside it. Its materials are plain: each one's color, or its fabric's image, without the .blend's "
          "wood grain, sheen or wool relief. The .glb is the same in glTF (meters, as glTF always is).\n",
          "## In Sketchup-tools\n",
          "Copy the .blend into `library/models/<id>/`, and paste the record from [library.yaml](library.yaml) into "
          "`library/models/models.yaml` (its size, version and facing come from the file). Then",
          "`assets.place(\"%s\", (x, y, 0), rot=..., objs=OBJS)` at its real size: give no width. %s.\n" % (
              order[0], cfg.get("rot_rule", "")),
          "```yaml", yaml.safe_dump({order[0]: lib[order[0]]}, sort_keys=False, width=110).rstrip(), "```", ""]
    tex = cfg.get("textures") or {}
    imgs = sorted({i for s in order for i in recs[s]["images"]})
    if imgs:
        L += ["## Textures and their rights\n", "| Image (packed) | Source and rights |", "|---|---|"]
        for i in imgs:
            src = i[len(prefix) + 1:] if i.startswith(prefix + " ") else i
            if src not in tex:
                sys.exit("model_card: %s's image %s has no source in share.yaml's model: textures:" % (name, src))
            L.append("| `%s` | %s |" % (i, tex[src].strip()))
        L.append("")
    L += ["## Footprint\n",
          "[%s-footprint.svg](../%s-footprint.svg): the top view to scale, the frame solid and each version's "
          "bedding outline dashed, for a room's plan.\n" % (name, name),
          "## Making them again\n", "```", cfg.get("command", "python3.11 designs/%s/model.py --export-all" % name), "```",
          "Add a line to [CHANGELOG.md](CHANGELOG.md) first: its newest line is the version.\n"]
    return "\n".join(x for x in L if x is not None)


def footprint(name, d, share, recs, order):
    """The top view to scale: the frame's parts (drawn lowest first, so the
    top ones show) solid, each version's bedding outline dashed, the sizes."""
    from svgdraw import SvgDraw
    with_fp = [s for s in order if recs[s].get("footprint")]
    if not with_fp:
        return
    fp0 = recs[with_fp[0]]["footprint"]
    rects = fp0["frame"]
    xs = [v for r in rects for v in (r[0], r[2])] + [p[0] for s in with_fp for p in recs[s]["footprint"]["overhang"]]
    ys = [v for r in rects for v in (r[1], r[3])] + [p[1] for s in with_fp for p in recs[s]["footprint"]["overhang"]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    K = min(9.0, 640.0 / (y1 - y0), 640.0 / (x1 - x0))
    M = 110.0
    W = (x1 - x0) * K + 2 * M + 330
    H = (y1 - y0) * K + 2 * M + 80
    svg = SvgDraw((int(W), int(H)))
    F = lambda s: type("Font", (), {"path": "sans.ttf", "size": s})   # noqa: E731

    def P(x, y):                        # +y (the back) up the sheet
        return M + (x - x0) * K, M + 60 + (y1 - y) * K
    for r in rects:
        (a, b), (c, e) = P(r[0], r[3]), P(r[2], r[1])
        svg.rectangle([(a, b), (c, e)], fill="#ffffff", outline=INK, width=1.0)
    for i, s in enumerate(with_fp):
        hull = recs[s]["footprint"]["overhang"]
        if len(hull) >= 3:
            col = DASHES[i % len(DASHES)]
            svg.parts.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="7 4"/>'
                             % (" ".join("%.2f,%.2f" % P(*p) for p in hull), col))
    fl, fh = recs[with_fp[0]]["frame_lo_in"], recs[with_fp[0]]["frame_hi_in"]

    def dim_h(xa, xb, y, label, col=DIM):
        (pa, py), (pb, _) = P(xa, y), P(xb, y)
        svg.line([(pa, py), (pb, py)], fill=col, width=0.9)
        for x in (pa, pb):
            svg.line([(x, py - 8), (x, py + 8)], fill=col, width=0.7)
            svg.line([(x - 4, py + 4), (x + 4, py - 4)], fill=col, width=1.2)
        svg.text(((pa + pb) / 2, py - 5), label, font=F(12), fill=col, anchor="md")

    def dim_v(x, ya, yb, label, col=DIM):
        (px, pa), (_, pb) = P(x, ya), P(x, yb)
        svg.line([(px, pa), (px, pb)], fill=col, width=0.9)
        for y in (pa, pb):
            svg.line([(px - 8, y), (px + 8, y)], fill=col, width=0.7)
            svg.line([(px - 4, y + 4), (px + 4, y - 4)], fill=col, width=1.2)
        svg.text((px - 7, (pa + pb) / 2), label, font=F(12), fill=col, anchor="rm")
    dim_h(fl[0], fh[0], y0 - 9.0, "frame " + frac(fh[0] - fl[0]))
    dim_v(x0 - 4.0, fl[1], fh[1], "frame " + frac(fh[1] - fl[1]))
    nh = 0
    for i, s in enumerate(with_fp):
        hull = recs[s]["footprint"]["overhang"]
        if len(hull) >= 3:
            col = DASHES[i % len(DASHES)]
            hx = [p[0] for p in hull]
            dim_h(min(hx), max(hx), y1 + 4.0 + 5.0 * nh, "%s %s" % (s.replace(name + "-", ""), frac(max(hx) - min(hx))), col)
            nh += 1
    # the origin, the front and back
    ox, oy = P(0, 0)
    svg.line([(ox - 10, oy), (ox + 10, oy)], fill=SOFT, width=0.8)
    svg.line([(ox, oy - 10), (ox, oy + 10)], fill=SOFT, width=0.8)
    svg.text((ox + 6, oy + 6), "origin", font=F(10), fill=SOFT, anchor="la")
    fx, fy = P(0, fl[1])
    svg.line([(fx, fy), (fx, fy + 34)], fill=INK, width=1.4)
    svg.polygon([(fx - 6, fy + 26), (fx + 6, fy + 26), (fx, fy + 38)], fill=INK, outline=INK, width=1)
    svg.text((fx + 10, fy + 26), "FRONT (-y): the empty \"%s\"" % recs[with_fp[0]]["front"], font=F(12), fill=INK, anchor="lm")
    bx, by = P(0, y1 + 4.0 + 5.0 * nh + 1.0)
    svg.text((bx, by), "BACK (+y)", font=F(12), fill=INK, anchor="md")
    # the title and the key
    tx, ty = M + (x1 - x0) * K + 60, M + 60
    svg.text((tx, ty), share["title"], font=F(20), fill=INK, anchor="la")
    svg.text((tx, ty + 26), "Footprint, from above", font=F(13), fill=SOFT, anchor="la")
    svg.text((tx, ty + 46), "x across, y front to back, in inches", font=F(12), fill=SOFT, anchor="la")
    for i in range(4):
        svg.rectangle([(tx + i * 3 * K, ty + 62), (tx + (i + 1) * 3 * K, ty + 68)], fill=INK if i % 2 == 0 else "#ffffff",
                      outline=INK, width=0.8)
    svg.text((tx + 12 * K + 8, ty + 65), '12"', font=F(11), fill=SOFT, anchor="lm")
    y = ty + 100
    svg.rectangle([(tx, y - 6), (tx + 24, y + 6)], fill="#ffffff", outline=INK, width=1.0)
    svg.text((tx + 32, y), "the frame %s x %s" % (frac(fh[0] - fl[0]), frac(fh[1] - fl[1])), font=F(12), fill=INK, anchor="lm")
    for i, s in enumerate(with_fp):
        hull = recs[s]["footprint"]["overhang"]
        if len(hull) < 3:
            continue
        y += 24
        col = DASHES[i % len(DASHES)]
        svg.parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.6" stroke-dasharray="7 4"/>'
                         % (tx, y, tx + 24, y, col))
        hx, hy = [p[0] for p in hull], [p[1] for p in hull]
        svg.text((tx + 32, y), "%s: the bedding, %s x %s" % (recs[s]["file"].replace(".blend", ""), frac(max(hx) - min(hx)),
                                                                 frac(max(hy) - min(hy))), font=F(12), fill=col, anchor="lm")
    y += 30
    svg.text((tx, y), "Version %s" % max(recs[s]["version"] for s in order), font=F(12), fill=SOFT, anchor="la")
    svg.save(os.path.join(d, "%s-footprint.svg" % name))


if __name__ == "__main__":
    write(sys.argv[1])

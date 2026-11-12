"""The export's check (tools/blender/deliver.py runs it after every export):
open an empty scene in a fresh Blender, append every object of the saved
file the way another repo's room does (Sketchup-tools' assets.place()),
and WITHOUT bpy.context.view_layer.update() measure it and assert:

- its box is the size the export measured, within 1/8", its bottom at
  z = 0 and its frame's footprint centered on the origin. Blender doesn't
  save matrix_world: an object appended without an update reads as the
  identity until the depsgraph runs (tested, Blender 4.5, 2026-11-12), so
  the bed's pillows and draped cloths, which had transforms of their own,
  came into Sketchup-tools' rooms displaced (2026-11-11). Every mesh's
  transform is applied, so what's read here is the truth;
- the frame alone is the size the design's sizes say;
- every vertex above tall_in is in the +y half (the bed's headboard to +y);
- no parents, every mesh's matrix the identity, every object, mesh,
  material and image named with the prefix, every object tagged with the
  version, every image packed, the named collections there;
- the front empty at the middle of the front, on the floor, pointing -y.

    python3.11 tools/blender/check_export.py <file.blend> '<the export record as JSON>'

Prints CHECK lines, CHECKED <json> and exits 1 on a failure.
"""
import json
import sys

import bpy
from mathutils import Vector

INCH = 0.0254
TOL = 0.125


def main():
    path, want = sys.argv[1], json.loads(sys.argv[2])
    prefix = want["prefix"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
        coll_names = list(src.collections)
    objs = [o for o in dst.objects if o]
    for o in objs:
        bpy.context.scene.collection.objects.link(o)
    # (deliberately no view_layer.update(): read what the file stored)
    meshes = [o for o in objs if o.type == "MESH"]
    fails, notes = [], []

    def ok(cond, msg):
        (notes if cond else fails).append(msg)

    pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]) / INCH
    hi = Vector([max(p[k] for p in pts) for k in range(3)]) / INCH
    size = hi - lo
    ok(all(abs(size[k] - want["size_in"][k]) <= TOL for k in range(3)),
       "size %.3f x %.3f x %.3f in (exported %s)" % (size.x, size.y, size.z, want["size_in"]))
    ok(abs(lo.z) <= 1 / 64, "bottom at z %.4f in" % lo.z)
    frame = set(n for c in want["frame"] for n in want["collections"][c])
    fp = [o.matrix_world @ v.co for o in meshes if o.name in frame for v in o.data.vertices]
    flo = Vector([min(p[k] for p in fp) for k in range(3)]) / INCH
    fhi = Vector([max(p[k] for p in fp) for k in range(3)]) / INCH
    ok(abs(flo.x + fhi.x) / 2 <= TOL and abs(flo.y + fhi.y) / 2 <= TOL,
       "frame footprint centered at (%.3f, %.3f) in" % ((flo.x + fhi.x) / 2, (flo.y + fhi.y) / 2))
    if want.get("expect_frame_in"):
        e = want["expect_frame_in"]
        fs = fhi - flo
        ok(all(abs(fs[k] - e[k]) <= TOL for k in range(3)),
           "frame %.3f x %.3f x %.3f in (the design's sizes: %s)" % (fs.x, fs.y, fs.z, e))
    if want.get("tall_in"):
        tall = [p for p in pts if p.z / INCH > want["tall_in"]]
        ok(tall and all(p.y > 0 for p in tall),
           "facing: %d vertices above %s in, all in the +y half" % (len(tall), want["tall_in"]))
    ok(all(o.parent is None for o in objs), "no parents")
    ok(all(o.matrix_world == o.matrix_world.Identity(4) and o.matrix_basis == o.matrix_basis.Identity(4)
           for o in meshes), "every mesh's matrix the identity")
    bad = [o.name for o in objs if not o.name.startswith(prefix + " ")]
    bad += [o.data.name for o in meshes if not o.data.name.startswith(prefix + " ")]
    ok(not bad, "objects and meshes named '%s ...'%s" % (prefix, (": not " + ", ".join(bad[:5])) if bad else ""))
    mats = {s.material for o in meshes for s in o.material_slots if s.material}
    bad = [m.name for m in mats if not m.name.startswith(prefix + " ")]
    ok(not bad, "%d materials named '%s ...'%s" % (len(mats), prefix, (": not " + ", ".join(bad)) if bad else ""))
    imgs = [i for i in bpy.data.images if i.source == "FILE"]
    bad = [i.name for i in imgs if not i.packed_file or not i.name.startswith(prefix + " ")]
    ok(not bad, "%d images packed and named '%s ...'%s" % (len(imgs), prefix, (": not " + ", ".join(bad)) if bad else ""))
    bad = [o.name for o in objs if o.get("design_render_version") != want["version"]]
    ok(not bad, "every object tagged design_render_version=%s%s" % (want["version"], (": not " + ", ".join(bad[:5])) if bad else ""))
    ok(sorted(coll_names) == sorted(want["collections"]), "collections %s" % ", ".join(sorted(coll_names)))
    fr = [o for o in objs if o.name == want["front"]]
    if fr:
        f = fr[0]
        # (its own transform: Blender doesn't save matrix_world, so an object
        # appended without an update reads as the identity; why every mesh's is)
        arrow = f.matrix_basis.to_3x3() @ Vector((0, 0, 1))
        loc = f.matrix_basis.translation / INCH
        ok(abs(loc.x) <= TOL and abs(loc.y - flo.y) <= TOL and abs(loc.z) <= TOL and arrow.y < -0.99,
           "'%s' at (%.2f, %.2f, %.2f) in, pointing (%.2f, %.2f, %.2f)" % ((f.name,) + tuple(loc) + tuple(arrow)))
    else:
        fails.append("no '%s' empty" % want["front"])
    for n in notes:
        print("CHECK ok:", n)
    for n in fails:
        print("FAIL:", n)
    print("CHECKED " + json.dumps(dict(size_in=[round(c, 3) for c in size], passed=notes, failed=fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

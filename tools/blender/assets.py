"""Real 3D models from library/models/ (models.yaml), placed in a room model
in its own inches (client, 2026-10-21: use free models instead of drawing
vases, baskets and benches from boxes).

    import assets
    assets.place("painted_wooden_bench", (x, y, 0), rot=90, width=45, objs=OBJS)

The model is appended from its .blend, its parts joined under one empty,
scaled to the size asked for (width, depth or height in inches; or its real
size), turned about the vertical axis, and set down with its base at z and
its footprint centered on (x, y). Its own materials are kept, unless
`tint` gives a hex color to repaint it in (a painted bench in the
scheme's paint), its old paint's wear showing through lightly.

To find more: python3 tools/fetch_models.py --list wicker chair
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INCH = 0.0254
TAG = "asset"     # on every part place() adds: export_dae() leaves them out of the light version


def _index():
    import yaml
    return yaml.safe_load(open(os.path.join(ROOT, "library", "models", "models.yaml"))) or {}


def _append(path):
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    new = [o for o in dst.objects if o is not None]
    for o in new:
        if o not in before:
            bpy.context.scene.collection.objects.link(o)
    return [o for o in new if o.type == "MESH"]


def _bbox(objs):
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
    return lo, hi


def _tint(objs, hx):
    h = hx.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    rgb = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    for o in objs:
        for slot in o.material_slots:
            m = slot.material
            if not m or not m.use_nodes:
                continue
            m = m.copy()
            slot.material = m
            bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if not bsdf:
                continue
            link = bsdf.inputs["Base Color"].links
            # repainted: the new color, with the old paint's wear and grain
            # laid over it lightly (an overlay at a third), so it isn't flat
            mix = m.node_tree.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "OVERLAY"
            mix.inputs["Factor"].default_value = 0.35
            mix.inputs["A"].default_value = (*rgb, 1.0)
            if link:
                m.node_tree.links.new(link[0].from_socket, mix.inputs["B"])
            else:
                mix.inputs["B"].default_value = bsdf.inputs["Base Color"].default_value
            m.node_tree.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])


def place(mid, at, rot=0.0, width=None, depth=None, height=None, tint=None, objs=None, name=None,
          only=None):
    """Place model `mid` with its footprint centered on at=(x, y) and its base
    at at[2], in inches; rot in degrees about z. One of width/depth/height
    (inches) sets the scale, keeping proportions; none: its real size.
    only: keep just the parts whose names end with one of these (a set's
    one cup and its saucer: only=("cup_small_01", "saucer_circular_04"))."""
    rec = _index()[mid]
    parts = _append(os.path.join(ROOT, rec["file"]))
    if only:
        keep = [o for o in parts if o.name.endswith(tuple(only))]
        for o in parts:
            if o not in keep:
                bpy.data.objects.remove(o)
        parts = keep
    for o in parts:              # flatten: no parents, world transforms kept
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.context.view_layer.update()
    lo, hi = _bbox(parts)
    size = hi - lo                                   # metres, as modeled
    want = None
    if width:
        want = width * INCH / size.x
    elif depth:
        want = depth * INCH / size.y
    elif height:
        want = height * INCH / size.z
    k = (want or 1.0) / INCH                         # to the room's inches
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    m = (Matrix.Translation(Vector(at)) @ Matrix.Rotation(math.radians(rot), 4, "Z")
         @ Matrix.Scale(k, 4) @ Matrix.Translation(-centre))
    for o in parts:
        o.matrix_world = m @ o.matrix_world
        o.name = (name or "Asset %s" % mid) + "_" + o.name
        o[TAG] = mid
    if tint:
        _tint(parts, tint)
    if objs is not None:
        objs.extend(parts)
    return parts

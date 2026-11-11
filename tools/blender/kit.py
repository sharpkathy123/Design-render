"""The shared building blocks for a design's Blender model (Design-render,
2026-11-10): parts in inches, materials from vanity_render_setup's recipes,
a plain studio to stand the thing in, cameras, the render, the joint check
and the parts list that tools/draw_views.py draws from.

    import kit
    kit.reset()
    kit.materials({"oak": "oak", "steel": {"color": (0.6, 0.6, 0.62), "roughness": 0.3, "metallic": 1.0}})
    kit.box("Top", 0, 0, 29, 60, 30, 30.75, "oak")
    kit.cyl("Leg", 1, 0, 29, x=2, y=2, key="steel")
    kit.check_joints()
    kit.write_parts("designs/thing/parts.json", name="Thing")
    kit.studio()
    kit.camera_auto(azimuth=-35, elevation=18)
    kit.render("designs/thing/renders/thing-front.jpg", quality="check")

Axes, as a drawing has them: x left to right across the front, y from the
front to the back, z up from the floor; inches throughout (the meshes are
made in Blender's meters). Every part goes in OBJS; box() parts also in
BOXES for the joint check; every part is listed in PARTS for the parts
list and the drawings.

Run a model with Blender's Python (python3.11; tools/bpy_python.py restarts
under it if needed).
"""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import bpy_python  # noqa: E402
bpy_python.ensure()
sys.path.insert(0, os.path.join(ROOT, "tools", "vendor"))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

spec_ = importlib.util.spec_from_file_location("vanity_render_setup", os.path.join(HERE, "vanity_render_setup.py"))
v = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(v)

INCH = 0.0254
OBJS, BOXES, PARTS = [], [], []
SPECS = {}          # material key -> its recipe (a dict for vanity_render_setup.build_material)
DIMS = []           # extra dimensions for the drawings: dim(...)

# Ready recipes (vanity_render_setup's, by name), for materials(): colors
# are linear 0..1. A wood recipe ("wood": True) gets its grain run along
# each part's longest side.
PRESETS = {
    "oak": dict(color=(0.17, 0.09, 0.04), roughness=0.45, coat=0.25, wood=True),       # stained quartersawn oak
    "light_oak": dict(color=(0.48, 0.30, 0.15), roughness=0.5, coat=0.15, wood=True),  # clear-finished white oak
    "maple": dict(color=(0.62, 0.47, 0.30), roughness=0.55, coat=0.1, wood=True),
    "walnut": dict(color=(0.09, 0.045, 0.025), roughness=0.45, coat=0.25, wood=True),
    "plywood": dict(color=(0.62, 0.47, 0.30), roughness=0.60),
    "white_paint": dict(color=(0.86, 0.85, 0.82), roughness=0.38, coat=0.15),
    "nickel": dict(color=(0.80, 0.76, 0.66), roughness=0.10, metallic=1.0),
    "chrome": dict(color=(0.90, 0.90, 0.92), roughness=0.05, metallic=1.0),
    "steel": dict(color=(0.55, 0.55, 0.56), roughness=0.35, metallic=1.0),
    "black_metal": dict(color=(0.03, 0.03, 0.03), roughness=0.35, metallic=0.8),
    "brass": dict(color=(0.50, 0.36, 0.17), roughness=0.35, metallic=1.0),
    "rubber": dict(color=(0.02, 0.02, 0.02), roughness=0.8),
    "marble": dict(color=(0.86, 0.86, 0.84), roughness=0.22, marble=True),
    "linen": dict(color=(0.80, 0.78, 0.70), roughness=0.95, sheen=0.6),
}


def hexcolor(h):
    """A '#rrggbb' color as linear 0..1, for a recipe's color."""
    return v.hex_linear(h)


# ---------------------------------------------------------------------------
# The scene and materials
# ---------------------------------------------------------------------------
def reset():
    """An empty scene (Blender's default cube, camera and light removed)."""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    OBJS.clear()
    BOXES.clear()
    PARTS.clear()
    DIMS.clear()
    SPECS.clear()


def materials(specs):
    """Name the materials a model uses: key -> a PRESETS name, a '#hex'
    color (a plain satin finish), or a recipe dict (vanity_render_setup's
    keys: color, roughness, metallic, coat, sheen, transmission, emission,
    wood, marble, speckle, ...; 'hex' in place of color). A recipe may also
    give 'label', the name the parts list uses (e.g. '3/4\" white oak')."""
    for key, s in specs.items():
        if isinstance(s, str):
            s = dict(PRESETS[s]) if s in PRESETS else dict(color=hexcolor(s), roughness=0.4)
        else:
            s = dict(PRESETS.get(s.get("preset"), {}), **{k: x for k, x in s.items() if k != "preset"})
        if "hex" in s:
            s["color"] = hexcolor(s.pop("hex"))
        SPECS[key] = s


def mat(key, grain="z"):
    """The Blender material for a key (a wood's made once per grain axis)."""
    spec = SPECS.get(key) or SPECS.setdefault(key, dict(color=(0.6, 0.6, 0.6), roughness=0.5))
    name = key if not spec.get("wood") else "%s grain %s" % (key, grain)
    m = bpy.data.materials.get("Vanity " + name.capitalize())
    if m is None:
        s = {k: x for k, x in spec.items() if k != "label"}
        if spec.get("wood"):
            s["grain"] = grain
        m = v.build_material(name, s)
    return m


# ---------------------------------------------------------------------------
# Parts (inches)
# ---------------------------------------------------------------------------
def _obj(name, bm, key, grain="z", smooth=False):
    me = bpy.data.meshes.new(name)
    for vert in bm.verts:
        vert.co *= INCH
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.data.materials.append(mat(key, grain))
    bpy.context.scene.collection.objects.link(o)
    OBJS.append(o)
    return o


def _longest(lo, hi):
    d = [hi[k] - lo[k] for k in range(3)]
    return "xyz"[d.index(max(d))]


def box(name, x0, y0, z0, x1, y1, z1, key, grain=None, part=True, round_edges=None, check=True, extra=0.0, note="with tenons"):
    """A rectangular part from corner to corner. A wood's grain runs along
    its longest side unless `grain` names the axis. part=False leaves it
    out of the parts list (a floor, a stand-in). round_edges: a bevel
    radius in inches (eased edges catch the light; default 1/16").
    check=False leaves it out of the joint and overlap checks (a tenon's
    proud end, a peg: they sit against a part's face on purpose). extra:
    length the cut list adds along the grain (tenons the model doesn't
    draw inside the parts they go into), and note what it is."""
    lo = (min(x0, x1), min(y0, y1), min(z0, z1))
    hi = (max(x0, x1), max(y0, y1), max(z0, z1))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for vert in bm.verts:
        vert.co = Vector(tuple(lo[k] if vert.co[k] < 0 else hi[k] for k in range(3)))
    g = grain or _longest(lo, hi)
    o = _obj(name, bm, key, g)
    if check:
        BOXES.append((o, lo, hi))
    r = 1 / 16 if round_edges is None else round_edges
    if r > 0:
        mod = o.modifiers.new("Bevel", "BEVEL")
        mod.width = min(r, min(hi[k] - lo[k] for k in range(3)) / 3) * INCH
        mod.segments = 2
        mod.limit_method = "ANGLE"
        mod.use_clamp_overlap = True
        mod.harden_normals = True
    if part:
        PARTS.append(dict(name=name, kind="box", key=key, lo=list(lo), hi=list(hi), grain=g, extra=extra,
                          note=note if extra else ""))
    return o


def prism(name, pts, axis, a0, a1, key, grain=None, part=True, smooth=False, extra=0.0):
    """A polygon extruded along an axis: pts are (u, v) in the other two
    axes in order (axis "y": (x, z); "x": (y, z); "z": (x, y)), from a0 to
    a1 along the axis. For angled legs, braces, arched aprons."""
    ax = "xyz".index(axis)
    others = [k for k in range(3) if k != ax]

    def p3(u, w, a):
        c = [0.0, 0.0, 0.0]
        c[others[0]], c[others[1]], c[ax] = u, w, a
        return c
    bm = bmesh.new()
    lo = [bm.verts.new(p3(u, w, a0)) for u, w in pts]
    hi = [bm.verts.new(p3(u, w, a1)) for u, w in pts]
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    us = [p[0] for p in pts]
    ws = [p[1] for p in pts]
    blo, bhi = p3(min(us), min(ws), min(a0, a1)), p3(max(us), max(ws), max(a0, a1))
    g = grain or _longest(blo, bhi)
    o = _obj(name, bm, key, g, smooth)
    if part:
        PARTS.append(dict(name=name, kind="prism", key=key, axis=axis, pts=[list(p) for p in pts],
                          a=[min(a0, a1), max(a0, a1)], lo=blo, hi=bhi, grain=g, extra=extra))
    return o


def cyl(name, r, a0, a1, x=0.0, y=0.0, key="steel", axis="z", segs=48, part=True):
    """A round part (a leg, a rod, a dowel) of radius r, from a0 to a1 along
    the axis; x, y are its center in the other two axes (for axis "x":
    y and z; "y": x and z)."""
    ax = "xyz".index(axis)
    others = [k for k in range(3) if k != ax]
    bm = bmesh.new()
    ring0, ring1 = [], []
    for i in range(segs):
        t = 2 * math.pi * i / segs
        for ring, a in ((ring0, a0), (ring1, a1)):
            c = [0.0, 0.0, 0.0]
            c[others[0]], c[others[1]], c[ax] = x + r * math.cos(t), y + r * math.sin(t), a
            ring.append(bm.verts.new(c))
    bm.faces.new(ring0)
    bm.faces.new(list(reversed(ring1)))
    for i in range(segs):
        j = (i + 1) % segs
        f = bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
        f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, key, axis)
    if part:
        lo, hi = [0.0] * 3, [0.0] * 3
        lo[ax], hi[ax] = min(a0, a1), max(a0, a1)
        lo[others[0]], hi[others[0]] = x - r, x + r
        lo[others[1]], hi[others[1]] = y - r, y + r
        PARTS.append(dict(name=name, kind="cyl", key=key, axis=axis, r=r, lo=lo, hi=hi, grain=axis))
    return o


def pyramid(name, x0, y0, x1, y1, z0, rise, key, flat=0.0):
    """A shallow pyramid over a rectangle at height z0 (a post's cap),
    rising `rise`, with a flat of `flat` inches across at its peak. Not a
    part of its own: it's cut on the post's end."""
    bm = bmesh.new()
    cx, cy, f = (x0 + x1) / 2, (y0 + y1) / 2, flat / 2
    base = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))]
    top = [bm.verts.new(p) for p in ((cx - f, cy - f, z0 + rise), (cx + f, cy - f, z0 + rise),
                                      (cx + f, cy + f, z0 + rise), (cx - f, cy + f, z0 + rise))]
    bm.faces.new(list(reversed(base)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((base[i], base[j], top[j], top[i]))
    bm.faces.new(top)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, key, "z")


def cut(o, *boxes):
    """Cut boxes (x0, y0, z0, x1, y1, z1, inches) out of a part: a notch,
    a mortise, a hole for a bolt."""
    o["cut"] = True
    for i, b in enumerate(boxes):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for vert in bm.verts:
            vert.co = Vector(tuple((b[k] if vert.co[k] < 0 else b[k + 3]) * INCH for k in range(3)))
        me = bpy.data.meshes.new("cutter")
        bm.to_mesh(me)
        bm.free()
        c = bpy.data.objects.new("cutter", me)
        bpy.context.scene.collection.objects.link(c)
        m = o.modifiers.new("cut%d" % i, "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = c
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(c, do_unlink=True)
    return o


def dim(label, a, b, view="front", offset=2.0):
    """An extra dimension for the drawings: from point a to b (inches,
    (x, y, z)), shown in one view ("front", "side" or "top"), offset that
    far from the line between them (positive: up or right in the view)."""
    DIMS.append(dict(label=label, a=list(a), b=list(b), view=view, offset=offset))


def bounds(objs=None):
    """The model's bounds, inches: (lo, hi)."""
    pts = [o.matrix_world @ Vector(c) for o in (objs or OBJS) for c in o.bound_box]
    lo = [min(p[k] for p in pts) / INCH for k in range(3)]
    hi = [max(p[k] for p in pts) / INCH for k in range(3)]
    return lo, hi


# ---------------------------------------------------------------------------
# Checks and the parts list
# ---------------------------------------------------------------------------
def check_joints():
    """JOINT lines: two boxes with faces in one plane, facing the same way
    and overlapping (a leg flush with the top it runs through): the
    renderer flickers between them and draws dark patches (RECIPES.md,
    "Joints"). Butt the pieces instead. Returns the lines."""
    live = {id(o) for o in OBJS}
    found = v.coincident_faces([o for o, _, _ in BOXES if id(o) in live and not o.get("cut")])
    for f in found:
        print("JOINT " + f, flush=True)
    return found


def check_overlaps(tol=0.01):
    """OVERLAP lines: two box parts that share volume (a leg run up into the
    top: fine in a render, wrong in the parts list and the drawings).
    Joinery that really interlocks (a tenon) can be listed in `allow`."""
    found = []
    bs = [(o.name, lo, hi) for o, lo, hi in BOXES if not o.get("cut")]
    for i, (na, a0, a1) in enumerate(bs):
        for nb, b0, b1 in bs[i + 1:]:
            if all(min(a1[k], b1[k]) - max(a0[k], b0[k]) > tol for k in range(3)):
                found.append("%s / %s" % (na, nb))
    for f in found:
        print("OVERLAP " + f, flush=True)
    return found


def write_parts(path, name="", notes=()):
    """The parts list, as JSON, for tools/draw_views.py and the cut list:
    every part's shape in inches, its material's key and label, the extra
    dimensions."""
    lo, hi = bounds()
    data = dict(name=name, notes=list(notes), bounds=[lo, hi], dims=DIMS,
                materials={k: s.get("label", k) for k, s in SPECS.items()},
                parts=PARTS)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    json.dump(data, open(path, "w"), indent=1)
    print("PARTS %d -> %s" % (len(PARTS), path), flush=True)


# ---------------------------------------------------------------------------
# Studio, camera, render
# ---------------------------------------------------------------------------
def studio(floor="#cfc8bd", wall="#e8e4dc", size=None, wall_y=None, warm=True, radius=30.0):
    """A plain photo studio: a floor, a wall behind with a soft curve into
    it (a sweep), a big soft key light, a fill and a rim, a dim gray world.
    The sweep stands behind the model's back (wall_y, inches; default 24"
    behind it; radius, the curve's: small for a thing that stands against
    a wall, as a bed does). Not parts: they're left out of the parts list."""
    lo, hi = bounds()
    span = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    size = size or max(240.0, span * 6)
    cx = (lo[0] + hi[0]) / 2
    wy = wall_y if wall_y is not None else hi[1] + max(24.0, span * 0.6)
    SPECS.setdefault("_floor", dict(color=hexcolor(floor), roughness=0.75))
    SPECS.setdefault("_wall", dict(color=hexcolor(wall), roughness=0.9))
    # the sweep: floor up into the wall on a 30" radius, one smooth piece
    R, n = radius, 12
    prof = [(-size, 0.0), (wy - R, 0.0)]
    prof += [(wy - R + R * math.sin(math.pi / 2 * k / n), R - R * math.cos(math.pi / 2 * k / n)) for k in range(1, n + 1)]
    prof += [(wy, size * 0.6)]
    bm = bmesh.new()
    left = [bm.verts.new((cx - size, y, z)) for y, z in prof]
    right = [bm.verts.new((cx + size, y, z)) for y, z in prof]
    for i in range(len(prof) - 1):
        f = bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
        f.smooth = i > 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj("Studio sweep", bm, "_floor")
    o.data.materials[0] = mat("_floor")
    OBJS.remove(o)
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.055, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    # (past the sweep's edges the camera sees the wall's color, not the dark
    # world that lights the scene: a side view looked out into black)
    if "Camera backdrop" not in nt.nodes:
        lp = nt.nodes.new("ShaderNodeLightPath")
        seen = nt.nodes.new("ShaderNodeBackground")
        seen.name = "Camera backdrop"
        seen.inputs["Color"].default_value = SPECS["_wall"]["color"] + (1.0,)
        seen.inputs["Strength"].default_value = 0.9
        mix = nt.nodes.new("ShaderNodeMixShader")
        out = nt.nodes.get("World Output")
        nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
        nt.links.new(bg.outputs[0], mix.inputs[1])
        nt.links.new(seen.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
    c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)) * INCH
    d = max(span, 30.0) * INCH
    tint = (1.0, 0.93, 0.85) if warm else (1.0, 1.0, 1.0)
    for nm, off, power, sz, col in (
            ("Key light", Vector((-1.6, -1.8, 2.0)), 650.0, 2.2, tint),
            ("Fill light", Vector((2.0, -1.4, 0.8)), 160.0, 3.0, (0.92, 0.95, 1.0)),
            ("Rim light", Vector((1.0, 2.0, 2.2)), 400.0, 1.2, tint)):
        ld = bpy.data.lights.new(nm, "AREA")
        ld.shape = "DISK"
        ld.size = sz * d
        ld.energy = power * (d / 1.5) ** 2
        ld.color = col
        lo_ = bpy.data.objects.new(nm, ld)
        lo_.location = c + off * d
        lo_.rotation_euler = (c - lo_.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(lo_)
    return o


def camera(eye, target, lens=50.0, name="Camera"):
    """A camera at eye looking at target (inches), lens in mm."""
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.01
    cd.clip_end = 500
    o = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)
    o.location = Vector(eye) * INCH
    o.rotation_euler = (Vector(target) * INCH - o.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return o


def camera_auto(azimuth=-35.0, elevation=15.0, lens=50.0, margin=1.15, aspect=4 / 3, target=None):
    """A camera framing the whole model: azimuth degrees round from straight
    in front (negative: from the left), elevation degrees above level."""
    lo, hi = bounds()
    c = target or [(lo[k] + hi[k]) / 2 for k in range(3)]
    corners = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    az, el = math.radians(azimuth), math.radians(elevation)
    # (the camera stands in front, at -y; from the left at negative azimuth)
    out = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    fwd = -out                                     # the way the camera looks
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd).normalized()
    half_w = 18.0 / lens          # (36 mm sensor width: tan of half the view)
    half_h = half_w / aspect
    dist = 0.0
    for p in corners:
        q = Vector(p) - Vector(c)
        dist = max(dist, q.dot(-fwd) + abs(q.dot(right)) * margin / half_w,
                   q.dot(-fwd) + abs(q.dot(up)) * margin / half_h)
    eye = Vector(c) - fwd * dist
    return camera(tuple(eye), tuple(c), lens)


QUALITY = {"check": (48, 1280, 960), "final": (384, 2400, 1800)}


def render(path, quality="check", size=None):
    """Render the scene's camera to a JPG. quality: "check" (quick, any
    time) or "final"; size (w, h) overrides its size."""
    samples, w, h = QUALITY[quality]
    if size:
        w, h = size
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    for vt in ("AgX", "Filmic"):
        try:
            sc.view_settings.view_transform = vt
            break
        except TypeError:
            continue
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sc.render.filepath = os.path.abspath(path)
    bpy.ops.render.render(write_still=True)
    print("RENDER %s" % path, flush=True)
    return path


def save_blend(path):
    """The model as a .blend, to open in Blender."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path), compress=True)

"""A design's 3D model for other repos' rooms (Sketchup-tools' notes, 2026-11-12:
designer/notes-for-design-render.md there): one call saves a version of the
design so it drops into a room with no work, checks it, and records it.

    import deliver
    deliver.export("designs/<name>/model/<name>-<version>.blend", design="<name>", prefix="Bed",
                   collections={"Bed frame": [...], "Bedding: quilt": [...]}, ...)

What it does, in order (RECIPES.md, "A model for another repo's rooms"):

1. Only meshes are kept (no lights, camera, studio), and every modifier is
   applied except the smoothing ones (Subdivision: those stay live, 0 in the
   viewport and their render level in renders, so a room stays light).
2. Every transform is applied and every parent cleared: each object's world
   matrix is the identity, so a stale matrix_world can't misplace anything
   (the bed's bedding came in displaced, 2026-11-11, from a file saved
   without view_layer.update()).
3. The model is moved so its frame's footprint is centered on the origin,
   its bottom at z = 0 (Blender meters, real size). Its front is -y, its
   back +y; an empty "<prefix> front" marks the middle of the front on the
   floor, its arrow pointing -y.
4. Objects, meshes, materials and images are named "<prefix> ..." (so a
   room's own "oak" isn't merged or copied to "oak.001"), objects sorted into
   the named collections given, every object tagged with the version
   (o["design_render_version"]), every image packed.
5. Saved, then also written as <stem>.glb (glTF, meters, its own Y-up) and
   sketchup/<stem>.dae (COLLADA, in inches, Z up, for SketchUp), with simple
   color-or-image materials.
6. Checked in a fresh Blender: every object appended into an empty scene
   WITHOUT view_layer.update(), and its size, floor, centering, facing,
   names, tags and packing asserted (tools/blender/check_export.py). A
   failure stops the export.
7. Recorded in designs/<name>/model/exports.json (sizes measured from the
   file, triangle counts, sha256s, the footprint), and tools/model_card.py
   writes the model's README, VERSION, library record and footprint drawing
   from it.
"""
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
INCH = 0.0254
TAG = "design_render_version"


def changelog_version(design):
    """The newest line of designs/<design>/model/CHANGELOG.md: ("2026-11-12a", "what changed")."""
    p = os.path.join(ROOT, "designs", design, "model", "CHANGELOG.md")
    for line in open(p):
        m = re.match(r"^- \*\*(\S+)\*\*:?\s*(.*)", line) or re.match(r"^- (\S+?):\s*(.*)", line)
        if m:
            return m.group(1), m.group(2).strip()
    sys.exit("No version line ('- 2026-11-12a: what changed') in %s" % p)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _named(prefix, n):
    """'Head post L' -> 'Bed head post L' (the first letter lowered, the prefix once)."""
    if n.startswith(prefix + " "):
        return n
    return "%s %s%s" % (prefix, n[:1].lower(), n[1:])


def _apply_modifiers(o):
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        if m.type == "SUBSURF":
            m.levels = 0                      # (viewport and the .glb/.dae: the cage; renders: render_levels)
            continue
        if m.type == "COLLISION":
            o.modifiers.remove(m)
            continue
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError as e:            # (a modifier with nothing to do: drop it)
            print("deliver: %s %s not applied (%s), removed" % (o.name, m.name, e), flush=True)
            o.modifiers.remove(m)


def _bbox(objs):
    pts = [o.matrix_world @ v.co for o in objs if o.type == "MESH" for v in o.data.vertices]
    lo = Vector([min(p[k] for p in pts) for k in range(3)])
    hi = Vector([max(p[k] for p in pts) for k in range(3)])
    return lo, hi


def _tris(objs, render=False):
    """Triangles in the meshes (render=True: with the smoothing at its render level)."""
    if not render:
        return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs if o.type == "MESH")
    keep = {}
    for o in objs:
        for m in o.modifiers:
            if m.type == "SUBSURF":
                keep[(o.name, m.name)] = m.levels
                m.levels = m.render_levels
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        if o.type != "MESH":
            continue
        me = o.evaluated_get(dg).to_mesh()
        n += sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
    for o in objs:
        for m in o.modifiers:
            if (o.name, m.name) in keep:
                m.levels = keep[(o.name, m.name)]
    return n


def _hull(pts):
    """The convex hull of (x, y) points, anticlockwise (Andrew's monotone chain)."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _base_color(m):
    """A material's flat stand-in for the .glb and .dae: (image, uv scale) if
    an image feeds its color, else (None, rgba)."""
    if m.use_nodes and m.node_tree:
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            sock = bsdf.inputs["Base Color"]
            if not sock.is_linked:
                return None, tuple(sock.default_value)
            seen, todo = set(), [sock.links[0].from_node]
            while todo:                                   # upstream, inputs in order: the first image
                n = todo.pop(0)
                if n.name in seen:
                    continue
                seen.add(n.name)
                if n.type == "TEX_IMAGE" and n.image:
                    scale = (1.0, 1.0)
                    v = n.inputs["Vector"]
                    if v.is_linked and v.links[0].from_node.type == "MAPPING":
                        s = v.links[0].from_node.inputs["Scale"].default_value
                        scale = (s[0], s[1])
                    return n.image, scale
                todo = [i.links[0].from_node for i in n.inputs if i.is_linked] + todo   # (depth first: A before B)
    return None, tuple(m.diffuse_color)


def _flat_materials(objs):
    """Swap every material for a plain one (a color, or its image straight off
    the UVs, the repeat baked into the UVs), for the interchange files; the
    .blend is already saved with the real ones."""
    done = {}
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            img, val = _base_color(m)
            if img is not None and o.data.uv_layers:
                for d in o.data.uv_layers.active.data:
                    d.uv = (d.uv[0] * val[0], d.uv[1] * val[1])
            if m.name not in done:
                f = bpy.data.materials.new(m.name + " flat")
                f.use_nodes = True
                b = f.node_tree.nodes["Principled BSDF"]
                if img is not None:
                    t = f.node_tree.nodes.new("ShaderNodeTexImage")
                    t.image = img
                    f.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
                else:
                    b.inputs["Base Color"].default_value = val
                src = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.use_nodes else None
                if src:
                    for k in ("Roughness", "Metallic"):
                        if not src.inputs[k].is_linked:
                            b.inputs[k].default_value = src.inputs[k].default_value
                done[m.name] = f
            slot.material = done[m.name]
    for name, f in done.items():          # the files' materials keep the prefixed names
        old = bpy.data.materials.get(name)
        if old:
            old.name = name + " (full)"
        f.name = name


def _write_dae(path, objs):
    """COLLADA for SketchUp: the coordinates in inches and its unit tag saying
    so, Z up, the textures copied beside it."""
    os.makedirs(os.path.dirname(path), exist_ok=True)      # (the exporter writes its images beside it)
    s = Matrix.Scale(1 / INCH, 4)               # (into the vertices: a node scaled 39.37x reads oddly in SketchUp)
    meshes = [o for o in objs if o.type == "MESH"]
    for o in meshes:
        o.data.transform(s)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        if o.type == "MESH":
            o.select_set(True)
    bpy.ops.wm.collada_export(filepath=path, selected=True, apply_modifiers=True, export_mesh_type_selection="view",
                              use_texture_copies=False, triangulate=False)
    txt = open(path).read()
    txt = re.sub(r'<unit name="[^"]*" meter="[^"]*"\s*/>', '<unit name="inch" meter="0.0254"/>', txt)
    txt = re.sub(r"<init_from>[^<]*[/\\]([^/\\<]+)</init_from>", r"<init_from>\1</init_from>", txt)   # beside it
    open(path, "w").write(txt)
    for o in meshes:
        o.data.transform(s.inverted())
    bpy.context.view_layer.update()


def start_all(model_dir):
    """Before exporting every version afresh: clear what the last round wrote
    (the SketchUp folder's images, the records), so nothing stale is left."""
    shutil.rmtree(os.path.join(model_dir, "sketchup"), ignore_errors=True)
    for f in ("exports.json",):
        if os.path.exists(os.path.join(model_dir, f)):
            os.remove(os.path.join(model_dir, f))


def export(path, design, prefix, collections, frame, about="", front_back="y", tall_in=None, expect_frame_in=None,
           object_names=None, material_names=None):
    """Save the scene's meshes as a version of the design (see the module's notes).

    collections: {"Bed frame": [objects], "Bedding: quilt": [...]}: every
        mesh in exactly one (an object in none goes in the first).
    frame: the collection names whose footprint is centered on the origin
        and drawn solid in the footprint (the rest: its overhang, dashed).
    tall_in: every vertex above this height (inches) must be in the +y half
        (the bed's headboard); None: no facing check.
    expect_frame_in: (x, y, z) inches the frame's box must measure, from the
        design's sizes (the export stops if it doesn't, within 1/8").
    object_names: a function from an object's name to its exported name
        (before the prefix): the bed's headboard parts all "headboard ...".
    material_names: [(start, name)]: a material whose name starts with
        `start` is called `name` (the rest of its name kept: " grain x").
    """
    version, change = changelog_version(design)
    path = os.path.abspath(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    mdir = os.path.dirname(path)
    # 1. meshes only, modifiers applied, 2. transforms applied, no parents
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    objs = list(bpy.data.objects)
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.context.view_layer.update()
    for o in objs:
        _apply_modifiers(o)
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
    # the collections
    member = {}
    for cname, cobjs in collections.items():
        for o in cobjs:
            if o.name in member:
                sys.exit("deliver: %s is in two collections (%s, %s)" % (o.name, member[o.name], cname))
            member[o.name] = cname
    first = next(iter(collections))
    groups = {c: [] for c in collections}
    for o in objs:
        groups[member.get(o.name, first)].append(o)
    # 3. the frame's footprint centered, the bottom at z 0
    fr = [o for c in frame for o in groups[c]]
    flo, fhi = _bbox(fr)
    alo, _ = _bbox(objs)
    shift = Vector((-(flo.x + fhi.x) / 2, -(flo.y + fhi.y) / 2, -alo.z))
    for o in objs:
        o.data.transform(Matrix.Translation(shift))
        o.data.update()
    # 4. names, collections, the version, packed images
    for o in objs:
        n = object_names(o.name) if object_names else o.name
        o.name = _named(prefix, n)
        o.data.name = o.name
        o[TAG] = version
        o["design_render_design"] = design
    starts = sorted(material_names or [], key=lambda t: -len(t[0]))
    for m in bpy.data.materials:
        if m.users == 0:
            continue
        for s, nm in starts:
            if m.name.startswith(s):
                m.name = "%s %s%s" % (prefix, nm, m.name[len(s):])     # (as given: "Bed Strawberry Thief")
                break
        else:
            m.name = _named(prefix, m.name)
    for img in bpy.data.images:
        if img.users and img.source == "FILE":
            img.name = _named(prefix, img.name)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for cname, cobjs in groups.items():
        c = bpy.data.collections.new(cname)
        bpy.context.scene.collection.children.link(c)
        for o in cobjs:
            for uc in list(o.users_collection):
                uc.objects.unlink(o)
            c.objects.link(o)
    lo, hi = _bbox(objs)
    flo, fhi = _bbox(fr)
    front = bpy.data.objects.new(prefix + " front", None)
    front.empty_display_type = "SINGLE_ARROW"
    front.empty_display_size = 12 * INCH
    front.location = (0.0, flo.y, 0.0)
    front.rotation_euler = (math.radians(90), 0.0, 0.0)      # its arrow (local +z) to -y
    front[TAG] = version
    front["design_render_design"] = design
    front["depth_in"] = round((fhi.y - flo.y) / INCH, 4)       # its back is this far behind it, along +y
    groups[first][0].users_collection[0].objects.link(front)
    bpy.ops.file.pack_all()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    bpy.context.scene.unit_settings.system = "IMPERIAL"
    bpy.context.scene.unit_settings.length_unit = "INCHES"
    bpy.context.view_layer.update()                           # (and the matrices stored fresh)
    os.makedirs(mdir, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0       # (no .blend1 beside it)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    print("EXPORT %s (%d objects)" % (path, len(bpy.data.objects)), flush=True)

    # what it measures, for the README and the check
    inch = lambda v: [round(c / INCH, 3) for c in v]   # noqa: E731
    rec = dict(file=os.path.basename(path), version=version, change=change, about=about,
               exported=datetime.date.today().isoformat(),
               size_in=inch(hi - lo), lo_in=inch(lo), hi_in=inch(hi),
               frame_size_in=inch(fhi - flo), frame_lo_in=inch(flo), frame_hi_in=inch(fhi),
               objects=len([o for o in objs]), triangles=_tris(objs), triangles_render=_tris(objs, render=True),
               collections={c: sorted(o.name for o in g) for c, g in groups.items()},
               materials=sorted(m.name for m in bpy.data.materials if m.users),
               images=sorted(i.name for i in bpy.data.images if i.users and i.source == "FILE"),
               front=prefix + " front", prefix=prefix, tall_in=tall_in, frame=list(frame))
    # the footprint: each frame part's top-view box (drawn in height order) and the rest's outline
    rec["footprint"] = dict(
        frame=sorted(([round(v, 3) for v in inch(a)[:2] + inch(b)[:2] + [inch(b)[2]]]
                      for a, b in (_bbox([o]) for o in fr)), key=lambda r: r[4]),
        overhang=[[round(x / INCH, 3), round(y / INCH, 3)] for x, y in
                  _hull([(p.x, p.y) for o in objs if o not in fr for p in (v.co for v in o.data.vertices)])])

    # 5. the interchange copies
    glb = os.path.join(mdir, stem + ".glb")
    dae = os.path.join(mdir, "sketchup", stem + ".dae")
    _flat_materials(objs)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=False, export_apply=True,
                              export_extras=True, export_yup=True)
    _write_dae(dae, objs)
    rec["sha256"] = {os.path.relpath(p, mdir): sha256(p) for p in (path, glb, dae)}
    for f in sorted(os.listdir(os.path.dirname(dae))):
        if not f.endswith(".dae"):
            rec.setdefault("dae_textures", []).append("sketchup/" + f)

    # 6. the check, in a fresh Blender
    want = dict(rec, expect_frame_in=list(expect_frame_in) if expect_frame_in else None)
    chk = subprocess.run([sys.executable, os.path.join(HERE, "check_export.py"), path, json.dumps(want)],
                         capture_output=True, text=True)
    out = [ln for ln in chk.stdout.splitlines() if ln.startswith(("CHECK", "FAIL"))]
    print("\n".join(out), flush=True)
    if chk.returncode:
        print(chk.stderr[-3000:], flush=True)
        sys.exit("deliver: %s failed its check" % path)
    rec["checked"] = json.loads(next(ln for ln in chk.stdout.splitlines() if ln.startswith("CHECKED "))[8:])

    # 7. the record, then the README, VERSION, library record and footprint
    jp = os.path.join(mdir, "exports.json")
    allr = json.load(open(jp)) if os.path.exists(jp) else {}
    allr[stem] = rec
    json.dump(allr, open(jp, "w"), indent=1, sort_keys=True)
    import model_card
    model_card.write(design)
    return rec

"""The queen bed frame (specs/bed-frame.md): an Arts & Crafts headboard in
quartersawn white oak, fumed: two square posts with pyramid caps, the
headboard's rails through-tenoned and pegged through them, seven wide flat
slats between, the top rail rounded for a separate draped quilt; low side
rails on bed bolts and a straight foot rail, through-
tenoned into two short legs, no posts at the foot. Sizes in sizes.py.

    python3.11 designs/bed-frame/model.py [--quality check|final] [--views corner,foot,head,footend] [--quilt | --bedding]

Writes designs/bed-frame/parts.json and renders/bed-frame-<view>[-quilt].jpg.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender"))
sys.path.insert(0, HERE)
import kit  # noqa: E402
import bpy  # noqa: E402
from sizes import *  # noqa: E402,F401,F403


def through_tenon(name, x_face, outward, y0, y1, z0, z1):
    """A through-tenon's proud end on a post's outer face (x_face), standing
    PROUD out (outward: -1 left, +1 right), its end chamfered."""
    xa, xb = x_face, x_face + outward * PROUD
    return kit.box(name, min(xa, xb), y0, z0, max(xa, xb), y1, z1, "oak", part=False, check=False, round_edges=0.09)


def peg(name, x, y_face, z):
    """A square oak peg through a post's front face, a little proud."""
    h = PEG / 2
    kit.box(name, x - h, y_face - PEG_PROUD, z - h, x + h, y_face, z + h, "peg", part=False, check=False,
            round_edges=0.04)


def bolt_cover(name, x, y_face, z, outward):
    """A brass bed-bolt cover over the bolt's counterbore."""
    kit.cyl(name, 0.8125, y_face, y_face + outward * 0.08, x=x, y=z, key="brass", axis="y", part=False)


def build():
    kit.reset()
    kit.materials({
        "oak": dict(preset="oak", color=kit.hexcolor("#3f2814"), label="QS white oak"),   # fumed, a deep brown
        "peg": dict(preset="oak", color=kit.hexcolor("#2e1c0e"), label="QS white oak"),    # end grain takes it darker
        "poplar": dict(color=kit.hexcolor("#cbb994"), roughness=0.6, label="poplar"),
        "pine": dict(color=kit.hexcolor("#d8c08e"), roughness=0.6, label="2x4 (SPF)"),
        "pine_dark": dict(color=kit.hexcolor("#2a1d12"), roughness=0.7, label="2x4 (SPF), stained dark"),
        "brass": dict(color=kit.hexcolor("#6b5130"), roughness=0.5, metallic=1.0, label="brass"),   # aged, darkened
    })
    # head posts, with their caps
    for nm, x in (("Head post L", 0.0), ("Head post R", W - POST)):
        kit.box(nm, x, L - POST, 0, x + POST, L, POST_BODY, "oak", extra=CAP_RISE, note="with its cap")   # (the cap is cut on its end)
        kit.pyramid(nm + " cap", x, L - POST, x + POST, L, POST_BODY, CAP_RISE, "oak", flat=CAP_FLAT)
    # the headboard: rails through-tenoned into the posts, pegged; slats on stub tenons
    x0, x1 = POST, W - POST
    hb_extra = 2 * (POST + PROUD)
    for nm, (z0, z1), r in (("Headboard bottom rail", HB_BOTTOM, 1 / 16), ("Headboard top rail", HB_TOP, 0.375)):
        kit.box(nm, x0, HB_Y, z0, x1, HB_Y + HB_RAIL_T, z1, "oak", round_edges=r, extra=hb_extra)
        ty = HB_Y + (HB_RAIL_T - HB_TENON_T) / 2
        for side, xf, out in (("L", 0.0, -1), ("R", W, 1)):
            through_tenon("%s tenon %s" % (nm, side), xf, out, ty, ty + HB_TENON_T, z0 + HB_SHOULDER, z1 - HB_SHOULDER)
            for k, zp in enumerate((z0 + HB_SHOULDER + PEG_IN, z1 - HB_SHOULDER - PEG_IN)):
                peg("%s peg %s%d" % (nm, side, k), xf - out * POST / 2, L - POST, zp)
    for i in range(HB_SLATS):
        sx = x0 + HB_GAP + i * (HB_SLAT_W + HB_GAP)
        kit.box("Headboard slat %d" % (i + 1), sx, HB_Y, HB_BOTTOM[1], sx + HB_SLAT_W, HB_Y + SLAT_T, HB_TOP[0],
                "oak", round_edges=0.125, extra=2 * SLAT_TENON[1])
    # the foot: two short capped legs; the rail straight (or arched: FOOT_ARCH), through-tenoned and pegged
    for nm, x in (("Foot leg L", 0.0), ("Foot leg R", W - POST)):
        kit.box(nm, x, 0, 0, x + POST, POST, FOOT_LEG, "oak", extra=CAP_RISE, note="with its cap")
        kit.pyramid(nm + " cap", x, 0, x + POST, POST, FOOT_LEG, CAP_RISE, "oak", flat=CAP_FLAT)
    if FOOT_ARCH > 0:
        kit.prism("Foot rail", foot_rail_profile(), "y", FOOT_IN - RAIL_T, FOOT_IN, "oak", extra=2 * (POST + PROUD))
    else:
        kit.box("Foot rail", POST, FOOT_IN - RAIL_T, FOOT_Z[0], W - POST, FOOT_IN, FOOT_Z[1], "oak", extra=2 * (POST + PROUD))
    ty = FOOT_IN - RAIL_T + (RAIL_T - FOOT_TENON_T) / 2
    for side, xf, out in (("L", 0.0, -1), ("R", W, 1)):
        through_tenon("Foot rail tenon " + side, xf, out, ty, ty + FOOT_TENON_T, *FOOT_TENON_Z)
        for k, zp in enumerate((FOOT_TENON_Z[0] + PEG_IN, FOOT_TENON_Z[1] - PEG_IN)):
            peg("Foot rail peg %s%d" % (side, k), xf - out * POST / 2, 0.0, zp)
    # side rails, bed-bolted to the foot legs and head posts (brass covers at the foot)
    for nm, x in (("Side rail L", RAIL_IN - RAIL_T), ("Side rail R", W - RAIL_IN)):
        kit.box(nm, x, POST, RAIL_Z[0], x + RAIL_T, L - POST, RAIL_Z[1], "oak", extra=2 * STUB[2], note="with stub tenons")
        for k, zb in enumerate(BOLT_Z):
            bolt_cover("%s bolt cover %d" % (nm, k), x + RAIL_T / 2, 0.0, zb, -1)
    # cleats, slats, the center rail on three legs
    ct = CLEAT_TOP
    for nm, x in (("Cleat L", RAIL_IN), ("Cleat R", W - RAIL_IN - CLEAT)):
        kit.box(nm, x, POST, ct - CLEAT, x + CLEAT, L - POST, ct, "pine", round_edges=0)
    gap = (IN_L - SLATS * SLAT_W) / (SLATS + 1)
    for i in range(SLATS):
        y = FOOT_IN + gap + i * (SLAT_W + gap)
        kit.box("Slat %d" % (i + 1), RAIL_IN, y, ct, W - RAIL_IN, y + SLAT_W, SLAT_TOP, "poplar", round_edges=0)
    cx = W / 2
    cr = (cx - CENTER[0] / 2, cx + CENTER[0] / 2)
    kit.box("Center rail", cr[0], FOOT_IN, ct - CENTER[1], cr[1], L - POST, ct, "pine", round_edges=0)
    ends = (FOOT_IN + CENTER_LEG_IN, (FOOT_IN + L - POST) / 2 - CENTER[1] / 2, L - POST - CENTER_LEG_IN - CENTER[1])
    for i, y in enumerate(ends):
        # (stained dark: from low down they can be seen under the foot rail)
        kit.box("Center leg %d" % (i + 1), cr[0], y, 0, cr[1], y + CENTER[1], ct - CENTER[1], "pine_dark", round_edges=0)

    # the builder's dimensions
    kit.dim("", (0, 0, 0), (0, 0, SLAT_TOP), "side", -4)
    kit.dim("", (0, L, HB_TOP[1]), (0, L, POST_BODY + CAP_RISE), "side", 3)
    kit.dim("", (0, L, 0), (0, L, HB_TOP[1]), "side", 7)
    kit.dim("", (0, 0, 0), (0, 0, FOOT_Z[1]), "side", -8)
    kit.dim("", (RAIL_IN, 0, HB_TOP[1]), (W - RAIL_IN, 0, HB_TOP[1]), "front", 5)
    kit.dim("", (POST + HB_GAP, L, HB_BOTTOM[1]), (POST + HB_GAP + HB_SLAT_W, L, HB_BOTTOM[1]), "front", -4)
    kit.dim("", (0, FOOT_IN, 0), (0, L - POST, 0), "top", -4)


def foot_rail_profile(n=24):
    """The foot rail seen from the front, (x, z), anticlockwise: flat for
    FOOT_FLAT from each leg, then its bottom edge arched up FOOT_ARCH, a
    circle's segment."""
    x0, x1 = POST, W - POST
    span = (x1 - x0) - 2 * FOOT_FLAT
    r = (span ** 2 / 4 + FOOT_ARCH ** 2) / (2 * FOOT_ARCH)
    mid = (x0 + x1) / 2
    arch = []
    for k in range(n + 1):
        x = x0 + FOOT_FLAT + span * k / n
        arch.append((x, FOOT_Z[0] + math.sqrt(max(0.0, r ** 2 - (x - mid) ** 2)) - (r - FOOT_ARCH)))
    return [(x0, FOOT_Z[0])] + arch + [(x1, FOOT_Z[0]), (x1, FOOT_Z[1]), (x0, FOOT_Z[1])]


def mattress(sheet="#ece8df"):
    """The mattress, for the renders (not a part); sheet: its cover's color
    (made up, a dark fitted sheet, so no white shows where the coverlet's
    tucked corners meet)."""
    kit.materials({"ticking": dict(color=kit.hexcolor(sheet), roughness=0.9, sheen=0.3)})
    m = kit.box("Mattress", RAIL_IN + CLEAR / 2, FOOT_IN + CLEAR / 2, SLAT_TOP, W - RAIL_IN - CLEAR / 2,
                L - POST - CLEAR / 2, MAT_TOP, "ticking", part=False, check=False, round_edges=2.0)
    m.modifiers["Bevel"].segments = 6
    kit.OBJS.remove(m)
    return m


TEXTURES = os.path.join(HERE, "textures")   # tools/make_fabric.py: our own patterns


def fabric_material(name, png, repeat, color_hint=None, sheen=0.15, roughness=0.85):
    """A cloth material printed with one of tools/make_fabric.py's patterns,
    by the cloth's own UVs; repeat: (times across, times along) the piece."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (repeat[0], repeat[1], 1.0)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(TEXTURES, png), check_existing=True)
    tex.interpolation = "Cubic"
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    hs = nt.nodes.new("ShaderNodeHueSaturation")       # (the bright studio washed the prints pastel)
    hs.inputs["Saturation"].default_value = 1.25
    hs.inputs["Value"].default_value = 0.85
    nt.links.new(tex.outputs["Color"], hs.inputs["Color"])
    nt.links.new(hs.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Sheen Weight"].default_value = sheen
    return m


def cloth(name, size, center, mat, collide, res=1.25, frames=70, mass=0.5, bend=1.0, thick=0.35, pin_head=0.0,
          foot_corners=0.0):
    """A piece of cloth size (x, y) inches, laid flat with its middle at
    center (inches) and dropped onto what's below with Blender's cloth
    simulation; the colliders are cleared again after. pin_head: hold
    that many inches of its head end (+y) still, as if tucked in: a
    coverlet slid off the foot of the bed without it (2026-11-11).
    foot_corners: cut that many inches square out of its two foot corners,
    so the sides and the foot tuck in flat instead of folding out over the
    rails at the corners."""
    I = kit.INCH
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=max(8, int(size[0] / res)),
                                    y_subdivisions=max(8, int(size[1] / res)), size=1.0)
    q = bpy.context.active_object
    q.name = name
    q.scale = (size[0] * I, size[1] * I, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    q.location = tuple(c * I for c in center)
    q.data.materials.append(mat)
    if foot_corners:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(q.data)
        hx, hy, c = size[0] / 2 * I, size[1] / 2 * I, foot_corners * I
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if abs(v.co.x) > hx - c + 1e-6 and v.co.y < -hy + c - 1e-6],
                         context="VERTS")
        bm.to_mesh(q.data)
        bm.free()
    if pin_head:
        vg = q.vertex_groups.new(name="pin")
        top = max(v.co.y for v in q.data.vertices)
        half = min(MAT_W, size[0]) / 2 * I       # (only over the mattress: pinned corners stood out in the air)
        vg.add([v.index for v in q.data.vertices if v.co.y > top - pin_head * I and abs(v.co.x) < half - 2 * I],
               1.0, "REPLACE")
    for o in collide:
        if "Collision" not in o.modifiers:
            o.modifiers.new("Collision", "COLLISION")
        o.collision.thickness_outer = 0.008
        o.collision.cloth_friction = 6.0
    cl = q.modifiers.new("Cloth", "CLOTH")
    st = cl.settings
    st.quality = 8
    st.mass = mass
    st.tension_stiffness = st.compression_stiffness = 30
    st.bending_stiffness = bend
    st.air_damping = 2.0
    if pin_head:
        st.vertex_group_mass = "pin"
    cl.collision_settings.distance_min = 0.004
    cl.collision_settings.collision_quality = 5          # (the throw's ends went through the coverlet)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    cl.point_cache.frame_start, cl.point_cache.frame_end = 1, frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    bpy.context.view_layer.objects.active = q
    bpy.ops.object.modifier_apply(modifier="Cloth")
    sc.frame_set(1)
    for o in collide:
        o.modifiers.remove(o.modifiers["Collision"])
    for p in q.data.polygons:
        p.use_smooth = True
    return q


def lay_on(top, under, gap):
    """Push any of top's points that ended up inside under (cloth on cloth
    collides poorly: the throw's hanging ends went through the coverlet)
    back out onto under's surface, gap inches clear."""
    from mathutils.bvhtree import BVHTree
    um = under.matrix_world        # (its draped sheet itself, before any thickness: normals all outward)
    tree = BVHTree.FromPolygons([um @ v.co for v in under.data.vertices], [tuple(p.vertices) for p in under.data.polygons])
    mw, inv = top.matrix_world, top.matrix_world.inverted()
    moved = 0
    for v in top.data.vertices:
        p = mw @ v.co
        loc, normal, _, dist = tree.find_nearest(p)
        if loc is None or dist > 4 * kit.INCH:
            continue
        side = (p - loc).dot(normal)
        if side < gap * kit.INCH:
            v.co = inv @ (loc + normal * gap * kit.INCH)
            moved += 1
    top.data.update()
    return moved


def finish_cloth(q, thick=0.35, up=False):
    so = q.modifiers.new("Solidify", "SOLIDIFY")
    so.thickness = thick * kit.INCH
    if up:                          # (built up off what it lies on, not down into it)
        so.offset = 1.0
    sub = q.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1


def headboard_cover(collide, mat):
    """The washable cover over the headboard, between the posts: down the
    front to the mattress, down the back to the bottom rail."""
    span = HB_SPAN - 0.75
    length = (HB_TOP[1] - MAT_TOP) + (HB_TOP[1] - HB_BOTTOM[1]) + 6.0
    q = cloth("Headboard cover", (span, length), (W / 2, HB_Y + HB_RAIL_T / 2 - 3.0, HB_TOP[1] + 1.0), mat,
              collide, res=length / 72, frames=80, mass=0.6, bend=2.0)
    finish_cloth(q, 0.4)
    return q


def quilt_material():
    """The first stand-in quilt for the headboard: pieced squares."""
    m = bpy.data.materials.new("Quilt")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (6.0, 6.0, 1.0)
    ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 1.0
    ck.inputs["Color1"].default_value = kit.hexcolor("#8a6a2a") + (1.0,)    # ochre
    ck.inputs["Color2"].default_value = kit.hexcolor("#4f5e3a") + (1.0,)    # sage green
    br = nt.nodes.new("ShaderNodeTexBrick")                                 # the stitched seams
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.005
    br.inputs["Brick Width"].default_value = 0.5
    br.inputs["Row Height"].default_value = 0.5
    br.offset = 0.0
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], ck.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
    nt.links.new(ck.outputs["Color"], br.inputs["Color1"])
    nt.links.new(ck.outputs["Color"], br.inputs["Color2"])
    br.inputs["Mortar"].default_value = kit.hexcolor("#a89466") + (1.0,)
    nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Sheen Weight"].default_value = 0.6
    return m


def quilt(collide):
    """The headboard covered with the stand-in quilt (--quilt)."""
    return headboard_cover(collide, quilt_material())


def pillow(name, cx, cy, cz, tilt, w=PILLOW[0], d=PILLOW[1], t=PILLOW[2], seed=0, mat=None):
    """A bed pillow: plump in the middle, thin at its seamed edge. Its
    middle at (cx, cy, cz) inches, tilted up toward the headboard by tilt
    degrees (0 flat, 90 standing)."""
    import bmesh
    import random
    rnd = random.Random(seed)
    n = 36
    bm = bmesh.new()
    rows = {}
    for side in (1, -1):
        for i in range(n + 1):
            for j in range(n + 1):
                u, v = -1 + 2 * i / n, -1 + 2 * j / n
                edge = i in (0, n) or j in (0, n)
                f = (max(0.0, 1 - abs(u) ** 2.2) * max(0.0, 1 - abs(v) ** 2.2)) ** 0.6   # a soft dome
                # the corners pulled in a little, the faces slightly uneven
                x = u * w / 2 * (1 - 0.05 * (1 - abs(v)) ** 2 * 0)
                y = v * d / 2
                z = side * t / 2 * f * (1 + 0.04 * rnd.uniform(-1, 1) * f)
                if edge and side < 0:
                    rows[(side, i, j)] = rows[(1, i, j)]
                else:
                    rows[(side, i, j)] = bm.verts.new((x, y, z))
    for side in (1, -1):
        for i in range(n):
            for j in range(n):
                q = [rows[(side, i, j)], rows[(side, i + 1, j)], rows[(side, i + 1, j + 1)], rows[(side, i, j + 1)]]
                bm.faces.new(q if side > 0 else list(reversed(q)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    for vert in bm.verts:
        vert.co *= kit.INCH
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (math.radians(tilt), 0.0, math.radians(rnd.uniform(-2.5, 2.5)))
    o.location = (cx * kit.INCH, cy * kit.INCH, cz * kit.INCH)
    sub = o.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    return o


def pillow_material():
    m = bpy.data.materials.new("Pillowcase")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = kit.hexcolor("#f4f2ec") + (1.0,)
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Sheen Weight"].default_value = 0.5
    nz = nt.nodes.new("ShaderNodeTexNoise")              # soft wrinkles
    nz.inputs["Scale"].default_value = 60.0
    nz.inputs["Detail"].default_value = 4.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def folded_blanket(cov):
    """A blanket folded in thirds across the foot: flat across the top of
    the bed, rounded over the mattress's edges, hanging straight down each
    side to just above the rails, its hems a little uneven. Built as a
    swept profile (x, z) along the bed (y), then laid onto the coverlet."""
    import bmesh
    I = kit.INCH
    tw, tl = THROW
    gap = 0.3                                    # over the coverlet, as draped (its sides bulge out:
    # a blanket shaped to the mattress was pushed about and crumpled, 2026-11-11)
    y0 = FOOT_IN + THROW_FROM_FOOT
    dg = bpy.context.evaluated_depsgraph_get()
    ev = cov.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co / I for v in ev.data.vertices]
    near = [p for p in pts if y0 - 1 <= p.y <= y0 + tl + 1 and p.z > MAT_TOP - THROW_DROP - 1]
    x0 = min(p.x for p in near) - gap
    x1 = max(p.x for p in near) + gap
    top = max(p.z for p in near if abs(p.x - W / 2) < 20) + gap
    r = 2.5                                      # the rounded edge it folds over
    drop = THROW_DROP
    path = []                                    # (x, z) along the blanket, left hem to right hem
    for k in range(13):                          # down the left side
        path.append((x0, top - r - (drop - r) * (1 - k / 12)))
    for k in range(1, 9):                        # over the left edge
        a = math.pi - (math.pi / 2) * k / 8
        path.append((x0 + r + r * math.cos(a), top - r + r * math.sin(a)))
    n = 40
    for k in range(1, n):                        # across the top
        path.append((x0 + r + (x1 - x0 - 2 * r) * k / n, top))
    for k in range(0, 9):                        # over the right edge
        a = math.pi / 2 - (math.pi / 2) * k / 8
        path.append((x1 - r + r * math.cos(a), top - r + r * math.sin(a)))
    for k in range(1, 13):                       # down the right side
        path.append((x1, top - r - (drop - r) * k / 12))
    seg = [0.0]
    for (ax, az), (bx, bz) in zip(path, path[1:]):
        seg.append(seg[-1] + math.hypot(bx - ax, bz - az))
    rows = 24
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    grid = []
    for j in range(rows + 1):
        t = j / rows
        y = y0 + tl * t
        row = []
        for i, (x, z) in enumerate(path):
            s = seg[i] / seg[-1]
            hang = max(0.0, (top - r) - z)       # how far down a side this point is
            # the hems ripple a little, and the top sags a touch between the folds
            dx = (0.25 * math.sin(7.0 * t + 3.0 * s) * hang / drop) * (-1 if x < W / 2 else 1)
            dz = -0.08 * math.sin(math.pi * t) if hang == 0 else 0.0
            row.append(bm.verts.new(((x + dx) * I, y * I, (z + dz) * I)))
        grid.append(row)
    hems = ([g[0].co.copy() for g in grid], [g[-1].co.copy() for g in grid])   # (meters) left, right
    for j in range(rows):
        for i in range(len(path) - 1):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (seg[ii] / seg[-1], jj / rows)
    me = bpy.data.meshes.new("Throw")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new("Throw", me)
    bpy.context.scene.collection.objects.link(o)
    m = fabric_material("Throw", "kilim.png", (seg[-1] / 10.0, 1.0), sheen=0.12)
    wool(m, (seg[-1] / WOOL_REPEAT, tl / WOOL_REPEAT))
    o.data.materials.append(m)
    # (normals up/out, so its thickness builds outward off the coverlet)
    if o.data.polygons[len(o.data.polygons) // 2].normal.z < 0:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
    finish_cloth(o, THROW_THICK, up=True)
    o.modifiers["Smooth"].levels = o.modifiers["Smooth"].render_levels = 2    # (a soft folded edge)
    fringe(hems, tl, top - r)
    return o


def wool(m, repeat):
    """Real wool under a printed material: Poly Haven's Caban (CC0), its
    nap and weave as a normal map and its shading darkening the color a
    little, at its own scale (WOOL_REPEAT inches)."""
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes["Texture Coordinate"]
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (repeat[0], repeat[1], 1.0)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def img(name, color):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEXTURES, name), check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.2
    nt.links.new(img("caban_nor_gl_1k.jpg", False).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.35
    base = bsdf.inputs["Base Color"].links[0].from_socket
    nt.links.new(base, mix.inputs["A"])
    nt.links.new(img("caban_ao_1k.jpg", True).outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Sheen Roughness"].default_value = 0.6


def fringe(hems, width, top_of_hang):
    """A short wool fringe along both hanging hems: strands about every
    FRINGE[1] inches, FRINGE[0] long, a little uneven."""
    import bmesh
    import random
    I = kit.INCH
    rnd = random.Random(11)
    flen, step = FRINGE
    bm = bmesh.new()
    for side, pts in ((-1, hems[0]), (1, hems[1])):
        n = int(width / step)
        for k in range(n):
            t = (k + 0.5) / n * (len(pts) - 1)
            a, b = pts[int(t)], pts[min(int(t) + 1, len(pts) - 1)]
            p = a.lerp(b, t - int(t))
            p.x += side * THROW_THICK / 2 * I
            ln = flen * rnd.uniform(0.85, 1.1) * I
            sway = side * rnd.uniform(-0.05, 0.3) * I + 0 * I
            twist = rnd.uniform(-0.25, 0.25) * I              # (strands lie every which way, softly)
            r = 0.045 * I
            ring0 = [bm.verts.new((p.x + r * math.cos(q), p.y + r * math.sin(q), p.z)) for q in (0, 1.57, 3.14, 4.71)]
            ring1 = [bm.verts.new((p.x + sway + r * 0.7 * math.cos(q), p.y + twist + r * 0.7 * math.sin(q), p.z - ln))
                     for q in (0, 1.57, 3.14, 4.71)]
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
    me = bpy.data.meshes.new("Throw fringe")
    bm.to_mesh(me)
    bm.free()
    f = bpy.data.objects.new("Throw fringe", me)
    bpy.context.scene.collection.objects.link(f)
    fm = bpy.data.materials.new("Fringe")
    fm.use_nodes = True
    b = fm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = kit.hexcolor("#c9ae7c") + (1.0,)
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Sheen Weight"].default_value = 0.5
    f.data.materials.append(fm)
    return f


def relax(o, factor=0.5, repeat=4):
    """Smooth a draped cloth's mesh a little (the throw looked torn where
    lay_on had pushed single points out)."""
    m = o.modifiers.new("Relax", "SMOOTH")
    m.factor, m.iterations = factor, repeat
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=m.name)


def bedding(frame, mat):
    """Made up after the client's picture (2026-11-11): Morris's Strawberry
    Thief over the headboard, an indigo block-print coverlet tucked in
    between the mattress and the rails, a kilim throw across the foot, and
    two pillows stacked flat at the head of each side."""
    hb = [o for o in frame if o.name.startswith(("Headboard", "Head post"))]
    posts = [o for o in frame if o.name.startswith("Head post")]
    # the coverlet: only the mattress (and the head posts) stop it, so its
    # edges fall straight down inside the rails, tucked in
    cw, cl_ = COVERLET
    cov = cloth("Coverlet", (cw, cl_), (W / 2, L - POST - 1.0 - cl_ / 2, MAT_TOP + 1.0),
                fabric_material("Coverlet", "blockprint.png", (cw / 6.0, cl_ / 6.0)), posts + [mat], frames=80, mass=0.5,
                bend=0.8, pin_head=3.0, foot_corners=COVERLET_CORNER)
    finish_cloth(cov, 0.3)          # (its thickness first: the throw fell through a bare sheet)
    # the throw: a blanket folded in thirds, shaped rather than simulated
    # (simulated, it crumpled and curled at its ends like a torn runner)
    folded_blanket(cov)
    span = HB_SPAN - 0.75
    length = (HB_TOP[1] - MAT_TOP) + (HB_TOP[1] - HB_BOTTOM[1]) + 6.0
    headboard_cover(hb + [mat], fabric_material("Headboard cover", "morris-strawberry-thief.jpg",
                                               (span / STRAWBERRY_REPEAT[0], length / STRAWBERRY_REPEAT[1])))
    # pillows: two stacked flat at the head of each side
    pm = pillow_material()
    w, d, t = PILLOW
    for k, side in enumerate((-1, 1)):
        x = W / 2 + side * (w / 2 + 0.25)
        y = HB_Y - 4.5 - d / 2
        for j in range(PILLOW_STACK):
            pillow("Pillow %d-%d" % (k, j), x + side * 0.4 * j, y + 0.6 * j, MAT_TOP + 0.5 + t * 0.42 + j * t * 0.78,
                   2.0 + 2.0 * j, seed=3 * k + j, mat=pm)


def export(path):
    """The bed alone, for other models to place (tools/blender/assets.py
    place(), or File > Append in Blender): every object named "Bed ...",
    no studio, lights or camera; its images packed in. Blender meters,
    the floor at z 0, the foot toward -y, the headboard toward +y."""
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        if not o.name.startswith("Bed "):
            o.name = "Bed " + o.name
    bpy.ops.file.pack_all()
    kit.save_blend(path)
    print("EXPORT %s (%d objects)" % (path, len(bpy.data.objects)), flush=True)


VIEWS = {
    # name: (azimuth, elevation, lens)  -- seen from the foot of the bed
    "corner": (-38.0, 20.0, 40.0),
    "foot": (0.0, 14.0, 50.0),
    "bedroom": (-28.0, 9.0, 32.0),        # as the client's picture is taken: low, from the foot's left
}


def head_close():
    """Close on the headboard's left post: its cap, the top rail's tenon and pegs."""
    kit.camera((-26.0, L - 38.0, 50.0), (POST / 2, L - 2.0, 52.0), lens=45.0)


def foot_close():
    """The foot's left corner: the foot rail, its tenon and pegs, the bolt covers."""
    kit.camera((-30.0, -34.0, 26.0), (8.0, 1.0, 11.0), lens=40.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="check", choices=("check", "final"))
    ap.add_argument("--views", default="corner,foot")
    ap.add_argument("--quilt", action="store_true")
    ap.add_argument("--bedding", action="store_true", help="made up: printed headboard cover, coverlet, throw, pillows")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--export", metavar="BLEND", help="save the bed (no studio, lights or camera) to a .blend and stop")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    build()
    kit.check_joints()
    kit.check_overlaps()
    kit.write_parts(os.path.join(HERE, "parts.json"), name="Queen bed frame",
                    notes=["Quartersawn white oak, fumed; poplar slats; 2x4 cleats and center rail. The headboard's rails "
                           "and the foot rail are through-tenoned and pegged; side rails on bed bolts. Joinery: bed-frame-joinery.svg.",
                           "Mattress 60\" x 80\" x 11\" on the slats (no box spring); its top 24\" from the floor."])
    if a.no_render:
        return
    lo, hi = kit.bounds()
    mat = mattress("#1c2c4a" if a.bedding else "#ece8df")
    if a.bedding:
        bedding(list(kit.OBJS), mat)
    elif a.quilt:
        hb = [o for o in kit.OBJS if o.name.startswith(("Headboard", "Head post"))]
        quilt(hb + [mat])
    if a.export:
        export(a.export)
        return
    kit.studio(wall_y=L + 0.5, radius=1.0)
    suffix = "-bedding" if a.bedding else "-quilt" if a.quilt else ""
    for v in a.views.split(","):
        if v == "head":
            head_close()
        elif v == "footend":
            foot_close()
        else:
            az, el, lens = VIEWS[v]
            kit.camera_auto(azimuth=az, elevation=el, lens=lens, target=[(lo[k] + hi[k]) / 2 for k in range(3)])
        kit.render(os.path.join(HERE, "renders", "bed-frame-%s%s.jpg" % (v, suffix)), quality=a.quality)


if __name__ == "__main__":
    main()

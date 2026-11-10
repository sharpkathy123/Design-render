"""The queen bed frame (specs/bed-frame.md): an Arts & Crafts headboard in
quartersawn white oak, fumed: two square posts with pyramid caps, the
headboard's rails through-tenoned and pegged through them, seven wide flat
slats between, the top rail rounded for a separate draped quilt; low side
rails on bed bolts and a foot rail with an arched bottom edge, through-
tenoned into two short legs, no posts at the foot. Sizes in sizes.py.

    python3.11 designs/bed-frame/model.py [--quality check|final] [--views corner,foot,head,footend] [--quilt]

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
        "brass": dict(preset="brass", label="brass"),
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
    # the foot: two legs no higher than the rail; the rail arched, through-tenoned and pegged
    for nm, x in (("Foot leg L", 0.0), ("Foot leg R", W - POST)):
        kit.box(nm, x, 0, 0, x + POST, POST, FOOT_LEG, "oak", extra=CAP_RISE, note="with its cap")
        kit.pyramid(nm + " cap", x, 0, x + POST, POST, FOOT_LEG, CAP_RISE, "oak", flat=CAP_FLAT)
    kit.prism("Foot rail", foot_rail_profile(), "y", FOOT_IN - RAIL_T, FOOT_IN, "oak", extra=2 * (POST + PROUD))
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
        # (stained dark: they show through the foot rail's arch)
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


def mattress():
    """The mattress, for the renders (not a part)."""
    kit.materials({"ticking": dict(color=kit.hexcolor("#ece8df"), roughness=0.9, sheen=0.5)})
    m = kit.box("Mattress", RAIL_IN + CLEAR / 2, FOOT_IN + CLEAR / 2, SLAT_TOP, W - RAIL_IN - CLEAR / 2,
                L - POST - CLEAR / 2, MAT_TOP, "ticking", part=False, check=False, round_edges=2.0)
    m.modifiers["Bevel"].segments = 6
    kit.OBJS.remove(m)
    return m


def quilt_material():
    """A stand-in quilt in Arts & Crafts colors: pieced squares, soft."""
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
    """A quilt laid over the headboard with Blender's cloth simulation:
    sized to cover it between the posts, down the front to the mattress
    and down the back to the bottom rail."""
    I = kit.INCH
    span = HB_SPAN - 0.75                      # between the posts, a little play
    length = (HB_TOP[1] - MAT_TOP) + (HB_TOP[1] - HB_BOTTOM[1]) + 6.0
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=72, size=1.0)
    q = bpy.context.active_object
    q.name = "Quilt"
    q.scale = (span * I, length * I, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    q.location = (W / 2 * I, (HB_Y + HB_RAIL_T / 2 - 3.0) * I, (HB_TOP[1] + 1.0) * I)
    q.data.materials.append(quilt_material())
    for o in collide:
        o.modifiers.new("Collision", "COLLISION")
        o.collision.thickness_outer = 0.004
        o.collision.cloth_friction = 8.0
    cl = q.modifiers.new("Cloth", "CLOTH")
    s = cl.settings
    s.quality = 8
    s.mass = 0.6
    s.tension_stiffness = s.compression_stiffness = 30
    s.bending_stiffness = 2.0
    s.air_damping = 2.0
    cl.collision_settings.distance_min = 0.004
    sc = bpy.context.scene
    frames = 80
    sc.frame_start, sc.frame_end = 1, frames
    cl.point_cache.frame_end = frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    bpy.context.view_layer.objects.active = q
    bpy.ops.object.modifier_apply(modifier="Cloth")
    so = q.modifiers.new("Solidify", "SOLIDIFY")
    so.thickness = 0.4 * I
    sub = q.modifiers.new("Smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    for p in q.data.polygons:
        p.use_smooth = True
    for o in collide:
        o.modifiers.remove(o.modifiers["Collision"])
    return q


VIEWS = {
    # name: (azimuth, elevation, lens)  -- seen from the foot of the bed
    "corner": (-38.0, 20.0, 40.0),
    "foot": (0.0, 14.0, 50.0),
}


def head_close():
    """Close on the headboard's left post: its cap, the top rail's tenon and pegs."""
    kit.camera((-26.0, L - 38.0, 50.0), (POST / 2, L - 2.0, 52.0), lens=45.0)


def foot_close():
    """The foot's left corner: the arched rail, its tenon and pegs, the bolt covers."""
    kit.camera((-30.0, -34.0, 26.0), (8.0, 1.0, 11.0), lens=40.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="check", choices=("check", "final"))
    ap.add_argument("--views", default="corner,foot")
    ap.add_argument("--quilt", action="store_true")
    ap.add_argument("--no-render", action="store_true")
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
    mat = mattress()
    if a.quilt:
        hb = [o for o in kit.OBJS if o.name.startswith(("Headboard", "Head post"))]
        quilt(hb + [mat])
    kit.studio(wall_y=L + 0.5, radius=1.0)
    suffix = "-quilt" if a.quilt else ""
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

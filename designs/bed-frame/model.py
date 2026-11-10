"""The queen bed frame (specs/bed-frame.md): an Arts & Crafts headboard in
quartersawn white oak, two square posts with pyramid caps and wide flat
slats between a rounded top rail and a bottom rail, made to be covered by a
separate quilt; low side rails and a foot rail with no posts at the foot.

    python3.11 designs/bed-frame/model.py [--quality check|final] [--views foot,corner,head] [--quilt]

Writes designs/bed-frame/parts.json and renders/bed-frame-<view>[-quilt].jpg.
Inches; x across the bed from the left as you face the headboard from the
foot, y from the foot to the head, z up from the floor.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender"))
import kit  # noqa: E402
import bpy  # noqa: E402

# --- the mattress (spec: queen; thickness and height ours, as asked) ------
MAT_W, MAT_L = 60.0, 80.0          # queen
CLEAR = 0.5                        # room round the mattress, each way in all
MAT_T = 11.0                       # a usual mattress, on slats: no box spring
SLAT_TOP = 13.0                    # so the mattress top is at 24", an easy height to sit on

# --- stock: quartersawn white oak (spec), poplar where nothing shows ------
POST = 2.75                        # head posts, 12/4 dressed (period beds: 2 1/2" to 3")
RAIL_T = 0.875                     # side and foot rails, 5/4 dressed to 7/8"
HB_RAIL_T = 1.25                   # the headboard's rails: 6/4 dressed
SLAT_T = 0.75                      # the headboard's slats: 4/4 dressed
REVEAL = 0.25                      # the headboard's face set back from the posts' faces

# --- heights ----------------------------------------------------------------
RAIL_Z = (8.0, 14.0)               # side rails, 6" tall; their top 1" above the slats holds the mattress
FOOT_Z = (8.0, 16.0)               # the foot rail: 3" above the slats, the mattress kept in place (spec: no posts)
HB_BOTTOM = (14.0, 19.0)           # the headboard's bottom rail, behind the mattress and pillows
HB_TOP = (44.5, 49.0)              # the top rail: 25" above the mattress top, at the shoulders sitting up
POST_BODY = 52.5                   # posts stand 3 1/2" above the top rail (above the folded quilt), and the cap
CAP_RISE = 0.625                   # a shallow pyramid cap, as Stickley's and Limbert's beds have
HB_SLATS, HB_GAP = 7, 1.0          # seven wide slats, 1" apart: a flat back to lean on, the fleck showing

# --- the support (poplar) ---------------------------------------------------
CLEAT = 1.5                        # 1 1/2" square cleats screwed inside the side rails
SLATS, SLAT_W = 13, 3.5            # 1x4 slats, about 2 1/2" apart
CENTER = (1.5, 3.5)                # a 2x4 on edge down the middle, on three legs (a queen needs it)

# --- the plan -------------------------------------------------------------
IN_W = MAT_W + CLEAR               # between the side rails
IN_L = MAT_L + CLEAR               # from the foot rail to the headboard
RAIL_IN = (POST - RAIL_T) / 2 + RAIL_T      # a rail centered on its post: its inner face this far in
W = IN_W + 2 * RAIL_IN
FOOT_IN = RAIL_IN                  # the foot rail likewise centered on the foot legs
L = FOOT_IN + IN_L + POST          # the mattress runs to the head posts' front faces
HB_Y = L - POST + REVEAL           # the headboard's front face


def build():
    kit.reset()
    kit.materials({
        "oak": dict(preset="oak", color=kit.hexcolor("#4a2e17"), label="QS white oak"),   # fumed, medium brown
        "poplar": dict(color=kit.hexcolor("#cbb994"), roughness=0.6, label="poplar"),
    })
    # head posts, with their caps
    for nm, x in (("Head post L", 0.0), ("Head post R", W - POST)):
        kit.box(nm, x, L - POST, 0, x + POST, L, POST_BODY, "oak")
        kit.pyramid(nm + " cap", x, L - POST, x + POST, L, POST_BODY, CAP_RISE, "oak", flat=0.25)
    # the headboard
    x0, x1 = POST, W - POST
    kit.box("Headboard bottom rail", x0, HB_Y, HB_BOTTOM[0], x1, HB_Y + HB_RAIL_T, HB_BOTTOM[1], "oak")
    kit.box("Headboard top rail", x0, HB_Y, HB_TOP[0], x1, HB_Y + HB_RAIL_T, HB_TOP[1], "oak",
            round_edges=0.375)
    sw = ((x1 - x0) - (HB_SLATS + 1) * HB_GAP) / HB_SLATS
    for i in range(HB_SLATS):
        sx = x0 + HB_GAP + i * (sw + HB_GAP)
        kit.box("Headboard slat %d" % (i + 1), sx, HB_Y, HB_BOTTOM[1], sx + sw, HB_Y + SLAT_T, HB_TOP[0], "oak",
                round_edges=0.125)
    # the foot: two legs no higher than the rail, and the rail between
    for nm, x in (("Foot leg L", 0.0), ("Foot leg R", W - POST)):
        kit.box(nm, x, 0, 0, x + POST, POST, FOOT_Z[1], "oak", round_edges=0.125)
    kit.box("Foot rail", POST, FOOT_IN - RAIL_T, FOOT_Z[0], W - POST, FOOT_IN, FOOT_Z[1], "oak")
    # side rails, from the foot legs to the head posts (bed-rail fasteners)
    for nm, x in (("Side rail L", RAIL_IN - RAIL_T), ("Side rail R", W - RAIL_IN)):
        kit.box(nm, x, POST, RAIL_Z[0], x + RAIL_T, L - POST, RAIL_Z[1], "oak")
    # cleats and slats
    ct = SLAT_TOP - SLAT_T
    for nm, x in (("Cleat L", RAIL_IN), ("Cleat R", W - RAIL_IN - CLEAT)):
        kit.box(nm, x, POST, ct - CLEAT, x + CLEAT, L - POST, ct, "poplar", round_edges=0)
    gap = (IN_L - SLATS * SLAT_W) / (SLATS + 1)
    for i in range(SLATS):
        y = FOOT_IN + gap + i * (SLAT_W + gap)
        kit.box("Slat %d" % (i + 1), RAIL_IN, y, ct, W - RAIL_IN, y + SLAT_W, SLAT_TOP, "poplar", round_edges=0)
    # the center rail, on three legs
    cx = W / 2
    cr = (cx - CENTER[0] / 2, cx + CENTER[0] / 2)
    kit.box("Center rail", cr[0], FOOT_IN, ct - CENTER[1], cr[1], L - POST, ct, "poplar", round_edges=0)
    ends = (FOOT_IN + 12.0, (FOOT_IN + L - POST) / 2 - CENTER[1] / 2, L - POST - 12.0 - CENTER[1])   # (set in, out of sight)
    for i, y in enumerate(ends):
        kit.box("Center leg %d" % (i + 1), cr[0], y, 0, cr[1], y + CENTER[1], ct - CENTER[1], "poplar", round_edges=0)

    # the builder's dimensions
    kit.dim("", (0, 0, 0), (0, 0, SLAT_TOP), "side", -4)
    kit.dim("", (0, L, HB_TOP[1]), (0, L, POST_BODY + CAP_RISE), "side", 3)
    kit.dim("", (0, L, 0), (0, L, HB_TOP[1]), "side", 7)
    kit.dim("", (0, 0, 0), (0, 0, FOOT_Z[1]), "side", -8)
    kit.dim("", (RAIL_IN, 0, HB_TOP[1]), (W - RAIL_IN, 0, HB_TOP[1]), "front", 4)
    kit.dim("", (POST + HB_GAP, L, HB_BOTTOM[1]), (POST + HB_GAP + sw, L, HB_BOTTOM[1]), "front", -4)
    kit.dim("", (0, FOOT_IN, 0), (0, L - POST, 0), "top", -4)


def mattress():
    """The mattress, for the renders (not a part)."""
    kit.materials({"ticking": dict(color=kit.hexcolor("#ece8df"), roughness=0.9, sheen=0.5)})
    m = kit.box("Mattress", RAIL_IN + CLEAR / 2, FOOT_IN + CLEAR / 2, SLAT_TOP, W - RAIL_IN - CLEAR / 2,
                L - POST - CLEAR / 2, SLAT_TOP + MAT_T, "ticking", part=False, round_edges=2.0)
    m.modifiers["Bevel"].segments = 6
    kit.OBJS.remove(m)
    return m


def quilt_material():
    """A quilt in Arts & Crafts colors: a pieced square pattern, soft."""
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
    span = W - 2 * POST - 0.75                 # between the posts, a little play
    length = (HB_TOP[1] - SLAT_TOP - MAT_T) + (HB_TOP[1] - HB_BOTTOM[1]) + 6.0
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=64, size=1.0)
    q = bpy.context.active_object
    q.name = "Quilt"
    q.scale = (span * I, length * I, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    # start it laid flat, 1" above the top rail, a little more down the front
    q.location = (W / 2 * I, (HB_Y + HB_RAIL_T / 2 - 3.0) * I, (HB_TOP[1] + 1.0) * I)
    q.data.materials.append(quilt_material())
    for o in collide:
        c = o.modifiers.new("Collision", "COLLISION")
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
    cl.collision_settings.use_self_collision = False
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 70
    cl.point_cache.frame_end = 70
    for f in range(1, 71):
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
    "side": (-80.0, 8.0, 50.0),
}


def head_close():
    """Close on the headboard's left post, its cap and the top rail."""
    kit.camera((-18.0, L - 40.0, 44.0), (POST + 6.0, L - 1.0, 42.0), lens=45.0)


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
                    notes=["Quartersawn white oak, poplar for the cleats, slats and center rail. "
                           "Headboard joints mortise and tenon; side rails on bed-rail fasteners.",
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
        else:
            az, el, lens = VIEWS[v]
            kit.camera_auto(azimuth=az, elevation=el, lens=lens, target=[(lo[k] + hi[k]) / 2 for k in range(3)])
        kit.render(os.path.join(HERE, "renders", "bed-frame-%s%s.jpg" % (v, suffix)), quality=a.quality)


if __name__ == "__main__":
    main()

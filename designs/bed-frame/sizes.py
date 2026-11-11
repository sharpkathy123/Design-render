"""Every size of the queen bed frame, in inches, in one place: the model
(model.py), the joinery sheet (draw_joinery.py) and BUILD.md's numbers all
come from here. specs/bed-frame.md has the client's answers they rest on.

x across the bed from the left as you face the headboard from the foot,
y from the foot to the head, z up from the floor.
"""

# --- the mattress -------------------------------------------------------
MAT_W, MAT_L = 60.0, 80.0          # queen
CLEAR = 0.5                        # room round the mattress, each way in all
MAT_T = 11.0                       # a usual mattress, on slats: no box spring
SLAT_TOP = 13.0                    # so the mattress top is at 24", an easy height to sit on
MAT_TOP = SLAT_TOP + MAT_T

# --- stock: quartersawn white oak, poplar and 2x4s where nothing shows -----
POST = 2.75                        # head posts and foot legs: two 6/4 boards glued up
RAIL_T = 0.875                     # side and foot rails, 5/4 dressed to 7/8"
HB_RAIL_T = 1.25                   # the headboard's rails: 6/4 dressed to 1 1/4"
SLAT_T = 0.75                      # the headboard's slats: 4/4 dressed to 3/4"
REVEAL = 0.25                      # the headboard's face set back from the posts' faces

# --- heights ------------------------------------------------------------
RAIL_Z = (8.0, 14.0)               # side rails, 6": their top 1" above the slats holds the mattress
FOOT_Z = (8.0, 16.0)               # the foot rail, 8" at its ends: 3" above the slats keeps the mattress in
FOOT_LEG = FOOT_Z[1] + 1.0          # the foot legs stand 1" above the rail, capped like the head posts:
                                   # short posts, as period beds had (client, 2026-11-10: "more authentic")
FOOT_ARCH = 0.0                    # straight: the arch (1 1/2") showed the center support under the
                                   # bed (client, 2026-11-11); set it to arch the bottom edge again
FOOT_FLAT = 3.0                    # (with an arch) flat for 3" from each leg before it starts
HB_BOTTOM = (14.0, 19.0)           # the headboard's bottom rail, 5", behind the mattress and pillows
HB_TOP = (51.5, 56.0)              # the top rail, 4 1/2": 32" above the mattress top, for a tall person lounging
POST_BODY = 59.5                   # posts stand 3 1/2" above the top rail (above the folded quilt), then the cap
CAP_RISE = 0.625                   # a shallow pyramid cap
CAP_FLAT = 0.25
HB_SLATS, HB_GAP = 7, 1.0          # seven wide flat slats, 1" apart

# --- joinery ------------------------------------------------------------
PROUD = 0.375                      # through-tenons stand this far out of the posts' outer faces, chamfered
HB_TENON_T = 0.5                   # the headboard rails' through-tenons, 1/2" thick (rail 1 1/4")
HB_SHOULDER = 0.5                  # their shoulders top and bottom
FOOT_TENON_T = 0.375               # the foot rail's through-tenons, 3/8" thick (rail 7/8")
FOOT_TENON_Z = (10.5, 15.5)        # and 5" tall, above the bed bolt (which crosses the leg below it)
SLAT_TENON = (0.375, 0.75, 0.5)    # the slats' stub tenons: thick, long, shoulder each side
PEG = 0.375                        # square oak pegs through the posts' faces into the tenons
PEG_PROUD = 0.0625
PEG_IN = 0.75                      # each peg this far in from its tenon's edge
BOLT_Z = (9.25,)                   # one bed bolt at each side-rail end (3/8" x 6"), as period beds have,
                                   # below the cleat so its nut hole can be reached, below the foot rail's tenon
BOLT_NUT = (3.25, 1.0, 0.75)       # its nut hole, from the rail's inside face: center from the rail end, diameter, depth
STUB = (0.375, 3.0, 0.5, 10.5)     # a stub tenon on each side-rail end, in a mortise in the post: thick, tall, long, bottom z
BOLT_LEN = 6.0
BOLT_COUNTERBORE = (1.0, 0.5)      # the head's recess in the post: diameter, depth (a brass cover over it)

# --- the support --------------------------------------------------------
CLEAT = 1.5                        # 1 1/2" square cleats, ripped from a 2x4, screwed inside the side rails
SLATS, SLAT_W = 13, 3.5            # poplar 1x4 slats, about 2 1/2" apart
CENTER = (1.5, 3.5)                # a 2x4 on edge down the middle, on three 2x4 legs
CENTER_LEG_IN = 12.0               # its end legs set in from the ends, out of sight

# --- bedding, for the renders (the client's picture, 2026-11-11) ------------
COVERLET_DROP = 10.0               # down each side and the foot, tucked in between the mattress and
                                   # the rails (client, 2026-11-11); its foot corners cut out square,
COVERLET_CORNER = COVERLET_DROP    # as wide as the drop (8" left loose flaps at the foot, 2026-11-11)
COVERLET = (MAT_W + 2 * COVERLET_DROP + 1.0, MAT_L + COVERLET_DROP)   # across, along
THROW_DROP = 8.5                   # a folded blanket across the foot, hanging to just above the rails
THROW = (MAT_W + 2 * THROW_DROP + 2.0, 20.0)   # across, along: folded in thirds (client, 2026-11-11)
THROW_THICK = 0.8                  # three layers of a wool blanket
THROW_FROM_FOOT = 7.0              # its near edge this far up the bed from the foot rail
PILLOW = (28.0, 19.0, 7.0)         # standard pillows: wide, deep, plump
PILLOW_STACK = 2                   # two stacked flat at the head of each side (client, 2026-11-11)
STRAWBERRY_REPEAT = (18.0, 19.6)   # Morris's Strawberry Thief, one repeat across and down, inches

# --- the plan (worked out) ----------------------------------------------
IN_W = MAT_W + CLEAR               # between the side rails
IN_L = MAT_L + CLEAR               # from the foot rail to the head posts
RAIL_IN = (POST - RAIL_T) / 2 + RAIL_T      # a rail centered on its post: its inner face this far in
W = IN_W + 2 * RAIL_IN
FOOT_IN = RAIL_IN                  # the foot rail likewise centered on the foot legs
L = FOOT_IN + IN_L + POST          # the mattress runs to the head posts' front faces
HB_Y = L - POST + REVEAL           # the headboard's front face
HB_SPAN = W - 2 * POST             # between the posts
HB_SLAT_W = (HB_SPAN - (HB_SLATS + 1) * HB_GAP) / HB_SLATS
CLEAT_TOP = SLAT_TOP - SLAT_T


def frac(x, den=16):
    """Inches to the nearest 1/16, as a shop drawing writes it: 29 3/4"."""
    import math
    n = int(round(abs(x) * den))
    whole, rest = divmod(n, den)
    g = math.gcd(rest, den) if rest else den
    s = ("%d" % whole if whole or not rest else "") + ((" " if whole else "") + "%d/%d" % (rest // g, den // g) if rest else "")
    return ("-" if x < 0 else "") + s + '"'

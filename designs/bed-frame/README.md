# Queen bed frame

From [specs/bed-frame.md](../../specs/bed-frame.md). Built by
[model.py](model.py) from [sizes.py](sizes.py)
(`python3.11 designs/bed-frame/model.py --views corner,foot,head,footend`;
add `--quilt` for the draped quilt; `python3 designs/bed-frame/draw_joinery.py`
and `python3 tools/draw_views.py designs/bed-frame/parts.json` for the drawings).

- **How to build it, with prices:** [BUILD.md](BUILD.md)
- **The bed as a 3D model for other repos' rooms:** [model/](model/README.md), made up, bare, or
  with the quilt, each as a .blend, a .glb and a SketchUp .dae, checked on every export, with its
  [version](model/VERSION), [changes](model/CHANGELOG.md) and [library records](model/library.yaml)
  (`python3.11 designs/bed-frame/model.py --export-all`)
- Footprint (top view to scale, for a room's plan): [bed-frame-footprint.svg](bed-frame-footprint.svg)
- Drawing (front, side, top, cut list): [bed-frame-drawing.svg](bed-frame-drawing.svg)
- Joinery (every mortise, tenon, peg and bolt): [bed-frame-joinery.svg](bed-frame-joinery.svg)
- Renders: [corner](renders/bed-frame-corner.jpg), [foot](renders/bed-frame-foot.jpg),
  [post top and through-tenon](renders/bed-frame-head.jpg), [the foot's corner](renders/bed-frame-footend.jpg),
  [with a quilt](renders/bed-frame-corner-quilt.jpg), [with a quilt, from the foot](renders/bed-frame-foot-quilt.jpg),
  [made up](renders/bed-frame-bedroom-bedding.jpg) (`--bedding`, after the client's picture, 2026-11-11:
  William Morris's Strawberry Thief over the headboard, public domain, from Cooper Hewitt
  ([sources](textures/SOURCES.md)); our own indigo block-print coverlet tucked in between the mattress and the
  rails, and kilim throw (`tools/make_fabric.py`); two pillows stacked flat at each side), [made up, from above](renders/bed-frame-corner-bedding.jpg)

## The design

64 7/8" wide over the tenons, 85 1/8" long, 60 1/8" to the post tops.

- **Headboard posts:** two 2 3/4" square posts with shallow pyramid caps.
  They stand 3 1/2" above the top rail, so they show above the folded quilt.
- **The headboard's rails** go right through the posts, with their tenons
  standing 3/8" proud on the outside faces. Each tenon is held by two square
  oak pegs through the posts' front faces. This through-tenon joinery is the
  most recognizable mark of Stickley's furniture.
- **Seven wide flat slats** sit flush with the rails' faces, so you lean
  against a flat panel.
- **The top rail** is at 56", 32" above the mattress top, so someone tall
  can sit up against it with pillows (raised from 49", 2026-11-10). It has
  well-rounded 3/8" edges.
- **Foot:** no tall posts. A straight foot rail keeps the mattress in
  place (an arched one showed the support under the bed, dropped
  2026-11-11). It's through-tenoned and pegged
  into two short legs. The legs have the same 2 3/4" section as the head
  posts and stand 1" above the rail with the same pyramid cap, as period
  beds' low posts did. Their tops are still 6" below the mattress top
  (decided 2026-11-10: hiding them under the rail would be a modern
  platform-bed look).
- **Side rails:** on one bed bolt and a stub tenon at each end, the way
  period beds were. The foot's bolts have aged-brass covers, the small
  round caps on the foot legs (darkened 2026-11-11 so they don't stand out).
- **Support:** 2x4 cleats inside the side rails, thirteen poplar slats, and
  a 2x4 center rail on three legs stained dark (they can be seen under
  the foot rail from low down).
- **Twin and king** (Sketchup-tools, 2026-11-14: a pair of twins for the
  NW bedroom, a king for the SE bedroom): the same bed at each size,
  `python3.11 designs/bed-frame/model.py --size twin` or `--size king`.
  The posts, rails and joinery are the queen's, and the headboard keeps
  the queen's slat width: four slats on the twin, nine on the king. The
  twin is 42 7/8" x 80 1/16" over the tenons, and the king
  80 7/8" x 85 1/16". Each has its own drawing and cut list
  ([twin](bed-frame-twin-drawing.svg), [king](bed-frame-king-drawing.svg)).
  BUILD.md's steps are the same for each.
- **Made up** (2026-11-15): Morris's Strawberry Thief on a coverlet tucked
  in between the mattress and the rails, its foot corners sewn; a white
  top sheet turned down 10"; a wool plaid blanket across the foot; white
  pillows two by two (one column on the twin, king pillows on the king);
  and a pieced Ohio Star quilt over the headboard, in the coverlet's
  navy, blues, sage, biscuit and strawberry red (client, 2026-11-15).
- **Finish:** fumed, a deep brown, as Stickley's workshops did it; or dyed
  to match (BUILD.md, step 15).

## Assumptions

- Mattresses 11" thick at every size (twin 38" x 75", queen 60" x 80",
  king 76" x 80"), on slats, no box spring; its top is 24" from
  the floor. A thicker mattress raises it: 13" puts the top at 26".
- Each post is two 6/4 boards glued up, quartersawn faces outward.

## More Arts & Crafts, if wanted later

Each of these adds wood or work:

- **Corbels** under the top rail's ends.
- **An arched top rail.** It would be hidden by the quilt, so it's not
  worth it.
- **Quartersawn faces on all four sides** of the posts (Stickley's
  "quadrilinear" posts).
- **Tapered posts.**
- **A low matching footboard.** Dropped: you asked for none.

## Questions

- **The twin's width:** asked for about 40" outside, it comes out 42 1/8"
  (42 7/8" over the tenons) with the queen's 2 3/4" posts and the rails
  centered on them. A 38" mattress, 1/2" of clearance and 1 13/16" each
  side for the rails make 42 1/8". Reaching 40" would take slimmer posts
  (about 1 3/4") or rails set flush inside the posts. Is 42 1/8" all
  right for the NW bedroom's pair?

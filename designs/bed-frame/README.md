# Queen bed frame

From [specs/bed-frame.md](../../specs/bed-frame.md). Built by
[model.py](model.py) from [sizes.py](sizes.py)
(`python3.11 designs/bed-frame/model.py --views corner,foot,head,footend`;
add `--quilt` for the draped quilt; `python3 designs/bed-frame/draw_joinery.py`
and `python3 tools/draw_views.py designs/bed-frame/parts.json` for the drawings).

- **How to build it, with prices:** [BUILD.md](BUILD.md)
- **The bed as a 3D model for other renders:** [model/](model/README.md)
  (`python3.11 designs/bed-frame/model.py [--bedding] --export <file.blend>`)
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
- **Finish:** fumed, a deep brown, as Stickley's workshops did it; or dyed
  to match (BUILD.md, step 15).

## Assumptions

- Mattress 60" x 80" x 11" on slats, no box spring; its top is 24" from
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

None open.

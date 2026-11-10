# Queen bed frame

From [specs/bed-frame.md](../../specs/bed-frame.md). Built by
[model.py](model.py) from [sizes.py](sizes.py)
(`python3.11 designs/bed-frame/model.py --views corner,foot,head,footend`;
add `--quilt` for the draped quilt; `python3 designs/bed-frame/draw_joinery.py`
and `python3 tools/draw_views.py designs/bed-frame/parts.json` for the drawings).

- **How to build it, with prices:** [BUILD.md](BUILD.md)
- Drawing (front, side, top, cut list): [bed-frame-drawing.svg](bed-frame-drawing.svg)
- Joinery (every mortise, tenon, peg and bolt): [bed-frame-joinery.svg](bed-frame-joinery.svg)
- Renders: [corner](renders/bed-frame-corner.jpg), [foot](renders/bed-frame-foot.jpg),
  [post top and through-tenon](renders/bed-frame-head.jpg), [the foot's corner](renders/bed-frame-footend.jpg),
  [with a quilt](renders/bed-frame-corner-quilt.jpg), [with a quilt, from the foot](renders/bed-frame-foot-quilt.jpg)

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
- **Foot:** no posts. A foot rail with a gently arched bottom edge (1 1/2"
  rise) keeps the mattress in place. It's through-tenoned and pegged into
  two short legs whose tops are flush with it.
- **Side rails:** on one bed bolt and a stub tenon at each end, the way
  period beds were, with brass covers on the foot's bolts.
- **Support:** 2x4 cleats inside the side rails, thirteen poplar slats, and
  a 2x4 center rail on three legs stained dark (they show through the
  arch).
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

- The foot legs are flush with the foot rail's top, so they read as plain
  corner blocks. Would you rather have them tucked under the rail, out of
  sight?

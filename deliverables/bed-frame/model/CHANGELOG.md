# The bed frame's 3D model: changes

Newest first, one line per change. The newest line's name is the version
(`model/VERSION`, and `o["design_render_version"]` on every object):
add a line here before exporting again (`python3.11 designs/bed-frame/model.py --export-all`).

- 2026-11-15b: made up as a designer would: a Morris coverlet falling 14" over the sides and foot (one uncut sheet, its corners folding over the legs), a white top sheet turned down 10", a wool plaid blanket with its ends over the sides, white sheets and pillowcases, a checked headboard cover; each textile one Pattern image at a known UV scale, no hue nodes
- 2026-11-15a: the coverlet's foot corners sewn after the drape, so no black slit shows where the flaps met (Sketchup-tools' notes); the export test checks it; cloth thickness left live
- 2026-11-12a: ready for other repos' rooms: checked in a fresh Blender, names prefixed, bedding in named collections, a quilt version, .glb and SketchUp .dae copies, a footprint drawing
- 2026-11-11d: the folded blanket in real wool, with a fringe (commit d9178ab)
- 2026-11-11c: a straight foot rail, so the support under the bed stays out of sight (commit 639a45c)
- 2026-11-11b: a neatly folded blanket, the coverlet tucked in again, a dark center rail (commit cb3bac4)
- 2026-11-11a: the first export: a folded blanket, neater coverlet corners (commit 04c3f27)

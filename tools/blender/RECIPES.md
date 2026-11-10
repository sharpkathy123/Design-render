# Recipes: how to model and render things well

_Copied from Sketchup-tools on 2026-11-10. Most of these were learned on the
house's rooms: the files they name there (props.py, loft_room.py, mudroom.py,
kitchen.py, the rooms/ folders) stayed in Sketchup-tools, but what they teach
applies here too. New recipes for this repo go under "Design-render" at the end._

What we've learned, so it isn't learned again (client, 2026-10-21: "do
something so that you don't need to re-learn how to render nice
curtains"). **Read this before modeling anything new, and add a recipe the
same day you learn one.** Each says what to call, what goes wrong, and
where it came from.

## Drawn once (2026-10-23)

The client, 2026-10-23: "how can we stop reverting to drawing things
poorly when we've already figured out how to draw them better?" (the mud
room's hand towels came out as slabs and its tissues as a ball, a day
after the second floor's draped towels and folded tissues). So:

- **What's been solved is drawn in one place, and every room calls it.**
  [props.py](props.py): `tissue_box()`, `soap_pump()`, `vase()`,
  `towel_ring()`, `toilet()` (2026-10-23: the old one, a 3" puck on a
  post, looked sunk in the floor from the half bath's look-around; the
  second floor's SketchUp toilet is swapped for it by
  `replace_toilet()`), and `towel(kind, at, facing)`, a marker where
  vanity_render_setup's cloth simulation drapes a real towel (HAND
  through a ring, BAR a hand towel over a bar, BARBATH a bath towel over
  a bar, BARMAT a bath mat, BATH over a hook). Never `hung_towel()` for
  a towel anyone will look at.
- **`check_docs.py` enforces it:** a room model that draws a tissue box,
  a soap pump, a towel ring or a towel slab itself is a PROBLEM.
- **Before drawing anything for a room, find the best version already
  rendered** (the second floor's renders are the reference for bath
  things) and put the new render beside it before sending. If the new
  one looks worse, it isn't done.
- When a new thing is solved, move it into props.py the same day and add
  it to the check.

## Before drawing anything: is there a real model?

- **Look in [library/models/models.yaml](../../library/models/models.yaml)
  first.** Free Poly Haven models (CC0, public domain): painted bench and
  settle, rocking chair, baskets, vases, a fern, an oil lamp, a clay pot,
  periwinkle sprigs. Place one with
  `assets.place("wicker_basket_01", (x, y, z), rot=90, width=16, objs=OBJS)`
  ([assets.py](assets.py)): inches, the room's own axes, scaled by width,
  depth or height, `tint="#hex"` to paint it.
- **To add one:** `python3 tools/fetch_models.py --list wicker chair` lists
  what Poly Haven has; add its id to `models.yaml` with a `use:` line, run
  `python3 tools/fetch_models.py`. Keep each under about 10 MB (the book set
  and potted plants were 25 to 60 MB and were left out). Other free sites
  (BlenderKit, Sketchfab, ambientCG) are blocked from the cloud sessions:
  the client can download from them and drop the file in `library/models/`.
- **Part of a set** (2026-10-23): `assets.place(..., only=("cup_small_01",
  "saucer_circular_04"))` keeps just the parts named (Poly Haven's
  `tea_set_01` gives a teacup on its saucer; `binder_notebook`'s
  `binder_notebook_closed`, a small book). Poly Haven has no mug: a plain
  white cylinder read as a roll of toilet paper.
- **Only draw from boxes** what no free model fits: built-ins to our sizes
  (cabinets, closets, benches against a wall), and anything that must match
  a real product's dimensions.

## Curtains (2026-10-18; rebuilt 2026-10-22)

- **Call `curtain()`** in [loft_room.py](loft_room.py) (the mud room uses
  it as `lr.curtain`). Since 2026-10-22 it builds a curtain the way the
  second floor's tub curtain is built (`build_tub` in
  tools/sketchup/rta_vanity.rb), which the client liked: **a row of soft
  round folds**, each a smooth tube 2 1/2"-3 1/2" across, one about every
  1.9" along the curtain, overlapping and staggered in and out, a little
  wider at the hem. Before that it was one rippled sheet: first an even
  zigzag (an accordion door), then uneven waves; both read thin and flat.
- **Fullness comes from the number of folds**, not their depth: give a
  stacked-back panel its real stacked width (14" for a 30" half-window of
  cloth), and `amp` only to make the folds deeper (1.4 is the usual).
- **Panels at a window** stack over the casing and a few inches of wall,
  and 5" of glass; the rod runs past the casing to hold them.
- **A heavy curtain (a portiere):** a dark, matte wool (`roughness 1.0,
  sheen 0.15`); a high sheen makes wool look like satin.

- **A patterned curtain: one sheet with UVs, not tubes** (2026-10-22, the
  photograph pass). With the print mapped by world position (the default
  for `pattern` materials) the print is projected straight through the
  folds, like a slide on a fluted column: it runs on unbroken and hides
  them (the client asked whether the pattern happened to line up with the
  folds). Use `drape()` in [mudroom.py](mudroom.py): one sheet in deep,
  uneven folds (pitch 3.6", depth up to about 6", fuller at the hem),
  ending on a crest so a leading-edge band faces the room, its UVs measured
  along the cloth, and give its material `uv=True`
  (vanity_render_setup.py then maps the print by UV, in metres of cloth).
  Folds read only with light from the side: see Lighting.

- **A window tight against a side wall** (2026-10-22): `curtain_panels`
  with a single span is a one-way draw; a span with a third value
  (`(65.0, 71.5, 3.6)`) is a narrow stationary panel with deeper, closer
  folds (amp 3.6, pitch 2.6), which reads as a full width of cloth in a
  tight stack, not a skimpy one. The rod runs into the wall, no finial there.
- **Check every stack against the furniture**: a floor-length stack 4 1/2"
  to 11" off the wall collides with anything closer to the wall than that
  (the lamp table in the corner did). Bring the furniture forward, or
  stop the stack.

## Freestanding furniture under windows (2026-10-22)

- **Check a model's seat height** (a ray cast down onto it, as in the notes
  of 2026-10-22): Poly Haven's `painted_wooden_bench` seats at 25", a stool's
  height. An asset dict's `zscale` (mudroom.py's build) scales it in height
  only: 0.715 brings that seat to 18".

- A bench or settle under a window stands 3" off the wall: the window's
  stool projects 2 1/2", and a bench back at 1" ran through it.
- Poly Haven's `wicker_basket_01` is a shallow tray: on a shelf it renders as
  a bare rim. For storage baskets use `basket()` in mudroom.py (open, woven
  willow texture).

## Cushions and pillows (2026-10-22)

- No usable pillow model: Poly Haven's `throw_pillows_01` is a heap of
  chevron pillows lying flat. Seat cushions: boxes with a `BEVEL` modifier
  (width 1.2 in the model's inches, 4 segments, smooth shading).
- **Throw pillows: `pillow()`** in [mudroom.py](mudroom.py) (2026-10-22;
  beveled boxes still read as boxes beside the client's inspiration
  picture): two faces puffed toward the middle meeting in a thin seam,
  the sides drawn in, pointed corners, a crease across the top; leaned
  back 14 degrees and each turned and tipped a few degrees differently;
  its print by UV (`uv=True`).
- Poly Haven's `painted_wooden_bench` (a settle with a boot shelf, 45")
  tinted in the scheme's paint makes a better bench than a drawn one.

## A bath's small things (2026-10-23)

- Every bath gets a soap pump by each sink, a tissue box, a small vase of
  flowers and a hand towel at each sink (DESIGN_PRINCIPLES.md), all from
  props.py (above). In the mud room `bath_things()` and `towel_ring()`
  call it; the vase is a stand-in that `vase_flowers()` swaps, after the
  mirror, for vanity_render_setup's glazed jar and sprigs, and
  `drape_towels()` drapes the towels.
- **Flowers need light and a light jar** (2026-10-23, the client: "why
  are the flowers so gloomy?"): a dark matte jar in a fixture's shadow
  (under a cabinet) turns the sprigs' leaves nearly black. Put the vase
  where the room's light falls on it, give it a light glossy glaze, a
  full head of clear colors (13 sprigs), and make every fixture in view
  cast light (sconces too, not only glow).
- **Anything cached between views must be cleared when the scene is**:
  mudroom.py's `build()` empties the scene for every view, so its list of
  vases and vanity_render_setup's `_SPRIGS` are cleared there too (the
  second view failed with "StructRNA ... has been removed").
- Check what hangs over a faucet: a cabinet's bottom 6"-8" over the
  spout's top, the spout reaching past its face.

## Lights: warm, like the real bulbs (2026-10-22)

- Point lights default to pure white, which makes a blue room look cold.
  Set `ld.color = (1.0, 0.86, 0.70)` (about 2700-3000K), as mudroom.py does.

## Fittings: build them round (2026-10-22)

- Faucets, valves and shower parts are turned objects: draw them from
  cylinders and cones (a stepped round escutcheon, a round hub and lever,
  an arm with a flange, a bell-shaped head), never boxes, as the second
  floor's do (rta_vanity.rb, the tub's fittings). The loft's first shower
  was boxes and read as a toy.

## Joints (2026-10-17)

- Two faces in the same place flicker into dark squares. Build like a
  carpenter: one piece butts the next; nothing runs through another to the
  same face. Every render lists `JOINT` lines first; fix them all.
  `--check-joints` checks without rendering.
- Stacked boxes that touch (a coat's shoulder on its body): overlap them a
  little instead of sharing a face.
- **A cabinet's top goes between its sides** (2026-11-06, the kitchen: the
  client's "black lines" down every visible cabinet side at the top of each
  box). A top run across the sides shares their outer faces; `top_board()`
  in [kitchen.py](kitchen.py) puts it between them and in front of the
  back. A door's panel stops a hair inside its rails, a door stops at the
  face frame's rail rather than running over it, and a molding's return
  butts the band rather than lapping it.
- **Pieces that must overlap where they meet** (crowns over neighboring
  cabinets and round a corner, the ceiling's coves) each get a different
  hair's breadth (`lap(wall)` in kitchen.py: 0.01" a wall, 0.0025" a
  piece along it), so no two share a face. The kitchen's black square
  where the crowns met at the corner was this.
- The kitchen has its own check since 2026-11-06:
  `python3.11 tools/blender/kitchen.py --layout A3 --check-joints` (767
  lines then; what's left is out of sight: undersides on the counter,
  tops under the crown).

## Wallpaper and fabric from a shop screenshot (2026-10-21)

- `python3 tools/make_paper_texture.py SCREENSHOT ID` cuts one exact
  repeat (it finds the paper, the repeat and any half drop) and prints the
  `render.repeat` in metres. Look at the 2 x 2 tiling it writes to
  `tools/art_texture_previews/`: no seams.
- **Measure colors from the screenshot** (hue bins), never from the
  listing's name: "pale blue" Golden Lily was sage green.
- Copyrighted designs get a plain stand-in for public pages:
  `python3 tools/make_shareable.py` (set `render.share_pattern`).

## Doors, closets and casings

- **A closet is a room, not a row of cabinets** (2026-10-18):
  `hall_closet()` in [mudroom.py](mudroom.py), five-panel doors by
  `five_panel()`, cased like the room's doors (`door_casing`).
- Keep a band of wall between a door's head cap and anything above it,
  or the two read as one dark mass.
- **Doors stand open unless asked otherwise** (client, 2026-10-26; the
  rule is in DESIGN_PRINCIPLES.md). A view whose camera stands where the
  open leaf swings hides the leaf (the view's hidden list in loft_room's
  `VIEWS`), it doesn't shut the door.
- Open doors stand at 90 degrees from their hinge; check what they hit.
  **A bath door seen from the hall stands open further** (2026-10-21: at 90
  degrees the leaf hid the half bath and the full bath): `bath_door()` in
  [mudroom.py](mudroom.py) turns the leaf about its hinge to
  `BATH_DOOR_OPEN` (115), still clear of the grab bar and sink. A turned
  box is invisible to the joint check (it sees boxes as drawn), so look
  at the leaf's edge in the render.
- **A door seen open, from both sides** (2026-10-26): `hall_door_leaf()`
  in [loft_room.py](loft_room.py), the same five-panel proportions as
  `five_panel()` (4 1/2" stiles and top rail, 9" bottom rail, 3 1/2" mid
  rails) but framed through its full thickness with the panels set in the
  middle, so both faces read; turned about its hinge by
  `LOFT_HALL_DOOR_OPEN`. A door standing 10" off a wall at 90 degrees
  hides that wall's art only from right across from it: check from where
  people actually look before moving the art.
- **Tile wrapped through an opening ends in a true bullnose**
  (2026-10-26: a 3/4" square box read as a square edge): `bullnose()` in
  [loft_room.py](loft_room.py) extrudes a profile whose aisle edge is a
  quarter round across the tile's whole thickness (1", the tile on its
  backer), standing 1/2" proud of the plaster so the casing butts the
  round's side. Only the round's faces are shaded smooth. Seen square on
  it barely shows: check it from an angle (`detail-casing`).

## Rugs

- **A rag rug of our own:** `python3 tools/make_rag_rug.py NAME --size WxL
  --colours ...` (hit-and-miss bands). Each color is drawn about equally
  often, so to let one lead, give it two or three shades (the mud room's:
  three blues, one amber, one rust); with the amber listed once among two
  blues it took over. In the model a box 0.3" thick with
  `pattern="photo", whole="XY"` stretches the picture once over it.

## Materials

- **Hammered copper:** polished on the facets, roughness about 0.18, a
  Voronoi bump by world position in metres (object coordinates in inches
  made the dents 1/70" and the copper flat).
- **The house's dark stain:** satin, roughness 0.8; glossier, its end faces
  mirror the walls (the "gold patches" of 2026-10-17).
- **Wicker:** `tools/make_wicker_texture.py` draws the weave.
- Stand-in coats in a closet are seen edge-on: 4-5" wide, 19" deep, a
  narrower shoulder box overlapping the top.

## Lighting
- **A photograph, not a diagram** (2026-10-22, the photograph pass):
  - **Clear glass with a view:** `clear_glass()` and `lake_view()` in
    mudroom.py: the panes nearly all transparent with a faint reflection,
    and outside, a lit sheet with a landscape photograph (a Poly Haven
    panorama's tonemapped JPG, CC0, cropped to the horizon), far enough
    out (about 35') that it isn't huge, its horizon at eye height, seen by
    the camera only (no light, no shadow). A glowing white pane looks like
    a lightbox.
  - **Glass you notice a little** (2026-10-22, the client: the view looked
    too clean and distracting, a bright picture pasted in): a reflection
    (glossy 13%) and a faint pale daylit haze (9%) on the panes, and the
    view's photo at 80% saturation, so it sits back behind the glass.
  - **Use the house's own view** when there's a photo (`VIEWS_OUT` in
    mudroom.py: the picture, where its horizon is, its width as hung): the
    client's photos are private, so `SHAREABLE=1` swaps in a CC0 one.
  - **Draw what's outside the glass:** a porch roof, its posts (a post
    just outside a window renders as a dark slab against the bright view:
    put guessed posts where they don't stand in the view).
  - **Daylight comes in at the window:** an area light just outside each
    window pointing into the room (under a porch, a wide panel at the
    porch's open edge, about 1400 W for the lake window). Check its direction (the mud room's
    pointed outward for days, hidden by the glowing glass). It's what
    models curtain folds and pillows; too strong (over about 400 W for a
    5' window) and the colors wash out.
  - **AgX - Medium High Contrast** look (set after `v.setup_render()`,
    which resets it): a photograph's contrast.
  - **A tall picture for a tall question** (how a cabinet sits in a 9'
    room): a view with "portrait" as its fourth item renders 3:4 upright
    (`bathtall` in mudroom.py); in loft_room.py, "portrait" as the sixth
    item, after the eye height, levels the camera too (`wctall`, 2026-10-23).
  - **A level camera:** look straight across and shift the lens
    (`shift_y`) to frame, so verticals stay upright; no lens under 17mm.
  - **Fill the openings:** what's seen through a door (a hall, a closet)
    needs at least a floor and a wall, or it renders as a gray void.

- Rooms are lit by their own fixtures (`fixture_lamps()` in
  [vanity_render_setup.py](vanity_render_setup.py)): a ceiling bowl 60, a
  small or shower light 18, a recessed one 22. **An enclosed WC's light
  is a full-size bulb (40)**: at 18 the WC rendered darker than the room
  (2026-10-21). Light a small closed room for what its real bulb gives,
  not by the fixture's size.

## Checking a render

- Quick renders (`--quality check`) any time; final ones only at night
  (CLAUDE.md).
- Zoom in on the joints, the curtains and anything new before sending.
  Compare with the last good render of the same view (side by side).

## Video and SketchUp from the renders and models (2026-10-23)

- **A slideshow video,** not an animation: `tools/build_video.py` pans and
  zooms slowly across the finished renders, with captions from each room's
  `document.yaml` (its `views` and `front_runner`), into
  `site/video/front-runners.mp4`. About 8 minutes to build, no rendering.
  A moving-camera walkthrough would need 24-30 final renders a second: days.
- **SketchUp:** a .skp can only be written by SketchUp, so
  `tools/export_sketchup.py` builds each front runner exactly as for a render
  and saves it as COLLADA instead (`EXPORT_DAE`, `export_dae()` in
  `vanity_render_setup.py`), zipped with its pictures in `exports/sketchup/`.
  The client imports it and saves. Check one by importing it back into
  Blender (`bpy.ops.wm.collada_import`) and rendering a plan cut: an
  orthographic camera from above with `clip_start` at 1.4 m below it, and
  `visible_shadow` off on everything (the ceiling otherwise darkens it all).
  Things it found: Blender writes `<texture>` without `texcoord` when an
  image node has no UV map node (an invalid file; fixed after export); the
  mud room's view outside is a 20 m plane (left out); the heavy things are
  the draped towels (13,000 faces each) and the Poly Haven flowers and vases,
  so the light version leaves out everything appended from a model file
  (`asset` property) and the towels. Patterns drawn by shader nodes (the hex
  tile) come in as plain color.

## 360-degree look-arounds (2026-10-23)

- `PANO=1` on any second-floor render turns the view's camera into an
  equirectangular one (`pano_camera()` in `vanity_render_setup.py`): level
  at eye height, in the walkway between the vanities and the tub (halfway
  along between the `opposite` and `hall` eyes), the picture's middle facing
  the hall door. `PANO_AT="x,y"` (meters) moves it; `PANO_RES` sets the
  width (the height is half).
- The first try, halfway between the two eyes, stood over the vanity: the
  countertop filled a quarter of the picture. Stand where a person would,
  clear of everything by a couple of feet.
- **4096 x 2048** is the size: as wide as every phone's graphics can take as
  one picture. A check render at 4096 takes about 15 minutes here; a final
  goes in the night queue.
- The page (`tools/build_pano.py`, `site/pano.yaml`) is its own few lines of
  WebGL, no library (cdnjs is blocked from the sessions, so a library viewer
  can't be tested). Test it in Playwright through a local `http.server`
  (a `file://` picture can't go into WebGL) with
  `--use-gl=swiftshader --enable-unsafe-swiftshader`.
- A curtain a foot or two from the camera smears in the check render; look
  at the final before judging it.
- **The loft and the mud room** take `PANO=<spot>`, a name in their `PANOS`
  (where to stand and what to face, in the room's inches): `aisle`;
  `mudroom`, `halfbath`. The mud room's first spot, at x 64, stood 34"
  from the 30"-deep coat closet, which filled a third of the picture: keep
  about 4 ft from any tall built-in.
- A quick render at 3072 x 1536 isn't a power of two: WebGL 1 shows it
  black unless the picture is clamped, not repeated (`build_pano.py`).
- A button can tilt as well as turn (`[name, u, pitch]` in `pano.yaml`): the
  half bath's toilet sits under its cabinet, out of a level view.

- The loft's PANOS spot can open the WC door (`LOFT_WC_DOOR_OPEN`,
  degrees, into the WC on its north hinges; client, 2026-10-23), so the
  look-around sees in.
- The half bath's views take `BATH_EXPOSURE` (+0.5) and a two-bulb ceiling
  bowl: the navy paper soaks up light, and the client found them really
  dark.

- **Shared building blocks** (2026-11-04, the reorganization): a room's
  model starts from [house_parts.py](house_parts.py), never drawing the
  house's own things again: `shell(s)` (walls, floor, ceiling, every
  opening trimmed, baseboards) for a room from `room_shell.shell(floor,
  room)`, or the pieces: `casing`, `jambs`, `leaf` (five-panel or glazed,
  open, knobs both faces), `window` (double-hung, stool and apron, view,
  daylight, register), `register`, `baseboard`, `baseboards`; `skip=`
  names the openings the room draws itself; `Face(runs, face, sign)`
  places any piece on any wall. The sizes come from `rooms/house/trim.yaml`
  (casing, plinth, baseboard and cap) through `house_trim.py`. No
  radiators: the house is forced air (DESIGN_PRINCIPLES.md, Heat). The mud
  room, kitchen, loft and second-floor bath still draw their own trim;
  move each over when it's next reworked, checking its joints and a quick
  render against the old one.
- **A room with no model yet** (2026-11-04): `plain_room.py --room <folder>`
  builds it from the measured plan with `house_parts.shell` (`tools/room_shell.py`): every wall near
  it with its openings cut, the floor's closures as walls, the house's trim
  (casings on plinth blocks, a head and cap, 8" baseboard and cap, double
  hungs with a stool and apron, five-panel doors open against the wall with
  `props.door_knob`, glazed pairs for doors 48" and wider), a floor
  register under each outside window, a schoolhouse globe, the CC0 lake
  view outside. `--plan 2FL:sw-bedroom` tries a room with no folder. What
  the model taught it: skip the model's single faces (`plane: true`; one
  ran across the NW bedroom's window), merge walls that overlap in one line
  (one filled the SW bedroom's closet door), put a door's trim on the face
  whose side isn't another room's (the closet inside the SW bedroom's box),
  and give no baseboard to a face that's another room's or buried in a
  wall. `--check-joints` still finds a few in the first-floor hall, the NE
  bedroom's chimney and the loft (its slopes aren't drawn): fix them when
  those rooms are started.

## Walk-throughs (2026-10-23)

- `WALK=<folder>` on a second-floor render (`walk_camera()`): from the hall
  door's eye to the look-around's spot, then a 70-degree turn right to the
  vanities, stepping back half a meter as it turns (a full 90 at the
  walkway's middle left the mirror filling the picture). 960 x 540, 12
  samples, 12 pictures a second, one fixed noise seed; `tools/build_walk.py`
  interpolates to 24 and encodes.
- About 42 seconds a picture here, 108 pictures: 75 minutes, more with
  anything else rendering.
- The third walk (client, 2026-10-23: every fixture, switch and fan, and
  the toilet's water supply): the switches by the hall door, the vanity's
  receptacles, the tub's light and fan, the WC's fan and switches, found
  by name (`nearest("Switch", ...)`, `nearest("Fan", ...)`); 31 1/2 s,
  379 pictures, four chunks. props.toilet now has its angle stop and
  braided supply line, and its lever on the left as you face it.
- The second walk (client, 2026-10-23: look into each space) has keys
  `(seconds, where, heading, pitch, lens)`: in, the vanity, the tub and
  shower, across to the WC, in at its vanity, down to the toilet; 21 1/2 s,
  259 pictures, rendered in chunks with `WALK_FRAMES` (no job over two
  hours). The WC view's eye marker is inside the WC wall's thickness:
  stand 30 cm in from it, or the jambs hide both sides. The lens widens
  from 20 to 16 mm in the WC. `WALK_DEBUG=1` writes the marker positions
  to `<folder>/points.txt`.

- **Any room's short walk** (2026-11-06, `tools/blender/walk.py`):
  `ROOM_WALK=<folder>` on the kitchen's, the mud room's or the loft's model
  glides from one of its own composed views to the next in `--views`'
  order (1 s at each, 2.2 s between, eased), at a 62" eye height, the
  lens 18-24 mm, the still's downward look softened to 60%. Choose the
  order so each move stays in the room: `ROOM_WALK_CHECK=1` ray-casts each
  straight move against the built scene (a wall's door counts as open) and
  prints `WALK_THROUGH` for anything in the way. Where none of the views
  leads through an opening, add a `walk-` view as a stepping stone (the
  loft's `walk-showerdoor`, square to the shower's opening). Views that
  hide a wall to see in are unhidden for the walk. A 6-view walk is about
  200 pictures.
- **Walks that span nights** (2026-11-06): the night's 180 minutes ran out
  at the kitchen walk's 156th picture and, rendering into a fresh /tmp
  folder, it would have started again from nothing every night. Now
  `walk.output()` (both kinds of walk) skips any picture already in the
  folder and deletes one cut off mid-write (no PNG end marker), and the
  render queue keeps `/tmp/walks` in GitHub's Actions cache between runs
  (restored before the queue, saved after it even when time runs out), so
  each night carries on. A walk's folder is named with its date; when the
  room changes, give it a new one so old pictures aren't mixed in, and the
  queue line deletes the folder once its video is made. The scene is kept
  between pictures (`use_persistent_data`; only the camera moves), which
  took the kitchen's from 28 to 22 s a picture here (about 30-40 s on
  GitHub). Rendering 8 pictures a second and interpolating to 24 was tried
  and rejected: it ghosts badly on the turns; 12 stays.

## Cloth: a throw (2026-10-24)

- The towels' cloth simulation drapes other cloth too: `drape_throw()` in
  [mudroom.py](mudroom.py), the settle's wool throw (client: boxes "won't
  look like wool throws until they are made more messy").
- **Collide with clean blocks built in world space, not the room.** The
  mud room is mirrored into place by a negative scale; cloth fell through
  the mirrored cushion, or slid off. A block the seat's shape (cushion top
  and front, down to the floor) and a floor slab, subdivided, with
  `collision.cloth_friction` 40, work.
- **Tuck an edge.** Dropped free, a throw slides off a seat whose front it
  hangs over. Pin its back two rows (`vertex_group_mass`), as a throw
  tucked behind a cushion is; the rest falls forward in folds.
- Soft wool: bending 0.6, tension 15, mass 0.5, 90 frames; a little sine
  rumple to start it, solidify 12 mm, subdivision 1.

## Gathered cloth: cafe curtains and shirred panels (2026-11-06)

The kitchen's cafe curtains and the Windrush shirred behind the glass
doors read as "flat panels with lines" (client, 2026-11-05): shallow,
even folds (the shirred ones 0.2" deep on a 1.1" pitch) shade as stripes.
`drape()` in [mudroom.py](mudroom.py) now gathers:

- **Uneven, deeper folds:** `jitter=(0.45, 1.5)` (fold depth from about
  half to one and a half times the mean), `amp` so the cloth is about two
  to two and a half times the opening's width.
- **Folds that wander:** `wobble` 0.05-0.09 (in folds) moves each fold a
  little sideways down its length; above 0.1 the sheet can fold over itself.
- **`taper=0` for cloth on a rod at each end** (shirred), as deep at the
  top as at the bottom; a cafe curtain keeps a little (0.3).
- **A heading past each rod:** a second short `drape()` the same width,
  above the rod (a cafe curtain's 1 1/4" ruffle over its rod pocket) or
  past each sash rod, inside the glass's edge where it shows, as a real
  shirred panel's does. The rod runs inside the cloth, its ends showing.
- A pair of panels stops at the mullion's edge, not in it.
- Fine folds get a finer mesh by themselves (12 points a fold).

## Crowding (2026-10-23)

- `crowding()` and `crowding_in_view()` (vanity_render_setup.py) print
  `CROWD` lines with the joints. The first finds a curtain within 3" of a
  wall fitting, or two fittings touching, in the room; the second, a
  curtain overlapping one or a counter *in the picture* by at least 8% of
  the smaller, which is what the client saw (the loft's Marigold curtain
  over the counter's end from the vanity). Merely touching outlines are
  not flagged: side by side on one wall is fine (the loft's tall mirror).
  Counters are found by their material (an imported vanity's top has a
  SketchUp name) and are only checked against curtains, which need only
  clear them by 1". The picture test fills each thing's projected faces
  (numpy; PIL won't load inside Blender): boxes took in the air over a
  long counter and flagged a curtain beyond it.
- A curtain's folds stand about 2" past the line it's built along: allow
  for them when keeping a panel off something. Only what the camera sees counts: a ray from the camera to
  points on each thing must meet it first, or the mud room's curtains
  "touched" the half bath's mirror through the wall.
- A camera made a moment ago has no matrix: `view_layer.update()` before
  projecting anything through it.
- Names decide the kinds (CROWD_KINDS); pairs meant to sit close (a towel
  ring under its sconce, a sconce by its mirror) are in CROWD_OK.

## Render rounds on GitHub (2026-10-21)

- GitHub's runner takes about **5-8 minutes per final render** (this cloud
  session: about 2-3 minutes alone, 8 with two at once). The first queue
  (6 mud room, 28 loft, 12 second floor) would have taken about 5 hours.
  Keep a queue under about 40 final renders, or split it over two runs.
- **Its log can't be read through the API until the job ends**, so a long
  silence is normal: don't cancel a run for being quiet. Watch it on the
  run's page on github.com (live), or just wait for its commit.
- The workflow stops itself at 290 minutes and still commits what finished.
- **A long queue carries on the next night** (2026-10-23): every line runs
  through `once NAME ...`, and the finished names are kept in
  `tools/render_queue.done`.
- **The queue is in priority order** (client, 2026-10-23): architecture
  and built-ins (walls, tile, trim, cabinets, layout) first, then fixtures
  and fittings, then textiles, accessories, art and styling, then options
  no longer in the running; within each, the front-runner scheme first.
  Leave out a view whose change doesn't show in it.


## What's in the cabinets: an open, labeled storage study (2026-10-29)

The client asked to see "what's in all the cabinets" for the kitchen's
layouts. [kitchen.py](kitchen.py) `--open`:

- **The doors and drawer fronts come off; the face frames stay**, so the
  cabinets still read as cabinets, and each compartment is filled with
  shapes the size of the real things (`fill()`: plates and bowls in stacks,
  glasses and mugs in rows, pots with lids, pans nested, sheets and platters
  on edge, a pantry shelf's boxes behind its cans, a trash pull-out's two
  bins). Shapes, not models: dozens of things per cabinet, and the
  question is what fits.
- **Labels on the picture:** each compartment records its label and its
  front's middle point (`LABELS`); after the camera is set, the points the
  camera sees (in frame, not behind anything: a ray cast) go to
  [tools/label_render.py](../label_render.py), which draws them with the
  system Python (PIL won't load inside Blender's), nudged apart.
- **One wall per view, from across the room, eye at 58"**, a little low so
  the base cabinets' insides show; place each camera clear of the room's
  table, or it fills the foreground.
- **A fill light behind the camera** (an area light the camera doesn't
  see): the insides of cabinets are otherwise in shadow.
- **A corner's carcass stops 3/4" short of its door faces**, as every
  carcass does; drawn to the front, the doors and the box shared a face
  and rendered black.
- **The layouts are data** (`rooms/kitchen/layouts.py`), read by both the
  plans and the model: one set of numbers.

## Beadboard ceilings, pendants and under-cabinet light (2026-10-30)

From the kitchen ([kitchen.py](kitchen.py), `beadboard()` and `lighting()`):

- **Beadboard:** the ceiling a plain box in its paint, and a thin darker
  strip (0.24" wide, 0.06" proud) every 3 1/2" for the grooves; at check
  quality that reads as boards. A small painted cove where it meets the
  walls finishes it.
- **A schoolhouse pendant:** a nickel canopy, a stem, a fitter, and a
  smooth opal sphere (emission) named `CEILING light ...`, which the view
  sets `visible_shadow = False` so the point light inside it isn't
  blocked by its own globe; the point light about 38 W for a 9" globe.
- **Under-cabinet light:** an emissive strip at each wall cabinet's front
  underside, and a downward area light the strip's length, about 2 W a
  foot: it lights the backsplash and counter as the real strips do.

## Cabinet feet and fillers (2026-11-06)

`kitchen.py`'s `run_feet()` and `fillers()`, after the client saw "weird
things" with the feet:

- **A filler is part of the run.** A gap of 6" or less between cabinets is
  a filler with a flush kick, so the feet treat it as one run; merging
  only 4" gaps split the run at the 6" pull-out and stood two feet face
  to face in the middle of it.
- **Fill both ends of a run, not just the far one.** A run that stops
  short of the wall it starts from (A3's south run, 1 1/2" off the east
  wall) left a black slot to the floor and drew a foot against the wall.
  The scribe filler goes in at either end, and a wall cabinet over it
  gets a matching strip (`upper_scribe()`, sized from its side panels).
  No foot within 6" of a wall: a scribed end is against the wall, not
  free-standing.
- **Find the feet in numbers before rendering:** build the layout in
  Blender's Python and print each `Foot` and `Toe kick` object's bounds
  (a quick script, about 20 s); the faults show as a pair of feet across
  a filler, or a run's end that doesn't reach a wall or a corner. Inside
  `build()`, objects are still in inches on the plan's axes; the room is
  scaled to meters and turned (its y flipped) only at the end.
- **A pale kick reads as a flat sheet on the floor** in a high view: the
  recessed kick and a corner's two sweeping feet, cream on a white floor,
  catch no shadow. That's the light, not the model.

## Kitchen things, from real models (2026-10-31)

- **Check a downloaded model's orientation before using it:** a Sketchfab
  model can come lying on its side or standing on end (the toaster, the
  chef's knife). Check it by its parts' extents, not by eye
  (2026-11-06: the toaster, "fixed" on 10-31, still lay on its back; its
  base part was the thin one along y, so y was up: turned 90 degrees about
  x, its base on z = 0). A model whose mesh hangs under a turned parent
  empty (Sketchfab's Y-up glTF root) can lie down when placed, the
  parent's turn lost: bake the parent into the mesh and remove the empties
  (the coffee canister, 2026-11-06). Fix it once in its .blend, by turning the mesh data
  itself (`assets.place()` resets the top-level transforms, so turning
  those does nothing), and note it in models.yaml's `use`.
- **A hung mug** (`hang_mug()` in kitchen.py): the mug model turned
  handle-up with its axis along the wall, then tipped about 40 degrees in
  the wall's plane, so it hangs diagonally from the hook; tinted with
  `assets.place(tint=...)`. Upright cylinders with a ring on top don't read
  as mugs.
- **Cloth laid flat** (potholders, seat pads): a photo pattern on a
  horizontal surface needs `floor=True`, or it's mapped as on a wall and
  runs into stripes (the stools' check read as rattan).
- **Every glass-fronted row gets its light** (`GLASS_ROWS` in kitchen.py):
  register each glass row where it's drawn, not from the layout's list of
  wall cabinets, or the odd ones (over a window, over the refrigerator,
  the pantries') stay dark.
- **A board leaned on the tile** (`lean_board()` in kitchen.py, 2026-11-06):
  the real board model stood on end, turned to face the room, tipped back
  12 degrees, its foot on the counter and its top on the tile. A flat box
  standing against the wall read as cardboard stuck there.
- **Cabinet knobs round, not flat-ended** (`cabinet_knob()`, 2026-11-06): a
  flat polished end is a little mirror, so a matched pair showed the cream
  wall in one and the dark casing in the other and looked like two knobs.
- **The coffee bar** (2026-11-06): a real drip coffee maker with its
  carafe (`sf_coffee_maker`) and lidded stoneware canisters
  (`sf_coffee_canister`, tinted), not a dark box and cylinders.
- **Show what an area is for:** a prep counter with a board, vegetables
  and a knife; the coffee bar with its maker and mugs; the range with a
  pot and potholders.

## Receptacles and heat registers (2026-11-04)

- A wall receptacle is `props.receptacle(prefix, at, out, z)`, beside
  `props.wall_switch()`: the house's single-gang nickel plate upright, a
  white GFCI face, its slots and its test and reset buttons, the face and
  buttons set a little into what's behind them (no shared faces). Used by
  the loft (between the mirrors) and the half bath (beside the pedestal,
  with its timer and switches, in the tile: the wall face is 3/8" out).
- The second floor's heat registers are `build_registers()` in
  `tools/sketchup/rta_vanity.rb` (`registers: true` in option D): a
  cast-iron grid (`iron`) over a black duct (`duct`), the floor grille
  standing 3/16" on the tile, the toe-kick grille on the drawer base's kick
  face. Their lengths are in `rooms/second-floor-bath/sizes.yaml`.
- **The right Python, by itself** (2026-11-04): Blender's module is only in
  `/usr/bin/python3.11` here. Every script that renders or starts a render
  calls `tools/bpy_python.py`'s `ensure()` first and restarts itself under
  that Python when started with plain `python3` (or `BPY_PYTHON`, if set).
  A new render script does the same, before `import bpy`.

## Leaded glass from the client's photo (2026-11-05)

- **Use the real glass, not bars of color:** the dining room's leaded
  windows are the client's photo of one panel
  (`designer/client_photos/ref_diningroom_stainedglass_wholehousepalette.jpg`),
  a material `pattern="photo", whole="YZ"` (stretched once over each
  pane; the axes are the wall's), with a low emission (0.75): higher, the
  AgX view washes the amber and periwinkle out. Each sash is its own box in
  an opening cut through the wall (`lr.cut`), its jambs lining the cut.
  `tools/blender/dining_study.py`'s `builtin()`.
- **A built-in from photos:** read the proportions off a straight-on photo
  (the counter's height as the scale), then draw the carpenter's pieces:
  sides, back, shelves, stiles and rails, doors over the frame, a stepped
  cornice; never one box with a glass face (the stand-in read as a slab).
- `dining_study.py --check-joints` lists its JOINTs (it had 225 before
  2026-11-05: overlapping corner beams, a cross of straps in one plane,
  wainscots meeting in a corner; a corner's plate rail runs in from one
  wall and the other's stops against it).


## A room that is mostly windows (2026-11-06, the sun porch)

From [sun_porch.py](sun_porch.py), the first room model built on
`house_parts` with its own windows (`skip=` the window ids in `openings()`):

- **A wide opening is a bank of sashes, not one double-hung:** a 9' 10"
  window drawn as one sash reads as a picture window. `window_bank()`
  splits it into sashes about 27" wide between 3 1/2" mullions, each a
  double-hung with a 3-over-1 upper sash (`sash_unit()`); the mullions
  stop under the head jamb and start half an inch in from the room face,
  or they share faces with the jambs.
- **A wall of windows trimmed as one band:** flat pier boards between the
  banks from stool to head, one frieze and cap the length of the wall, the
  stool run on the whole wall over a beadboard wainscot. The runs along x
  (west, east) stop against the south wall's pieces of the same depth
  (`give()`), never lapped. Receptacles in beadboard sit on its beads
  (0.56" out), or the plates share faces with them.
- **The blue ceiling:** `house_parts.walls()` draws the ceiling slab in
  `plainceiling`: set that key to the blue, not `ceiling`. In a room that
  is mostly glass the kitchen's #CCD8EE reads white; #BACAEC reads as the
  pale blue.
- **Beams against door heads:** check a beam's underside against every
  door's casing cap (head + 5 1/2"); a door taller than the windows can
  put its cap in a beam's way. Put beams over the piers instead.
- **A pano's spot under a ceiling fan** fills the top of the look-around
  with blades: move the spot and regenerate the buttons from it
  (`room_shell.stops(s)` with `s["spot"]`, `s["face"]` set, as
  `sun_porch.pano_spot()`).

## Washer and dryer, stacked (2026-11-06, the laundry)

From [laundry.py](laundry.py) `machine()` and `stack()`: no free model of a
current 27" front-loader came up, so they're drawn from the spec sheet's
sizes: a white enamel body, a control panel 6" deep along the top, a
chrome door ring and dark glass (cylinders turned 90 degrees on y), the
dryer's back lined up with the washer's (its front 2" proud) on a 1/2"
stacking kit. The feet go 3/4" under the body, not flush with its bottom
(a JOINT otherwise). Set them in a drain pan from the wall to 2" in front
of the washer. A built-in beside them reads original when its wall
cabinet runs to the ceiling, its cap against the plaster.

## Design-render

- **Wood grain follows the part** (2026-11-10): `kit.box()` runs a wood
  recipe's grain along the part's longest side (the `grain` key on
  `vanity_render_setup.build_material`, added here: the house's oak only
  ran up and down, which made a table top look speckled). Pass `grain=` to
  turn it.

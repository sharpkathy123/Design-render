# Notes for Claude Code

Blender designs that aren't part of the house: furniture, shelters,
one-off builds. The tools were copied from Sketchup-tools on 2026-11-10;
the house's own rules don't apply here, but its lessons in
[tools/blender/RECIPES.md](tools/blender/RECIPES.md) do. Read that before
modeling something new.

## From a spec to a design

Each design starts as a text spec, `specs/<name>.md`, and ends up in
`designs/<name>/`:

| File | What it is |
|---|---|
| `sizes.py` | every size, in inches |
| `model.py` | the Blender model, built with `tools/blender/kit.py` |
| `BUILD.md` | for something to be built: materials with prices, tools, steps |
| `README.md` | what was built, the assumptions, open questions, links |
| `share.yaml` | what goes in its shareable folder, `deliverables/<name>/` |
| `parts.json` | the parts list, written by the model |
| `<name>-drawing.svg` | front, side, top, dimensions, cut list |
| `renders/<name>-<view>.jpg` | the pictures |
| `model/` | the 3D model for other repos' rooms: `<name>-<version>.blend`, `.glb`, `sketchup/*.dae`, `CHANGELOG.md` (by hand), and `README.md`, `VERSION`, `library.yaml`, `exports.json` (written by the export) |
| `<name>-footprint.svg` | the top view to scale, for a room's plan (written by the export) |

1. **Read the whole spec.** Every size goes into the design's `sizes.py`
   (one size, one number: the model, the drawings and the build notes all
   read it), with where it came from. Don't
   invent sizes that matter. Where the spec is silent, pick the usual
   size (a 30" table height, 3/4" stock), say so in the README under
   "Assumptions", and keep going. Put real questions under "Questions",
   and mention them in the reply.
2. **Model it** in inches: x across the front, y front to back, z up.
   Use `kit.box`, `kit.cyl`, `kit.prism` and `kit.cut`, one call per real
   piece, so the parts list is the cut list. Butt pieces the way a builder
   would: nothing runs through another piece.
3. **Check:** `kit.check_joints()` (JOINT: faces in one plane that flicker
   in a render) and `kit.check_overlaps()` (OVERLAP: two pieces sharing
   wood). Fix every line, or say why it stays.
4. **Draw:** `kit.write_parts(...)`, then
   `python3 tools/draw_views.py designs/<name>/parts.json`. Add
   `kit.dim(...)` for the sizes a builder needs beyond the overall ones.
5. **Render** a check-quality view or two (`kit.studio()`,
   `kit.camera_auto()`, `kit.render(..., quality="check")`). Look at
   the picture before sending it. If something looks wrong, fix it first.
   Final quality only when asked: it's slow on this machine.
6. **Export the 3D model** (Sketchup-tools, 2026-11-12: everything it had
   to fix to put the bed in its rooms, in its
   `designer/notes-for-design-render.md`; the next design must drop in
   with no work). Every design gets one, through `tools/blender/deliver.py`
   `export()`; `designs/bed-frame/model.py` (`VERSIONS`, `export()`,
   `export_all()`) is the pattern to copy:
   - **A version each time.** Add a line to `model/CHANGELOG.md` first,
     newest on top (`- 2026-11-12a: what changed`). Its name becomes the
     version in `model/VERSION` (with every file's sha256) and on every
     object (`o["design_render_version"]`).
   - **Every choice, findable.** One file per version a room might show
     (made up, bare, a different cover), since rooms append every object
     in a file. Inside each, the parts in named collections (`Bed frame`,
     `Bedding: quilt`). Name parts so a script can find them: all of the
     back as `<prefix> headboard ...`, or whatever the back is called.
   - **Prefixed names:** a short prefix (`Bed`) on every object, mesh,
     material and image. Give materials real names through
     `material_names` (`Bed oak fumed`, `Bed Strawberry Thief`), and give
     a procedural material a `diffuse_color` (its .glb and .dae color).
   - **Facing:** the front to -y, the back to +y, the footprint centered
     on the origin, the floor at z = 0. Pass `tall_in` when the back is
     the tall part, so the check asserts it, and `expect_frame_in` from
     `sizes.py`.
   - `python3.11 designs/<name>/model.py --export-all` writes each version's
     .blend, .glb and SketchUp .dae (inches), then **checks each in a fresh
     Blender** without `view_layer.update()` (size, floor, centering,
     facing, names, tags, packing, collections). A failed check stops it:
     fix the model, never the check. Then it writes `model/README.md` (the
     sizes measured from the files, never typed; triangles; placing;
     SketchUp; rights), `VERSION`, `library.yaml` (records ready to paste
     into Sketchup-tools' `library/models/models.yaml`, with `version` and
     `facing`) and `<name>-footprint.svg`. Its prose comes from
     share.yaml's `model:` section: `facing`, `rot_rule`, `license`,
     `versions` (name, use, about) and `textures` (every packed image's
     source and rights: the export stops on one that isn't listed).
   - **Look at it placed:** load a version with Sketchup-tools'
     `assets.place()` turned 90 degrees, and render it (RECIPES.md, "A
     model for another repo's rooms").
   - Keep the bedding or other soft parts' smoothing modest, and say in the
     reply if a file is over about 100,000 triangles in the viewport.
   - List everything in `model/` in share.yaml's `files:` (the
     `sketchup/` folder as one entry) and the footprint under
     `drawings:`.
7. **Build the deliverables** (client, 2026-11-11: everything for each
   design in one folder, to share): list what to share in the design's
   `share.yaml`, then `python3 tools/build_deliverables.py <name>`. It writes
   `deliverables/<name>/` (a landing page, a printable build packet PDF,
   each drawing as SVG and PDF, the build guide, the renders) and the index
   `deliverables/README.md`. Never edit `deliverables/` by hand; rerun it
   after any change to the design.
8. **Commit and push**, then reply with what was built, the assumptions,
   the questions, the model's version, and the link to its deliverables
   page.

Run a model with `python3.11 designs/<name>/model.py [--quality check|final] [--views front,back]`.
Blender's module is `bpy` for Python 3.11
(`python3.11 -m pip install -r tools/render_requirements.txt` if it's
missing; `tools/bpy_python.py` restarts a script under 3.11 when needed).
The drawings and other tools are plain `python3`.

## Standards

- **SVG for drawings, JPG for renders.** The Claude app shows an .svg as
  code, so to show a drawing in the chat run
  `SCRATCH=<scratchpad> python3 tools/svg_view.py <drawing.svg>` and send
  the page. Run `python3 tools/stamp_svg.py` after drawing, to date the sheets.
- **Free ready-made things first, for anything new** (client, 2026-11-11:
  "look for pre-existing free Blender things to use that will look nicer
  and use up less of my Claude minutes"). Before modeling, simulating or
  drawing any object, material or texture, look for a free one:
  - **models:** Poly Haven, CC0, through `tools/fetch_models.py`; and
    Sketchfab (`python3 tools/fetch_models.py --sketchfab <words>`, CC0 or
    CC Attribution only, credit in the record; the client's token is in
    this environment as SKETCHFAB_API_TOKEN, 2026-11-11);
  - **materials and textures:** Poly Haven's textures, CC0, include fabric,
    wood and plaster;
  - **historic patterns:** public domain scans on Wikimedia Commons (Cooper
    Hewitt, the Met, the V&A).

  Use what fits, and build or simulate only what's left: the design itself,
  and what nothing free matches. The repo is public, so only CC0, public
  domain or CC-BY (with credit) goes in. Say in the reply what was found
  and used.
- **Real models before boxes** for props and accessories (Poly Haven, CC0):
  `python3 tools/fetch_models.py --list <words>`, add the id to
  `library/models/models.yaml`, `python3 tools/fetch_models.py <id>`, place
  with `tools/blender/assets.py`. Build the design itself from parts.
- **Materials** come from `kit.PRESETS` or a recipe dict
  (`tools/blender/vanity_render_setup.py` `build_material` lists the
  keys). Give each a `label` for the cut list ("3/4\" white oak").
- **Add a recipe to RECIPES.md** the day you work out how to model or
  render something well.
- American spelling; inches written as 29 3/4".

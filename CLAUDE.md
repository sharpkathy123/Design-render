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
6. **Build the deliverables** (client, 2026-11-11: everything for each
   design in one folder, to share): list what to share in the design's
   `share.yaml`, then `python3 tools/build_deliverables.py <name>`. It writes
   `deliverables/<name>/` (a landing page, a printable build packet PDF,
   each drawing as SVG and PDF, the build guide, the renders) and the index
   `deliverables/README.md`. Never edit `deliverables/` by hand; rerun it
   after any change to the design.
7. **Commit and push**, then reply with what was built, the assumptions,
   the questions, and the link to its deliverables page.

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
  - **models:** Poly Haven, CC0, through `tools/fetch_models.py`;
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

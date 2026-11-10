# Design-render

A spinoff of the Sketchup-tools repo for designing and rendering things
that aren't part of the house, like a kitty shelter and a wooden bed frame.

Each design starts as a text spec in [specs/](specs/) and is built into
[designs/](designs/): a Blender model, a dimensioned drawing with a cut
list, and renders. How that's done is in [CLAUDE.md](CLAUDE.md).

## Tools

- `tools/blender/kit.py`: parts in inches, materials, a studio, cameras,
  renders, the joint check, the parts list
- `tools/draw_views.py`: the drawing sheet (front, side, top, cut list) from a parts list
- `tools/blender/vanity_render_setup.py`: the material recipes and render setup (from Sketchup-tools)
- `tools/blender/assets.py`, `tools/fetch_models.py`: real CC0 models from Poly Haven
- `tools/blender/walk.py`: a camera walk-around
- `tools/svgdraw.py`, `tools/svg_view.py`, `tools/stamp_svg.py`: SVG drawing, viewing, dating
- `tools/label_render.py`: labels on a render
- `tools/blender/RECIPES.md`: what was learned about modeling and rendering well

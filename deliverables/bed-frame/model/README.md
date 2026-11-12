<!-- Written by tools/model_card.py from exports.json, CHANGELOG.md and share.yaml: edit those. -->
# Queen bed frame as a 3D model, for rendering rooms

**Version 2026-11-12a:** ready for other repos' rooms: checked in a fresh Blender, names prefixed, bedding in named collections, a quilt version, .glb and SketchUp .dae copies, a footprint drawing ([VERSION](VERSION) has every file's sha256; [CHANGELOG](CHANGELOG.md)). Every object in the files carries it too, as `o["design_render_version"]`.


## The files

| Version | Blender 4.5 | glTF (meters) | SketchUp (inches) | Size over everything, W x D x H | Triangles (viewport / render) |
|---|---|---|---|---|---|
| **Queen bed frame, made up** | [bed-frame-made-up.blend](bed-frame-made-up.blend) | [bed-frame-made-up.glb](bed-frame-made-up.glb) | [sketchup/bed-frame-made-up.dae](sketchup/bed-frame-made-up.dae) | 64 7/8" x 85 1/8" x 60 1/8" | 70,556 / 358,640 |
| **Queen bed frame, bare** | [bed-frame-bare.blend](bed-frame-bare.blend) | [bed-frame-bare.glb](bed-frame-bare.glb) | [sketchup/bed-frame-bare.dae](sketchup/bed-frame-bare.dae) | 64 7/8" x 85 1/8" x 60 1/8" | 4,912 / 4,912 |
| **Queen bed frame, with a quilt over the headboard** | [bed-frame-quilt.blend](bed-frame-quilt.blend) | [bed-frame-quilt.glb](bed-frame-quilt.glb) | [sketchup/bed-frame-quilt.dae](sketchup/bed-frame-quilt.dae) | 64 7/8" x 85 1/8" x 60 1/8" | 21,260 / 70,304 |

- **bed-frame-made-up.blend**: The bed made up: William Morris's Strawberry Thief over the headboard, an indigo block-print coverlet tucked in, a folded kilim blanket across the foot, four white pillows stacked two by two, a dark fitted sheet. Collections: `Bed frame` (59); `Bed mattress` (1); `Bedding: Strawberry Thief` (1); `Bedding: coverlet, throw and pillows` (7).
- **bed-frame-bare.blend**: The frame and a mattress with a white sheet, nothing else. Collections: `Bed frame` (59); `Bed mattress` (1).
- **bed-frame-quilt.blend**: The frame, a mattress with a white sheet, and a pieced quilt (ochre and sage squares) draped over the headboard. Collections: `Bed frame` (59); `Bed mattress` (1); `Bedding: quilt` (1).

The frame alone is 64 7/8" x 85 1/8" x 60 1/8" (W x D x H), the same in every file. Sizes are measured from the saved files by the export's check, not typed.

## What's in them

- Only meshes, and one empty: every object, mesh, material and image is named `Bed ...`, so appending them into a room that has its own `oak` or `brass` neither merges them nor makes `.001` copies. Materials: `Bed 2x4 pine`, `Bed 2x4 pine stained dark`, `Bed Strawberry Thief`, `Bed block-print coverlet`, `Bed brass aged`, `Bed kilim wool`, `Bed mattress sheet`, `Bed oak fumed grain x`, `Bed oak fumed grain y`, `Bed oak fumed grain z`, `Bed oak fumed pegs grain x`, `Bed pillowcase`, `Bed poplar`, `Bed quilt`, `Bed wool fringe`.
- Real size in Blender meters (the scene's display unit set to inches). The floor is at z = 0 and the frame's footprint is centered on the origin.
- The foot faces -y and the headboard +y, with its back face at the bed's +y end: stand it with that face against a wall.
- An empty, `Bed front`, at the middle of the front on the floor, its arrow pointing -y (out of the front); its `depth_in` property is how far behind it the back is. Place by the front or by the back without measuring.
- Every transform applied, no parents: each mesh's matrix is the identity. (Blender doesn't save `matrix_world`: an object appended without `view_layer.update()` reads as the identity, so an object with a transform of its own lands in the wrong place; these can't.) Modifiers applied, except any smoothing (Subdivision), left at 0 in the viewport and on in renders; the triangle counts above are both ways. The empty is the one object with a transform: read it after an update.
- Every image packed into the .blend.
- Checked on every export (`tools/blender/check_export.py`): a fresh Blender appends every object into an empty scene without `view_layer.update()`, and the size, floor, centering, facing, names, version tags, packing and collections are asserted.

## Placing it

In Blender: File > Append, the file, `Object`, and select every `Bed ...` object (or `Collection`, and the collections you want).

In a script, append the collections you want and move their objects together; the footprint is centered on (x, y), turn is degrees about z, skip names collections to leave out (a choice of bedding), and the last lines check the facing:

```python
import bpy, math
from mathutils import Matrix, Vector

def place(path, x, y, turn=0.0, skip=()):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c not in skip]
    parts = [o for c in dst.collections for o in c.objects]
    for o in parts:
        bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    m = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(turn), 4, "Z")
    for o in parts:
        o.matrix_world = m @ o.matrix_world
    bpy.context.view_layer.update()
    # the facing: everything above 50.0" (the back) is behind the turned front
    back = Vector((-math.sin(math.radians(turn)), math.cos(math.radians(turn)), 0))
    tall = [o.matrix_world @ v.co for o in parts if o.type == "MESH" for v in o.data.vertices
            if (o.matrix_world @ v.co).z > 50.0 * 0.0254]
    assert all((p - Vector((x, y, 0))).dot(back) > 0 for p in tall), "facing the wrong way"
    return parts
```

Appending every object instead (`dst.objects = list(src.objects)`, as Sketchup-tools' `assets.place()` does) brings in the whole file: each file holds one choice of bedding, so that's always one bed.

## In SketchUp

File > Import, COLLADA (.dae), `sketchup/<file>.dae`: it's in inches, Z up, the same facing; keep the images beside it. Its materials are plain: each one's color, or its fabric's image, without the .blend's wood grain, sheen or wool relief. The .glb is the same in glTF (meters, as glTF always is).

## In Sketchup-tools

Copy the .blend into `library/models/<id>/`, and paste the record from [library.yaml](library.yaml) into `library/models/models.yaml` (its size, version and facing come from the file). Then
`assets.place("bed-frame-made-up", (x, y, 0), rot=..., objs=OBJS)` at its real size: give no width. rot=0: the headboard to the room's +y; in a room whose x runs south, rot=90 puts it to the north wall.

```yaml
bed-frame-made-up:
  use: the Arts & Crafts queen bed, made up (Design-render's bed frame)
  name: Queen bed frame, made up
  size_in:
  - 64.9
  - 85.1
  - 60.1
  source: https://github.com/sharpkathy123/Design-render/tree/main/deliverables/bed-frame
  version: Design-render 2026-11-12a (model/VERSION and CHANGELOG.md in the source)
  license: our own design; the Strawberry Thief scan is public domain (Cooper Hewitt, CC0)
  file: library/models/bed-frame-made-up/bed-frame-made-up.blend
  facing: 'rot=0: the headboard to the room''s +y; in a room whose x runs south, rot=90 puts it to the north wall'
```

## Textures and their rights

| Image (packed) | Source and rights |
|---|---|
| `Bed blockprint.png` | our own, drawn by `tools/make_fabric.py` (this repo, public) |
| `Bed caban_ao_1k.jpg` | Poly Haven, [Caban](https://polyhaven.com/a/caban), CC0: the wool's shading |
| `Bed caban_nor_gl_1k.jpg` | Poly Haven, [Caban](https://polyhaven.com/a/caban) (photography colormass, processing Rico Cilliers), CC0: the wool's weave and nap |
| `Bed kilim.png` | our own, drawn by `tools/make_fabric.py` (this repo, public) |
| `Bed morris-strawberry-thief.jpg` | William Morris, *Strawberry Thief*, designed 1883 (printed about 1934), [Cooper Hewitt, Smithsonian Design Museum, object 18340065](https://collection.cooperhewitt.org/objects/18340065/): the design is public domain and Cooper Hewitt releases the image as CC0 ([on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Textile,_Strawberry_Thief,_designed_1883,_printed_ca._1934_%28CH_18340065%29.jpg)). One repeat, cut from the scan to tile. |

## Footprint

[bed-frame-footprint.svg](../bed-frame-footprint.svg): the top view to scale, the frame solid and each version's bedding outline dashed, for a room's plan.

## Making them again

```
python3.11 designs/bed-frame/model.py --export-all
```
Add a line to [CHANGELOG.md](CHANGELOG.md) first: its newest line is the version.

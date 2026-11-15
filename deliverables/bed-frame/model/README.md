<!-- Written by tools/model_card.py from exports.json, CHANGELOG.md and share.yaml: edit those. -->
# Queen bed frame as a 3D model, for rendering rooms

**Version 2026-11-15c:** the coverlet tucked into the frame again, its foot corners sewn (client: tucked in, not covering the frame); the headboard's cover a plain light blue, the coverlet's (#9db0cc); a twin (38" x 75" mattress, for a pair in the NW bedroom) and a king (76" x 80", for the SE bedroom), each made up and bare, the posts, rails and joinery the queen's; the king with king pillows; a footprint drawing and cut list for each ([VERSION](VERSION) has every file's sha256; [CHANGELOG](CHANGELOG.md)). Every object in the files carries it too, as `o["design_render_version"]`.


## The files

| Version | Blender 4.5 | glTF (meters) | SketchUp (inches) | Size over everything, W x D x H | Triangles (viewport / render) |
|---|---|---|---|---|---|
| **Queen bed frame, made up** | [bed-frame-made-up.blend](bed-frame-made-up.blend) | [bed-frame-made-up.glb](bed-frame-made-up.glb) | [sketchup/bed-frame-made-up.dae](sketchup/bed-frame-made-up.dae) | 64 7/8" x 85 1/8" x 60 1/8" | 68,932 / 352,144 |
| **Queen bed frame, bare** | [bed-frame-bare.blend](bed-frame-bare.blend) | [bed-frame-bare.glb](bed-frame-bare.glb) | [sketchup/bed-frame-bare.dae](sketchup/bed-frame-bare.dae) | 64 7/8" x 85 1/8" x 60 1/8" | 4,912 / 4,912 |
| **Queen bed frame, with a quilt over the headboard** | [bed-frame-quilt.blend](bed-frame-quilt.blend) | [bed-frame-quilt.glb](bed-frame-quilt.glb) | [sketchup/bed-frame-quilt.dae](sketchup/bed-frame-quilt.dae) | 64 7/8" x 85 1/8" x 60 1/8" | 21,260 / 70,304 |
| **Twin bed frame, made up** | [bed-frame-twin-made-up.blend](bed-frame-twin-made-up.blend) | [bed-frame-twin-made-up.glb](bed-frame-twin-made-up.glb) | [sketchup/bed-frame-twin-made-up.dae](sketchup/bed-frame-twin-made-up.dae) | 42 7/8" x 80 1/8" x 60 1/8" | 46,616 / 263,856 |
| **Twin bed frame, bare** | [bed-frame-twin-bare.blend](bed-frame-twin-bare.blend) | [bed-frame-twin-bare.glb](bed-frame-twin-bare.glb) | [sketchup/bed-frame-twin-bare.dae](sketchup/bed-frame-twin-bare.dae) | 42 7/8" x 80 1/8" x 60 1/8" | 4,588 / 4,588 |
| **King bed frame, made up** | [bed-frame-king-made-up.blend](bed-frame-king-made-up.blend) | [bed-frame-king-made-up.glb](bed-frame-king-made-up.glb) | [sketchup/bed-frame-king-made-up.dae](sketchup/bed-frame-king-made-up.dae) | 80 7/8" x 85 1/8" x 60 1/8" | 76,644 / 382,344 |
| **King bed frame, bare** | [bed-frame-king-bare.blend](bed-frame-king-bare.blend) | [bed-frame-king-bare.glb](bed-frame-king-bare.glb) | [sketchup/bed-frame-king-bare.dae](sketchup/bed-frame-king-bare.dae) | 80 7/8" x 85 1/8" x 60 1/8" | 5,128 / 5,128 |

- **bed-frame-made-up.blend**: The bed made up: a coverlet in William Morris's Strawberry Thief tucked in between the mattress and the rails, its foot corners sewn; a plain white top sheet turned down about 10" over it; a wool plaid blanket folded across the foot; four white pillows stacked two by two; a plain light blue cover, the coverlet's blue, over the headboard; a white fitted sheet. Collections: `Bed frame` (59); `Bed mattress` (1); `Bedding: coverlet, top sheet, blanket and pillows` (8); `Bedding: headboard cover` (1).
- **bed-frame-bare.blend**: The frame and a mattress in a white fitted sheet, nothing else. Collections: `Bed frame` (59); `Bed mattress` (1).
- **bed-frame-quilt.blend**: The frame, a mattress in a white fitted sheet, and a pieced quilt (ochre and sage squares) draped over the headboard. Collections: `Bed frame` (59); `Bed mattress` (1); `Bedding: quilt` (1).
- **bed-frame-twin-made-up.blend**: The same bed at twin size (a 38" x 75" mattress; the posts, rails and joinery the queen's, four headboard slats), made up the same way, with one column of two pillows. Collections: `Bed frame` (56); `Bed mattress` (1); `Bedding: coverlet, top sheet, blanket and pillows` (6); `Bedding: headboard cover` (1).
- **bed-frame-twin-bare.blend**: The twin frame and a mattress in a white fitted sheet. Collections: `Bed frame` (56); `Bed mattress` (1).
- **bed-frame-king-made-up.blend**: The same bed at king size (a 76" x 80" mattress; the posts, rails and joinery the queen's, nine headboard slats), made up the same way, with king pillows (36" x 20") stacked two by two. Collections: `Bed frame` (61); `Bed mattress` (1); `Bedding: coverlet, top sheet, blanket and pillows` (8); `Bedding: headboard cover` (1).
- **bed-frame-king-bare.blend**: The king frame and a mattress in a white fitted sheet. Collections: `Bed frame` (61); `Bed mattress` (1).

The frame alone is 64 7/8" x 85 1/8" x 60 1/8" (W x D x H), the same in each of its files.
The twin's frame alone is 42 7/8" x 80 1/8" x 60 1/8" (W x D x H), the same in each of its files.
The king's frame alone is 80 7/8" x 85 1/8" x 60 1/8" (W x D x H), the same in each of its files.

Sizes are measured from the saved files by the export's check, not typed.

## What's in them

- Only meshes, and one empty: every object, mesh, material and image is named `Bed ...`, so appending them into a room that has its own `oak` or `brass` neither merges them nor makes `.001` copies. Materials: `Bed 2x4 pine`, `Bed 2x4 pine stained dark`, `Bed blanket`, `Bed brass aged`, `Bed coverlet`, `Bed headboard cover`, `Bed mattress sheet`, `Bed oak fumed grain x`, `Bed oak fumed grain y`, `Bed oak fumed grain z`, `Bed oak fumed pegs grain x`, `Bed pillowcase`, `Bed poplar`, `Bed quilt`, `Bed top sheet`.
- Real size in Blender meters (the scene's display unit set to inches). The floor is at z = 0 and the frame's footprint is centered on the origin.
- The foot faces -y and the headboard +y, with its back face at the bed's +y end: stand it with that face against a wall.
- An empty, `Bed front`, at the middle of the front on the floor, its arrow pointing -y (out of the front); its `depth_in` property is how far behind it the back is. Place by the front or by the back without measuring.
- Every transform applied, no parents: each mesh's matrix is the identity. (Blender doesn't save `matrix_world`: an object appended without `view_layer.update()` reads as the identity, so an object with a transform of its own lands in the wrong place; these can't.) Modifiers applied, except two kept live: a cloth's thickness (Solidify, so its sheet's own edges can be checked for open seams) and any smoothing (Subdivision, at 0 in the viewport and on in renders); the triangle counts above are both ways, thickness included. Sizes are of the meshes, without the cloth's thickness (under 1/2"). The empty is the one object with a transform: read it after an update.
- Every image packed into the .blend.
- Checked on every export (`tools/blender/check_export.py`): a fresh Blender appends every object into an empty scene without `view_layer.update()`, and the size, floor, centering, facing, names, version tags, packing and collections are asserted, and a sewn cloth (the coverlet) has no open edge at its corners.

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
  version: Design-render 2026-11-15c (model/VERSION and CHANGELOG.md in the source)
  license: our own design; the Strawberry Thief scan is public domain (Cooper Hewitt, CC0)
  file: library/models/bed-frame-made-up/bed-frame-made-up.blend
  facing: 'rot=0: the headboard to the room''s +y; in a room whose x runs south, rot=90 puts it to the north wall'
```

## Swapping a pattern

Each textile is its own material with one image: the node named `Pattern`, through a mapping named `Repeat`. The cloth's UVs are one unit to a meter of the cloth laid flat, so a print whose repeat is R inches takes `Repeat`'s scale 39.37 / R both ways (a different repeat across and down: each its own). No hue or saturation nodes: a print's color is in its image.

```python
m = bpy.data.materials["Bed coverlet"]
m.node_tree.nodes["Pattern"].image = bpy.data.images.load("golden-lily.jpg")
m.node_tree.nodes["Repeat"].inputs["Scale"].default_value = (39.37 / 21.0, 39.37 / 21.0, 1)   # a 21" repeat
```

| Material | Its pattern now | Repeat (across x along) |
|---|---|---|
| `Bed blanket` | `plaid.png` | 8" x 8" |
| `Bed coverlet` | `morris-strawberry-thief-print.jpg` | 18" x 19 5/8" |
| `Bed headboard cover` | `linen-blue.png` | 3" x 3" |
| `Bed mattress sheet` | `percale.png` | 2" x 2" |
| `Bed pillowcase` | `percale.png` | 2" x 2" |
| `Bed quilt` | `quilt.png` | 18" x 18" |
| `Bed top sheet` | `percale.png` | 2" x 2" |

## Textures and their rights

| Image (packed) | Source and rights |
|---|---|
| `Bed caban_nor_gl_1k.jpg` | Poly Haven, [Caban](https://polyhaven.com/a/caban) (photography colormass, processing Rico Cilliers), CC0: the wool's weave and nap, as the blanket's relief |
| `Bed linen-blue.png` | our own plain linen, drawn by `tools/make_fabric.py` (this repo, public), in the Strawberry Thief's leaf blue lightened (#9db0cc) |
| `Bed morris-strawberry-thief-print.jpg` | William Morris, *Strawberry Thief*, designed 1883 (printed about 1934), [Cooper Hewitt, Smithsonian Design Museum, object 18340065](https://collection.cooperhewitt.org/objects/18340065/): the design is public domain and Cooper Hewitt releases the image as CC0 ([on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Textile,_Strawberry_Thief,_designed_1883,_printed_ca._1934_%28CH_18340065%29.jpg)). One repeat, cut from the scan to tile, its color deepened a little (saturation 1.25, value 0.85) in the image. |
| `Bed percale.png` | our own plain white sheeting, drawn by `tools/make_fabric.py` (this repo, public) |
| `Bed plaid.png` | our own wool plaid, drawn by `tools/make_fabric.py` (this repo, public) |
| `Bed quilt.png` | our own pieced squares, drawn by `tools/make_fabric.py` (this repo, public) |

## Footprint

The top view to scale, the frame solid and each version's bedding outline dashed, for a room's plan: [the design's own size](../bed-frame-footprint.svg), [twin](../bed-frame-twin-footprint.svg), [king](../bed-frame-king-footprint.svg).

## Making them again

```
python3.11 designs/bed-frame/model.py --export-all
```
Add a line to [CHANGELOG.md](CHANGELOG.md) first: its newest line is the version.

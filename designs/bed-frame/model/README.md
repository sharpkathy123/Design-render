# The bed frame as a 3D model, for rendering rooms

Two Blender files (Blender 4.5), made by `designs/bed-frame/model.py --export`:

- **`bed-frame-made-up.blend`**: the bed made up: William Morris's Strawberry
  Thief over the headboard, an indigo block-print coverlet tucked in, a
  folded kilim blanket across the foot, four white pillows stacked two by
  two, and a dark fitted sheet. The fabric images are packed into the file.
- **`bed-frame-bare.blend`**: the frame and a mattress with a white sheet,
  nothing else.

## What's in them

- Only the bed's meshes, all named `Bed ...`: no lights, camera, floor or
  walls. Its materials are the fumed quartersawn oak, aged brass bolt
  covers and the fabrics.
- Real size in Blender meters. Over everything, the made-up bed is
  66 1/2" across, 85 5/8" long and 60 1/8" to the post tops. The frame
  alone is 64 7/8" x 85 1/8".
- The floor is at z = 0. The foot faces -y and the headboard is toward +y,
  with its back face at the bed's +y end. Stand it with that face against a
  wall.

## Placing it

In Blender: File > Append, then the file, Object, and select every `Bed ...`
object.

In a script, append every object and move them together. The bed's footprint
is centered on (x, y), and turn is degrees about z:

```python
import bpy, math
from mathutils import Matrix, Vector

def place_bed(path, x, y, turn=0.0):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    parts = [o for o in dst.objects if o]
    for o in parts:
        bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in parts for c in o.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)])
    hi = Vector([max(p[k] for p in pts) for k in range(3)])
    m = (Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(turn), 4, "Z")
         @ Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))
    for o in parts:
        o.matrix_world = m @ o.matrix_world
    return parts
```

In Sketchup-tools: copy the file into `library/models/bed-frame-made-up/`
and add a record to `library/models/models.yaml`:

```yaml
bed-frame-made-up:
  use: the Arts & Crafts queen bed, made up (Design-render's bed frame)
  name: Queen bed frame, made up
  size_in: [66.5, 85.6, 60.1]
  source: https://github.com/sharpkathy123/Design-render/tree/main/deliverables/bed-frame
  license: our own design; the Strawberry Thief scan is public domain (Cooper Hewitt, CC0)
  file: library/models/bed-frame-made-up/bed-frame-made-up.blend
```

Then place it with
`assets.place("bed-frame-made-up", (x, y, 0), rot=..., objs=OBJS)` at its
real size: give no width. With rot=0 the headboard is toward the room's +y.

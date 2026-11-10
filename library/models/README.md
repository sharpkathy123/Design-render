# Models

Free 3D models for the renders, so furniture and accessories don't have to be
drawn from boxes (client, 2026-10-21). All are from
[Poly Haven](https://polyhaven.com/) and released as CC0 (public domain):
free to use and share, no credit required.

- **[models.yaml](models.yaml)** lists them: what each is for, its real size
  in inches, its author and source.
- **To add one:** `python3 tools/fetch_models.py --list <words>` shows what
  Poly Haven has; add its id to `models.yaml` with a `use:` line and run
  `python3 tools/fetch_models.py` (1k textures; keep each under about 10 MB).
- **To use one in a room model:** `assets.place(id, (x, y, z), rot=..., width=..., tint="#hex")`
  ([tools/blender/assets.py](../../tools/blender/assets.py)); the mud room's
  options take an `assets:` list. Trial: [the painted bench and a vase in the mud room](../../rooms/mud-room/renders/mudroom-library-models-trial-quick.jpg).
- The second floor's vases of flowers (D10) use `ceramic_vase_01`,
  `ceramic_vase_02` and `periwinkle_plant` through
  `tools/blender/vanity_render_setup.py`; only their color, roughness and
  opacity maps are kept, and the renderer builds its own materials.

Not here: anything copyrighted. Models from other sites (BlenderKit,
Sketchfab) can't be downloaded from the cloud sessions; download them
yourself and drop the file in a folder here, with its license in `models.yaml`.

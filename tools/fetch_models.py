"""Download the free 3D models listed in library/models/models.yaml (client,
2026-10-21: a library of real models for the renders, instead of drawing
every vase, bench and basket from boxes).

Every model so far is from Poly Haven (polyhaven.com), released as CC0: in
the public domain, free to use and share, no credit required. Each goes in
library/models/<id>/ as Poly Haven's 1k .blend with its textures, plus its
real size (from Poly Haven's own record) written back into models.yaml.

    python3 tools/fetch_models.py          # fetch any that are missing
    python3 tools/fetch_models.py ID ...   # fetch just these (Design-render, 2026-11-10)
    python3 tools/fetch_models.py --list   # what Poly Haven has, by keyword

Then, in a Blender model: assets.place("painted_wooden_bench", ...)
(tools/blender/assets.py).

Sketchfab too (client, 2026-10-30: household things Poly Haven doesn't
have): a record whose `source` is a sketchfab.com/3d-models/... page is
downloaded through Sketchfab's API with the client's token (the
environment variable SKETCHFAB_API_TOKEN, from sketchfab.com, Settings,
Password & API), as glTF, and saved as a .blend beside it with Blender's
Python. Only CC0 and CC Attribution models (attribution recorded in the
record's `author`, `license` and `source`); NonCommercial and
NoDerivatives ones are refused: the house is let, and recoloring is
deriving.

    python3 tools/fetch_models.py --sketchfab toaster   # search: name, license, faces, page
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "vendor"))
import yaml  # noqa: E402

MODELS = os.path.join(ROOT, "library", "models")
INDEX = os.path.join(MODELS, "models.yaml")
UA = {"User-Agent": "design-render model fetcher"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def sketchfab(mid, rec):
    """Download a Sketchfab model as glTF and save it as a .blend (see above)."""
    import io
    import subprocess
    import zipfile
    out = os.path.join(MODELS, mid)
    uid = rec["source"].rstrip("/").split("-")[-1]
    info = json.loads(get("https://api.sketchfab.com/v3/models/%s" % uid))
    lic = (info.get("license") or {}).get("label", "")
    if "NonCommercial" in lic or "NoDeriv" in lic or not lic:
        raise SystemExit("%s: its license (%s) won't do: CC0 or CC Attribution only" % (mid, lic or "none"))
    token = os.environ.get("SKETCHFAB_API_TOKEN")
    if not token:
        raise SystemExit("SKETCHFAB_API_TOKEN isn't set: the client's Sketchfab API token, in the environment")
    req = urllib.request.Request("https://api.sketchfab.com/v3/models/%s/download" % uid,
                                 headers=dict(UA, Authorization="Token " + token))
    with urllib.request.urlopen(req, timeout=60) as r:
        links = json.loads(r.read())
    os.makedirs(out, exist_ok=True)
    if links.get("glb"):
        src = os.path.join(out, "model.glb")
        open(src, "wb").write(get(links["glb"]["url"]))
    else:
        zipfile.ZipFile(io.BytesIO(get(links["gltf"]["url"]))).extractall(os.path.join(out, "gltf"))
        src = os.path.join(out, "gltf", "scene.gltf")
    blend = os.path.join(out, mid + ".blend")
    conv = ("import bpy, json, sys\n"
            "bpy.ops.wm.read_factory_settings(use_empty=True)\n"
            "bpy.ops.import_scene.gltf(filepath=sys.argv[-2])\n"
            "ms = [o for o in bpy.data.objects if o.type == 'MESH']\n"
            "from mathutils import Vector\n"
            "pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]\n"
            "lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]\n"
            "print('SIZE', json.dumps([round((hi[i] - lo[i]) / 0.0254, 1) for i in range(3)]))\n"
            "bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1], compress=True)\n")
    r = subprocess.run(["/usr/bin/python3.11", "-c", conv, src, blend], capture_output=True, text=True)
    size = [l for l in r.stdout.splitlines() if l.startswith("SIZE ")]
    if not os.path.exists(blend):
        raise SystemExit("%s: Blender couldn't convert it: %s" % (mid, r.stderr[-400:]))
    if size:
        rec["size_in"] = json.loads(size[0][5:])
    # (the .blend packs the textures: the download itself isn't kept)
    import shutil
    if os.path.exists(os.path.join(out, "model.glb")):
        os.remove(os.path.join(out, "model.glb"))
    shutil.rmtree(os.path.join(out, "gltf"), ignore_errors=True)
    rec.setdefault("name", info.get("name"))
    rec.setdefault("author", (info.get("user") or {}).get("displayName") or (info.get("user") or {}).get("username"))
    rec["license"] = lic
    rec["file"] = os.path.relpath(blend, ROOT)


def fetch(mid, rec):
    if "sketchfab.com" in (rec.get("source") or ""):
        return sketchfab(mid, rec)
    out = os.path.join(MODELS, mid)
    files = json.loads(get("https://api.polyhaven.com/files/%s" % mid))
    blend = files["blend"]["1k"]["blend"]
    todo = [(blend["url"], os.path.basename(blend["url"]))]
    todo += [(v["url"], k) for k, v in (blend.get("include") or {}).items()]
    for url, rel in todo:
        path = os.path.join(out, rel)
        if os.path.exists(path):
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "wb").write(get(url))
        time.sleep(0.5)
    info = json.loads(get("https://api.polyhaven.com/info/%s" % mid))
    rec.setdefault("name", info.get("name"))
    rec.setdefault("author", ", ".join(info.get("authors", {})))
    if info.get("dimensions"):
        rec["size_in"] = [round(d / 25.4, 1) for d in info["dimensions"]]   # (mm, as Poly Haven gives it)
    rec.setdefault("source", "https://polyhaven.com/a/%s" % mid)
    rec.setdefault("license", "CC0 (public domain)")
    rec["file"] = os.path.relpath(os.path.join(out, os.path.basename(blend["url"])), ROOT)


def main():
    if "--sketchfab" in sys.argv:
        import urllib.parse
        q = " ".join(sys.argv[sys.argv.index("--sketchfab") + 1:])
        res = json.loads(get("https://api.sketchfab.com/v3/search?type=models&downloadable=true&count=24&q=" +
                             urllib.parse.quote(q)))
        for r in res.get("results", []):
            lic = (r.get("license") or {}).get("label", "?")
            if "NonCommercial" in lic or "NoDeriv" in lic:
                continue
            print("%s | %s | %s faces | %s" % (r["name"], lic, r.get("faceCount"), r.get("viewerUrl")))
        return
    if "--list" in sys.argv:
        words = [w.lower() for w in sys.argv[2:]] or ["chair", "bench", "vase", "basket", "plant", "lamp"]
        assets = json.loads(get("https://api.polyhaven.com/assets?t=models"))
        for k, v in sorted(assets.items()):
            text = " ".join([k] + v.get("tags", []) + v.get("categories", [])).lower()
            if any(w in text for w in words):
                print(k, "-", v.get("name"))
        return
    index = yaml.safe_load(open(INDEX)) or {}
    only = [a for a in sys.argv[1:] if not a.startswith("-")]   # (ids given: fetch just those)
    changed = False
    for mid, rec in index.items():
        if only and mid not in only:
            continue
        if rec.get("file") and os.path.exists(os.path.join(ROOT, rec["file"])):
            continue
        print("fetching", mid)
        fetch(mid, rec)
        changed = True
    if changed:
        with open(INDEX, "w") as f:
            f.write("# The 3D models the renders can use (tools/fetch_models.py fetches them;\n"
                    "# tools/blender/assets.py places them). size_in: width, depth, height, inches.\n")
            yaml.safe_dump(index, f, sort_keys=False, allow_unicode=True, width=100)
    print("models: %d listed" % len(index))


if __name__ == "__main__":
    main()

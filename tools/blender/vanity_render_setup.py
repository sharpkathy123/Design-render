"""Turn an exported SketchUp vanity into a ready-to-render Blender scene.

Works with the model built by rta_vanity.rb (materials named Vanity_*),
exported from SketchUp as COLLADA (.dae), OBJ, FBX, STL or glTF.

In Blender: open the Scripting workspace, open this file, set MODEL_PATH
below (or import the model yourself first and leave it empty), press Run.

From a terminal (renders straight to a PNG):
    blender -b -P vanity_render_setup.py -- --model vanity.dae --render vanity.png
    blender -b -P vanity_render_setup.py -- --model vanity.dae --finish oak --render oak.png
    blender -b -P vanity_render_setup.py -- --model vanity.dae --faucet chrome --render chrome.png
    blender -b -P vanity_render_setup.py -- --model vanity.dae --view entry --render entry.png
    blender -b -P vanity_render_setup.py -- --model vanity.dae --view opposite --render tub.png

Views: "front" looks straight at the vanities; if the model has the whole room
(tub, toilet, ceiling), those are cut away so they don't block the view.
"entry" stands in the entry hallway and looks into the room; "opposite"
stands in front of the vanities and looks across at the tub and toilet (both
need a model built with a whole room).

Tested with Blender 4.5 LTS. COLLADA import was removed in Blender 5.0, so
for .dae files use Blender 4.5 (or earlier), save a .blend, and open that
in newer versions -- or export OBJ from SketchUp instead (see README).
"""

import json
import math
import os
import re
import sys

import bpy
from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
MODEL_PATH = ""            # e.g. r"C:\Projects\bath\vanity.dae"; empty = use the open scene
OBJ_UP_AXIS = "Z"          # SketchUp is Z-up; use "Y" if your OBJ exporter swapped Y/Z
CLEAR_SCENE = True         # delete all objects before importing MODEL_PATH
RENDER_PATH = ""           # set to render a still when the script runs
SAMPLES = 128
RESOLUTION = (1920, 1440)
BEVEL_WIDTH = 0.0015       # metres; softens SketchUp's razor edges. 0 = off
EYE_HEIGHT = 1.60          # metres (63"): every view is taken from eye level
STONE_EDGE = 0.006         # metres; eased (rounded-over) edge on the marble top and
                           # splashes, about 1/4". The rounded corners are in the model
VIEW = "front"             # "front" (the vanities), "entry" (from the entry hallway) or
                           # "opposite" (across the room to the tub and toilet)
FINISH = "white"           # cabinet finish: a key of FINISHES below

# Cabinet finishes. Colours are linear-ish sRGB triples in 0..1.
FINISHES = {
    "white": dict(color=(0.86, 0.85, 0.82), roughness=0.38, coat=0.15),   # satin white paint
    "oak":   dict(color=(0.17, 0.09, 0.04), roughness=0.45, coat=0.25, wood=True),  # stained quarter-sawn oak
}
# Other paint colours: navy (0.05, 0.08, 0.15), sage (0.35, 0.42, 0.33).

FAUCET = "nickel"          # faucet and drain finish: a key of FAUCETS below
FAUCETS = {
    "nickel": dict(color=(0.80, 0.76, 0.66), roughness=0.10, metallic=1.0),  # polished nickel (warm)
    "chrome": dict(color=(0.90, 0.90, 0.92), roughness=0.05, metallic=1.0),  # polished chrome (cool)
}

# Material recipes, keyed by the SketchUp material name after "Vanity_".
# Colours are linear-ish sRGB triples in 0..1.
MATERIALS = {
    "finish":     FINISHES[FINISH],
    "upper":      FINISHES["white"],   # tall (linen) cabinets: white paint, whatever FINISH is
    "interior":   dict(color=(0.62, 0.47, 0.30), roughness=0.60),              # maple plywood
    "basket_shadow": dict(color=(0.10, 0.06, 0.03), roughness=0.9),        # the dark gaps in a woven basket
    "ivyleaf":    dict(color=(0.035, 0.11, 0.03), roughness=0.45, coat=0.4),  # glossy dark ivy leaves
    "planter":    dict(color=(0.11, 0.19, 0.08), roughness=0.3, coat=0.5),   # an art-pottery planter (its glaze from the scheme)
    "countertop": dict(color=(0.86, 0.86, 0.84), roughness=0.22, marble=True),   # honed Carrara-type marble
    # for white quartz instead: dict(color=(0.90, 0.90, 0.88), roughness=0.12, speckle=True)
    "hardware":   FAUCETS[FAUCET],     # pulls match the faucets
    "faucet":     FAUCETS[FAUCET],
    "sink":       dict(color=(0.95, 0.95, 0.95), roughness=0.05, coat=0.6),    # glazed ceramic
    "mirror":     dict(color=(0.95, 0.95, 0.95), roughness=0.0, metallic=1.0),
    "floor":      dict(color=(0.86, 0.86, 0.84), roughness=0.3, hex=0.0635),   # white 2 1/2" hex tile
    # for 12x24 grey tile instead: dict(color=(0.45, 0.45, 0.44), roughness=0.45, tiles=True)
    "wall":       dict(color=(0.445, 0.723, 0.730), roughness=0.85),           # robin's egg blue paint
    "ceiling":    dict(color=(0.93, 0.93, 0.91), roughness=0.9),               # white ceiling paint
    "tile":       dict(color=(0.88, 0.88, 0.86), roughness=0.08, coat=0.5, subway=True),  # 3x6 subway tile
    "trim":       dict(color=(0.86, 0.85, 0.82), roughness=0.35, coat=0.1),    # painted window trim
    "glass":      dict(color=(0.92, 0.96, 1.0), emission=2.5),                 # window: daylight
    # the house's own door hardware (client, 2026-10-30: designer/client_photos/house_door_original_fivepanel.jpg):
    # aged, unlacquered brass, a little worn; props.door_knob()
    "doorbrass":  dict(color=(0.50, 0.36, 0.17), roughness=0.35, metallic=1.0),
    "keyhole":    dict(color=(0.02, 0.02, 0.02), roughness=0.8),
    "porcelain":  dict(color=(0.95, 0.95, 0.94), roughness=0.05, coat=0.7),    # tub and toilet
    "curtain":    dict(color=(0.80, 0.78, 0.70), roughness=0.95, sheen=0.6),   # linen shower curtain
    "opal":       dict(color=(1.0, 0.86, 0.66), roughness=0.3, emission=3.0),  # lit opal-glass shades, warm white
    "amber":      dict(color=(0.39, 0.05, 0.03), roughness=0.05, transmission=0.85),  # amber glass vases
    "shelfprint": dict(color=(0.89, 0.85, 0.75), roughness=0.9),                       # D6-SUNNY/SKY plate (hidden otherwise)
    "shelfprint2": dict(color=(0.89, 0.85, 0.75), roughness=0.9),                      # and the tub-side shelf's
    "toiletprint": dict(color=(0.89, 0.85, 0.75), roughness=0.9),                      # the print over the toilet (hidden otherwise)
    "vanityprint": dict(color=(0.88, 0.84, 0.73), roughness=0.9),                      # D11: the plates flanking the vanity mirrors
    "vanityprint2": dict(color=(0.88, 0.84, 0.73), roughness=0.9),                     # (left and right; hidden when the spot is empty)
    "flowervase": dict(color=(0.9, 0.93, 0.92), roughness=0.03, transmission=0.95),    # D10: clear glass vases of flowers
    "stem":       dict(color=(0.08, 0.16, 0.04), roughness=0.6),                     # their stems and leaves
    "bloom_a":    dict(color=(0.69, 0.20, 0.03), roughness=0.7, sheen=0.3),          # blooms (set by scheme)
    "bloom_b":    dict(color=(0.79, 0.39, 0.01), roughness=0.7, sheen=0.3),
    "bloom_c":    dict(color=(0.39, 0.05, 0.03), roughness=0.7, sheen=0.3),
    "bloom_eye":  dict(color=(0.07, 0.03, 0.01), roughness=0.7),
    "leanprint":  dict(color=(0.76, 0.30, 0.05), roughness=0.8),                     # D6 leaning print (placeholder)
    "soap":       dict(color=(0.15, 0.04, 0.01), roughness=0.08, transmission=0.7),   # brown glass soap pumps
    "pump":       dict(color=(0.72, 0.36, 0.20), roughness=0.3, metallic=1.0),       # copper pump tops
    "wastecan":   dict(color=(0.80, 0.79, 0.76), roughness=0.22, metallic=1.0),      # the toilet's step can: polished stainless, fingerprint-proof (a soft polish)
    "tissue_box": dict(color=(0.39, 0.05, 0.03), roughness=0.25, coat=0.5),         # glazed ceramic
    "tissue":     dict(color=(0.95, 0.95, 0.93), roughness=0.9, sheen=0.3),
    "iron":       dict(color=(0.018, 0.017, 0.016), roughness=0.55, metallic=0.6),  # the heat registers: cast iron, satin black
    "duct":       dict(color=(0.002, 0.002, 0.002), roughness=1.0),                 # the dark duct behind a grille
    "accent":     dict(color=(0.028, 0.109, 0.102), roughness=0.08, coat=0.5),   # glazed accent tile: wainscot base, liner
    "border":     dict(color=(0.028, 0.109, 0.102), roughness=0.3, hex=0.0635),  # the hex floor tile in the accent colour
    "frosted":    dict(color=(0.85, 0.88, 0.90), emission=1.2),                 # obscure glass, lit from outside
    "section":    dict(color=(0.55, 0.55, 0.55), roughness=1.0, emission=1.0),  # a wall's cut end, light grey as on a drawing
    # textiles in the stained glass colours
    "rug":        dict(color=(0.011, 0.042, 0.216), roughness=1.0, sheen=0.8),  # blue rag runner
    "cream":      dict(color=(0.82, 0.75, 0.56), roughness=1.0, sheen=0.6),
    "orange":     dict(color=(0.63, 0.14, 0.015), roughness=0.95, sheen=0.7),   # hand towels, rug bands
    "yellow":     dict(color=(0.76, 0.43, 0.021), roughness=0.95, sheen=0.6),   # cafe curtain, rug bands
    "tan":        dict(color=(0.52, 0.38, 0.19), roughness=1.0, sheen=0.6),     # Persian-style runner: border
    "navy":       dict(color=(0.013, 0.023, 0.078), roughness=1.0, sheen=0.7),  # and bands
    "towel":      dict(color=(0.87, 0.85, 0.80), roughness=1.0, sheen=0.8),     # white hand towels
    "black":      dict(color=(0.02, 0.02, 0.02), roughness=0.3),                # switch buttons, receptacle slots
    # (for a model part whose spot the scheme leaves empty: it's hidden)
    "print":      dict(color=(0.88, 0.84, 0.73), roughness=0.9),
    "print2":     dict(color=(0.88, 0.84, 0.73), roughness=0.9),
    "artblock_a": dict(color=(0.88, 0.84, 0.73), roughness=0.85),
    "artblock_b": dict(color=(0.88, 0.84, 0.73), roughness=0.85),
    "artblock_c": dict(color=(0.88, 0.84, 0.73), roughness=0.85),
    "arch":       dict(color=(0.57, 0.30, 0.04), roughness=0.9),                # a colour-block arch (none now)
}
# Matte black hardware: color=(0.03, 0.03, 0.03), roughness=0.35.

# The scheme: a room's file of spots (rooms/<room>/room.yaml), the scheme's
# picks for them (rooms/<room>/schemes/<scheme>.yaml) and the library items
# they name (library/<category>/<id>/item.yaml), whose render values
# override the recipes above. SCHEME picks the scheme (default: oak with
# oak cabinets, white otherwise), ROOM the room.
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
LIBRARY = os.path.join(ROOT, "library")
ROOM = os.environ.get("ROOM", "second-floor-bath")
try:
    import yaml
except ImportError:
    # (Blender's own Python has no PyYAML: the pure-Python copy in tools/vendor)
    sys.path.insert(0, os.path.join(ROOT, "tools", "vendor"))
    import yaml


# hang towels at the model's towel markers (a cloth simulation per render)
TOWELS = os.environ.get("TOWELS", "1") != "0"
TEXTURES = os.path.join(LIBRARY, "textures")
# D10's vases of flowers: Poly Haven (CC0) models in models/ -- a round
# glazed jar (counter), a slim bottle (window sill) and periwinkle sprigs,
# whose pink flowers are recoloured in each scheme's three bloom colours
MODELS = os.path.join(LIBRARY, "models")
FLOWERS = os.environ.get("FLOWERS", "1") != "0"


def hex_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def load_library():
    """Every library item, by id."""
    items = {}
    for dirpath, _, files in os.walk(LIBRARY):
        if "item.yaml" in files:
            rec = yaml.safe_load(open(os.path.join(dirpath, "item.yaml")))
            items[rec["id"]] = rec
    # SHAREABLE=1: copyrighted designs swapped for simple stand-ins in their own
    # colours (library/textures/share/, made by tools/make_shareable.py), so a
    # render can be shown to others (client, 2026-10-15)
    if os.environ.get("SHAREABLE"):
        for rec in items.values():
            r = rec.get("render") or {}
            alt = os.path.join("library", "textures", "share", rec["id"] + ".png")
            if rec.get("rights") == "copyrighted" and r.get("image") and os.path.exists(os.path.join(ROOT, alt)):
                r["image"] = alt
    return items


def scheme_name(finish="white"):
    return os.environ.get("SCHEME") or ("oak" if finish == "oak" else "white")


def scheme_path(rd, name):
    """A scheme's file: rooms/<room>/schemes/<name>.yaml, or a trial's,
    rooms/<room>/trials/<name>.yaml (a what-if, rendered but kept out of the
    documents, mood boards and schedule until the client picks it)."""
    p = os.path.join(rd, "schemes", name + ".yaml")
    return p if os.path.exists(p) else os.path.join(rd, "trials", name + ".yaml")


def load_scheme(finish="white"):
    """The room, the library and this scheme's pick for every spot: the
    room's defaults, then the scheme's own, then any SPOTS=spot=item,...
    given for a test (SPOTS=walls=paint-bm-perfect-peach-2167-50; a+b for
    two plates in one frame)."""
    rd = os.path.join(ROOT, "rooms", ROOM)
    room = yaml.safe_load(open(os.path.join(rd, "room.yaml")))
    sch = yaml.safe_load(open(scheme_path(rd, scheme_name(finish))))
    picks = {sp: {"item": iid} for sp, iid in (room.get("defaults") or {}).items()}
    picks.update(sch.get("spots") or {})
    for kv in filter(None, os.environ.get("SPOTS", "").split(",")):
        sp, iid = kv.split("=", 1)
        ids = [i.strip() for i in iid.split("+")]     # a+b: several plates in one frame
        if ids in ([""], ["none"]):                   # spot=none: leave the spot empty
            picks.pop(sp.strip(), None)
            continue
        keep = {k: v for k, v in (picks.get(sp.strip()) or {}).items() if k not in ("item", "items", "label")}
        picks[sp.strip()] = dict(keep, **({"items": ids} if len(ids) > 1 else {"item": ids[0]}))
    return room, sch, picks, load_library()


def recipe(r):
    """A render recipe from a file: '#rrggbb' colours to linear, image paths
    from the repository root, pairs (a repeat) as tuples."""
    out = {}
    for k, v in r.items():
        if v is None:
            continue
        if isinstance(v, str) and re.fullmatch("#[0-9A-Fa-f]{6}", v):
            v = hex_linear(v)
        elif k == "image":
            v = os.path.normpath(os.path.join(ROOT, v))
        elif k == "colors":
            v = recipe(v)
        elif k == "variants":
            v = dict(v)
        elif k == "ramp":
            v = tuple(hex_linear(x) if isinstance(x, str) else tuple(x) for x in v)
        elif isinstance(v, list):
            v = tuple(v)
        out[k] = v
    return out


def spot_item(picks, lib, spot):
    """The library item in a spot, or None when it's empty."""
    iid = (picks.get(spot) or {}).get("item")
    if not iid or iid == "none":
        return None
    if iid not in lib:
        raise KeyError("%s: no library item %r" % (spot, iid))
    return lib[iid]


def spot_items(picks, lib, spot):
    """The library items in a spot, as a list: several for a plural
    `items` pick (two or three plates side by side in one frame -- the
    same list convention scheme_towels already uses for bath towels),
    one for a singular `item` pick, none when the spot is empty."""
    ids = (picks.get(spot) or {}).get("items")
    if ids:
        out = []
        for iid in ids:
            if iid not in lib:
                raise KeyError("%s: no library item %r" % (spot, iid))
            out.append(lib[iid])
        return out
    item = spot_item(picks, lib, spot)
    return [item] if item is not None else []


def spot_slots(room, item, spot, images=True):
    """{slot: recipe} that the item in a spot fills. An image not already
    made for the spot (`fitted`) is fitted to it here: a plate put on the
    spot's mat (settings `mat`), or one repeat of a fabric tiled to the
    size of a part it's stretched over (settings `size_in`)."""
    sd = room["spots"][spot]
    r = item.get("render") or {}
    if "slots" in r:
        return {k: recipe(v) for k, v in r["slots"].items()}
    merged = dict(r, **(sd.get("settings") or {}))
    mat = merged.pop("mat", None)
    size = merged.pop("size_in", None)
    fitted = merged.pop("fitted", False)
    caption = merged.pop("caption", None)
    if images and merged.get("image") and not fitted:
        src = os.path.join(ROOT, merged["image"])
        if mat:
            merged["image"] = matted_image(src, mat["opening"], mat["plate"], caption=caption)
        elif size and merged.get("whole") and merged.get("repeat"):
            merged["image"] = tiled_image(src, merged["repeat"], size)
    return {slot: recipe(merged) for slot in sd["slots"]}


def spot_slots_multi(room, items, spot, images=True):
    """Like spot_slots(), for a spot whose pick is a plural `items` list:
    a multi_matted_image() of all of them side by side on one mat,
    instead of one plate alone. Needs the spot's `mat_multi` setting (a
    landscape opening wide enough that one portrait plate alone leaves a
    sea of empty mat either side -- the vanity-side peg-shelf frame,
    client-approved 2026-10-09, see designer/history/BRIEF.md)."""
    sd = room["spots"][spot]
    merged = dict(sd.get("settings") or {})
    mat_multi = merged.pop("mat_multi", None)
    merged.pop("mat", None)
    merged.pop("fitted", None)
    merged.pop("caption", None)
    if images and mat_multi:
        srcs = [os.path.join(ROOT, it["render"]["image"]) for it in items]
        captions = [(it.get("render") or {}).get("caption") for it in items]
        merged["image"] = multi_matted_image(
            srcs, mat_multi["opening"],
            plate_h=mat_multi.get("plate_h", 9.5),
            gutter=mat_multi.get("gutter", 0.55),
            captions=captions)
        merged.setdefault("color", mat_multi.get("color", "#F2EDE0"))
        merged.setdefault("pattern", "photo")
    return {slot: recipe(merged) for slot in sd["slots"]}


def _image_array(path):
    """An image file as a float array, top row first, RGB."""
    import numpy as np
    im = bpy.data.images.load(path, check_existing=True)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, im.channels)[::-1, :, :3]
    return a


def _image_array_rgba(path):
    """Like `_image_array`, but keeps the alpha channel (adding an opaque
    one if the file has none), for an image meant to be composited over
    something rather than fill a rectangle outright -- a caption label."""
    import numpy as np
    im = bpy.data.images.load(path, check_existing=True)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, im.channels)[::-1, :, :]
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones((h, w, 1), dtype=np.float32)], axis=2)
    return a


def _composite(canvas, rgba, x, y):
    """Alpha-blends `rgba` (an (h, w, 4) array) onto `canvas` with its
    top-left corner at (x, y); clips to the canvas if it would overhang."""
    import numpy as np
    h, w = rgba.shape[:2]
    H, W = canvas.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    alpha = src[..., 3:4]
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - alpha) + src[..., :3] * alpha


def _save_array(a, name):
    import numpy as np
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "vanity-fitted")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, name)
    h, w = a.shape[:2]
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = a
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    return out


def _resize(a, w, h):
    import numpy as np
    ys = np.clip(((np.arange(h) + 0.5) * a.shape[0] / h).astype(int), 0, a.shape[0] - 1)
    xs = np.clip(((np.arange(w) + 0.5) * a.shape[1] / w).astype(int), 0, a.shape[1] - 1)
    return a[ys][:, xs]


def _caption_path(src):
    """Where tools/make_art_texture.py wrote this item's pre-rendered,
    antialiased caption image (if any) -- same basename as the texture,
    under library/textures/captions/."""
    base = os.path.splitext(os.path.basename(src))[0]
    return os.path.join(ROOT, "library", "textures", "captions", base + ".png")


def matted_image(src, opening, plate, ppi=80, colour="#F2EDE0", caption=None):
    """The plate (stretched to `plate` inches) centred on an off-white mat
    the size of the frame's `opening`, with a faint shadow round it, a thin
    rule marking the plate window, and -- if `tools/make_art_texture.py` has
    rendered a caption image for this item -- that caption composited under
    it (client-approved mockup, 2026-10-09: see designer/history/BRIEF.md). The
    caption is a pre-rendered, antialiased PNG (serif type, via PIL) rather
    than text drawn live here, since Blender's bundled Python has no font
    library -- see `_caption_path`. `ppi` defaults higher than the plain,
    captionless mat used to (was 40) because text needs real resolution to
    look crisp; it was effectively ~95-100ppi in the approved mockup. When
    there's a caption, the plate+caption are centred as one group, not the
    plate alone, so the label doesn't crowd the mat's bottom edge."""
    import numpy as np
    W, H = int(opening[0] * ppi), int(opening[1] * ppi)
    # the plate at its own proportions, as big as the `plate` box allows (as
    # tools/make_prints.py cuts the real window), never stretched to fill
    # it: a tall narrow plate was drawn a third too wide (client, 2026-10-16)
    src_img = _image_array(src)
    s_ = min(plate[0] * ppi / src_img.shape[1], plate[1] * ppi / src_img.shape[0])
    pw, ph = max(1, int(src_img.shape[1] * s_)), max(1, int(src_img.shape[0] * s_))
    rule = np.array([0.30, 0.24, 0.16], dtype=np.float32)  # a fine dark-umber rule, not black
    out = np.ones((H, W, 3), dtype=np.float32) * np.array([int(colour[i:i + 2], 16) / 255.0 for i in (1, 3, 5)],
                                                          dtype=np.float32)

    cap_rgba = None
    cap_h = 0
    cap_gap = max(8, ppi // 5)
    if caption:
        cap_path = _caption_path(src)
        if os.path.exists(cap_path):
            raw = _image_array_rgba(cap_path)
            ch, cw = raw.shape[:2]
            margin = max(10, ppi // 4)
            target_h = max(1, int(0.22 * ppi))                      # a modest printed-label size
            max_w = W - 2 * margin
            if cw > 0 and ch > 0:
                scale = target_h / ch
                if cw * scale > max_w:                               # shrink further to fit the mat's width
                    scale = max_w / cw
                new_w, new_h = max(1, int(cw * scale)), max(1, int(ch * scale))
                cap_rgba = _resize(raw, new_w, new_h)
                cap_h = new_h + cap_gap

    x0 = (W - pw) // 2
    y0 = max(0, (H - cap_h - ph - int(0.48 * ppi)) // 2 + int(0.24 * ppi))   # (room for the bevel and rule round it)

    # a cut mat, as tools/make_prints.py draws the real one: the plate seen
    # through a window with a white bevel round it (lit from the upper left:
    # its top and left sides in shade), the shadow the cut edge casts on the
    # plate, and a fine rule drawn on the mat a little way out (it was a
    # flat panel with a hairline round the plate; client, 2026-10-16)
    t = max(1, ppi // 40)
    bev = max(2, int(0.14 * ppi))
    gap = max(3, int(0.34 * ppi))
    core = np.array([0.985, 0.975, 0.955], dtype=np.float32)
    out[y0 - bev:y0 + ph + bev, x0 - bev:x0 + pw + bev] = core                     # the bevel, lit sides
    out[y0 - bev:y0, x0 - bev:x0 + pw + bev] = core * 0.86                         # top side, in shade
    out[y0 - bev:y0 + ph + bev, x0 - bev:x0] = core * 0.90                         # left side, in shade
    out[y0:y0 + ph, x0:x0 + pw] = _resize(src_img, pw, ph)                         # the plate
    sh = max(1, bev // 2)
    out[y0:y0 + sh, x0:x0 + pw] *= 0.82                                            # the cut edge's shadow
    out[y0:y0 + ph, x0:x0 + sh] *= 0.86
    r0, r1 = (y0 - bev - gap, x0 - bev - gap), (y0 + ph + bev + gap, x0 + pw + bev + gap)
    if r0[0] - t >= 0 and r0[1] - t >= 0 and r1[0] + t <= H and r1[1] + t <= W:
        out[r0[0] - t:r0[0], r0[1] - t:r1[1] + t] = rule                           # rule: top
        out[r1[0]:r1[0] + t, r0[1] - t:r1[1] + t] = rule                           # rule: bottom
        out[r0[0] - t:r1[0] + t, r0[1] - t:r0[1]] = rule                           # rule: left
        out[r0[0] - t:r1[0] + t, r1[1]:r1[1] + t] = rule                           # rule: right

    if cap_rgba is not None:
        cw = cap_rgba.shape[1]
        _composite(out, cap_rgba, (W - cw) // 2, min(H - cap_rgba.shape[0], y0 + ph + bev + gap + t + cap_gap))

    return _save_array(out, "mat-%s-%gx%g.png" % (os.path.splitext(os.path.basename(src))[0], opening[0], opening[1]))


def multi_matted_image(srcs, opening, plate_h=9.5, gutter=0.55, ppi=80, colour="#F2EDE0", captions=None):
    """Two or three portrait plates side by side on one mat the size of
    `opening`, for a landscape frame too wide for matted_image()'s single
    plate without a sea of empty mat either side. Each plate is `plate_h`
    inches tall; its own width follows its own aspect ratio, with
    `gutter` inches between adjacent plates. Same visual rules as
    matted_image() (off-white mat, faint shadow, thin umber rule round
    each plate window, caption centred under each) and the group as a
    whole is centred on the mat, same convention as the single-plate
    caption-plus-plate group. Ported from a standalone PIL prototype used
    for the mockup the client approved (designer/history/BRIEF.md, 2026-10-09) to
    these bpy-based image helpers (_image_array, _resize, _composite,
    _save_array) -- Blender's bundled Python has no PIL."""
    import numpy as np
    W, H = int(opening[0] * ppi), int(opening[1] * ppi)
    rule = np.array([0.30, 0.24, 0.16], dtype=np.float32)
    out = np.ones((H, W, 3), dtype=np.float32) * np.array(
        [int(colour[i:i + 2], 16) / 255.0 for i in (1, 3, 5)], dtype=np.float32)

    ph = int(plate_h * ppi)
    t = max(1, ppi // 24)
    cap_gap = max(8, ppi // 5)
    captions = captions or [None] * len(srcs)

    plates, caps = [], []
    total_w = 0
    cap_h_max = 0
    for src, caption in zip(srcs, captions):
        arr = _image_array(src)
        sh, sw = arr.shape[:2]
        pw = max(1, int(ph * sw / sh))
        plates.append((_resize(arr, pw, ph), pw))
        total_w += pw

        cap = None
        if caption:
            cap_path = _caption_path(src)
            if os.path.exists(cap_path):
                raw = _image_array_rgba(cap_path)
                ch, cw = raw.shape[:2]
                target_h = max(1, int(0.22 * ppi))
                scale = target_h / ch
                cap = _resize(raw, max(1, int(cw * scale)), max(1, int(ch * scale)))
                cap_h_max = max(cap_h_max, cap.shape[0])
        caps.append(cap)

    n = len(srcs)
    gutter_px = int(gutter * ppi)
    group_w = total_w + gutter_px * (n - 1)
    group_h = ph + (cap_gap + cap_h_max if cap_h_max else 0)
    x0 = (W - group_w) // 2
    y0 = max(0, (H - group_h) // 2)

    cx = x0
    for (plate, pw), cap in zip(plates, caps):
        # each plate in its own cut window, as in matted_image (a bevel lit
        # from the upper left, the cut edge's shadow) and its own fine rule
        bev, gap, tt = max(2, int(0.14 * ppi)), max(3, int(0.18 * ppi)), max(1, ppi // 40)
        core = np.array([0.985, 0.975, 0.955], dtype=np.float32)
        out[y0 - bev:y0 + ph + bev, cx - bev:cx + pw + bev] = core
        out[y0 - bev:y0, cx - bev:cx + pw + bev] = core * 0.86
        out[y0 - bev:y0 + ph + bev, cx - bev:cx] = core * 0.90
        out[y0:y0 + ph, cx:cx + pw] = plate                                          # the plate
        sh = max(1, bev // 2)
        out[y0:y0 + sh, cx:cx + pw] *= 0.82
        out[y0:y0 + ph, cx:cx + sh] *= 0.86
        a0, a1 = y0 - bev - gap, cx - bev - gap
        b0, b1 = y0 + ph + bev + gap, cx + pw + bev + gap
        if a0 - tt >= 0 and a1 - tt >= 0 and b0 + tt <= H and b1 + tt <= W:
            out[a0 - tt:a0, a1 - tt:b1 + tt] = rule
            out[b0:b0 + tt, a1 - tt:b1 + tt] = rule
            out[a0 - tt:b0 + tt, a1 - tt:a1] = rule
            out[a0 - tt:b0 + tt, b1:b1 + tt] = rule
        if cap is not None:
            cw = cap.shape[1]
            _composite(out, cap, cx + (pw - cw) // 2, min(H - cap.shape[0], b0 + tt + cap_gap))
        cx += pw + gutter_px

    name = "multi-%s-%gx%g.png" % (
        "-".join(os.path.splitext(os.path.basename(s))[0] for s in srcs), opening[0], opening[1])
    return _save_array(out, name)


def tiled_image(src, repeat, size_in, ppi=20):
    """One repeat of a fabric (`repeat`, metres) tiled to `size_in` inches."""
    import numpy as np
    rw, rh = (repeat, repeat) if not isinstance(repeat, (list, tuple)) else repeat
    tw, th = max(1, int(rw / INCH * ppi)), max(1, int(rh / INCH * ppi))
    tile = _resize(_image_array(src), tw, th)
    W, H = int(size_in[0] * ppi), int(size_in[1] * ppi)
    reps = (H // th + 1, W // tw + 1, 1)
    return _save_array(np.tile(tile, reps)[:H, :W], "tile-%s-%gx%g.png" % (
        os.path.splitext(os.path.basename(src))[0], size_in[0], size_in[1]))


def apply_scheme(finish="white"):
    """Fill MATERIALS (and FINISHES, FAUCETS) from the scheme's picks."""
    room, sch, picks, lib = load_scheme(finish)
    for slot, r in (room.get("fixed") or {}).items():
        MATERIALS[slot] = recipe(r)
    for spot in room["spots"]:
        items = spot_items(picks, lib, spot)
        if not items or any(it is None or not it.get("render") for it in items):
            continue
        slots = spot_slots_multi(room, items, spot) if len(items) > 1 \
            else spot_slots(room, items[0], spot)
        for slot, r in slots.items():
            if slot.startswith("FINISHES."):
                FINISHES[slot.split(".", 1)[1]] = r
            elif slot.startswith("FAUCETS."):
                FAUCETS[slot.split(".", 1)[1]] = r
            else:
                MATERIALS[slot] = r
    if os.environ.get("WALL_HEX"):
        # WALL_HEX=#rrggbb tries a paint chip that isn't in the library yet
        MATERIALS["wall"]["color"] = hex_linear(os.environ["WALL_HEX"])
    return os.path.relpath(scheme_path(os.path.join(ROOT, "rooms", ROOM), scheme_name(finish)), ROOT)


def scheme_towels(scheme=None, finish="white"):
    """The towels' colours: {'hand': hex, 'bath': [hex, ...]} (D2)."""
    room, sch, picks, lib = load_scheme(finish)
    hand = spot_item(picks, lib, "hand-towels")
    bath = [lib[i] for i in (picks.get("bath-towels") or {}).get("items", [])]
    white = "#F5F3EC"
    return {"hand": hand["render"]["color"] if hand else white,
            "bath": [b["render"]["color"] for b in bath] or [white]}


def scheme_flowers(scheme=None, finish="white"):
    """D10: the vases' glaze and the flowers' three colours."""
    room, sch, picks, lib = load_scheme(finish)
    vase = spot_item(picks, lib, "vases")
    fl = spot_item(picks, lib, "flowers")
    glaze = vase["render"]["color"] if vase else "#F2ECE1"
    rough = (vase or {}).get("render", {}).get("roughness", 0.3)
    # the window sill's vase can be a different piece (window-vase); else
    # the same glaze as the counter's
    wv = spot_item(picks, lib, "window-vase") or vase
    wglaze = wv["render"]["color"] if wv else glaze
    wrough = (wv or {}).get("render", {}).get("roughness", rough)
    if fl and "slots" in fl["render"]:
        cols = [fl["render"]["slots"][k]["color"] for k in ("bloom_a", "bloom_b", "bloom_c")]
    elif fl:
        cols = [fl["render"]["color"]] * 3
    else:
        cols = ["#E8B9C4", "#8C9AD8", "#F3EBD6"]
    return {"glaze": glaze, "colours": cols, "roughness": rough,
            "window_glaze": wglaze, "window_roughness": wrough}
# A design in rta_vanity.rb with its own colour (colors: { finish: [...] }) exports
# a material such as Vanity_Finish_1F2A44; it gets the recipe above in that colour.


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
def import_model(path):
    ext = os.path.splitext(path)[1].lower()
    before = set(bpy.data.objects)
    if ext == ".dae":
        if not hasattr(bpy.ops.wm, "collada_import"):
            raise RuntimeError("This Blender has no COLLADA importer (removed in 5.0). "
                               "Use Blender 4.5 LTS for .dae, or export OBJ from SketchUp.")
        bpy.ops.wm.collada_import(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path, up_axis=OBJ_UP_AXIS,
                              forward_axis="NEGATIVE_Z" if OBJ_UP_AXIS == "Y" else "Y")
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".stl":
        bpy.ops.wm.stl_import(filepath=path)
    else:
        raise RuntimeError("Unsupported file type: " + ext)
    return [o for o in bpy.data.objects if o not in before]


def world_bbox(objs):
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
    return lo, hi


def fix_scale(objs):
    """SketchUp works in inches; if the model came in 1 inch = 1 m, shrink it."""
    bpy.context.view_layer.update()
    lo, hi = world_bbox(objs)
    size = max(hi - lo)
    if size > 20:  # a vanity plus room is ~3 m, never 20+
        s = 0.0254
        for o in objs:
            if o.parent is None:
                o.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ o.matrix_world
        bpy.context.view_layer.update()
        print("Scaled model from inches to metres")


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def set_input(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return


def srgb_to_linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def build_material(key, spec, hex_color=None):
    name = "Vanity " + key.capitalize()
    if hex_color:
        name += " " + hex_color.upper()
        spec = dict(spec, color=tuple(srgb_to_linear(int(hex_color[i:i + 2], 16) / 255.0)
                                      for i in (0, 2, 4)))
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-300, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    color = spec["color"] + (1.0,)
    set_input(bsdf, ["Base Color"], color)
    set_input(bsdf, ["Roughness"], spec.get("roughness", 0.5))
    set_input(bsdf, ["Metallic"], spec.get("metallic", 0.0))
    set_input(bsdf, ["Coat Weight", "Clearcoat"], spec.get("coat", 0.0))
    set_input(bsdf, ["Sheen Weight", "Sheen"], spec.get("sheen", 0.0))
    set_input(bsdf, ["Transmission Weight", "Transmission"], spec.get("transmission", 0.0))
    if spec.get("transmission"):
        set_input(bsdf, ["IOR"], 1.5)
    mat.diffuse_color = color  # viewport colour
    if spec.get("emission"):
        set_input(bsdf, ["Emission Color", "Emission"], color)
        set_input(bsdf, ["Emission Strength"], spec["emission"])

    if spec.get("hammered"):
        # hammered metal: shallow dents (a Voronoi pattern, about 1/2" across)
        # as a bump, and the dents' hollows a shade darker (patina)
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 70.0
        # (by world position, in metres: an object's own coordinates are in
        # inches in the loft, which made the dents 1/70" and the copper flat)
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nt.links.new(geo.outputs["Position"], vor.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.6
        bump.inputs["Distance"].default_value = 0.003
        nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = tuple(c * 0.55 for c in color[:3]) + (1.0,)
        ramp.color_ramp.elements[1].position = 0.6
        ramp.color_ramp.elements[1].color = color
        nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    if spec.get("speckle"):
        # fine grey flecks, like a quartz slab
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 180.0
        tex.inputs["Detail"].default_value = 4.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.58
        ramp.color_ramp.elements[0].color = color
        ramp.color_ramp.elements[1].position = 0.64
        ramp.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1.0)
        coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(coord.outputs["Object"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    if spec.get("marble"):
        # soft grey veins: a distorted wave pattern squeezed into thin lines
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        # (spec C5: honed white with FINE grey veining -- thin, light,
        # wandering lines, not the bold sweeping veins of a "Calacatta" slab)
        wave.inputs["Scale"].default_value = spec.get("vein_scale", 2.0)
        wave.inputs["Distortion"].default_value = spec.get("vein_distortion", 11.0)
        wave.inputs["Detail"].default_value = 4.0
        wave.inputs["Detail Scale"].default_value = 1.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = tuple(spec.get("vein", (0.62, 0.63, 0.65))) + (1.0,)
        ramp.color_ramp.elements[1].position = spec.get("vein_width", 0.035)
        ramp.color_ramp.elements[1].color = color
        geo = nt.nodes.new("ShaderNodeNewGeometry")  # world position, in metres
        nt.links.new(geo.outputs["Position"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    if spec.get("wood"):
        # quartersawn oak, by world position (metres): fine straight grain
        # running up and down, a slower tone change from board to board, and
        # the ray fleck quartersawing is known for -- short pale ribbons
        # across the grain -- all blended through one colour ramp, darker
        # and lighter than the stain's own two tones so the figure shows
        geo = nt.nodes.new("ShaderNodeNewGeometry")

        # (Design-render, 2026-11-10: spec "grain" turns the grain to run
        # along x or y, for a table top or a rail; "z", up and down, by default)
        ga = "xyz".index(spec.get("grain", "z"))

        def noise_at(scale, size, detail, distortion=0.0):
            mp = nt.nodes.new("ShaderNodeMapping")
            sc = list(scale)
            sc[ga], sc[2] = scale[2], scale[ga]
            mp.inputs["Scale"].default_value = sc
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = size
            nz.inputs["Detail"].default_value = detail
            nz.inputs["Distortion"].default_value = distortion
            nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
            nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
            return nz.outputs["Fac"]

        def node_math(op, a, b):
            m = nt.nodes.new("ShaderNodeMath")
            m.operation = op
            for k, v in enumerate((a, b)):
                if isinstance(v, float):
                    m.inputs[k].default_value = v
                else:
                    nt.links.new(v, m.inputs[k])
            return m.outputs[0]

        grain = noise_at((260.0, 260.0, 5.0), 1.0, 12.0, 0.6)     # lines ~2mm apart
        board = noise_at((10.0, 10.0, 0.8), 1.0, 2.0)             # board-to-board tone
        fleck_n = noise_at((70.0, 70.0, 420.0), 1.0, 3.0, 1.5)    # ~1.5cm ribbons, ~2mm tall
        fleck = nt.nodes.new("ShaderNodeMapRange")                # keep only the peaks
        fleck.inputs["From Min"].default_value = 0.6
        fleck.inputs["From Max"].default_value = 0.72
        nt.links.new(fleck_n, fleck.inputs["Value"])
        fac = node_math("ADD", node_math("MULTIPLY", grain, 0.6), node_math("MULTIPLY", board, 0.4))
        fac = node_math("ADD", fac, node_math("MULTIPLY", fleck.outputs["Result"], 0.3))
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        lo, hi = spec.get("ramp", (tuple(c * 0.55 for c in spec["color"]),
                                   tuple(min(1.0, c * 1.5) for c in spec["color"])))
        cr = ramp.color_ramp
        cr.elements[0].position = 0.25
        cr.elements[0].color = tuple(c * 0.7 for c in lo) + (1.0,)    # darkest grain
        cr.elements[1].position = 0.85
        cr.elements[1].color = tuple(min(1.0, c * 1.35) for c in hi) + (1.0,)   # fleck
        for pos, col in ((0.42, lo), (0.62, hi)):
            e = cr.elements.new(pos)
            e.color = tuple(col) + (1.0,)
        nt.links.new(fac, ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        # a touch of texture from the grain, and the fleck a little glossier
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.08
        bump.inputs["Distance"].default_value = 0.0005
        nt.links.new(grain, bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        rough = node_math("SUBTRACT", float(spec.get("roughness", 0.45)), node_math("MULTIPLY", fleck.outputs["Result"], 0.12))
        nt.links.new(rough, bsdf.inputs["Roughness"])
    if spec.get("subway"):
        # 3" x 6" running bond with light grout, on any vertical wall: bricks
        # run along x + y (whichever the wall follows) and up z; world metres
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        add = nt.nodes.new("ShaderNodeMath")
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        nt.links.new(sep.outputs["X"], add.inputs[0])
        nt.links.new(sep.outputs["Y"], add.inputs[1])
        nt.links.new(add.outputs[0], comb.inputs["X"])
        nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.offset = 0.5
        brick.inputs["Color1"].default_value = color
        brick.inputs["Color2"].default_value = tuple(c * 0.97 for c in spec["color"]) + (1.0,)
        brick.inputs["Mortar"].default_value = tuple(spec.get("grout", (0.62, 0.62, 0.60))) + (1.0,)
        brick.inputs["Scale"].default_value = 1.0
        brick.inputs["Mortar Size"].default_value = 0.0015
        brick.inputs["Brick Width"].default_value = 0.1524
        brick.inputs["Row Height"].default_value = 0.0762
        nt.links.new(comb.outputs[0], brick.inputs["Vector"])
        nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    if spec.get("planks"):
        # a floor of narrow boards (spec["planks"] metres wide) running along
        # x, across the loft's aisle: a tone from board to board, end joints
        # staggered, a fine dark seam, and a grain streaked along each board
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(sep.outputs["X"], comb.inputs["X"])
        nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
        lo, hi = spec.get("ramp", (tuple(c * 0.75 for c in spec["color"]), tuple(min(1.0, c * 1.25) for c in spec["color"])))
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.offset = 0.37
        brick.inputs["Color1"].default_value = tuple(lo) + (1.0,)
        brick.inputs["Color2"].default_value = tuple(hi) + (1.0,)
        brick.inputs["Mortar"].default_value = tuple(c * 0.35 for c in lo) + (1.0,)
        brick.inputs["Scale"].default_value = 1.0
        brick.inputs["Mortar Size"].default_value = 0.0007
        brick.inputs["Bias"].default_value = 0.0
        brick.inputs["Brick Width"].default_value = 1.1
        brick.inputs["Row Height"].default_value = spec["planks"]
        nt.links.new(comb.outputs[0], brick.inputs["Vector"])
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (4.0, 160.0, 1.0)
        nt.links.new(comb.outputs[0], mp.inputs["Vector"])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = 8.0
        nz.inputs["Distortion"].default_value = 0.4
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        gr = nt.nodes.new("ShaderNodeMapRange")
        gr.inputs["To Min"].default_value = 0.8
        gr.inputs["To Max"].default_value = 1.15
        nt.links.new(nz.outputs["Fac"], gr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMixRGB")
        mul.blend_type = "MULTIPLY"
        mul.inputs["Fac"].default_value = 1.0
        nt.links.new(brick.outputs["Color"], mul.inputs["Color1"])
        nt.links.new(gr.outputs["Result"], mul.inputs["Color2"])
        nt.links.new(mul.outputs["Color"], bsdf.inputs["Base Color"])
    if spec.get("hex"):
        # hexagonal mosaic, spec["hex"] metres across the flats, grey grout
        size = spec["hex"]
        img = hex_tile_image(color, tuple(spec.get("grout", (0.58, 0.58, 0.56))) + (1.0,))
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.extension = "REPEAT"
        tex.interpolation = "Cubic"
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (1 / size, 1 / (size * math.sqrt(3)), 1)
        geo = nt.nodes.new("ShaderNodeNewGeometry")  # world position, in metres
        nt.links.new(geo.outputs["Position"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if spec.get("pattern"):
        # a printed or woven fabric: a small repeating image, spec["pattern"]
        # names it; mapped by world position, across a vertical surface
        # (along x + y, up z) or, for a rug, across the floor (x, y)
        if spec.get("image"):
            img = bpy.data.images.load(spec["image"], check_existing=True)
        else:
            img = pattern_image(spec["pattern"], spec["colors"])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.extension = "REPEAT"
        tex.interpolation = "Cubic"
        if spec.get("whole"):
            # one image stretched once over the object's own bounds (a rug, a
            # print), across the two world axes named in spec["whole"]
            tex.extension = "EXTEND"
            tc = nt.nodes.new("ShaderNodeTexCoord")
            gsep = nt.nodes.new("ShaderNodeSeparateXYZ")
            gcomb = nt.nodes.new("ShaderNodeCombineXYZ")
            nt.links.new(tc.outputs["Generated"], gsep.inputs[0])
            a, b = spec["whole"]
            nt.links.new(gsep.outputs[a], gcomb.inputs["X"])
            nt.links.new(gsep.outputs[b], gcomb.inputs["Y"])
            nt.links.new(gcomb.outputs[0], tex.inputs["Vector"])
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            if spec.get("emission"):   # a backlit fabric glows in its own print
                em = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
                nt.links.new(tex.outputs["Color"], em)
            return mat
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        if spec.get("uv"):
            # cloth with its own UVs in metres of fabric (the mud room's
            # curtains and pillows, 2026-10-22), so the print follows the
            # folds instead of being projected straight through them
            tc = nt.nodes.new("ShaderNodeTexCoord")
            nt.links.new(tc.outputs["UV"], sep.inputs[0])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        size = spec.get("repeat", 0.1)
        sx, sy = size if isinstance(size, tuple) else (size, size)
        if spec.get("floor") or spec.get("uv"):
            ux = nt.nodes.new("ShaderNodeMath")
            ux.operation = "DIVIDE"
            nt.links.new(sep.outputs["X"], ux.inputs[0])
            ux.inputs[1].default_value = sx
            uy = nt.nodes.new("ShaderNodeMath")
            uy.operation = "DIVIDE"
            nt.links.new(sep.outputs["Y"], uy.inputs[0])
            uy.inputs[1].default_value = sy
        else:
            add = nt.nodes.new("ShaderNodeMath")
            nt.links.new(sep.outputs["X"], add.inputs[0])
            nt.links.new(sep.outputs["Y"], add.inputs[1])
            ux = nt.nodes.new("ShaderNodeMath")
            ux.operation = "DIVIDE"
            nt.links.new(add.outputs[0], ux.inputs[0])
            ux.inputs[1].default_value = sx
            uy = nt.nodes.new("ShaderNodeMath")
            uy.operation = "DIVIDE"
            nt.links.new(sep.outputs["Z"], uy.inputs[0])
            uy.inputs[1].default_value = sy
        nt.links.new(ux.outputs[0], comb.inputs["X"])
        nt.links.new(uy.outputs[0], comb.inputs["Y"])
        nt.links.new(comb.outputs[0], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if spec.get("tiles"):
        # 12" x 24" tiles with light grout, in metres
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.offset = 0.5
        brick.inputs["Color1"].default_value = color
        brick.inputs["Color2"].default_value = tuple(c * 0.92 for c in spec["color"]) + (1.0,)
        brick.inputs["Mortar"].default_value = (0.75, 0.74, 0.72, 1.0)
        brick.inputs["Scale"].default_value = 1.0
        brick.inputs["Mortar Size"].default_value = 0.002
        brick.inputs["Brick Width"].default_value = 0.6096
        brick.inputs["Row Height"].default_value = 0.3048
        geo = nt.nodes.new("ShaderNodeNewGeometry")  # world position, in metres
        nt.links.new(geo.outputs["Position"], brick.inputs["Vector"])
        nt.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    if key == "wall":
        # where a view cuts a wall open, its inside (the faces' backs) shows
        # light grey, as on a drawing's section, not black (client, 2026-10-15)
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (0.55, 0.55, 0.55, 1.0)
        em.inputs["Strength"].default_value = 1.0
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
        nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


FANCY_PATTERNS = ("runner", "botanical", "iris", "lily", "chrysanthemum")


def fancy_image(kind, colors):
    """The more detailed textile and art images, drawn with numpy:
      runner    -- (D3) a whole 26" x 60" runner: guard stripes, a border
                   of rosettes on a running vine, a field of stepped
                   medallions, with a little abrash (dye variation)
      botanical -- (D4) black botanical line art on off-white paper
      iris      -- (D1) a periwinkle block-print iris on pale linen
      lily      -- (P9-OAK) Golden Lily style: amber lilies, cream buds,
                   olive leaves on meandering stems, navy ground
      chrysanthemum -- (P9-WHITE) Chrysanthemum (Willow Ware) style: big
                   layered blue flower heads, pale-blue leaves, white ground
    The repeating ones tile seamlessly."""
    import numpy as np
    name = "Vanity pattern " + kind
    img = bpy.data.images.get(name)
    if img:
        return img
    c = {k: np.array(tuple(v)[:3]) for k, v in colors.items()}
    w, h = {"runner": (1200, 520), "botanical": (330, 420)}.get(kind, (512, 512))
    X, Y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    img_rgb = np.broadcast_to(c["ground"], (h, w, 3)).copy()
    rng = np.random.default_rng(5)

    def mix(mask, col, a=1.0):
        img_rgb[mask] = img_rgb[mask] * (1 - a) + col * a

    def wrap(d):  # shortest distance across a seamless tile
        return (d + 0.5) % 1.0 - 0.5

    def ellipse(cx, cy, a, b, ang=0.0, tile=True, xs=X, ys=Y):
        dx, dy = xs - cx, ys - cy
        if tile:
            dx, dy = wrap(dx), wrap(dy)
        ca, sa = np.cos(ang), np.sin(ang)
        xr, yr = dx * ca + dy * sa, -dx * sa + dy * ca
        return (xr / a) ** 2 + (yr / b) ** 2

    def petal_head(cx, cy, r, n, depth, tile=True):
        dx, dy = X - cx, Y - cy
        if tile:
            dx, dy = wrap(dx), wrap(dy)
        rr, th = np.hypot(dx, dy), np.arctan2(dy, dx)
        return rr, th, rr < r * (1 - depth + depth * np.abs(np.cos(n * th / 2)))

    if kind == "runner":
        # inches over the rug: 60 long (x), 26 wide (y)
        xi, yi = X * 60.0, Y * 26.0
        edge = np.minimum(np.minimum(xi, 60 - xi), np.minimum(yi, 26 - yi))
        # the dark wool ground, lifted a little so it keeps its colour (not
        # near-black) under the room's light
        g = np.clip(c["ground"] * 1.6, 0, 1)
        img_rgb[:] = g
        border = g * 0.55 + c["cream"] * 0.08
        mix(edge < 0.5, g * 0.5)
        mix((edge >= 0.5) & (edge < 1.0), c["cream"], 0.85)
        band = (edge >= 1.0) & (edge < 3.6)
        mix(band, border)
        mix((edge >= 3.6) & (edge < 4.0), c["amber"], 0.8)
        mix((edge >= 4.0) & (edge < 4.3), g * 0.6)
        # the border: a running vine with a rosette every 3"
        along = np.where(np.minimum(yi, 26 - yi) <= np.minimum(xi, 60 - xi), xi, yi)
        mid = 2.3
        vine = np.abs(edge - mid - 0.6 * np.sin(along * np.pi / 1.5)) < 0.12
        mix(band & vine, c["amber"], 0.75)
        ph = (along % 3.0) - 1.5
        rr = np.hypot(ph, edge - mid)
        th = np.arctan2(edge - mid, ph)
        ros = rr < 0.85 * (0.6 + 0.4 * np.abs(np.cos(4 * th)))
        mix(band & ros, c["cream"], 0.8)
        mix(band & (rr < 0.35), c["orange"], 0.9)
        # the field: staggered stepped medallions, small stars between
        field = edge >= 4.3
        fx, fy = xi - 30.0, yi - 13.0
        px_, py_ = 7.5, 6.0
        row = np.floor(fy / py_ + 0.5)
        ox = fx - px_ * (np.floor((fx - (row % 2) * px_ / 2) / px_ + 0.5)) - (row % 2) * px_ / 2
        oy = fy - py_ * row
        # a diamond medallion with a scalloped edge
        step = (np.abs(ox) / 3.0 + np.abs(oy) / 2.4) * (1 + 0.1 * np.cos(8 * np.arctan2(oy, ox)))
        mix(field & (step < 1.0), c["cream"], 0.55)
        mix(field & (step < 0.72), g * 0.8 + c["orange"] * 0.25)
        mix(field & (step < 0.45), c["amber"], 0.8)
        mix(field & (step < 0.18), g * 0.6)
        star = np.hypot(np.abs(ox) - px_ / 2, np.abs(oy) - py_ / 2)
        ang = np.arctan2(np.abs(oy) - py_ / 2, np.abs(ox) - px_ / 2)
        mix(field & (star < 0.9 * (0.5 + 0.5 * np.abs(np.cos(4 * ang)))), c["orange"], 0.6)
        # abrash and a woven texture
        img_rgb *= (1 + 0.05 * np.sin(xi * 0.9 + np.sin(xi * 0.23) * 2))[..., None]
        img_rgb += rng.normal(0, 0.012, img_rgb.shape)
    elif kind == "botanical":
        # a stem with paired leaves and a flower head, in fine black line,
        # on the paper (inside the mat)
        ink = c["ink"]
        xs, ys = X, Y
        stem_x = 0.5 + 0.05 * np.sin(ys * 5.0)
        line = (np.abs(xs - stem_x) < 0.006) & (ys > 0.12) & (ys < 0.78)
        mix(line, ink)
        for k, yl in enumerate((0.22, 0.34, 0.46, 0.58)):
            for side in (-1, 1):
                sx = 0.5 + 0.05 * np.sin(yl * 5.0)
                cx, cy = sx + side * 0.13, yl + 0.04
                e = ellipse(cx, cy, 0.13, 0.045, side * 0.5, tile=False)
                mix((e > 0.82) & (e < 1.0), ink)                      # outline
                vein = np.abs((ys - yl) - (xs - sx) * side * 0.35) < 0.004
                mix(vein & (e < 0.95) & (np.abs(xs - sx) > 0.01), ink)  # midrib
        rr = np.hypot(xs - 0.5, (ys - 0.84) * 1.3)
        th = np.arctan2(ys - 0.84, xs - 0.5)
        outer = 0.1 * (0.7 + 0.3 * np.abs(np.cos(3 * th)))
        mix(np.abs(rr - outer) < 0.005, ink)
        mix(np.abs(rr - 0.025) < 0.004, ink)
        img_rgb += rng.normal(0, 0.006, img_rgb.shape)
    elif kind == "iris":
        blue = c["blue"] * 0.8 + c["ground"] * 0.2
        for cx, cy in ((0.27, 0.3), (0.77, 0.8)):
            # sword leaves and stem, then the flower: three falls, two standards
            for dx, tilt in ((-0.07, 0.25), (0.06, -0.2)):
                mix(ellipse(cx + dx, cy - 0.12, 0.018, 0.2, tilt) < 1, c["green"], 0.85)
            mix((np.abs(wrap(X - cx)) < 0.008) & (wrap(Y - cy) < 0) & (wrap(Y - cy) > -0.3), c["green"], 0.9)
            for ang, oy in ((0.0, 0.05), (1.1, 0.02), (-1.1, 0.02)):
                mix(ellipse(cx + 0.06 * np.sin(ang), cy - oy, 0.035, 0.08, ang) < 1, blue)
            for ang in (0.45, -0.45):
                mix(ellipse(cx + 0.035 * np.sin(ang), cy + 0.08, 0.025, 0.07, ang) < 1, blue * 0.85)
            mix(ellipse(cx, cy + 0.01, 0.012, 0.03) < 1, c["amber"], 0.8)
        # a block print never takes the ink evenly
        speck = rng.random((h, w)) < 0.08
        mix(speck, c["ground"], 0.5)
    elif kind == "lily":
        olive, amber, cream = c["green"], c["amber"], c["cream"]
        for base, phase in ((0.25, 0.0), (0.75, 0.5)):
            sx = base + 0.1 * np.sin(2 * np.pi * (Y + phase))
            mix(np.abs(wrap(X - sx)) < 0.007, olive, 0.9)
            for k in range(4):
                vy = (k / 4 + phase / 2) % 1
                side = 1 if k % 2 else -1
                lx = base + 0.1 * np.sin(2 * np.pi * (vy + phase)) + side * 0.07
                e = ellipse(lx, vy, 0.075, 0.022, side * 0.6)
                mix(e < 1, olive, 0.85)
                mix((e < 1) & (np.abs(wrap(Y - vy) - wrap(X - lx) * side * 0.6) < 0.003), olive * 0.6)
        for fx, fy, ang in ((0.14, 0.12, 0.3), (0.86, 0.62, -0.3), (0.4, 0.45, -0.2), (0.6, 0.95, 0.2)):
            for dx in (-1, 0, 1):   # a lily: three flared petals, streaked
                e = ellipse(fx + dx * 0.035, fy + 0.03 * abs(dx), 0.026, 0.07, ang + dx * 0.55)
                mix(e < 1, amber)
                mix((e < 1) & (e > 0.55), amber * 0.8 + c["orange"] * 0.2)
            mix(ellipse(fx, fy - 0.05, 0.02, 0.02) < 1, cream)
            for sdx in (-0.012, 0.0, 0.012):   # stamens
                mix(ellipse(fx + sdx, fy + 0.09, 0.004, 0.004) < 1, cream)
        for bx, by in rng.random((22, 2)):     # small cream buds and dots
            mix(ellipse(bx, by, 0.009, 0.013, bx * 3) < 1, cream, 0.9)
        img_rgb += rng.normal(0, 0.008, img_rgb.shape)
    elif kind == "chrysanthemum":
        blue, pale = c["blue"], c["pale"]
        for base, phase in ((0.5, 0.0),):
            sx = base + 0.22 * np.sin(2 * np.pi * Y)
            mix(np.abs(wrap(X - sx)) < 0.01, pale)
        for vy, side in ((0.05, 1), (0.3, -1), (0.55, 1), (0.8, -1)):
            lx = 0.5 + 0.22 * np.sin(2 * np.pi * vy) + side * 0.1
            e = ellipse(lx, vy, 0.11, 0.045, side * 0.5)
            rr, th, _ = petal_head(lx, vy, 1, 1, 0)
            serr = 1 + 0.12 * np.sin(th * 18)
            mix(e < serr, pale)
            mix((e < 1) & (np.abs(wrap(Y - vy) - wrap(X - lx) * side * 0.5) < 0.004), blue, 0.7)
        for fx, fy, r in ((0.2, 0.22, 0.15), (0.8, 0.72, 0.15), (0.72, 0.18, 0.07), (0.28, 0.7, 0.07)):
            rr, th, outer = petal_head(fx, fy, r, 18, 0.3)
            mix(outer, blue)
            lines = (np.abs(np.cos(9 * th)) < 0.18) & (rr > r * 0.3) & outer
            mix(lines, c["ground"], 0.85)                          # white between petals
            _, _, inner = petal_head(fx, fy, r * 0.55, 12, 0.35)
            mix(inner, blue * 0.75)
            mix(inner & (np.abs(np.cos(6 * th)) < 0.2), pale)
            mix(rr < r * 0.14, pale)
        for bx, by in rng.random((16, 2)):
            mix(ellipse(bx, by, 0.01, 0.01) < 1, pale, 0.8)
        img_rgb += rng.normal(0, 0.006, img_rgb.shape)

    rgba = np.concatenate([np.clip(img_rgb, 0, 1), np.ones((h, w, 1))], axis=2)
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.pack()
    return img


def pattern_image(kind, colors, px=96):
    """Small repeating textile images in the stained-glass palette.
    colors: dict of name -> linear RGB. Kinds:
      shade   -- cream ground, an Arts & Crafts square-and-diamond motif
      curtain -- cream ground, paired narrow stripes (a cousin of the shade)
      rug     -- dark ground, a small stepped-diamond geometric
      rug_small -- a small, tonal all-over motif in amber and orange,
                   blended into the ground rather than laid on top
      medallion -- (D3) a vintage all-over medallion in gold, orange and
                   ivory on the rug's dark ground
      lily    -- (P9-OAK) a Golden Lily style print: meandering olive stems,
                 amber lilies with cream centres, on a navy ground
      chrysanthemum -- (P9-WHITE) a Chrysanthemum (Willow Ware) style print:
                 big blue flower heads and pale-blue foliage on white
      print   -- off-white paper with a soft botanical wash
    """
    if kind in FANCY_PATTERNS:
        return fancy_image(kind, colors)
    import numpy as np
    if kind in ("lily", "medallion", "chrysanthemum"):
        px = 256  # bigger motifs, over a bigger repeat
    name = "Vanity pattern " + kind
    img = bpy.data.images.get(name)
    if img:
        return img
    c = {k: np.array(tuple(v) + (1.0,)) for k, v in colors.items()}
    u = (np.arange(px) + 0.5) / px
    uu, vv = np.meshgrid(u, u)
    rgba = np.broadcast_to(c["ground"], (px, px, 4)).copy()

    def paint(mask, col):
        rgba[mask] = col

    if kind == "shade":
        d = np.maximum(abs(uu - 0.5), abs(vv - 0.5))           # square rings
        paint((d > 0.36) & (d < 0.40), c["blue"])
        dia = abs(uu - 0.5) + abs(vv - 0.5)                      # diamond
        paint(dia < 0.16, c["amber"])
        paint(dia < 0.06, c["orange"])
        for cx, cy in ((0, 0), (1, 0), (0, 1), (1, 1)):          # corner dots
            paint(np.hypot(uu - cx, vv - cy) < 0.07, c["orange"])
    elif kind == "curtain":
        paint((abs(uu - 0.30) < 0.025) | (abs(uu - 0.40) < 0.025), c["blue"])
        paint(abs(uu - 0.80) < 0.02, c["amber"])
    elif kind == "rug":
        dia = abs(uu - 0.5) + abs(vv - 0.5)
        paint((dia > 0.28) & (dia < 0.36), c["amber"])
        paint(dia < 0.10, c["blue"])
        paint((abs(uu - 0.5) < 0.03) & (abs(vv - 0.5) > 0.42), c["blue"])
        noise = np.random.default_rng(3).normal(0, 0.02, (px, px, 1))
        rgba[..., :3] = np.clip(rgba[..., :3] + noise, 0, 1)
    elif kind == "rug_small":
        def tone(mask, col, a):
            rgba[mask, :3] = rgba[mask, :3] * (1 - a) + col[:3] * a
        dia = abs(uu - 0.5) + abs(vv - 0.5)
        tone((dia > 0.30) & (dia < 0.38), c["amber"], 0.45)       # diamond
        tone(dia < 0.09, c["orange"], 0.55)                       # centre dot
        for cx, cy in ((0, 0), (1, 0), (0, 1), (1, 1)):          # corner dots
            tone(np.hypot(uu - cx, vv - cy) < 0.06, c["amber"], 0.4)
        noise = np.random.default_rng(3).normal(0, 0.015, (px, px, 1))
        rgba[..., :3] = np.clip(rgba[..., :3] + noise, 0, 1)
    elif kind == "medallion":
        def tone(mask, col, a):
            rgba[mask, :3] = rgba[mask, :3] * (1 - a) + col[:3] * a
        r = np.hypot(uu - 0.5, vv - 0.5)
        dia = abs(uu - 0.5) + abs(vv - 0.5)
        tone((dia > 0.30) & (dia < 0.35), c["amber"], 0.7)        # diamond frame
        tone((r > 0.16) & (r < 0.20), c["cream"], 0.6)            # ring
        tone(r < 0.09, c["orange"], 0.7)                          # centre
        petals = (r > 0.08) & (r < 0.15) & (abs(np.cos(4 * np.arctan2(vv - 0.5, uu - 0.5))) > 0.7)
        tone(petals, c["amber"], 0.55)
        for cx, cy in ((0, 0), (1, 0), (0, 1), (1, 1)):           # corner rosettes
            rc = np.hypot(uu - cx, vv - cy)
            tone(rc < 0.10, c["cream"], 0.45)
            tone(rc < 0.05, c["orange"], 0.6)
        noise = np.random.default_rng(3).normal(0, 0.02, (px, px, 1))
        rgba[..., :3] = np.clip(rgba[..., :3] + noise, 0, 1)
    elif kind == "chrysanthemum":
        def tone(mask, col, a=1.0):
            rgba[mask, :3] = rgba[mask, :3] * (1 - a) + col[:3] * a
        # scrolling pale-blue foliage behind, then two big blue flower heads
        sx = 0.5 + 0.2 * np.sin(2 * np.pi * vv)
        tone(abs(uu - sx) < 0.02, c["pale"], 1.0)
        for vy, side in ((0.1, 1), (0.35, -1), (0.6, 1), (0.85, -1)):
            lx = 0.5 + 0.2 * np.sin(2 * np.pi * vy) + side * 0.11
            tone(((uu - lx) / 0.11) ** 2 + ((vv - vy) / 0.04) ** 2 < 1, c["pale"], 1.0)
        for fx, fy in ((0.22, 0.25), (0.78, 0.75)):
            r = np.hypot(uu - fx, vv - fy)
            ang = np.arctan2(vv - fy, uu - fx)
            petals = r < 0.13 + 0.03 * np.cos(12 * ang)             # a ragged ring of petals
            tone(petals, c["blue"], 1.0)
            tone(petals & (abs(np.cos(12 * ang)) < 0.25) & (r > 0.05), c["ground"], 0.8)   # white between petals
            tone(r < 0.045, c["pale"], 1.0)
            tone(r < 0.02, c["blue"], 1.0)
    elif kind == "lily":
        def tone(mask, col, a=1.0):
            rgba[mask, :3] = rgba[mask, :3] * (1 - a) + col[:3] * a
        sx = 0.5 + 0.13 * np.sin(2 * np.pi * vv)                  # a meandering stem
        tone(abs(uu - sx) < 0.02, c["green"], 0.9)
        for vy, side in ((0.2, 1), (0.45, -1), (0.7, 1), (0.95, -1)):   # leaves
            lx = 0.5 + 0.13 * np.sin(2 * np.pi * vy) + side * 0.1
            tone(((uu - lx) / 0.1) ** 2 + ((vv - vy) / 0.035) ** 2 < 1, c["green"], 0.85)
        for fx, fy in ((0.18, 0.15), (0.82, 0.65)):
            for dx in (-0.06, 0.0, 0.06):                        # three petals
                tone(((uu - fx - dx) / 0.04) ** 2 + ((vv - fy - abs(dx) * 0.8) / 0.1) ** 2 < 1, c["amber"], 0.95)
            tone(np.hypot(uu - fx, vv - fy + 0.05) < 0.025, c["cream"], 1.0)
        rng = np.random.default_rng(11)
        for _ in range(8):                                        # small cream buds
            bx, by = rng.uniform(0, 1, 2)
            tone(np.hypot(uu - bx, vv - by) < 0.015, c["cream"], 0.9)
    elif kind == "print":
        rng = np.random.default_rng(7)
        wash = np.zeros((px, px))
        for _ in range(9):
            cx, cy, r = rng.uniform(0.2, 0.8), rng.uniform(0.15, 0.85), rng.uniform(0.05, 0.14)
            wash += np.exp(-((uu - cx) ** 2 + (vv - cy) ** 2) / (2 * r * r))
        stem = np.exp(-((uu - 0.5 - 0.1 * np.sin(vv * 6)) ** 2) / 0.0004) * (vv < 0.85)
        w = np.clip(wash * 0.5, 0, 1)[..., None]
        rgba[..., :3] = rgba[..., :3] * (1 - w) + c["green"][:3] * w
        rgba[stem > 0.5] = c["amber"]
    img = bpy.data.images.new(name, px, px, alpha=False)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.pack()
    return img


def hex_tile_image(tile, grout, px=128):
    """A repeating image of hexagonal tiles: one tile's width across and two
    rows high (hex centres at the corners and the middle), so it repeats
    seamlessly when mapped to size x size*sqrt(3)."""
    import numpy as np
    name = "Vanity hex tile " + "-".join("%.3f" % v for v in tile[:3])
    img = bpy.data.images.get(name)
    if img:
        return img
    w, h = px, int(round(px * math.sqrt(3)))
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h * math.sqrt(3)
    uu, vv = np.meshgrid(u, v)
    centres = [(0, 0), (1, 0), (0, math.sqrt(3)), (1, math.sqrt(3)), (0.5, math.sqrt(3) / 2)]
    d = np.sort(np.stack([np.hypot(uu - cx, vv - cy) for cx, cy in centres]), axis=0)
    joint = (d[1] - d[0]) < 0.05          # about 1/16" of grout on a 2 1/2" tile
    rgba = np.where(joint[..., None], np.array(grout), np.array(tile))
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.pack()
    return img


def material_key(name):
    """'Vanity_Finish' -> ('finish', None); 'Vanity_Finish_1F2A44' -> ('finish', '1f2a44')."""
    low = name.lower().replace(" ", "_")
    # longest first, so 'print2' isn't taken for 'print'
    for key in sorted(MATERIALS, key=len, reverse=True):
        m = re.search("vanity_" + key + r"(?:_([0-9a-f]{6})(?![0-9a-f]))?", low)
        if m:
            return key, m.group(1)
    return None, None


def assign_materials(objs):
    built = {}
    missing = set()
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if slot.material is None:
                continue
            key, hex_color = material_key(slot.material.name)
            if key and MATERIALS.get(key, {}).get("variants"):
                # an image drawn for several sizes (our period rugs): the one
                # whose length is closest to this object's, so the pattern
                # isn't stretched or squashed (2026-10-15)
                length = max(o.dimensions) / INCH
                vs = MATERIALS[key]["variants"]
                best = min(vs, key=lambda L: abs(float(L) - length))
                spec = dict(MATERIALS[key], image=os.path.normpath(os.path.join(ROOT, vs[best])))
                spec.pop("variants")
                if (key, best) not in built:
                    built[key, best] = build_material(key, spec, hex_color)
                slot.material = built[key, best]
                continue
            if key:
                if (key, hex_color) not in built:
                    built[key, hex_color] = build_material(key, MATERIALS[key], hex_color)
                slot.material = built[key, hex_color]
            else:
                missing.add(slot.material.name)
    if missing:
        print("Materials left as imported:", sorted(missing))


def dump_sizes(objs, path=None):
    """What the model actually draws, for tools/check_sizes.py (client,
    2026-10-29: the loft's vanity was 21" deep in the parts list and the
    renders but 20" on every plan): each named piece's extent in inches,
    {name: [x0, y0, z0, x1, y1, z1]}, several pieces of one name joined
    into one box. Written to SIZES_OUT (or path) when it's set."""
    path = path or os.environ.get("SIZES_OUT")
    if not path:
        return
    I = 0.0254
    out = {}
    bpy.context.view_layer.update()
    for o in objs:
        if o.type != "MESH" or len(o.data.vertices) == 0:
            continue
        pts = [o.matrix_world @ vx.co for vx in o.data.vertices]
        b = [min(p[k] for p in pts) / I for k in range(3)] + [max(p[k] for p in pts) / I for k in range(3)]
        name = o.name.split(".")[0] if o.name[-4:-3] == "." and o.name[-3:].isdigit() else o.name
        if name in out:
            a = out[name]
            b = [min(a[k], b[k]) for k in range(3)] + [max(a[k], b[k]) for k in range(3, 6)]
        out[name] = [round(c, 3) for c in b]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(dict(sorted(out.items())), f, indent=0)
    print("SIZES %d pieces -> %s" % (len(out), path), flush=True)


def coincident_faces(objs, hidden=None):
    """Joints where two boxes have faces in one plane, facing the same way
    and overlapping: the renderer can't tell which is in front and draws
    dark or speckled patches there (client, 2026-10-17). Any model, after
    fix_scale: the boxes are the meshes whose corners are all their bounds'
    corners. A face is left out when it is unseen: flat on the floor, or
    against a third box's opposite face (a wall, a cabinet side), or when
    hidden(axis, sign, value, lo, hi) says so (inches). Returns lines."""
    I = 0.0254
    e = 1e-4
    bs = []
    for o in objs:
        if o.type != "MESH" or o.hide_render or len(o.data.vertices) < 8:
            continue
        pts = {tuple(round(c / I, 3) for c in (o.matrix_world @ vx.co)) for vx in o.data.vertices}
        lo = [min(p[k] for p in pts) for k in range(3)]
        hi = [max(p[k] for p in pts) for k in range(3)]
        if all(abs(p[k] - lo[k]) < 0.01 or abs(p[k] - hi[k]) < 0.01 for p in pts for k in range(3)) \
                and all(hi[k] - lo[k] > e for k in range(3)):
            bs.append((o.name, lo, hi))

    def covered(ax, sign, val, lo, hi, skip):
        # a third box whose opposite face lies in this plane over the overlap
        for nm, b0, b1 in bs:
            if nm in skip:
                continue
            if abs((b0[ax] if sign > 0 else b1[ax]) - val) < e and \
                    all(b0[k] <= lo[k] + e and b1[k] >= hi[k] - e for k in range(3) if k != ax):
                return True
        return False
    found = []
    for i, (na, a0, a1) in enumerate(bs):
        for nb, b0, b1 in bs[i + 1:]:
            lo = [max(a0[k], b0[k]) for k in range(3)]
            hi = [min(a1[k], b1[k]) for k in range(3)]
            for ax in range(3):
                if any(hi[k] - lo[k] <= e for k in range(3) if k != ax):
                    continue
                for sign, va, vb in ((-1, a0[ax], b0[ax]), (1, a1[ax], b1[ax])):
                    if abs(va - vb) >= e:
                        continue
                    if (ax == 2 and sign < 0 and abs(va) < e) or covered(ax, sign, va, lo, hi, (na, nb)) \
                            or (hidden and hidden(ax, sign, va, lo, hi)):
                        continue
                    found.append("%s / %s: their %s%s faces at %.2f\"" % (na, nb, "-+"[sign > 0], "xyz"[ax], va))
    return found


def add_bevels(objs):
    """A 1-2 mm edge bevel catches highlights the way real cabinets do."""
    if BEVEL_WIDTH <= 0:
        return
    for o in objs:
        if o.type != "MESH" or "Bevel" in o.modifiers:
            continue
        keys = {material_key(s.material.name)[0] for s in o.material_slots if s.material}
        if keys & {"finish", "countertop"}:
            stone = "countertop" in keys and STONE_EDGE > 0
            mod = o.modifiers.new("Bevel", "BEVEL")
            width = STONE_EDGE if stone else BEVEL_WIDTH
            mod.width = width / max(o.matrix_world.to_scale())  # modifier works in local units
            mod.segments = 4 if stone else 2
            mod.limit_method = "ANGLE"
            mod.use_clamp_overlap = True
            mod.harden_normals = True


def smooth_round_parts(objs):
    """Smooth the cylinders (pulls, faucet) while keeping box edges crisp."""
    meshes = [o for o in objs if o.type == "MESH"]
    if not meshes:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))  # Blender 4.1+
    except (AttributeError, RuntimeError):
        bpy.ops.object.shade_smooth()
        for o in meshes:
            if hasattr(o.data, "use_auto_smooth"):
                o.data.use_auto_smooth = True
                o.data.auto_smooth_angle = math.radians(35)


# ---------------------------------------------------------------------------
# Camera, lights, render settings
# ---------------------------------------------------------------------------
def tagged(o, tag):
    """True if the object, or a group it sits in, is named with tag."""
    while o is not None:
        if tag in o.name.upper():
            return True
        o = o.parent
    return False


def apply_view(objs, view):
    """Hide the view markers; for the front view (the camera stands back
    past the far wall), hide the far side of the room (tub, toilet, opposite
    wall) from the camera only: the mirrors still reflect it, and it still
    shades the room as it would."""
    for o in objs:
        if any(tagged(o, t) for t in ("VIEW_ENTRY", "VIEW_OPPOSITE", "VIEW_WC", "VIEW_HALL", "TOWEL_")):
            o.hide_render = True
        elif view == "front" and tagged(o, "OPPOSITE_SIDE"):
            o.visible_camera = False


def marker(objs, tag):
    found = [o for o in objs if o.type == "MESH" and tagged(o, tag)]
    if not found:
        return None
    lo, hi = world_bbox(found)
    return (lo + hi) / 2


def vanity_bbox(objs):
    keys = ("vanity countertop", "vanity finish")
    core = [o for o in objs if o.type == "MESH" and not o.hide_render and o.visible_camera  # skip what the view cuts away
            and not tagged(o, "PEG RAIL")  # in the vanities' finish, but out in the hallway
            and any(s.material and s.material.name.lower().startswith(keys) for s in o.material_slots)]
    return world_bbox(core or objs)


FIXTURE_TAGS = ("CEILING LIGHT", "SHOWER LIGHT")


def fixture_lamps(objs, scale=1.0):
    """Light the room from its own fixtures, as the real ones will: a lamp
    in each one's glass, most of it down through the glass (a wide, soft
    spot) and, for a bowl or drum on the ceiling, a little up onto the
    ceiling (a weak point lamp); the glass itself casts no shadow. (The
    rooms used to be lit by a panel just under the ceiling that shone only
    down: the ceiling got no direct light, what rose above the panel went
    dark, the walls just under it caught a bright band, and the fixture
    shadowed the floor under itself; client, 2026-10-16.) Returns how many
    fixtures it lit."""
    groups = {}
    for o in objs:
        if o.type != "MESH":
            continue
        a = o
        while a is not None and not any(t in a.name.upper() for t in FIXTURE_TAGS):
            a = a.parent
        if a is not None:
            groups.setdefault(a.name, []).append(o)
    for name, parts in groups.items():
        lo, hi = world_bbox(parts)
        c = (lo + hi) / 2
        for p in parts:
            p.visible_shadow = False
        recessed = (hi.z - lo.z) < 0.02          # a recessed downlight: flat, all down
        small = max(hi.x - lo.x, hi.y - lo.y) < 0.25
        energy = (22 if recessed else 18 if small else 60) * scale
        if "WC" in name.upper():
            # the enclosed WC's small drum takes a full-size bulb (about 800
            # lumens, as the room's bowl), not a shower light's: at 18 the WC
            # rendered noticeably darker than the room (client, 2026-10-21)
            energy = 40 * scale
        d = bpy.data.lights.new(name + " lamp", "SPOT")
        d.spot_size = math.radians(110 if recessed else 160)
        d.spot_blend = 1.0
        d.shadow_soft_size = 0.05 if recessed else 0.09
        d.energy = energy
        lamp = bpy.data.objects.new(name + " lamp", d)
        lamp.location = (c.x, c.y, lo.z - 0.01 if recessed else c.z)
        lamp.visible_glossy = False
        bpy.context.scene.collection.objects.link(lamp)
        if not recessed:
            u = bpy.data.lights.new(name + " lamp up", "POINT")
            u.shadow_soft_size = 0.09
            u.energy = energy * 0.2
            up = bpy.data.objects.new(name + " lamp up", u)
            up.location = (c.x, c.y, c.z)
            up.visible_glossy = False
            bpy.context.scene.collection.objects.link(up)
    return len(groups)


def setup_camera_and_lights(objs, view="front"):
    lo, hi = vanity_bbox(objs)
    center = (lo + hi) / 2
    width = hi.x - lo.x

    target = bpy.data.objects.new("Camera Target", None)
    target.location = (center.x, center.y, lo.z + 0.55 * (hi.z - lo.z))
    bpy.context.scene.collection.objects.link(target)

    cam_data = bpy.data.cameras.new("Vanity Camera")
    cam_data.lens = 35
    cam = bpy.data.objects.new("Vanity Camera", cam_data)
    dist = max(1.8, width * 0.95 + 0.9, (hi.z - lo.z) * 1.6)  # step back for a tall linen cabinet
    # slightly off-centre for a single vanity; square-on for a wide row of designs
    cam.location = (center.x - 0.2 * min(width, 1.8), lo.y - dist, 1.45)
    tag = {"entry": "VIEW_ENTRY", "opposite": "VIEW_OPPOSITE", "wc": "VIEW_WC", "hall": "VIEW_HALL"}.get(view)
    eye = marker(objs, tag + "_EYE") if tag else None
    bpy.context.scene.view_settings.exposure = 0.0
    if tag:
        if eye is None:
            raise RuntimeError("No %s view in this model: build a design with a whole room." % view)
        cam.location = eye
        target.location = marker(objs, tag + "_TARGET")
        cam_data.lens = 22 if view in ("entry", "hall") else 15
        bpy.context.scene.view_settings.exposure = -0.5  # a white room: keep some contrast
    else:
        cam.location.z = EYE_HEIGHT
        # a whole room seen from the front: the same exposure as the other
        # room views, so one wall colour reads the same in all of them
        if any(o.name.split(".")[0] == "CEILING" for o in objs):
            bpy.context.scene.view_settings.exposure = -0.5
            # and a touch longer lens: standing back behind the far wall, a
            # 35 mm one saw past the ends of the room's ceiling and side wall
            # (a black corner at top left and a strip down the right)
            cam_data.lens = 38
    # Keep the camera level at eye height, so walls and cabinets stay upright,
    # and frame what it was aimed at by shifting the lens instead of tilting.
    look = target.location.copy()
    flat = math.hypot(look.x - cam.location.x, look.y - cam.location.y)
    target.location.z = cam.location.z
    if flat > 0:
        shift = (look.z - cam.location.z) / flat * cam_data.lens / cam_data.sensor_width
        cam_data.shift_y = max(-0.35, min(0.35, shift))
    # CLOSEUP=curtain|shade: from the same eye, a long lens filling the frame
    # with the decorative curtain panel nearest the camera, or the shade
    close = os.environ.get("CLOSEUP")
    # CLOSEUP=shelf-vanity|shelf-tub: the framed plate over that peg shelf,
    # square on, from the middle of the room at the plate's height (from the
    # room's own views these side-wall frames are seen almost edge on)
    facing = close in ("shelf-vanity", "shelf-tub")
    # CLOSEUP=door-vanity|door-tub: that peg shelf as you'd see it walking
    # in: its frame, shelf and hooks and the door beside them, three-quarter
    # on, from across the room and a step further in, at eye height
    # (each shelf's plate by its object's name, as room.yaml names them: both
    # plates still carry the same placeholder material at this point)
    shelf_plate = {"shelf-vanity": "Wall art across_", "door-vanity": "Wall art across_",
                   "shelf-tub": "Wall art upright_", "door-tub": "Wall art upright_"}

    def plates(key=None):
        return [o for o in objs if o.type == "MESH" and o.name.split(".")[0].endswith("_Plate")
                and any(k in o.name for k in ([key] if key else set(shelf_plate.values())))]
    door_side = close in ("door-vanity", "door-tub")
    if door_side:
        parts = plates(shelf_plate[close])
        both = plates()
        h_eye, h_tgt = marker(objs, "VIEW_HALL_EYE"), marker(objs, "VIEW_HALL_TARGET")
        if parts and h_eye is not None and h_tgt is not None:
            lo_, hi_ = world_bbox(parts)
            c = (lo_ + hi_) / 2
            blo, bhi = world_bbox(both)
            mid_y = (blo.y + bhi.y) / 2
            out = 1.0 if mid_y > c.y else -1.0
            across = abs(mid_y - c.y) * 2            # wall to wall
            to_door = 1.0 if h_tgt.x > h_eye.x else -1.0
            # stand by the opposite wall, nearer the door than the frame, and
            # look back across at it (the space by the door is too narrow to
            # step back from it square on)
            cam.location = (c.x + to_door * float(os.environ.get("DOOR_BACK", "0.55")),
                            c.y + out * (across - 0.12), EYE_HEIGHT)
            target.location = (c.x, c.y, c.z - 0.3)
            cam_data.lens = float(os.environ.get("DOOR_LENS", "20"))
            cam_data.shift_y = 0.0
            bpy.context.scene.view_settings.exposure = -0.2
        close = None
    # CLOSEUP=toilet: the wall over the toilet, square on: the framed art, the
    # tank and the cabinet above, from as far back as the room (or the WC)
    # allows, measured by a ray from the art out into the room
    if close == "toilet":
        # (names carry a tag in front: OPPOSITE_SIDE_Toilet art_Plate)
        art = [o for o in objs if o.type == "MESH" and "Toilet art_" in o.name and not o.hide_render]
        bowl = [o for o in objs if o.type == "MESH" and "Toilet_" in o.name]
        if art and bowl:
            lo_, hi_ = world_bbox(art)
            c = (lo_ + hi_) / 2
            tc = (world_bbox(bowl)[0] + world_bbox(bowl)[1]) / 2
            out = 1.0 if tc.y > c.y else -1.0
            start = Vector((c.x, c.y + out * 0.05, c.z))            # at the art's height: clear of tank and cabinet
            hit, loc, *_ = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(), start, Vector((0, out, 0)))
            room = abs(loc.y - c.y) if hit else 2.0
            dist = max(0.9, min(2.2, room - 0.15))
            # level, at the art's height, so the walls stay upright
            cam.location = (c.x, c.y + out * dist, c.z + 0.1)
            target.location = (c.x, c.y, c.z + 0.1)
            cam_data.lens = cam_data.sensor_width * dist / 2.0    # about 2 m across: tank to cabinet
            cam_data.shift_y = 0.0
            bpy.context.scene.view_settings.exposure = 0.0
        close = None
    if facing:
        parts = plates(shelf_plate[close])
        both = plates()
        if parts:
            lo_, hi_ = world_bbox(parts)
            c = (lo_ + hi_) / 2
            blo, bhi = world_bbox(both)
            mid_y = (blo.y + bhi.y) / 2       # between the two shelves' walls
            out = 1.0 if mid_y > c.y else -1.0
            dist = min(1.1, abs(mid_y - c.y) * 1.8)
            cam.location = (c.x, c.y + out * dist, c.z)
            target.location = c
            span = max(hi_.x - lo_.x, hi_.z - lo_.z) * 1.9   # the frame, a little wall and the shelf top
            cam_data.lens = cam_data.sensor_width * dist / span
            cam_data.shift_y = 0.0
            bpy.context.scene.view_settings.exposure = 0.2   # (the room's lights are aimed elsewhere)
        close = None
    if close:
        def is_(o):
            return o.type == "MESH" and not o.hide_render and any(
                s.material and material_key(s.material.name)[0] == close for s in o.material_slots)
        parts = [o for o in objs if is_(o)]
        if parts:
            if close == "curtain":
                # the panel (one of two, at each end of the tub) nearer the eye
                xs = sorted(((world_bbox([o])[0] + world_bbox([o])[1]) / 2).x for o in parts)
                cut = (xs[0] + xs[-1]) / 2
                near_low = abs(xs[0] - cam.location.x) < abs(xs[-1] - cam.location.x)
                parts = [o for o in parts if (((world_bbox([o])[0] + world_bbox([o])[1]) / 2).x < cut) == near_low]
            lo_, hi_ = world_bbox(parts)
            c = (lo_ + hi_) / 2
            if close == "curtain":
                c.z = min(c.z, 1.45)          # the middle of the panel at eye level, not its top
            target.location = c
            dist = (c - cam.location).length
            span = max(0.35, max(hi_.x - lo_.x, hi_.y - lo_.y) * (1.4 if close == "shade" else 2.2))
            cam_data.lens = cam_data.sensor_width * dist / span
            cam_data.shift_y = 0.0
            bpy.context.scene.view_settings.exposure = -0.3
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    def area(name, loc, size, energy, rot, size_y=None):
        data = bpy.data.lights.new(name, "AREA")
        data.size = size
        if size_y:
            data.shape = "RECTANGLE"
            data.size_y = size_y
        data.energy = energy
        light = bpy.data.objects.new(name, data)
        light.location = loc
        light.rotation_euler = rot
        bpy.context.scene.collection.objects.link(light)

    # ceiling panel over the vanity, softer fill from behind the camera; with
    # a ceiling in the model, both stay under it
    # (the room's own ceiling and floor, by name: the light fixtures, the
    # soffit and everything else in a "Second floor" design match the tags)
    ceiling = [o for o in objs if o.type == "MESH" and o.name.split(".")[0] == "CEILING" and not o.hide_render] or \
        [o for o in objs if o.type == "MESH" and tagged(o, "CEILING") and not o.hide_render]
    top = world_bbox(ceiling)[0].z - 0.05 if ceiling else 2.45
    floor = [o for o in objs if o.type == "MESH" and o.name.split(".")[0] == "Floor"] or \
        [o for o in objs if o.type == "MESH" and o.name.upper().find("FLOOR") >= 0]
    if floor:
        # the open part of the room: not under the soffit over the tub
        rlo, rhi = world_bbox(floor)
        soffit = [o for o in objs if o.type == "MESH" and tagged(o, "SOFFIT")]
        if soffit:
            slo, shi = world_bbox(soffit)
            if shi.y < (rlo.y + rhi.y) / 2:
                rlo = rlo.copy()
                rlo.y = max(rlo.y, shi.y)
        rc = (rlo + rhi) / 2
    lit = fixture_lamps(objs) if ceiling and floor else 0
    if view in ("entry", "opposite", "wc", "hall") and floor:
        if not lit:
            area("Ceiling Light", (rc.x, rc.y, top), max(0.8, (rhi.x - rlo.x) * 0.6), 60, (0, 0, 0),
                 max(0.8, (rhi.y - rlo.y) * 0.6))
        # a small fill just behind the camera, clear of the walls beside it
        # (a larger one ahead of it lit up the nearest wall)
        back = (target.location - eye).normalized()
        area("Fill Light", (eye.x - 0.25 * back.x, eye.y - 0.25 * back.y, min(top, eye.z + 0.3)), 0.4, 10,
             back.to_track_quat("-Z", "Y").to_euler())
    elif ceiling and floor:
        # the front view of a whole room: the ceiling light over the middle
        # of the room, clear of the walls (one near the vanity wall cut a
        # hard, bright band across it), and the fill from behind the camera
        if not lit:
            area("Ceiling Light", (center.x, (rc.y + lo.y) / 2, top), max(1.0, min(width, rhi.y - rlo.y) * 0.6),
                 110 * max(1.0, width / 1.8), (0, 0, 0))
        # the fill inside the room, high in front of the tub soffit (outside
        # it, behind the camera, it would be shut out by the far wall), aimed
        # at the vanity and unseen by the camera
        # (aimed level: a tilted panel's back edge cuts a shadow line across
        # the ceiling; a level one's falls along the soffit's edge)
        fy = rlo.y + 0.15
        fz = min(1.9, top - 0.3)
        area("Fill Light", (center.x + 0.3 * width, fy, fz), 1.0, 40,
             (Vector((center.x, lo.y + 0.5, fz)) - Vector((center.x + 0.3 * width, fy, fz)))
             .to_track_quat("-Z", "Y").to_euler())
        fill = bpy.data.objects.get("Fill Light")
        if fill is not None:
            fill.visible_camera = False
            fill.visible_glossy = False
        # and a weak one behind the camera, for the cut ends of the walls
        # nearest it (the far wall, which now casts shadows, keeps it out of
        # the room)
        area("Edge Light", (cam.location.x, cam.location.y - 0.3, cam.location.z + 0.3), 1.0, 20,
             (math.radians(80), 0, 0))
    else:
        area("Ceiling Light", (center.x, lo.y + 0.2, min(2.45, top)), max(1.0, width), 90 * max(1.0, width / 1.8), (0, 0, 0))
        area("Fill Light", (center.x + 0.6 * width, lo.y - 1.6, min(1.8, top)), 1.5, 45,
             (math.radians(70), 0, math.radians(20)))

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1.0)
        bg.inputs["Strength"].default_value = 0.15


def open_hall_door():
    """The second floor's door from the hallway, built shut, turned open
    square into the room about its hinge (client, 2026-10-25: the SketchUp
    files with every door open). The leaf is its stiles, rails, panels and
    lever; the hinge is on the side away from the lever, at the room-side
    face (the casing's side: the model trims only the room's side)."""
    leaf = [o for o in bpy.context.scene.objects
            if o.name.startswith("Hallway door_") and re.search(r"_(Stile|Rail|Panel|Door lever)", o.name)]
    casing = [o for o in bpy.context.scene.objects if o.name.startswith("Hallway door_Casing")]
    if not leaf or not casing:
        return
    def box_of(objs):
        pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
        return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]
    lo, hi = box_of([o for o in leaf if "Door lever" not in o.name])   # the slab itself, not the lever's reach
    clo, chi = box_of(casing)
    ax = 0 if hi[0] - lo[0] < hi[1] - lo[1] else 1       # the leaf's thin direction (through the wall)
    wd = 1 - ax                                          # its width
    room_up = (clo[ax] + chi[ax]) / 2 > (lo[ax] + hi[ax]) / 2   # the room is on the casing's side
    face = hi[ax] if room_up else lo[ax]
    lv = [o for o in leaf if "Door lever" in o.name]
    vlo, vhi = box_of(lv) if lv else (hi, hi)          # (bounding boxes: imported pieces keep their origin at 0)
    lc = (vlo[wd] + vhi[wd]) / 2
    hinge_w = lo[wd] if abs(lc - hi[wd]) < abs(lc - lo[wd]) else hi[wd]
    pivot = Vector((0.0, 0.0, 0.0))
    pivot[ax], pivot[wd] = face, hinge_w
    # the turn that carries the latch edge into the room
    latch = Vector((0.0, 0.0, 0.0))
    latch[ax], latch[wd] = face, (hi[wd] if hinge_w == lo[wd] else lo[wd])
    for sgn in (1, -1):
        rot = Matrix.Translation(pivot) @ Matrix.Rotation(sgn * math.pi / 2, 4, "Z") @ Matrix.Translation(-pivot)
        moved = rot @ latch
        if (moved[ax] > face) == room_up:
            break
    for o in leaf:
        o.matrix_world = rot @ o.matrix_world
    bpy.context.view_layer.update()


# The groups a SketchUp model is sorted into (client, 2026-10-25: "more groups
# and/or layers so we can separate out doors, windows, walls, cabinets,
# fixtures, little things"), named in the style of the U.S. National CAD
# Standard's layers (A- architecture, P- plumbing, E- electrical, I- interiors)
# and made into layers by room.rb (export_rb()). The first that matches
# a piece's name wins; the shell version keeps only DAE_SHELL.
DAE_GROUPS = [
    ("I-ARTW_Art", r"_art_|^Print"),
    ("A-WALL_Walls", r"(^|_)(wall|wall_end|Partition|Hallway_chase|Hallway_end|SOFFIT|Wallpaper|Wainscot_tile|Wainscot_cap|"
                     r"Shower_tile|Tile_Tile_(back|end))(_|$)|_wall$|^Window_wall|^Walk-in_(east|south)_wall"),
    ("A-FLOR_Floors_and_ceilings", r"^(?!.*Tub)(.*(^|_)(Floor|floor|ceiling|Porch_\w+)$|(.*_)?CEILING(_hallway|_east_slope|_west_slope)?$|"
                                   r".*Tile_Tile_ceiling)"),
    ("A-DOOR_Doors", r"^(?!.*(cabinet|Cupboard|Linen_press|vanity|Vanity)).*((^|_)(door|Door|Closet_door)(_|$)|Walk-in_(casing|head|jamb)|"
                     r"Shower_opening|Plinth_block|Hall_door)"),
    ("A-GLAZ_Windows", r"^Window_(?!.*(curtain|Curtain|Shade|shade))"),
    ("A-BASE_Baseboards", r"[Bb]aseboard"),
    ("A-CASE_Cabinets_and_built-ins", r"cabinet|Cupboard|Seat_drawer|^Knob$|Linen_press_(?!top_)|Vanity_OO|WC_vanity_OO|FILLER|Countertop|"
                                      r"[Bb]acksplash|Sidesplash|Walk-in_(shelf|rod)|Hat_shelf|Hook_board|Peg_rail_(Rail|Shelf|Bracket)"),
    ("A-ACCS_Mirrors_and_bath_accessories", r"Grab_bar|grab_bar|Paper_holder|Towel_(bar|ring)|[Hh]ook|[Mm]irror"),
    ("P-FIXT_Plumbing_fixtures", r"Toilet_|(^|_)Tub(_|$)|Sink|Faucet|faucet|spout|Shower_(arm|head|valve|diverter|flange|fittings)|"
                                 r"Hand_shower|Hose|Slide_bar|_Slider|^WEST_Slider"),
    ("E-LITE_Lights_switches_and_outlets", r"light|Sconce|Switch|Outlets|Fans_"),
    ("I-FURN_Furniture", r"Bench_|Entry_stool|Pop-up_table|Hall_table|Settle|Seat_cushion|Lamp_|lamp_|bench|sofa|chair|settle"),
    ("I-DECO_Curtains_rugs_and_decorations", r"."),
]
DAE_SHELL = ("A-WALL_Walls", "A-FLOR_Floors_and_ceilings", "A-DOOR_Doors", "A-GLAZ_Windows")


def dae_group(o):
    import assets
    name = o.name
    mid = o.get(assets.TAG)
    if mid:
        name = "%s_%s" % (mid, name)   # (a downloaded model: furniture or a decoration by its id)
    name = re.sub(r"\.\d{3}$", "", name).replace(" ", "_")
    for group, pattern in DAE_GROUPS:
        if re.search(pattern, name):
            return group


def export_rb(path, groups):
    """The same room as a Ruby script that builds it inside SketchUp Make 2016
    (client, 2026-10-26: SketchUp 2016 imports a .dae as one component of loose
    faces, dropping every group, name and material name, so its layers can't
    be made after the import). Each piece becomes a named group on the layer
    for its kind (DAE_GROUPS), in plain colors (no pictures). Run with
    load "<folder>/room.rb" in the Ruby Console. Units: inches."""
    import json
    depsgraph = bpy.context.evaluated_depsgraph_get()
    k = 1 / INCH                                     # meters to inches
    colors = {}
    out = []
    for g, empty in sorted(groups.items()):
        out.append("G.call(%s)" % json.dumps(g.replace("_", " ", 1).replace("_", " ")))
        for o in empty.children:
            if o.type != "MESH":
                continue
            ev = o.evaluated_get(depsgraph)
            me = ev.to_mesh()
            mw = o.matrix_world
            vs = []
            for v in me.vertices:
                c = mw @ v.co
                vs += ["%.3f" % (c.x * k), "%.3f" % (c.y * k), "%.3f" % (c.z * k)]
            mats = []
            for slot in o.material_slots:
                m = slot.material
                name = re.sub(r"^[A-Z]-[A-Z]{4} ", "", m.name) if m else "plain"
                if name not in colors:
                    rgb = (0.8, 0.8, 0.8)
                    if m and m.use_nodes:
                        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                        if b and not b.inputs["Base Color"].is_linked:
                            rgb = tuple(b.inputs["Base Color"].default_value)[:3]
                        elif m:
                            rgb = tuple(m.diffuse_color)[:3]
                    elif m:
                        rgb = tuple(m.diffuse_color)[:3]
                    # linear to sRGB 0-255
                    colors[name] = [int(round(255 * (c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)))
                                    for c in rgb]
                mats.append(name)
            fs = {}
            for poly in me.polygons:
                mn = mats[poly.material_index] if mats and poly.material_index < len(mats) else "plain"
                fs.setdefault(mn, []).append(list(poly.vertices))
            colors.setdefault("plain", [204, 204, 204])
            for mn, faces in fs.items():
                out.append("P.call(%s,%s,[%s],%s)" % (json.dumps(re.sub(r"\.\d{3}$", "", o.name)), json.dumps(mn),
                                                      ",".join(vs), json.dumps(faces, separators=(",", ":"))))
            ev.to_mesh_clear()
    head = """# The room, built inside SketchUp Make 2016 (tools/blender/vanity_render_setup.py,
# export_rb()). Window > Ruby Console, then: load "C:/the/folder/room.rb"
# Each piece is a named group on the layer for its kind (A-WALL Walls,
# A-DOOR Doors, A-GLAZ Windows...), in plain colors; inches.
model = Sketchup.active_model
model.start_operation("Build the room", true)
top = model.active_entities.add_group
top.name = %s
COLORS = %s
mats = {}
COLORS.each { |n, c| mats[n] = model.materials[n] || model.materials.add(n); mats[n].color = Sketchup::Color.new(*c) }
layer = nil
G = lambda { |name| layer = model.layers[name] || model.layers.add(name) }
count = Hash.new(0)
P = lambda do |name, mat, v, faces|
  pts = v.each_slice(3).map { |a| Geom::Point3d.new(*a) }
  g = top.entities.add_group
  g.name = name
  g.layer = layer
  faces.each do |idx|
    begin
      f = g.entities.add_face(idx.map { |i| pts[i] })
      f.material = mats[mat] if f
    rescue ArgumentError
      (1...idx.size - 1).each do |j|   # not flat or too small: as triangles
        begin
          f = g.entities.add_face(pts[idx[0]], pts[idx[j]], pts[idx[j + 1]])
          f.material = mats[mat] if f
        rescue ArgumentError
        end
      end
    end
  end
  count[layer.name] += 1
end
""" % (json.dumps(os.path.splitext(os.path.basename(os.path.dirname(path)))[0] or "room"),
       "{" + ", ".join("%s => %s" % (json.dumps(n), json.dumps(c)) for n, c in colors.items()) + "}")
    tail = """model.commit_operation
count.sort.each { |t, n| puts "#{t}: #{n} pieces" }
puts "Done. Turn the layers on and off in Window > Layers."
"""
    open(path, "w").write(head + "\n".join(out) + "\n" + tail)
    print("Exported", path)


def export_dae(path, light=False, shell=False):
    """The built room as COLLADA (.dae) for SketchUp (File > Import), in
    meters, its images copied beside it (tools/export_sketchup.py). light:
    without the downloaded models (vases, flowers, baskets, benches) and the
    draped towels, which are heavy for SketchUp 2016. Lights, cameras, the
    photo backdrops outside the windows and anything hidden from the render
    are left out; curves and text become meshes."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import assets
    scene = bpy.context.scene
    for o in list(scene.objects):
        heavy = o.get(assets.TAG) or re.search(r"(^|_)Towel(\.\d+)?$", o.name)   # (draped cloth: 13,000 faces a towel)
        drop = (o.type in ("CAMERA", "LIGHT", "LIGHT_PROBE") or o.hide_render or (light and heavy)
                or o.name.startswith("Window view"))   # (the mud room's photo outside: a 20 m backdrop)
        if drop:
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    curvy = [o for o in scene.objects if o.type in ("CURVE", "FONT", "SURFACE", "META")]
    if curvy:
        for o in curvy:
            o.select_set(True)
        bpy.context.view_layer.objects.active = curvy[0]
        bpy.ops.object.convert(target="MESH")
    bpy.context.view_layer.update()
    open_hall_door()
    # every piece into its group (DAE_GROUPS), so SketchUp gets one group per
    # kind of thing; shell: only the walls, floors and ceilings, doors and windows
    bpy.context.view_layer.update()
    groups = {}
    coded = {}
    for o in [o for o in scene.objects if o.type == "MESH"]:
        g = dae_group(o)
        if (shell and g not in DAE_SHELL) or o.name.startswith("Camera Target"):
            bpy.data.objects.remove(o)
            continue
        if g not in groups:
            groups[g] = bpy.data.objects.new(g, None)
            scene.collection.objects.link(groups[g])
        mw = o.matrix_world.copy()
        o.parent = groups[g]
        o.matrix_world = mw
        # SketchUp 2016 imports the whole file as one component of loose faces,
        # dropping every group and name; only the faces' materials survive
        # (client, 2026-10-26). So each material is copied per group, named with
        # the group's code ("A-DOOR trim"), (no longer needed by room.rb, which sorts by group; harmless).
        code = g.split("_")[0]
        if o.data.users > 1:
            o.data = o.data.copy()
        if not o.material_slots:
            o.data.materials.append(None)
        for slot in o.material_slots:
            base = slot.material
            key = (code, base.name if base else "")
            if key not in coded:
                coded[key] = base.copy() if base else bpy.data.materials.new("plain")
                coded[key].name = "%s %s" % (code, base.name if base else "plain")
            slot.material = coded[key]
    while True:   # the empties left holding nothing
        bare = [o for o in scene.objects if o.type == "EMPTY" and not o.children and o.name not in groups
                and o.instance_type == "NONE"]
        if not bare:
            break
        for o in bare:
            bpy.data.objects.remove(o)
    bpy.context.view_layer.update()
    # SketchUp reads meters, as the room models are built; one built in
    # inches (its typical piece tens of units across) is scaled down. (The
    # median: the mud room's view outside is one 22 m plane.)
    sizes = sorted(max(o.dimensions) for o in scene.objects if o.type == "MESH")
    if sizes and sizes[len(sizes) // 2] > 5:
        k = Matrix.Scale(INCH, 4)
        for o in scene.objects:
            if o.parent is None:
                o.matrix_world = k @ o.matrix_world
    # images made in memory (the matted art, the cut papers) need a file to copy
    folder = os.path.dirname(path)
    for img in bpy.data.images:
        if img.users and img.type == "IMAGE" and (img.source == "GENERATED" or img.packed_file):
            img.filepath_raw = os.path.join(folder, re.sub(r"[^A-Za-z0-9_-]+", "_", img.name) + ".png")
            img.file_format = "PNG"
            img.save()
    export_rb(os.path.join(folder, "room.rb"), groups)
    bpy.ops.wm.collada_export(filepath=path, apply_modifiers=True, triangulate=False,
                              use_texture_copies=True, export_global_forward_selection="Y",
                              export_global_up_selection="Z")
    # (an image node with no UV map node is written without its texcoord,
    # which makes the file invalid: name the UV map every mesh has)
    text = open(path).read()
    text = re.sub(r'<texture texture="([^"]*)"/>', r'<texture texture="\1" texcoord="UVMap"/>', text)
    open(path, "w").write(text)
    print("Exported", path)


def pano_camera():
    """PANO=1: the view's camera becomes a 360-degree one (equirectangular,
    2:1), level at eye height in the middle of the room: in the walkway
    between the vanities and the tub, halfway along from the view across to
    the tub to the view back to the hall, or at PANO_AT="x,y" in meters (the
    loft's and the mud room's scripts set it from their PANOS). The
    picture's middle looks at the hallway door, or at PANO_FACE="x,y".
    PANO_RES: its width (default 3072). For the look-around page
    (tools/build_pano.py)."""
    scene = bpy.context.scene
    objs = list(scene.objects)
    at = os.environ.get("PANO_AT")
    if at:
        x, y = map(float, at.split(","))
    else:
        # (the hall view's eye is midway between the vanity front and the
        # tub: keep its distance across, halfway along between the two eyes)
        a, b = marker(objs, "VIEW_OPPOSITE_EYE"), marker(objs, "VIEW_HALL_EYE")
        x, y = (a.x + b.x) / 2, b.y
    cam = scene.camera
    cam.location = (x, y, EYE_HEIGHT)
    cam.data.type = "PANO"
    cam.data.panorama_type = "EQUIRECTANGULAR"
    cam.data.shift_x = cam.data.shift_y = 0
    face = os.environ.get("PANO_FACE")
    fx, fy = map(float, face.split(",")) if face else marker(objs, "VIEW_ENTRY_EYE").xy
    yaw = math.atan2(fy - y, fx - x) - math.pi / 2
    cam.rotation_mode = "XYZ"
    cam.rotation_euler = (math.pi / 2, 0, yaw)
    for c in cam.constraints:            # (a Track To would undo the level aim)
        cam.constraints.remove(c)
    w = int(os.environ.get("PANO_RES", "3072"))
    scene.render.resolution_x, scene.render.resolution_y = w, w // 2


# The things on a wall that can crowd each other, by name; a curtain wants
# CURTAIN_CLEAR inches from any of them, any two others not to touch.
CROWD_KINDS = [
    ("curtain", r"curtain(?!.*(rod|ring|bracket|liner|finial))"),
    ("towel", r"towel|TOWEL_"),
    ("sconce", r"sconce"),
    ("mirror", r"mirror|medicine cabinet"),
    ("art", r"(?<!switch )(art_|wall art|print|plate_)(?!.*switch)"),
    ("switch", r"switch"),
    ("outlet", r"outlet|receptacle|gfci"),
    ("hook", r"hook|peg rail"),
    ("grab bar", r"grab bar"),
    ("paper holder", r"paper holder"),
    # (client, 2026-10-23: the loft's window curtain ran into the counter's
    # end from the vanity view; counters are looked at against curtains only)
    ("counter", r"countertop|counter ?top|vanity top|backsplash"),
]
# pairs designed to sit close: a towel ring under a sconce, a sconce beside
# its mirror, a hook or towel on a peg rail
CROWD_OK = {frozenset(p) for p in (("towel", "sconce"), ("sconce", "mirror"), ("towel", "hook"),
                                   ("hook", "art"), ("towel", "grab bar"), ("towel", "mirror"))}
CURTAIN_CLEAR = 3.0


def crowd_kind(o):
    """The CROWD_KINDS kind of o, by its name or its materials' (an imported
    vanity's top is named by SketchUp, but its material says countertop)."""
    label = " ".join([o.name] + [m.name for m in getattr(o.data, "materials", []) if m])
    for kind, pat in CROWD_KINDS:
        if re.search(pat, o.name if kind != "counter" else label, re.I):
            return kind
    return None


def crowding(objs):
    """Wall things that crowd each other (client, 2026-10-23: the Marigold
    window curtains merged with the fittings beside them; a check for every
    room, like the joints'): a curtain within CURTAIN_CLEAR inches of a
    towel, sconce, mirror, picture, switch, hook, grab bar or paper holder,
    or two of those touching or overlapping. Returns 'a / b: n" apart'
    lines, printed as CROWD ... before each render."""
    meshes = [o for o in objs if o.type == "MESH" and not o.hide_render and o.visible_camera]
    sizes = sorted(max(o.dimensions) for o in meshes) or [0]
    unit = 1.0 if sizes[len(sizes) // 2] > 5 else INCH          # the scene in inches, or meters
    found = {}
    for o in meshes:
        kind = crowd_kind(o)
        if kind:
            lo, hi = world_bbox([o])
            found.setdefault(kind, []).append((o.name, lo / unit, hi / unit))
    out, seen = [], set()
    kinds = sorted(found)
    for i, ka in enumerate(kinds):
        for kb in kinds[i + 1:]:
            if frozenset((ka, kb)) in CROWD_OK or ("counter" in (ka, kb) and "curtain" not in (ka, kb)):
                continue
            # (a curtain need only clear a counter, not stand 3" off it: the
            # loft's sits 1 1/2" beside the counter's end and 2" above it)
            need = (1.0 if "counter" in (ka, kb) else CURTAIN_CLEAR) if "curtain" in (ka, kb) else 0.0
            for na, la, ha in found[ka]:
                for nb, lb, hb in found[kb]:
                    gap = max(max(la[k] - hb[k], lb[k] - ha[k]) for k in range(3))
                    if gap < need or (need == 0.0 and gap < 0.0):
                        key = (re.split(r"[_.]", na)[0], re.split(r"[_.]", nb)[0])
                        if key not in seen:
                            seen.add(key)
                            out.append('%s (%s) / %s (%s): %.1f" apart' % (na, ka, nb, kb, max(gap, 0.0)))
    return out


# The walkway check (client, 2026-10-24: "I feel like I keep mentioning
# walkway problems"): clear floor in every doorway, along each room's paths
# and in front of its fixtures, printed as CLEAR ... lines with the joints
# and the crowding. DESIGN_RULES.md §5 has the numbers and their sources.
CLEAR_DOOR = 24.0        # clear in front of a doorway, each side (the door's width where wider, for its swing)
CLEAR_TOILET = 21.0      # in front of a toilet (IRC R307), and 15" from its center to either side
CLEAR_TOILET_SIDE = 15.0
CLEAR_SINK = 21.0        # in front of a sink (IRC R307)
CLEAR_TOL = 1.5          # trim, baseboards, plates and pulls stand about this far out
CLEAR_PROTRUDE = 4.0     # a wall-hung thing 27" up or more may stand this far into a path (ADA 307.2)
# Never in the way: the floor and what lies flat on it, the room's own shell
# and trim, and what hangs above head height
CLEAR_SKIP = re.compile(r"(^|_)(Floor|Hall floor|Bath floor|Hallway floor)\b|floor$|(?<![a-z])(rug|runner|bath mat)(?![a-z])|"
                        r"Baseboard|baseboard|Plinth block|Wainscot|Wallpaper|Frieze|Picture rail|CEILING|Ceiling|"
                        r"Window view|Shade|shade", re.I)
DOOR_LEAF = re.compile(r"door leaf|Bath door|Closet door|Hallway door_(Stile|Rail|Panel|Door lever)|Knob|knob", re.I)
# doors whose leaf swings away from the room's middle (into a closet): the
# room's side needs only CLEAR_DOOR, the swing side the door's width; a room
# script adds a door's label here (the mud room's walk-in, 2026-11-05)
SWING_AWAY = set()
DOOR_PIECES = (            # (what to call it, the pieces that frame it, how they frame it)
    ("the hall door", r"^Hall door jamb", "jamb"),
    ("the WC door", r"^WEST_WC door jamb", "jamb"),
    ("the shower opening", r"^WEST_Shower opening return", "jamb"),
    ("a doorway from the hall", r"^Door jamb", "jamb"),
    ("the walk-in's door", r"^Walk-in jamb", "jamb"),
    ("the hall door", r"^Hallway door_Casing", "casing"),
)


def _clusters(boxes, ax):
    """Pieces grouped into openings: those whose spans along ax overlap."""
    groups = []
    for b in sorted(boxes, key=lambda b: b[0][ax]):
        for g in groups:
            if any(b[0][ax] <= h[1][ax] + 0.1 and h[0][ax] <= b[1][ax] + 0.1 for h in g):
                g.append(b)
                break
        else:
            groups.append([b])
    return groups


def door_zones(meshes, unit):
    """The clear floor each side of every doorway, found from the pieces that
    frame it (DOOR_PIECES): as deep as CLEAR_DOOR, or the opening's width
    where wider and a leaf hangs in it (so the door's whole swing is clear).
    A cased side only (the hallway's other side isn't modeled)."""
    zones = []
    leaves = [world_bbox([o]) for o in meshes if DOOR_LEAF.search(o.name)]
    leaves = [(lo / unit, hi / unit) for lo, hi in leaves]
    slo, shi = world_bbox(meshes)
    centre = [(slo[k] + shi[k]) / 2 / unit for k in range(2)]
    for label, pat, how in DOOR_PIECES:
        boxes = [tuple(v / unit for v in world_bbox([o])) for o in meshes if re.search(pat, o.name)]
        if not boxes:
            continue
        lo = [min(b[0][k] for b in boxes) for k in range(2)]
        hi = [max(b[1][k] for b in boxes) for k in range(2)]
        ax = 0 if hi[0] - lo[0] > hi[1] - lo[1] else 1     # along the wall
        nx = 1 - ax                                        # through it
        for g in (_clusters(boxes, ax) if how == "jamb" else [boxes]):     # (a door's two casings never overlap)
            glo = [min(b[0][k] for b in g) for k in range(2)]
            ghi = [max(b[1][k] for b in g) for k in range(2)]
            if how == "jamb":
                a, b = glo[ax] + 0.75, ghi[ax] - 0.75     # inside the jambs
                faces = ((glo[nx], -1), (ghi[nx], 1))
            else:
                # two casings on the room's face of the wall: the opening
                # between their inner edges, the room on the side toward the
                # middle of the scene (the hallway beyond isn't modeled)
                ins = sorted(g, key=lambda b_: b_[0][ax])
                a, b = ins[0][1][ax], ins[-1][0][ax]
                room_lo = centre[nx] < (glo[nx] + ghi[nx]) / 2
                faces = ((ghi[nx], -1),) if room_lo else ((glo[nx], 1),)
            width = b - a
            mid = [0.0, 0.0]
            mid[ax], mid[nx] = (a + b) / 2, faces[0][0]
            hung = any(math.dist(mid, [(l[0][k] + l[1][k]) / 2 for k in range(2)]) < width + 6 for l in leaves)
            depth = max(CLEAR_DOOR, width) if hung else CLEAR_DOOR
            for face, sgn in faces:
                toward_middle = (centre[nx] - face) * sgn > 0
                d_ = CLEAR_DOOR if (label in SWING_AWAY and toward_middle) else depth
                z0, z1 = (face, face + sgn * d_) if sgn > 0 else (face - d_, face)
                lo_, hi_ = [0.0, 0.0], [0.0, 0.0]
                lo_[ax], hi_[ax] = a, b
                lo_[nx], hi_[nx] = z0, z1
                zones.append(dict(name="%s (%.0f\" wide), %.0f\" in front" % (label, width, d_), lo=lo_, hi=hi_,
                                  skip=DOOR_LEAF))
    return zones


def fixture_zones(meshes, unit):
    """The clear floor in front of each toilet and sink (IRC R307): 21" in
    front, and for a toilet 15" from its center to any side wall, partition
    or cabinet. A toilet faces away from its tank, a sink away from its
    mirror (or the wall its faucet comes out of)."""
    def box(objs):
        lo, hi = world_bbox(objs)
        return [lo[0] / unit, lo[1] / unit, lo[2] / unit], [hi[0] / unit, hi[1] / unit, hi[2] / unit]
    zones = []
    toilets = {}
    for o in meshes:
        m = re.match(r"(.*?)Toilet_", o.name)
        if m and not re.search(r"Toilet_(Supply|Lever)", o.name):
            toilets.setdefault(m.group(1), []).append(o)
    for pre, parts in toilets.items():
        tank = [o for o in parts if re.search(r"Toilet_Tank$", o.name)]
        if not tank:
            continue
        (tlo, thi), (alo, ahi) = box(tank), box(parts)
        tc = [(tlo[k] + thi[k]) / 2 for k in range(2)]
        ac = [(alo[k] + ahi[k]) / 2 for k in range(2)]
        ax = 0 if abs(ac[0] - tc[0]) > abs(ac[1] - tc[1]) else 1     # the way it faces
        sgn = 1 if ac[ax] > tc[ax] else -1
        lat = 1 - ax
        front = ahi[ax] if sgn > 0 else alo[ax]
        back = alo[ax] if sgn > 0 else ahi[ax]
        c = (tlo[lat] + thi[lat]) / 2
        lo_, hi_ = [0.0, 0.0], [0.0, 0.0]
        lo_[lat], hi_[lat] = c - CLEAR_TOILET_SIDE, c + CLEAR_TOILET_SIDE
        lo_[ax], hi_[ax] = sorted((front, front + sgn * CLEAR_TOILET))
        zones.append(dict(name="21\" in front of the toilet", lo=lo_, hi=hi_,
                          skip=re.compile(r"Toilet_|Paper holder|Grab bar|grab bars", re.I)))   # (wall-hung where code puts them)
        lo2, hi2 = list(lo_), list(hi_)
        lo2[ax], hi2[ax] = sorted((back, front))
        zones.append(dict(name="15\" each side of the toilet's center", lo=lo2, hi=hi2, z=(0.0, 20.0),
                          skip=re.compile(r"Toilet_|Paper holder|Grab bar|grab bars|Waste can|Supply|Tissue box|Towel", re.I)))
    mirrors = [box([o]) for o in meshes if re.search(r"Mirror_Glass$|Mirror glass$", o.name)]
    counters = [box([o]) for o in meshes if re.search(r"Countertop$", o.name)]
    for o in meshes:
        if not re.search(r"(Sink_Sink|Sink basin)(\.\d+)?$", o.name):
            continue
        blo, bhi = box([o])
        bc = [(blo[k] + bhi[k]) / 2 for k in range(2)]
        if not mirrors:
            continue
        mlo, mhi = min(mirrors, key=lambda m: math.dist(bc, [(m[0][k] + m[1][k]) / 2 for k in range(2)]))
        mc = [(mlo[k] + mhi[k]) / 2 for k in range(2)]
        ax = 0 if mhi[0] - mlo[0] < mhi[1] - mlo[1] else 1     # (a mirror is thin through its wall)
        sgn = 1 if bc[ax] > mc[ax] else -1
        lat = 1 - ax
        front = bhi[ax] if sgn > 0 else blo[ax]
        for clo, chi in counters:                          # (the counter's edge, where there is one)
            if clo[lat] <= bc[lat] <= chi[lat] and clo[ax] <= bc[ax] <= chi[ax]:
                front = chi[ax] if sgn > 0 else clo[ax]
        lo_, hi_ = [0.0, 0.0], [0.0, 0.0]
        lo_[lat], hi_[lat] = blo[lat], bhi[lat]
        lo_[ax], hi_[ax] = sorted((front, front + sgn * CLEAR_SINK))
        zones.append(dict(name="21\" in front of the sink", lo=lo_, hi=hi_))
    return zones


def clearances(objs, paths=()):
    """What stands in the clear floor of a doorway, a path or a fixture.
    paths: (name, (x0, y0), (x1, y1), clear width needed) rectangles in the
    scene's units, from the room's own script. Returns lines like
    'the hall door (24" wide), 24" in front: Bench (stands 6" into it)'."""
    meshes = [o for o in objs if o.type == "MESH" and not o.hide_render and o.visible_camera]
    sizes = sorted(max(o.dimensions) for o in meshes) or [0]
    unit = 1.0 if sizes[len(sizes) // 2] > 5 else INCH
    # (and not the spare flower stems some loft builds leave at the origin,
    # inside the walls' corner, out of sight: they're no one's walkway)
    meshes = [o for o in meshes if o.visible_get() and not (
        o.name.startswith("periwinkle") and max(map(abs, world_bbox([o])[0][:2])) < 6.0 * (1.0 if unit == 1.0 else INCH))]
    zones = door_zones(meshes, unit) + fixture_zones(meshes, unit)
    if os.environ.get("CLEAR_DEBUG"):
        for zn in zones:
            print("ZONE %s %s %s" % (zn["name"], [round(v, 1) for v in zn["lo"]], [round(v, 1) for v in zn["hi"]]), flush=True)
    for name, a, b, need in paths:
        zones.append(dict(name="%s (%.0f\" clear)" % (name, need), lo=[min(a[0], b[0]), min(a[1], b[1])],
                          hi=[max(a[0], b[0]), max(a[1], b[1])]))
    boxes = []
    for o in meshes:
        if CLEAR_SKIP.search(o.name) or DOOR_LEAF.search(o.name):
            continue                       # (a door stands open in the renders, shut in use: its swing is the doorway's zone)
        lo, hi = world_bbox([o])
        boxes.append((o.name, lo / unit, hi / unit))
    out = []
    for zn in zones:
        z0, z1 = zn.get("z", (0.0, 80.0))
        worst = {}
        for name, lo, hi in boxes:
            if zn.get("skip") is not None and zn["skip"].search(name):
                continue
            if lo[2] >= z1 or hi[2] <= z0 + 1.0:          # (flat on the floor: a rug or mat)
                continue
            ox = min(hi[0], zn["hi"][0]) - max(lo[0], zn["lo"][0])
            oy = min(hi[1], zn["hi"][1]) - max(lo[1], zn["lo"][1])
            into = min(ox, oy)
            if into <= CLEAR_TOL or (lo[2] >= 27.0 and into <= CLEAR_PROTRUDE):
                continue
            bare = re.sub(r"^(WEST_|OPPOSITE_SIDE_|Counter items_)", "", name)    # (the view-cutting prefixes)
            key = " ".join(re.split(r"[_.]| \d", bare)[0].split()[:2])     # (a piece's parts as one: "Hall cabinet")
            if os.environ.get("CLEAR_DEBUG"):
                print("HIT %s: %s %s %s" % (zn["name"], name, [round(v, 1) for v in lo], [round(v, 1) for v in hi]), flush=True)
            if key not in worst or into > worst[key][0]:
                worst[key] = (into, name)
        for key, (into, name) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
            out.append('%s: %s stands %.1f" into it' % (zn["name"], key, into))
    return out


def crowding_in_view(objs, cam=None, share=0.08):
    """The same, as the camera sees it: a curtain whose outline in the
    picture (its faces projected, not its box) overlaps a towel, sconce,
    mirror, picture, switch, hook, grab bar, paper holder or counter by at
    least `share` of the smaller one
    (only touching was flagged at first, and a curtain beside the loft's
    tall mirror, well apart, was called crowded; client, 2026-10-23)
    (client, 2026-10-23: the Marigold window curtain ran together with the
    towel, sconce and mirror beside it, 10" apart in the room but lined up
    from the vanity view). Returns lines like crowding()'s."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    bpy.context.view_layer.update()              # (a camera just made has no matrix yet)
    cam = cam or scene.camera
    meshes = [o for o in objs if o.type == "MESH" and not o.hide_render and o.visible_camera]
    rects = {}
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eye = cam.matrix_world.translation

    def seen(o):
        """Whether the camera sees any of o: a ray to its middle and to
        points near its corners meets o first (a wall between hides it)."""
        corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
        mid = sum(corners, Vector()) / 8
        for p in [mid] + [mid.lerp(c, 0.8) for c in corners]:
            d = p - eye
            hit, _, _, _, ob, _ = scene.ray_cast(depsgraph, eye, d.normalized(), distance=d.length + 1e-4)
            if not hit or ob.name == o.name:
                return True
        return False
    import numpy as np                             # (PIL won't load inside Blender)
    GW, GH = 320, 240                              # the picture, coarsely: each thing's outline drawn in it

    def outline(o):
        """o's silhouette in the picture: every face projected and filled
        (its bounding box first took in the air over a long counter's near
        end, and called a curtain beyond it crowded; 2026-10-23)."""
        ev = o.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = o.matrix_world
        pv = [world_to_camera_view(scene, cam, mw @ vt.co) for vt in me.vertices]
        P = np.array([(q.x * GW, (1 - q.y) * GH) for q in pv])
        front = np.array([q.z > 0 for q in pv])
        im = np.zeros((GH, GW), dtype=bool)
        me.calc_loop_triangles()
        for t in me.loop_triangles:
            i = list(t.vertices)
            if not front[i].all():
                continue
            a, b, c = P[i]
            x0, x1 = max(int(min(a[0], b[0], c[0])), 0), min(int(max(a[0], b[0], c[0])) + 1, GW)
            y0, y1 = max(int(min(a[1], b[1], c[1])), 0), min(int(max(a[1], b[1], c[1])) + 1, GH)
            if x0 >= x1 or y0 >= y1:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-9:
                continue
            l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
            l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
            im[y0:y1, x0:x1] |= (l1 >= -0.05) & (l2 >= -0.05) & (1 - l1 - l2 >= -0.05)
        ev.to_mesh_clear()
        return im
    for o in meshes:
        kind = crowd_kind(o)
        if not kind or not seen(o):
            continue
        m = outline(o)
        if m.any():
            rects.setdefault(kind, []).append((o.name, m))
    out, seen = [], set()
    for na, ma in rects.get("curtain", []):
        for kind, items in rects.items():
            if kind == "curtain":
                continue
            for nb, mb in items:
                both = int((ma & mb).sum())
                if both and both >= share * min(int(ma.sum()), int(mb.sum())):
                    key = (re.split(r"[_.]", na)[0], re.split(r"[_.]", nb)[0])
                    if key not in seen:
                        seen.add(key)
                        out.append("%s (curtain) / %s (%s): overlapping in the picture" % (na, nb, kind))
    return out


def add_entry_stool(objs):
    """A small Mission stool tucked in the nook between the vanity's end and
    the entry hallway (client, 2026-10-24: "a small stool tucked in the
    corner next to the vanity as you walk into the second floor bathroom,
    such that it does not block the walkway at all"): 12" x 12", 18" high,
    its back against the vanity wall, wholly behind the countertop's front
    edge, so neither the walkway nor the 30 3/8" pinch at the corner
    narrows. Quarter-sawn oak in the house's medium-dark stain (the oak
    vanity's, the picture frames'), four square legs, low stretchers, a
    woven rush seat: somewhere to sit for socks, a step for a child at the
    sink, a perch for a folded towel. Layout D only (the nook is there)."""
    import bmesh
    names = {o.name: o for o in objs if o.type == "MESH"}
    top = names.get("Vanity_Countertop")
    if not top or not any(n.startswith("Hallway chase") for n in names):
        return
    wall = names.get("Vanity wall")
    lo, hi = world_bbox([top])
    wy = world_bbox([wall])[0].y if wall else hi.y                 # the vanity wall's face
    I = INCH
    x0 = hi.x + 2.0 * I                                             # 2" off the countertop's end
    y1 = wy - 1.25 * I                                              # clear of the baseboard and its cap
    x1, y0 = x0 + 12.0 * I, y1 - 12.0 * I
    oak = build_material("stooloak", FINISHES["oak"])
    rush = build_material("stoolrush", dict(color=(0.42, 0.31, 0.15), roughness=0.9, sheen=0.3))
    made = []

    def bx(name, a, b, mat):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for vv in bm.verts:
            vv.co = Vector(((a[0] + b[0]) / 2 + vv.co.x * (b[0] - a[0]), (a[1] + b[1]) / 2 + vv.co.y * (b[1] - a[1]),
                            (a[2] + b[2]) / 2 + vv.co.z * (b[2] - a[2])))
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        o.data.materials.append(mat)
        bev = o.modifiers.new("Ease", "BEVEL")
        bev.width, bev.segments = 0.0015, 2
        objs.append(o)
        made.append(o)
    leg, h = 1.25 * I, 18.0 * I
    for xa in (x0, x1 - leg):
        for ya in (y0, y1 - leg):
            bx("Entry stool_Leg", (xa, ya, 0.0), (xa + leg, ya + leg, h - 0.75 * I), oak)
    # the seat's frame rails, a rush seat woven over them, a little domed
    for ya in (y0, y1 - 0.75 * I):
        bx("Entry stool_Rail", (x0 + leg, ya, h - 2.75 * I), (x1 - leg, ya + 0.75 * I, h - 0.75 * I), oak)
    for xa in (x0, x1 - 0.75 * I):
        bx("Entry stool_Rail", (xa, y0 + leg, h - 2.75 * I), (xa + 0.75 * I, y1 - leg, h - 0.75 * I), oak)
    bx("Entry stool_Seat", (x0 + 0.1 * I, y0 + 0.1 * I, h - 0.75 * I), (x1 - 0.1 * I, y1 - 0.1 * I, h), rush)
    # low stretchers, staggered so they don't meet
    for ya in (y0 + 0.25 * I, y1 - 1.0 * I):
        bx("Entry stool_Stretcher", (x0 + leg, ya, 5.0 * I), (x1 - leg, ya + 0.75 * I, 6.25 * I), oak)
    for xa in (x0 + 0.25 * I, x1 - 1.0 * I):
        bx("Entry stool_Stretcher", (xa, y0 + leg, 7.5 * I), (xa + 0.75 * I, y1 - leg, 8.75 * I), oak)
    return made


def replace_toilet(objs):
    """The SketchUp model's toilet (a 3" puck on a post, which looked sunk
    in the floor from above) swapped for props.toilet, every room's
    (client, 2026-10-23): the same place, its tank against the same wall,
    the same materials, its parts still named <tag>Toilet_<part> for the
    views that frame it."""
    parts = [o for o in objs if o.type == "MESH" and "Toilet_" in o.name
             and not any(k in o.name.lower() for k in ("art", "cabinet", "grab", "paper"))]
    if not parts:
        return
    lo, hi = world_bbox(parts)
    tank = [o for o in parts if "Tank" in o.name] or parts
    tlo, thi = world_bbox(tank)
    c, tc = (lo + hi) / 2, (tlo + thi) / 2
    # toward the wall behind it, along whichever axis the tank sits off center
    if abs(tc.x - c.x) > abs(tc.y - c.y):
        d = Vector((math.copysign(1, tc.x - c.x), 0, 0))
        back = Vector((hi.x if d.x > 0 else lo.x, tc.y, lo.z))
    else:
        d = Vector((0, math.copysign(1, tc.y - c.y), 0))
        back = Vector((tc.x, hi.y if d.y > 0 else lo.y, lo.z))
    porcelain = tank[0].material_slots[0].material if tank[0].material_slots else None
    metal = next((o.material_slots[0].material for o in objs
                  if o.type == "MESH" and "Faucet" in o.name and o.material_slots), None)
    tag = parts[0].name.split("Toilet_")[0]
    for o in parts:
        objs.remove(o)
        bpy.data.objects.remove(o)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import props
    new = props.toilet(tag, 0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    turn = math.atan2(d.y, d.x) - math.atan2(-1.0, 0.0)
    m = (Matrix.Translation(back + d * (0.25 * INCH)) @ Matrix.Rotation(turn, 4, "Z")
         @ Matrix.Scale(INCH, 4))
    for o in new:
        o.matrix_world = m @ o.matrix_world
        lever = "Lever" in o.name
        mat = (metal or porcelain) if lever else porcelain
        if mat:
            o.data.materials.clear()
            o.data.materials.append(mat)
        objs.append(o)


def walk_camera():
    """WALK=<folder>: a low-quality walk-through instead of a still
    (client, 2026-10-23), looking into each part of the room and at every
    fixture, switch and fan: the switches by the hall door; in to the
    middle of the room (where the look-around stands); a turn right to the
    vanity and its receptacles, stepping back so its mirror isn't all the
    picture; left to the tub and shower, and up to its light and fan;
    across to the WC's door; in at the WC's vanity, down to the toilet and
    its water supply, up to the WC's fan, round to its switches. 12 pictures a
    second, 960 x 540, WALK_SAMPLES (default 12), one fixed noise pattern so
    the grain doesn't crawl. Writes <folder>/walk_####.png; tools/build_walk.py
    fills in the pictures between and makes the video. WALK_FRAMES="a-b"
    renders only those (to check the path, or to split a long walk)."""
    scene = bpy.context.scene
    objs = list(scene.objects)
    a, b = marker(objs, "VIEW_OPPOSITE_EYE"), marker(objs, "VIEW_HALL_EYE")
    start = marker(objs, "VIEW_ENTRY_EYE")
    mid = Vector(((a.x + b.x) / 2, b.y, start.z))
    h = math.atan2(mid.y - start.y, mid.x - start.x)            # walking in
    fwd = Vector((math.cos(h), math.sin(h), 0))
    right = Vector((math.cos(h - math.pi / 2), math.sin(h - math.pi / 2), 0))   # the vanity's side

    def toward(p, q):
        return math.atan2(q.y - p.y, q.x - p.x)

    def centre(word):
        found = [o for o in objs if o.type == "MESH" and word in o.name]
        lo, hi = world_bbox(found)
        return (lo + hi) / 2
    wc_eye, wc_target = marker(objs, "VIEW_WC_EYE"), marker(objs, "VIEW_WC_TARGET")
    out = (wc_eye - wc_target)
    out.z = 0
    out.normalize()
    # (the WC view's eye is in the thickness of the WC's wall: the stop
    # before the door 25 cm out from it, and the one inside 30 cm in, past
    # the jambs, so the vanity on one side and the toilet on the other show)
    wc = wc_eye + out * 0.25
    wc.z = start.z
    inside = wc_eye - out * 0.3
    inside.z = start.z
    vanity_wc, bowl = centre("WC vanity_Countertop"), centre("Toilet_Bowl")
    D = math.radians
    if os.environ.get("WALK_DEBUG"):
        for nm, q in (("start", start), ("mid", mid), ("wc_eye", wc_eye), ("wc_target", wc_target), ("wc", wc),
                      ("vanity_wc", vanity_wc), ("bowl", bowl), ("opp", a), ("hall", b)):
            open(os.path.join(os.environ["WALK"], "points.txt"), "a").write("%s %.3f %.3f %.3f\n" % (nm, q.x, q.y, q.z))
    def nearest(word, p):
        """The middle of the visible thing named `word` nearest p."""
        best = None
        for o in objs:
            if o.type == "MESH" and word in o.name and not o.hide_render:
                lo, hi = world_bbox([o])
                c = (lo + hi) / 2
                if best is None or (c - p).length < (best - p).length:
                    best = c
        return best

    def up(p, q):
        """How far up (radians) to look from p at q."""
        return math.atan2(q.z - p.z, math.hypot(q.x - p.x, q.y - p.y))
    hall_sw = nearest("Switch", start)
    tub_stop = mid + right * 0.4
    tub_fan, wc_fan = nearest("Fan", tub_stop), nearest("Fan", bowl)
    wc_sw = nearest("Switch", inside)
    # (seconds, where, which way, how far down, lens): each move eases in
    # and out; in the WC the lens widens toward the WC view's, the room
    # being only 3' across. (client, 2026-10-23: every fixture, switch and
    # fan in the walk, and where the toilet's water comes out of the wall)
    keys = [(0.0, start, h, 0.0, 20),
            (1.5, start, toward(start, hall_sw), up(start, hall_sw), 20),     # the switches by the door
            (2.3, start, toward(start, hall_sw), up(start, hall_sw), 20),
            (4.0, start.lerp(mid, 0.15), h, 0.0, 20),
            (7.5, mid, h, 0.0, 20),                                            # in to the middle
            (9.5, mid - fwd * 0.5, h - D(70), -D(8), 20),                      # the vanity, its receptacles
            (11.0, mid - fwd * 0.5, h - D(70), -D(8), 20),
            (13.5, tub_stop, h + D(80), -D(3), 20),                            # the tub and shower
            (14.5, tub_stop, h + D(80), -D(3), 20),
            (16.0, tub_stop, toward(tub_stop, tub_fan), up(tub_stop, tub_fan) - D(5), 20),   # its light and fan
            (17.0, tub_stop, toward(tub_stop, tub_fan), up(tub_stop, tub_fan) - D(5), 20),
            (19.0, wc, toward(wc, wc_target), -D(5), 20),                      # across to the WC's door
            (21.0, inside, toward(inside, vanity_wc), -D(14), 16),             # in, to its vanity
            (22.5, inside, toward(inside, vanity_wc), -D(14), 16),
            (24.5, inside, toward(inside, bowl), -D(38), 16),                  # down to the toilet and its supply
            (26.0, inside, toward(inside, bowl), -D(38), 16),
            (27.5, inside, toward(inside, wc_fan), up(inside, wc_fan) - D(8), 16),   # the WC's fan
            (28.5, inside, toward(inside, wc_fan), up(inside, wc_fan) - D(8), 16),
            (30.0, inside, toward(inside, wc_sw), up(inside, wc_sw), 16),      # its switches by the door
            (31.5, inside, toward(inside, wc_sw), up(inside, wc_sw), 16)]
    # (the shortest way round from each heading to the next)
    for i in range(1, len(keys)):
        t, p, yaw, pitch, lens = keys[i]
        prev = keys[i - 1][2]
        yaw = prev + (yaw - prev + math.pi) % (2 * math.pi) - math.pi
        keys[i] = (t, p, yaw, pitch, lens)
    fps = 12
    n = int(keys[-1][0] * fps) + 1
    cam = scene.camera
    for c in cam.constraints:
        cam.constraints.remove(c)
    cam.data.lens, cam.data.sensor_width = 20, 36
    cam.data.shift_x = cam.data.shift_y = 0
    cam.rotation_mode = "XYZ"
    ease = lambda u: u * u * (3 - 2 * u)
    for f in range(n):
        t = f / fps
        i = max(j for j in range(len(keys)) if keys[j][0] <= t + 1e-9)
        k0, k1 = keys[i], keys[min(i + 1, len(keys) - 1)]
        u = ease((t - k0[0]) / (k1[0] - k0[0])) if k1[0] > k0[0] else 0.0
        p = k0[1].lerp(k1[1], u)
        cam.location = (p.x, p.y, start.z)
        yaw = k0[2] + (k1[2] - k0[2]) * u
        pitch = k0[3] + (k1[3] - k0[3]) * u
        cam.data.lens = k0[4] + (k1[4] - k0[4]) * u
        cam.data.keyframe_insert("lens", frame=f + 1)
        cam.rotation_euler = (math.pi / 2 + pitch, 0, yaw - math.pi / 2)
        cam.keyframe_insert("location", frame=f + 1)
        cam.keyframe_insert("rotation_euler", frame=f + 1)
    scene.render.fps = fps
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import walk    # (tools/blender/walk.py: resumes where a stopped night left off)
    walk.output(scene, os.environ["WALK"], n)


def setup_render():
    if os.environ.get("EXPORT_DAE"):
        # (tools/export_sketchup.py: the scene is built; save it, render nothing)
        export_dae(os.environ["EXPORT_DAE"], bool(os.environ.get("EXPORT_LIGHT")), bool(os.environ.get("EXPORT_SHELL")))
        sys.exit(0)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    for vt in ("AgX", "Filmic"):
        try:
            scene.view_settings.view_transform = vt
            break
        except TypeError:
            continue
    if os.environ.get("PANO"):
        pano_camera()
    if os.environ.get("WALK"):
        walk_camera()
        sys.exit(0)


SETUP_OBJECTS = ("Camera Target", "Vanity Camera", "Ceiling Light", "Fill Light")


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Towels: draped with Blender's cloth simulation at the model's TOWEL_ markers
# ---------------------------------------------------------------------------
INCH = 0.0254
def towel_material(hexcol):
    """Plain terry in one solid colour (D2), the towel item's."""
    name = "Vanity towel %s" % hexcol.upper()
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], hex_linear(hexcol) + (1.0,))
    set_input(bsdf, ["Roughness"], 1.0)
    set_input(bsdf, ["Sheen Weight", "Sheen"], 0.5)
    # the terry's sheen in its own colour: a white one washes a rust or navy
    # towel out to coral or slate
    if "Sheen Tint" in bsdf.inputs and bsdf.inputs["Sheen Tint"].type == "RGBA":
        bsdf.inputs["Sheen Tint"].default_value = hex_linear(hexcol) + (1.0,)
    # the terry loops: a fine bump
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 900.0
    nz.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.001
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def towel_markers(objs):
    """[(kind, centre, facing)] for each TOWEL_ marker, facing the room."""
    import mathutils
    dirs = {"XP": (1, 0, 0), "XN": (-1, 0, 0), "YP": (0, 1, 0), "YN": (0, -1, 0)}
    found = {}
    for o in objs:
        if o.type != "MESH":
            continue
        p, tag = o, None
        while p is not None and tag is None:
            if "TOWEL_" in p.name.upper():
                tag = p.name.upper()[p.name.upper().index("TOWEL_"):]
            p = p.parent
        if not tag:
            continue
        lo, hi = world_bbox([o])
        c = (lo + hi) / 2
        kind = ("HAND" if "HAND" in tag else "BARBATH" if "BARBATH" in tag else "BARMAT" if "BARMAT" in tag
                else "BAR" if "BAR" in tag else "BATH")
        face = next(v for k, v in dirs.items() if ("_" + k) in tag)
        key = (kind, round(c.x, 3), round(c.y, 3), round(c.z, 3))
        found[key] = (kind, c, mathutils.Vector(face))
    return list(found.values())


def drape_towel(kind, c, n, scheme, seed):
    """Build one towel's grid, pin it, and let it fall; returns the object."""
    import bmesh, mathutils, random
    rnd = random.Random(seed)
    up = mathutils.Vector((0, 0, 1))
    t = up.cross(n).normalized()                      # along the wall
    pts, pins = [], []
    if kind == "HAND":
        # pulled through the ring and folded over its bottom: a front and a
        # back layer joined over the top, gathered into pleats where the
        # ring holds it (about 4 1/2" across) and fanning out below it to
        # the towel's full width
        # a standard 16" x 28" hand towel, gathered to about 4 1/2" to pass
        # through the ring
        W, L, R = 16 * INCH, 28 * INCH, 0.45 * INCH
        H = (L - math.pi * R) / 2
        nu, nv = 28, 54
        top = c + up * R
        gmin, gmax = 0.28, 0.62            # gathered at the ring, still in folds below
        for i in range(nu + 1):
            u = -W / 2 + W * i / nu
            for j in range(nv + 1):
                s_ = L * j / nv
                if s_ < H:
                    off, z = R, -(H - s_)
                elif s_ < H + math.pi * R:
                    a = (s_ - H) / R
                    off, z = R * math.cos(a), R * math.sin(a)
                else:
                    off, z = -R, -(s_ - H - math.pi * R)
                below = max(0.0, -z)                          # how far down from the fold
                k = min(1.0, below / H)
                g = gmin + (gmax - gmin) * math.sqrt(k)           # widening gently, not flaring
                # the width the gathering takes up goes into soft vertical folds
                pleat = (1 - g) * 0.75 * INCH * math.sin(2 * math.pi * u / (2.2 * INCH))
                side = 1 if off >= 0 else -1
                off += side * pleat + rnd.uniform(-1, 1) * 0.0015
                pts.append(top + t * (u * g) + n * off + up * z)
                pins.append(H - 0.01 <= s_ <= H + math.pi * R + 0.01)
    elif kind.startswith("BAR"):
        # a hand towel on a towel bar: folded in half lengthwise (8" wide)
        # and hung over the bar by its middle, the two halves falling
        # front and back, a little fuller at the hem
        # (2026-10-23, props.py: BARBATH a 27" x 52" bath towel folded in
        # thirds lengthwise, 9" wide; BARMAT a 20" x 30" bath mat)
        W, L, R = {"BAR": (8, 28, 0.55), "BARBATH": (9, 52, 0.6), "BARMAT": (19, 30, 0.75)}[kind]
        W, L, R = W * INCH, L * INCH, R * INCH
        H = (L - math.pi * R) / 2
        nu, nv = 14, 50
        top = c + up * R
        for i in range(nu + 1):
            u = -W / 2 + W * i / nu
            for j in range(nv + 1):
                s_ = L * j / nv
                if s_ < H:
                    off, z = -R, -(H - s_)
                elif s_ < H + math.pi * R:
                    a = math.pi - (s_ - H) / R
                    off, z = R * math.cos(a), R * math.sin(a)
                else:
                    off, z = R, -(s_ - H - math.pi * R)
                off += (0.004 if off > 0 else -0.004) * min(1.0, max(0.0, -z) / 0.25) + rnd.uniform(-1, 1) * 0.0012
                pts.append(top + t * u + n * off + up * z)
                pins.append(H - 0.01 <= s_ <= H + math.pi * R + 0.01)
    else:
        # a full bath towel, 27" x 52", put over the hook by the middle of its
        # long edge: a short flap of that edge falls behind the hook, the
        # rest hangs in front, and the two halves fall away either side
        W, L, R, F = 52 * INCH, 27 * INCH, 0.5 * INCH, 4 * INCH
        nu, nv = 48, 34
        # (the marker is just short of the hook's tip: the towel goes up and
        # over the tip, its fold resting on the ball, so the hook is hidden
        # and doesn't poke through; the client's call, 2026-10-11)
        R = 0.6 * INCH
        c = c + n * (0.35 * INCH) + up * (1.3 * INCH)
        top = c + up * R
        for i in range(nu + 1):
            u = -W / 2 + W * i / nu
            for j in range(nv + 1):
                s_ = L * j / nv                               # from the long edge
                if s_ < F:                                    # the flap, behind the hook
                    off, z = -R, -(F - s_)
                elif s_ < F + math.pi * R:                    # over the hook
                    a = math.pi - (s_ - F) / R
                    off, z = R * math.cos(a), R * math.sin(a)
                else:                                         # hanging in front
                    off, z = R, -(s_ - F - math.pi * R)
                off += 0.012 * math.cos(math.pi * u / W) * min(1.0, max(0.0, -z) / 0.2) + rnd.uniform(-1, 1) * 0.002
                pts.append(top + t * u + n * off + up * z)
                pins.append(F - 0.01 <= s_ <= F + math.pi * R + 0.01 and abs(u) < 2.0 * INCH)
    me = bpy.data.meshes.new("Towel")
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    uvl = bm.loops.layers.uv.new()
    for i in range(nu):
        for j in range(nv):
            k = i * (nv + 1) + j
            f = bm.faces.new((vs[k], vs[k + nv + 1], vs[k + nv + 2], vs[k + 1]))
            for lp, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = (a / nu, b / nv)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Towel", me)
    bpy.context.scene.collection.objects.link(ob)
    vg = ob.vertex_groups.new(name="pin")
    vg.add([k for k, p in enumerate(pins) if p], 1.0, "REPLACE")
    # something to fall against: the wall
    wall = bpy.data.objects.new("Towel wall", bpy.data.meshes.new("Towel wall"))
    wall_c = c - n * {"HAND": 2.5, "BATH": 3.75}.get(kind, 2.4) * INCH   # (a bath towel's c is already 0.35" out)
    corners = [wall_c + t * a + up * b for a, b in ((-0.5, -1.2), (0.5, -1.2), (0.5, 0.3), (-0.5, 0.3))]
    wall.data.from_pydata(corners, [], [(0, 1, 2, 3)])
    bpy.context.scene.collection.objects.link(wall)
    wall.modifiers.new("Collision", "COLLISION")
    wall.hide_render = True
    cl = ob.modifiers.new("Cloth", "CLOTH")
    st = cl.settings
    st.quality = 6
    st.mass = 0.35
    st.tension_stiffness = st.compression_stiffness = 25
    st.shear_stiffness = 12
    st.bending_stiffness = 2.5          # thick terry doesn't crumple like sheeting
    st.air_damping = 4.0              # settle rather than swing
    st.vertex_group_mass = "pin"
    cc = cl.collision_settings
    cc.distance_min = 0.004
    cc.use_self_collision = True
    cc.self_distance_min = 0.003
    cl.point_cache.frame_start, cl.point_cache.frame_end = 1, 110
    return ob, wall


_SPRIGS = {}


def _append_objects(blend, names):
    """Append the named objects from a .blend file (not linked to a scene)."""
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    objs = [o for o in dst.objects if o is not None]
    for o in objs:
        o["asset"] = blend      # (assets.TAG: copies keep it; export_dae()'s light version leaves them out)
    return objs


def _sprig_image(hexes):
    """The periwinkle texture with its pink flowers recoloured: the big
    flower in the first colour and the small one in the second (keeping
    each petal's shading), and the yellowed leaves turned green."""
    import numpy as np
    key = "sprig_" + "_".join(h.strip("#") for h in hexes)
    if key in bpy.data.images:
        return bpy.data.images[key]
    src = bpy.data.images.load(os.path.join(MODELS, "periwinkle_plant", "textures", "periwinkle_plant_diff_1k.jpg"),
                               check_existing=True)
    w, h = src.size
    a = np.array(src.pixels[:], dtype=np.float32).reshape(h, w, 4)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # pink: red and blue both well above green; feathered at the edges
    pink = np.clip((np.minimum(r - g, b - g) - 0.04) / 0.12, 0, 1)
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    ref = float((lum * pink).sum() / max(pink.sum(), 1.0))
    rows = np.arange(h)[:, None] / h       # bottom-up, as Blender stores them
    cols = np.arange(w)[None, :] / w
    small = (cols > 0.78) & (rows < 0.42)  # the small flower, lower right
    for i, hx in enumerate(hexes[:2]):
        t = np.array(hex_linear(hx)) ** (1 / 2.2)
        zone = small if i == 1 else ~small
        k = (pink * zone)[..., None]
        shade = np.clip(lum / ref, 0.55, 1.25)[..., None]
        a[..., :3] = a[..., :3] * (1 - k) + np.clip(t * shade, 0, 1) * k
    # yellowed leaves (red above green above blue, little blue) to leaf green
    yel = np.clip(((r - b) - 0.35) / 0.15, 0, 1) * np.clip((g - 0.3) / 0.1, 0, 1) * (1 - pink)
    leaf = np.array([0.30, 0.42, 0.14])
    a[..., :3] = a[..., :3] * (1 - yel[..., None]) + leaf * (lum / 0.45)[..., None].clip(0.5, 1.3) * yel[..., None]
    img = bpy.data.images.new(key, w, h, alpha=False)
    img.colorspace_settings.name = src.colorspace_settings.name
    img.pixels.foreach_set(a.ravel())
    img.pack()
    return img


def _sprig_material(hexes):
    name = "Sprig " + " ".join(hexes)
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = _sprig_image(hexes)
    alpha = nt.nodes.new("ShaderNodeTexImage")
    alpha.image = bpy.data.images.load(os.path.join(MODELS, "periwinkle_plant", "textures", "periwinkle_plant_opacity_1k.png"),
                                       check_existing=True)
    alpha.image.colorspace_settings.name = "Non-Color"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(alpha.outputs["Color"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.55
    for k in ("Subsurface Weight", "Subsurface"):
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = 0.15
            break
    if hasattr(m, "blend_method"):
        m.blend_method = "HASHED"
    return m


def _vase_material(model, hx, roughness=0.3):
    name = "Vase %s %s %.2f" % (model, hx, roughness)
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(MODELS, model, "textures", model + "_diff_1k.jpg"), check_existing=True)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*hex_linear(hx), 1.0)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    # (a glossy glaze gets a clear coat; a matte art-pottery glaze doesn't)
    for k in ("Coat Weight", "Clearcoat"):
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = 0.4 if roughness < 0.5 else 0.0
            break
    return m


def _flower_heads(sprig):
    """A copy of a sprig with only its flowers (the faces textured from the
    two flowers in its atlas), to thicken a bouquet's blooms."""
    import bmesh
    key = sprig.name + " heads"
    if key in bpy.data.meshes:
        return bpy.data.meshes[key]
    me = sprig.data.copy()
    me.name = key
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active
    drop = []
    for f in bm.faces:
        u = sum(l[uv].uv.x for l in f.loops) / len(f.loops)
        v = sum(l[uv].uv.y for l in f.loops) / len(f.loops)
        big = 0.28 < u < 0.54 and 0.50 < v < 0.77
        small = 0.78 < u < 0.98 and 0.20 < v < 0.41
        if not (big or small):
            drop.append(f)
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    bm.to_mesh(me)
    bm.free()
    return me


def _stem(a, b, r=0.0018):
    """A plain green stem from a to b (metres), for the part of a sprig
    inside a clear vase."""
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=d.length, location=(a + b) / 2,
                                        rotation=d.to_track_quat("Z", "Y").to_euler())
    o = bpy.context.active_object
    o.name = "Sprig stem"
    m = bpy.data.materials.get("Sprig stem") or bpy.data.materials.new("Sprig stem")
    m.diffuse_color = (0.12, 0.22, 0.05, 1.0)
    if not m.use_nodes:
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.22, 0.05, 1.0)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
    o.data.materials.append(m)
    return o


def _bouquet(scheme, mouth, height, n, colours, seed, floor=None):
    """n periwinkle sprigs fanning out of a vase mouth: each scaled so it
    stands 'height' (metres) from a point a little inside the mouth, and
    leaning out, in a three-colour mix. With 'floor' (a clear vase's
    inside bottom), each sprig's stem carries on down to it, seen through
    the glass."""
    import random
    rnd = random.Random(seed)
    names = ["periwinkle_plant_0%d_LOD1" % i for i in range(1, 7)]
    if not _SPRIGS:
        # (appended once: a second load would come in renamed)
        loaded = _append_objects(os.path.join(MODELS, "periwinkle_plant", "periwinkle_plant_1k.blend"), names)
        _SPRIGS.update({n: o for n in names for o in loaded if o.name.split(".")[0] == n})
    src = _SPRIGS
    names = [n for n in names if n in src]
    pairs = [(colours[i % 3], colours[(i + 1) % 3]) for i in range(3)]
    out = []
    for k in range(n):
        base = src[names[k % len(names)]]
        o = base.copy()
        o.data = base.data.copy()
        o.data.materials.clear()
        o.data.materials.append(_sprig_material(pairs[k % 3]))
        h0 = max(base.dimensions.z, 1e-3)
        sc = height * rnd.uniform(0.85, 1.15) / h0
        o.scale = (sc, sc, sc)
        lean = 0.0 if k == 0 else rnd.uniform(0.25, 0.6)
        turn = k * 2.39996 + rnd.uniform(-0.3, 0.3)
        o.rotation_euler = (lean * math.cos(turn), lean * math.sin(turn), rnd.uniform(0, 2 * math.pi))
        o.location = (mouth.x, mouth.y, mouth.z - 0.25 * height)
        bpy.context.scene.collection.objects.link(o)
        out.append(o)
        if floor is not None:
            # down through the neck to the bottom, splaying a little
            top = Vector(o.location)
            foot = Vector((mouth.x + 0.004 * math.cos(turn), mouth.y + 0.004 * math.sin(turn), floor + 0.004))
            out.append(_stem(foot, top + Vector((0, 0, 0.01))))
        # and as many again of just the flowers, turned and leaning
        # differently, for a fuller head of blooms
        heads = _flower_heads(base)
        if len(heads.polygons):
            f = bpy.data.objects.new(o.name + " heads", heads.copy())
            f.data.materials.clear()
            f.data.materials.append(_sprig_material(pairs[(k + 1) % 3]))
            # (a little shorter and more upright than the sprigs, so no
            # flower floats out past the stems)
            f.scale = tuple(x * 0.85 for x in o.scale)
            lean2 = rnd.uniform(0.1, 0.35)
            turn2 = turn + 1.2 + rnd.uniform(-0.3, 0.3)
            f.rotation_euler = (lean2 * math.cos(turn2), lean2 * math.sin(turn2), rnd.uniform(0, 2 * math.pi))
            f.location = o.location
            bpy.context.scene.collection.objects.link(f)
            out.append(f)
    return out



def turn_whole_images(objs):
    """A print stretched once over its object (spec "whole") is laid across
    two world axes, XZ for the vanity wall's frames. A frame of the same spot
    on a wall facing the other way (layout D's frame on the WC wall) is flat
    in X: lay its picture across Y and Z instead, or it collapses to a line.
    And a picture seen from the other side of its axis (the tub-side peg
    shelf's frame faces the vanity, the vanity wall's frames face the tub)
    would read mirrored, its caption backwards: flip it to face the room
    (client, 2026-10-16)."""
    floor = [o for o in objs if o.type == "MESH" and o.name.split(".")[0] == "Floor"] or \
        [o for o in objs if o.type == "MESH" and "FLOOR" in o.name.upper()]
    centre = None
    if floor:
        flo, fhi = world_bbox(floor)
        centre = (flo + fhi) / 2
    for o in objs:
        if o.type != "MESH" or o.hide_render:
            continue
        lo, hi = world_bbox([o])
        flat_x = (hi.x - lo.x) <= 0.01 and (hi.y - lo.y) >= 0.05
        flat_y = (hi.y - lo.y) <= 0.01 and (hi.x - lo.x) >= 0.05
        if not (flat_x or flat_y):
            continue
        mid = (lo + hi) / 2
        # seen looking -y (the room on its +y side), or looking +x (the room
        # on its -x side), the picture's left is at +x (or +y): flip it
        flip = centre is not None and ((flat_y and centre.y > mid.y) or (flat_x and centre.x < mid.x))
        for sl in o.material_slots:
            m = sl.material
            if not (m and m.use_nodes):
                continue
            nt = m.node_tree
            for n in list(nt.nodes):
                if not (n.type == "SEPXYZ" and any(l.from_socket.name == "Generated" for l in n.inputs[0].links)):
                    continue
                for out in ("X", "Y"):
                    for l in list(n.outputs[out].links):
                        if l.to_node.type != "COMBXYZ" or l.to_socket.name != "X":
                            continue
                        src = n.outputs["Y"] if flat_x else n.outputs["X"]
                        if flip:
                            inv = nt.nodes.new("ShaderNodeMath")
                            inv.operation = "SUBTRACT"
                            inv.inputs[0].default_value = 1.0
                            nt.links.new(src, inv.inputs[1])
                            src = inv.outputs[0]
                        nt.links.new(src, l.to_socket)


def stage_scheme(objs, finish):
    """Hide what the scheme leaves out: the model parts of each spot it
    leaves empty (none), and of a spot with layers (a peg shelf's
    colour blocks or plate) the layer its item doesn't fill."""
    room, sch, picks, lib = load_scheme(finish)

    def hide(o):
        o.hide_render = True
        o.hide_viewport = True
    for spot, sd in room["spots"].items():
        prefix = sd.get("objects")
        if not prefix:
            continue
        items = spot_items(picks, lib, spot)
        if len(items) > 1:     # (several plates side by side in one frame)
            filled = set(spot_slots_multi(room, items, spot, images=False))
        elif items and items[0].get("render"):
            filled = set(spot_slots(room, items[0], spot, images=False))
        else:
            filled = set()
        for o in objs:
            if prefix not in o.name:
                continue
            if not filled:
                hide(o)
                continue
            for layer, slot in (sd.get("layers") or {}).items():
                if slot not in filled and prefix + layer in o.name:
                    hide(o)


def add_flowers(objs, finish):
    """D10: replace the model's simple vases of flowers with the Poly Haven
    ones: on the counter a round glazed jar and on the window sill a slim
    bottle, in the scheme's opaque glaze, each the size of the model's
    vase, filled with sprigs; and sprigs in the peg shelf's own bud vase."""
    if not FLOWERS or not os.path.isdir(MODELS):
        return
    scheme = scheme_name(finish)
    fl = scheme_flowers(finish=finish)
    glaze = fl["glaze"]
    colours = tuple(fl["colours"])

    def parts(prefix):
        return [o for o in objs if o.type == "MESH" and o.name.startswith(prefix)]

    seed = 7
    for where, model, n, glaze, rough in (
            ("Counter items_Vase of flowers", "ceramic_vase_02", 11, fl["glaze"], fl["roughness"]),
            ("Window_Vase of flowers", "ceramic_vase_01", 6, fl["window_glaze"], fl["window_roughness"]),
            # (the loft's WC, on the tank lid: client, 2026-10-23)
            ("WEST_WC_Vase of flowers", "ceramic_vase_01", 6, fl["window_glaze"], fl["window_roughness"])):
        vase = parts(where + "_Bud vase")
        if not vase:
            continue
        lo, hi = world_bbox(vase)
        for o in parts(where):
            o.hide_render = True
            o.hide_viewport = True
        src = _append_objects(os.path.join(MODELS, model, model + "_1k.blend"), [model])
        if not src:
            continue
        v = src[0]
        v.data = v.data.copy()
        v.data.materials.clear()
        v.data.materials.append(_vase_material(model, glaze, rough))
        bpy.context.scene.collection.objects.link(v)
        bpy.context.view_layer.update()
        vlo, vhi = world_bbox([v])
        h = hi.z - lo.z
        sc = h / max(vhi.z - vlo.z, 1e-4)
        v.scale = tuple(x * sc for x in v.scale)
        bpy.context.view_layer.update()
        vlo, vhi = world_bbox([v])
        c = (lo + hi) / 2
        v.location.x += c.x - (vlo.x + vhi.x) / 2
        v.location.y += c.y - (vlo.y + vhi.y) / 2
        v.location.z += lo.z - vlo.z
        objs.append(v)
        objs.extend(_bouquet(scheme, Vector((c.x, c.y, hi.z)), h * (1.25 if n > 8 else 1.15), n, colours, seed))
        seed += 1
    # the peg shelf: sprigs in its own bud vase, in place of the simple ones
    shelf = parts("Peg rail_Flowers_")
    if shelf:
        lo, hi = world_bbox(shelf)
        for o in shelf:
            o.hide_render = True
            o.hide_viewport = True
        c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        # (the glass vase they stand in: the shelf's bud vase nearest them)
        glass = parts("Peg rail_Bud vase")
        floor = None
        if glass:
            def mid(o):
                lo_, hi_ = world_bbox([o])
                return ((lo_ + hi_) / 2).xy
            near = [o for o in glass if (mid(o) - c.xy).length < 0.05]
            if near:
                floor = world_bbox(near)[0].z + 0.003
        objs.extend(_bouquet(scheme, c, 0.11, 5, colours, seed, floor))


def add_towels(objs, finish, cache=None, bath=True):
    """Hang a towel at every TOWEL_ marker (hand towels through the rings,
    bath towels on some of the hooks), draped by a short cloth simulation,
    then frozen, thickened and given the scheme's striped terry. The draped
    shapes are saved to `cache` (a JSON file beside the model), so the other
    views and finishes of the same model reuse them."""
    marks = towel_markers(objs)
    if not marks:
        return []
    scheme = scheme_name(finish)
    scene = bpy.context.scene
    shapes = None
    if cache and os.path.exists(cache):
        shapes = json.load(open(cache))
    if shapes is None:
        sims = [drape_towel(k, c, n, scheme, seed) for seed, (k, c, n) in enumerate(marks)]
        for f in range(1, 111):
            scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        shapes = []
        for ob, wall in sims:
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            shapes.append({"verts": [list(v.co) for v in me.vertices],
                           "faces": [list(p.vertices) for p in me.polygons],
                           "uvs": [list(d.uv) for d in me.uv_layers[0].data]})
            bpy.data.meshes.remove(me)
            bpy.data.objects.remove(ob)
            bpy.data.objects.remove(wall)
        scene.frame_set(1)
        if cache:
            json.dump(shapes, open(cache, "w"))
    towels = []
    # plain towels: the scheme's matched pair at the rings, and the bath
    # towels on the hooks in its colours, in turn
    kinds = [k for k, c, n in marks]
    tc = scheme_towels(finish=finish)
    colour = {}
    nb = 0
    for i, k in enumerate(kinds):
        if k in ("HAND", "BAR"):
            colour[i] = tc["hand"]
        else:
            colour[i] = tc["bath"][nb % len(tc["bath"])]
            nb += 1
    # the one bath towel the entry view keeps: on the hook at the bathroom
    # end of the shelves (least along x), smallest in the frame
    baths = [i for i, k in enumerate(kinds) if k == "BATH"]
    entry_hook = min(baths, key=lambda i: marks[i][1].x) if baths else None
    for ti, sh in enumerate(shapes):
        if bath == "entry" and kinds[ti] == "BATH" and ti != entry_hook:
            continue                                      # (left out of this view)
        if not bath and kinds[ti] == "BATH":
            continue
        mat = towel_material(colour[ti])
        me = bpy.data.meshes.new("Towel")
        me.from_pydata([tuple(v) for v in sh["verts"]], [], [tuple(f) for f in sh["faces"]])
        uvl = me.uv_layers.new()
        for d, uv in zip(uvl.data, sh["uvs"]):
            d.uv = uv
        tw = bpy.data.objects.new("Towel", me)
        scene.collection.objects.link(tw)
        tw.data.materials.append(mat)
        so = tw.modifiers.new("Thickness", "SOLIDIFY")
        so.thickness = 0.006
        so.offset = 0.0
        sd = tw.modifiers.new("Smooth", "SUBSURF")
        sd.levels = sd.render_levels = 1
        for p in tw.data.polygons:
            p.use_smooth = True
        towels.append(tw)
    return towels


def main(model_path=MODEL_PATH, render_path=RENDER_PATH, finish=FINISH, faucet=FAUCET, view=VIEW):
    print("Using the scheme:", apply_scheme(finish=finish))
    MATERIALS["finish"] = FINISHES[finish]
    MATERIALS["faucet"] = FAUCETS[faucet]
    MATERIALS["hardware"] = FAUCETS[faucet]
    if model_path:
        if CLEAR_SCENE:
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o)
        objs = import_model(model_path)
    else:
        objs = list(bpy.context.scene.objects)
    # re-running: drop the camera and lights made last time
    for name in SETUP_OBJECTS:
        o = bpy.data.objects.get(name)
        if o:
            if o in objs:
                objs.remove(o)
            bpy.data.objects.remove(o)
    fix_scale(objs)
    # the joints with faces in one place, listed before every render
    # (CHECK_JOINTS: list them and render nothing)
    for f in coincident_faces(objs):
        print("JOINT " + f, flush=True)
    for f in crowding(objs):
        print("CROWD " + f, flush=True)
    assign_materials(objs)
    smooth_round_parts(objs)
    add_bevels(objs)
    replace_toilet(objs)
    if os.environ.get("ENTRY_STOOL", "1") != "0":
        add_entry_stool(objs)
    apply_view(objs, view)
    if TOWELS:
        # (the entry view stands among the hallway hooks: only the bath
        # towel on the hook at the bathroom end, or they'd fill the foreground)
        add_towels(objs, finish, model_path and os.path.join(os.path.dirname(model_path), "towels-3.json"),
                   bath="entry" if view == "entry" else True)
    stage_scheme(objs, finish)
    turn_whole_images(objs)
    add_flowers(objs, finish)
    setup_camera_and_lights(objs, view)
    for f in crowding_in_view(objs):
        print("CROWD %s: %s" % (view, f), flush=True)
    # the walkway check, once the props are placed (CHECK_JOINTS: then stop)
    for f in clearances(objs):
        print("CLEAR " + f, flush=True)
    if os.environ.get("CHECK_JOINTS"):
        dump_sizes(objs)
        return
    # (repainted after the camera is placed: the framing finds the vanity,
    # mirrors included, by its finish)
    if "mirrorframe" in MATERIALS:
        mf = build_material("mirrorframe", MATERIALS["mirrorframe"], None)
        for o in objs:
            if o.type == "MESH" and ("_Mirror_" in o.name or "_Medicine cabinet_" in o.name) and "Glass" not in o.name:
                for slot in o.material_slots:
                    slot.material = mf
    setup_render()
    if render_path:
        if render_path.lower().endswith((".jpg", ".jpeg")):
            bpy.context.scene.render.image_settings.file_format = "JPEG"
            bpy.context.scene.render.image_settings.quality = 90
        bpy.context.scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)
        print("Rendered", render_path)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"model_path": MODEL_PATH, "render_path": RENDER_PATH, "finish": FINISH, "faucet": FAUCET,
            "view": VIEW}
    i = 0
    while i < len(argv):
        if argv[i] == "--model":
            opts["model_path"] = argv[i + 1]
        elif argv[i] == "--render":
            opts["render_path"] = argv[i + 1]
        elif argv[i] == "--finish":
            opts["finish"] = argv[i + 1]
        elif argv[i] == "--faucet":
            opts["faucet"] = argv[i + 1]
        elif argv[i] == "--view":
            opts["view"] = argv[i + 1]
        i += 2
    return opts


if __name__ == "__main__":
    main(**parse_args())

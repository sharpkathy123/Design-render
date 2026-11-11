"""A room's short walk-through (client, 2026-11-06: "I'm getting antsy to see
them"): the camera glides from one of the room's own composed views to the
next, pausing at each, at eye height, 12 pictures a second, 960 x 540,
WALK_SAMPLES (default 12), one fixed noise pattern so the grain doesn't
crawl. tools/build_walk.py fills in the pictures between and makes the video.

Any room model with views can use it (the kitchen, the mud room, the loft):
build the room, set up its first view's camera and lights as for a still,
then call render(stops, folder) with each stop's eye and target in Blender's
world (meters) and its lens. ROOM_WALK=<folder> in the environment turns a
model's run into a walk; ROOM_WALK_CHECK=1 only lists where the path would
pass through something solid (WALK_THROUGH lines), renders nothing. A walk
resumes: pictures already in the folder are skipped (output()). The
second floor bath's own walk (WALK=, vanity_render_setup.walk_camera) is
older and goes fixture by fixture.

    ROOM_WALK=/tmp/walks/kitchen-A3-1106 python3.11 tools/blender/kitchen.py --layout A3 --views dining,nook,sink,range,fridge,east
    python3 tools/build_walk.py /tmp/walks/kitchen-A3-1106 site/video/kitchen-walk.mp4
"""
import math
import os

import bpy
from mathutils import Vector

FPS = 12
EYE = 62 * 0.0254            # the walk's eye height, a standing person's


def _yaw_pitch(eye, target):
    d = target - eye
    return math.atan2(d.y, d.x), math.atan2(d.z, math.hypot(d.x, d.y))


def keys(stops, hold=1.0, move=2.2):
    """(time, eye, yaw, pitch, lens) for each stop's arrival and departure."""
    out, t = [], 0.0
    for i, (eye, target, lens) in enumerate(stops):
        e = Vector((eye.x, eye.y, EYE))
        yaw, pitch = _yaw_pitch(e, target)
        pitch *= 0.6                                  # (a person glances down less than a still's framing)
        lens = min(max(lens, 18.0), 24.0)
        if i:
            t += move
        out.append((t, e, yaw, pitch, lens))
        t += hold
        out.append((t, e, yaw, pitch, lens))
    for i in range(1, len(out)):                      # the shortest way round from each heading to the next
        prev = out[i - 1][2]
        tt, e, yaw, pitch, lens = out[i]
        out[i] = (tt, e, prev + (yaw - prev + math.pi) % (2 * math.pi) - math.pi, pitch, lens)
    return out


def through(stops, objs=()):
    """Where the straight path between stops passes through something solid at eye height (a ray cast on
    the evaluated scene, so a wall's door or opening counts as open)."""
    ks = keys(stops)
    dg = bpy.context.evaluated_depsgraph_get()
    found = []
    for k0, k1 in zip(ks, ks[1:]):
        a, b = k0[1], k1[1]
        d = b - a
        if d.length < 1e-4:
            continue
        hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg, a, d.normalized(), distance=d.length)
        if hit:
            found.append("%s at %.2f, %.2f (between %.1fs and %.1fs)" % (ob.name, loc.x, loc.y, k0[0], k1[0]))
    return found


def render(stops, folder, objs=()):
    if os.environ.get("ROOM_WALK_CHECK"):
        for f in through(stops, objs):
            print("WALK_THROUGH " + f, flush=True)
        print("WALK seconds %.1f" % keys(stops)[-1][0], flush=True)
        return
    scene = bpy.context.scene
    cam = scene.camera
    for c in list(cam.constraints):
        cam.constraints.remove(c)
    cam.data.sensor_width = 36
    cam.data.shift_x = cam.data.shift_y = 0
    cam.rotation_mode = "XYZ"
    ks = keys(stops)
    n = int(ks[-1][0] * FPS) + 1
    ease = lambda u: u * u * (3 - 2 * u)
    for f in range(n):
        t = f / FPS
        i = max(j for j in range(len(ks)) if ks[j][0] <= t + 1e-9)
        k0, k1 = ks[i], ks[min(i + 1, len(ks) - 1)]
        u = ease((t - k0[0]) / (k1[0] - k0[0])) if k1[0] > k0[0] else 0.0
        cam.location = k0[1].lerp(k1[1], u)
        yaw = k0[2] + (k1[2] - k0[2]) * u
        pitch = k0[3] + (k1[3] - k0[3]) * u
        cam.data.lens = k0[4] + (k1[4] - k0[4]) * u
        cam.data.keyframe_insert("lens", frame=f + 1)
        cam.rotation_euler = (math.pi / 2 + pitch, 0, yaw - math.pi / 2)
        cam.keyframe_insert("location", frame=f + 1)
        cam.keyframe_insert("rotation_euler", frame=f + 1)
    scene.render.fps = FPS
    output(scene, folder, n)


def _whole_png(path):
    """A frame cut off by a stopped render has no PNG end marker (or no bytes)."""
    try:
        with open(path, "rb") as f:
            f.seek(-12, 2)
            return f.read()[4:8] == b"IEND"
    except OSError:
        return False


def output(scene, folder, n):
    """Render frames 1..n (or WALK_FRAMES="a-b") into <folder>/walk_####.png, resuming (2026-11-06): a
    frame already in the folder is skipped, so a walk stopped by the night's time limit carries on the
    next night from where it stopped (the render queue keeps the folder in GitHub's Actions cache); a frame
    cut off mid-write is deleted and made again. The scene is kept between frames (only the camera moves),
    which saves its few seconds of rebuilding each picture. Shared with the second floor's walk_camera()."""
    os.makedirs(folder, exist_ok=True)
    have = 0
    for nm in sorted(os.listdir(folder)):
        if nm.startswith("walk_") and nm.endswith(".png"):
            if _whole_png(os.path.join(folder, nm)):
                have += 1
            else:
                os.remove(os.path.join(folder, nm))
    first, last = 1, n
    if os.environ.get("WALK_FRAMES"):
        first, last = map(int, os.environ["WALK_FRAMES"].split("-"))
    scene.frame_start, scene.frame_end = first, last
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    scene.render.resolution_percentage = 100
    scene.cycles.samples = int(os.environ.get("WALK_SAMPLES", "12"))
    scene.cycles.seed = 0
    scene.cycles.use_animated_seed = False
    scene.render.use_persistent_data = True
    scene.render.use_overwrite = False
    scene.render.use_placeholder = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(folder, "walk_####")
    print("WALK frames", n, "already made", have, flush=True)
    bpy.ops.render.render(animation=True)

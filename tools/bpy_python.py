"""Run under the Python that has Blender's module (bpy).

Blender's Python module is installed for one Python only (here
/usr/bin/python3.11; on the render workflow, its `python`), and a render
started with plain `python3` used to fail half-way, after the model was
built (2026-11-04). Every script that renders, or starts a render, calls
ensure() first: when this Python can't import bpy, it starts itself again
under one that can (BPY_PYTHON if set, else /usr/bin/python3.11 or
python3.11 on the path), with the same arguments; failing that it stops
at once with a plain message."""
import importlib.util
import os
import shutil
import sys


def ensure():
    if importlib.util.find_spec("bpy"):
        return
    if os.environ.get("BPY_REEXEC") or not sys.argv or sys.argv[0] in ("-c", ""):
        sys.exit("This Python (%s) has no Blender module (bpy): run it with /usr/bin/python3.11." % sys.executable)
    here = os.path.realpath(sys.executable)
    for alt in (os.environ.get("BPY_PYTHON"), "/usr/bin/python3.11", shutil.which("python3.11")):
        if alt and os.path.exists(alt) and os.path.realpath(alt) != here:
            sys.stderr.write("(no bpy in %s: running under %s instead)\n" % (sys.executable, alt))
            os.environ["BPY_REEXEC"] = "1"
            os.execv(alt, [alt] + sys.argv)
    sys.exit("No Python here has Blender's module (bpy): install it (pip install bpy) for Python 3.11.")

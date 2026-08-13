import math
import os
import re
import numpy as np
from PIL import Image

R_OHM = 2200.0
C_FARAD = 4.7e-9
SAMPLE_RATE = 32000.0
OVERSAMPLE = 24
SIZE = 700
GAIN = 0.45


def load_path(source_file):
    src = open(source_file).read()
    src = re.sub(r"^import (board|audiocore|audiopwmio|array)\n", "", src, flags=re.M)
    src = re.sub(r"^a$", "", src, flags=re.M)
    src = src.split("frame = array")[0]
    namespace = {}
    exec(src, namespace)
    return namespace["path"]


def rc_filter(path):
    tau = (R_OHM * C_FARAD)
    dt = (1.0 / (SAMPLE_RATE * OVERSAMPLE))
    alpha = (1.0 - math.exp((-dt / tau)))
    held = np.repeat(np.array(path, dtype=float), OVERSAMPLE, axis=0)
    out = np.empty_like(held)
    state = held[0].copy()
    for i in range(len(held)):
        state = (state + ((held[i] - state) * alpha))
        out[i] = state
    return out


def render(points, out_file):
    canvas = np.zeros((SIZE, SIZE), dtype=float)
    px = (((points[:, 0] * GAIN) + 0.5) * (SIZE - 1))
    py = (((-points[:, 1] * GAIN) + 0.5) * (SIZE - 1))
    ix = np.clip(px.astype(int), 0, (SIZE - 1))
    iy = np.clip(py.astype(int), 0, (SIZE - 1))
    np.add.at(canvas, (iy, ix), 1.0)
    canvas = (canvas / max(canvas.max(), 1.0))
    canvas = np.power(canvas, 0.35)
    rgb = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    rgb[:, :, 1] = (canvas * 255).astype(np.uint8)
    rgb[:, :, 0] = (canvas * 90).astype(np.uint8)
    rgb[:, :, 2] = (canvas * 120).astype(np.uint8)
    Image.fromarray(rgb).save(out_file)
    return canvas


HERE = os.path.dirname(os.path.abspath(__file__))
path = load_path(os.path.join(HERE, "cat_xy.py"))
filtered = rc_filter(path)
render(filtered, "sim_filtered.png")
arr = np.array(path, dtype=float)
seg = [np.linspace(arr[i], arr[(i + 1) % len(arr)], OVERSAMPLE, endpoint=False) for i in range(len(arr))]
render(np.concatenate(seg), "sim_ideal.png")
print("points:", len(path), "| simulated samples:", len(filtered))
print("frame rate:", round((SAMPLE_RATE / len(path)), 1), "Hz")

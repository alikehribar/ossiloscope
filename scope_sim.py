import math
import os
import re
import sys
import numpy as np
from PIL import Image

R_OHM = 2200.0
C_FARAD = 4.7e-9
OVERSAMPLE = 24
SIZE = 700
VOLT_FULL = 3.3


def load_frame(source_file):
    # Run the firmware up to the point where it hands the buffer to the DMA.
    # Reading `frame` rather than `path` means the two firmware files arrive
    # here in the same unit: 0-65535 duty, which is 0-3.3 V on the pin.
    # Their `path` variables do not agree (-1..1 in one, 0..255 in the other).
    src = open(source_file).read()
    src = re.sub(r"^import (board|audiocore|audiopwmio|analogio|usb_cdc)\n", "", src, flags=re.M)
    src = src.split("sample = audiocore")[0]
    namespace = {}
    exec(src, namespace)
    pairs = np.frombuffer(namespace["frame"], dtype="<u2").reshape(-1, 2)
    return ((pairs / 65535.0) * 3.3), namespace["SAMPLE_RATE"]


def rc_filter(path, sample_rate):
    tau = (R_OHM * C_FARAD)
    dt = (1.0 / (sample_rate * OVERSAMPLE))
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
    # The full 0-3.3 V rail maps to the canvas, so a drawing that uses only
    # part of the rail looks small here, exactly as it does on the screen.
    px = ((points[:, 0] / VOLT_FULL) * (SIZE - 1))
    py = ((1.0 - (points[:, 1] / VOLT_FULL)) * (SIZE - 1))
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
source = (sys.argv[1] if (len(sys.argv) > 1) else os.path.join(HERE, "cat_outline_livescope_fw.py"))
stem = os.path.splitext(os.path.basename(source))[0]
path, sample_rate = load_frame(source)
filtered = rc_filter(path, sample_rate)
render(filtered, ("sim_%s_filtered.png" % stem))
seg = [np.linspace(path[i], path[((i + 1) % len(path))], OVERSAMPLE, endpoint=False) for i in range(len(path))]
render(np.concatenate(seg), ("sim_%s_ideal.png" % stem))

tau = (R_OHM * C_FARAD)
dwell = (1.0 / sample_rate)
print("%s | points: %d | sample rate: %d Hz" % (stem, len(path), sample_rate))
print("frame rate: %.1f Hz" % (sample_rate / len(path)))
# Reported the way REPORT.md sections 4 and 6 do it: the dwell measured in time
# constants, and how far through the step the filter gets in that time.
print("RC time constant: %.2f us" % (tau * 1e6))
print("time per point: %.3f us = %.3f tau | settles to %.1f %%" % (
    (dwell * 1e6), (dwell / tau), (100.0 * (1.0 - math.exp((-dwell / tau))))))

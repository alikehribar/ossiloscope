"""Compare the outline the board was told to draw with the one it read back."""

import ast
import sys

import numpy as np

import livescope

CAPTURE = (sys.argv[2] if (len(sys.argv) > 2) else "live_capture.npy")
# Which firmware drew the capture. Any file with an X_POINTS/Y_POINTS table.
FIRMWARE = (sys.argv[1] if (len(sys.argv) > 1) else "cat_outline.py")


def firmware_shape():
    # cat_outline.py imports board and audiocore, so it cannot be imported on
    # the Mac. Parse the file instead and read only the two literal tuples,
    # which keeps the point list in exactly one place.
    tree = ast.parse(open(FIRMWARE).read())
    named = {t.id: n.value for n in tree.body if isinstance(n, ast.Assign)
             for t in n.targets if isinstance(t, ast.Name)}
    xs = ast.literal_eval(named["X_POINTS"])
    ys = ast.literal_eval(named["Y_POINTS"])
    return list(zip(xs, ys))


def measured_pass():
    # find_period locates one full lap of the drawing inside the burst;
    # median_filter removes single-sample ADC spikes. Both come from the
    # live viewer, so this is exactly what livescope.py puts on screen.
    samples = np.load(CAPTURE)
    period = livescope.find_period(samples)
    volts = ((samples[:period] / 65535.0) * 3.3)
    return livescope.median_filter(volts, 7)


def expected_volts():
    # The corner list closed into a loop and put on the same 0-3.3 V scale
    # the firmware writes, so the two traces can be laid over each other.
    corners = firmware_shape()
    loop = np.array((list(corners) + [corners[0]]), dtype=float)
    # Fill each straight segment with points so that distance to "the line"
    # is measured against the whole line and not only against its ends.
    steps = np.linspace(0.0, 1.0, 40, endpoint=False)[:, None]
    dense = (loop[:-1][None, :, :] + (steps[:, :, None] * np.diff(loop, axis=0)[None]))
    # dense is (step, segment, xy). Transposing puts the fill points back in
    # walking order, segment by segment, so the result can also be drawn.
    return ((dense.transpose(1, 0, 2).reshape(-1, 2) / 255.0) * 3.3)


def nearest_distance(trace, target):
    # For every measured point, the distance to the closest point on the
    # intended outline. This asks "is the dot on the line?" and ignores how
    # far along the line it happens to be.
    gaps = (trace[:, None, :] - target[None, :, :])
    return np.sqrt((gaps ** 2).sum(axis=2)).min(axis=1)


def draw(trace, want, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    panels = (("Sent to the PWM pins", want, "#e8e0c8"),
              ("Read back through the ADC", trace, "#39ff5a"))
    # A wide, short drawing wastes most of a side by side figure, so the two
    # panels are stacked instead once the word is wider than it is tall.
    span = (want.max(axis=0) - want.min(axis=0))
    wide = (span[0] > (2.0 * span[1]))
    grid, size = ((2, 1), (9, 5.4)) if wide else ((1, 2), (10, 5.4))
    fig, axes = plt.subplots(grid[0], grid[1], figsize=size, facecolor="black")
    for (ax, (title, points, colour)) in zip(axes, panels):
        ax.set_facecolor("black")
        ax.plot(points[:, 0], points[:, 1], "-", color=colour, linewidth=1.0)
        ax.set_title(title, color="#e8e0c8")
        ax.set_xlabel("X  GP2  (V)", color="#39ff5a")
        ax.set_ylabel("Y  GP3  (V)", color="#39ff5a")
        ax.tick_params(colors="#39ff5a")
        ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=110, facecolor="black")
    print("wrote", path)


if __name__ == "__main__":
    trace = measured_pass()
    want = expected_volts()
    gap = nearest_distance(trace, want)
    print("pass length:", len(trace), "pairs")
    for (name, col) in (("X", 0), ("Y", 1)):
        print(name, "expected min/max: %.3f %.3f" % (want[:, col].min(), want[:, col].max()),
              "| measured min/max: %.3f %.3f" % (trace[:, col].min(), trace[:, col].max()))
    print("off-path distance mean/median/max (mV): %.1f %.1f %.1f"
          % ((gap.mean() * 1000), (np.median(gap) * 1000), (gap.max() * 1000)))
    draw(trace, want, (FIRMWARE.replace(".py", "") + "_compare.png"))

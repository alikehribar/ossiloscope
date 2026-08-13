import glob
import fcntl
import os
import select
import numpy as np

MAGIC = b"\xab\xcd\xef\x01"
BURST = 2048
PAYLOAD = (BURST * 4)


def find_port():
    # macOS names the port after the USB address the board landed on, so it
    # changes whenever you replug or use a different socket. Never hardcode it.
    ports = sorted(glob.glob("/dev/cu.usbmodem*"))
    if (not ports):
        raise SystemExit("no board found - is the Pico plugged in?")
    return ports[0]


def find_period(samples, low=150, high=1600):
    # One burst covers several passes of the drawing, and they start at
    # different points, so overlaying them makes false spikes at corners.
    # Autocorrelation finds the lag where the trace best matches itself,
    # which is the length of exactly one pass.
    signal = (samples[:, 0] - samples[:, 0].mean())
    spectrum = np.fft.rfft(signal, (2 * len(signal)))
    correlation = np.fft.irfft((spectrum * np.conj(spectrum)))[:len(signal)]
    limit = min(high, (len(signal) - 1))
    if (limit <= low):
        return len(samples)
    return (low + int(np.argmax(correlation[low:limit])))


def median_filter(samples, width):
    # Removes single-sample ADC spikes. A median keeps corners sharp, where a
    # moving average would round them off. Wrap mode because the path is a loop.
    pad = (width // 2)
    extended = np.pad(samples, ((pad, pad), (0, 0)), mode="wrap")
    stack = np.stack([extended[i:(i + len(samples))] for i in range(width)], axis=0)
    return np.median(stack, axis=0)


def read_frame(fd, state):
    while True:
        idx = state["buf"].find(MAGIC)
        if ((idx >= 0) and (len(state["buf"]) >= (idx + 4 + PAYLOAD))):
            chunk = state["buf"][(idx + 4):(idx + 4 + PAYLOAD)]
            state["buf"] = state["buf"][(idx + 4 + PAYLOAD):]
            return np.frombuffer(chunk, dtype="<u2").reshape(-1, 2)
        if select.select([fd], [], [], 2.0)[0]:
            try:
                state["buf"] += os.read(fd, 262144)
            except OSError as error:
                raise SystemExit("Pico disconnected; reconnect it and run again.") from error
        else:
            return None


def live():
    lock = open("/tmp/livescope.lock", "w")
    try:
        fcntl.flock(lock, (fcntl.LOCK_EX | fcntl.LOCK_NB))
    except BlockingIOError:
        raise SystemExit("livescope.py is already running; close the old window first.")
    import matplotlib
    matplotlib.use("MacOSX")
    import matplotlib.pyplot as plt
    fd = os.open(find_port(), (os.O_RDWR | os.O_NONBLOCK))
    state = {"buf": b""}
    plt.ion()
    fig, ax = plt.subplots(figsize=(7.5, 7.5), facecolor="black")
    ax.set_facecolor("black")
    ax.set_aspect("auto")
    ax.set_xlabel("X  GP2  (V)", color="#39ff5a")
    ax.set_ylabel("Y  GP3  (V)", color="#39ff5a")
    ax.tick_params(colors="#39ff5a")
    trace, = ax.plot([], [], "-", color="#39ff5a", linewidth=1.3, alpha=0.95)
    plt.show(block=False)
    plt.pause(0.05)
    read_frame(fd, state)
    while plt.fignum_exists(fig.number):
        frame = read_frame(fd, state)
        if frame is None:
            continue
        one_pass = frame[:find_period(frame)]
        volts = median_filter(((one_pass / 65535.0) * 3.3), 7)
        trace.set_data(volts[:, 0], volts[:, 1])
        # Scale each axis to its own signal, the way a scope's separate
        # V/div knobs do. A shared 0-3.3 V axis squashes wide, short
        # drawings into a sliver where noise dominates.
        for (axis, col) in ((ax.set_xlim, 0), (ax.set_ylim, 1)):
            lo, hi = np.percentile(volts[:, col], (1.0, 99.0))
            pad = (((hi - lo) * 0.06) + 0.01)
            axis((lo - pad), (hi + pad))
        plt.pause(0.001)
    os.close(fd)


if __name__ == "__main__":
    import sys
    if ("--headless" in sys.argv):
        fd = os.open(find_port(), (os.O_RDWR | os.O_NONBLOCK))
        state = {"buf": b""}
        frames = [f for f in (read_frame(fd, state) for _ in range(6)) if f is not None]
        os.close(fd)
        print("frames:", len(frames), "| pairs each:", (len(frames[0]) if frames else 0))
        if frames:
            np.save("live_capture.npy", np.concatenate(frames))
            print("saved live_capture.npy")
    else:
        live()

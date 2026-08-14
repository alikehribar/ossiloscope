import glob
import fcntl
import os
import select
import sys
import numpy as np

MAGIC = b"\xab\xcd\xef\x01"
BURST = 2048
PAYLOAD = (BURST * 4)
GREEN = "#39ff5a"


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


def read_frame(fd, buf):
    # buf is a bytearray the caller keeps between calls: serial arrives in
    # arbitrary chunks, so leftovers have to survive until the next burst.
    while True:
        idx = buf.find(MAGIC)
        if ((idx >= 0) and (len(buf) >= (idx + 4 + PAYLOAD))):
            chunk = bytes(buf[(idx + 4):(idx + 4 + PAYLOAD)])
            del buf[:(idx + 4 + PAYLOAD)]
            return np.frombuffer(chunk, dtype="<u2").reshape(-1, 2)
        if select.select([fd], [], [], 2.0)[0]:
            try:
                buf += os.read(fd, 262144)
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
    fd, buf = os.open(find_port(), (os.O_RDWR | os.O_NONBLOCK)), bytearray()
    plt.ion()
    fig = plt.figure(figsize=(7.5, 7.5), facecolor="black")
    plt.subplot(facecolor="black")
    plt.xlabel("X  GP2  (V)", color=GREEN)
    plt.ylabel("Y  GP3  (V)", color=GREEN)
    plt.tick_params(colors=GREEN)
    trace, = plt.plot([], [], "-", color=GREEN, linewidth=1.3)
    plt.show(block=False)
    plt.pause(0.05)
    read_frame(fd, buf)  # the first burst can be a partial one, so drop it
    while plt.fignum_exists(fig.number):
        frame = read_frame(fd, buf)
        if frame is None:
            continue
        one_pass = frame[:find_period(frame)]
        volts = median_filter(((one_pass / 65535.0) * 3.3), 7)
        trace.set_data(volts[:, 0], volts[:, 1])
        # Scale each axis to its own signal, the way a scope's separate
        # V/div knobs do. A shared 0-3.3 V axis squashes wide, short
        # drawings into a sliver where noise dominates.
        for (set_limits, col) in ((plt.xlim, 0), (plt.ylim, 1)):
            lo, hi = np.percentile(volts[:, col], (1.0, 99.0))
            pad = (((hi - lo) * 0.06) + 0.01)
            set_limits((lo - pad), (hi + pad))
        plt.pause(0.001)
    os.close(fd)


def headless():
    fd, buf = os.open(find_port(), (os.O_RDWR | os.O_NONBLOCK)), bytearray()
    frames = [f for f in (read_frame(fd, buf) for _ in range(6)) if f is not None]
    os.close(fd)
    if (not frames):
        raise SystemExit("board sent nothing; is a streaming firmware loaded?")
    np.save("live_capture.npy", np.concatenate(frames))
    print("frames:", len(frames), "| pairs each:", len(frames[0]), "| saved live_capture.npy")


if __name__ == "__main__":
    if ("--headless" in sys.argv):
        headless()
    else:
        live()

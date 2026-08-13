import array
import math
import audiocore
import audiopwmio
import board

SAMPLE_RATE = 32000
POINT_COUNT = 400
HEAD_R = 0.62


def polar(angle_deg, radius):
    a = math.radians(angle_deg)
    return ((radius * math.cos(a)), (radius * math.sin(a)))


def arc(a0, a1, radius, steps):
    return [polar((a0 + (((a1 - a0) * i) / steps)), radius) for i in range(steps + 1)]


def circle(cx, cy, radius, steps):
    points = []
    for i in range(steps + 1):
        a = ((2.0 * math.pi) * (i / steps))
        points.append((
            (cx + (radius * math.cos(a))),
            (cy + (radius * math.sin(a))),
        ))
    return points


EAR_TIP_R = (0.72, 0.95)
EAR_TIP_L = (-0.72, 0.95)
EYE_R = (0.24, 0.16)
EYE_L = (-0.24, 0.16)
EYE_SIZE = 0.09
NOSE_L = (-0.08, -0.06)
NOSE_R = (0.08, -0.06)
NOSE_B = (0.0, -0.18)
WHISKERS = (
    ((-0.10, -0.10), (-0.66, -0.02)),
    ((-0.10, -0.15), (-0.66, -0.24)),
    ((0.10, -0.10), (0.66, -0.02)),
    ((0.10, -0.15), (0.66, -0.24)),
)

p25 = polar(25, HEAD_R)
p70 = polar(70, HEAD_R)
p110 = polar(110, HEAD_R)
p155 = polar(155, HEAD_R)

# Corner points only. The beam visits these in order, and the resampler below
# fills the straight runs between them.
outline = [p25, EAR_TIP_R, p70]
outline += arc(70, 110, HEAD_R, 8)
outline += [p110, EAR_TIP_L, p155]
outline += arc(155, 385, HEAD_R, 46)
outline += [p25, EYE_R]
outline += circle(EYE_R[0], EYE_R[1], EYE_SIZE, 12)
outline += [EYE_R, EYE_L]
outline += circle(EYE_L[0], EYE_L[1], EYE_SIZE, 12)
outline += [EYE_L, NOSE_L, NOSE_R, NOSE_B, NOSE_L]

# Each whisker is drawn out and back along the same line, because the beam
# cannot jump. The return stroke lands on the outgoing one and stays invisible.
for (start, end) in WHISKERS:
    outline += [start, end, start]


def even_spaced_path(corners, count):
    corners = (list(corners) + [corners[0]])

    # Distance travelled from the start up to each corner, used as a ruler.
    walked = [0.0]
    for i in range(1, len(corners)):
        dx = (corners[i][0] - corners[(i - 1)][0])
        dy = (corners[i][1] - corners[(i - 1)][1])
        walked.append((walked[-1] + math.sqrt(((dx * dx) + (dy * dy)))))

    # The beam spends the same time on every point, so equal spacing along the
    # line makes every stroke equally bright. Corner points alone left the long
    # strokes six times dimmer than the short ones.
    path = []
    segment = 0
    for step in range(count):
        target = ((walked[-1] * step) / count)
        while ((segment < (len(walked) - 2)) and (walked[(segment + 1)] < target)):
            segment += 1
        span = (walked[(segment + 1)] - walked[segment])
        fraction = (0.0 if (span == 0.0) else ((target - walked[segment]) / span))
        start, end = corners[segment], corners[(segment + 1)]
        path.append((
            (start[0] + ((end[0] - start[0]) * fraction)),
            (start[1] + ((end[1] - start[1]) * fraction)),
        ))
    return path


path = even_spaced_path(outline, POINT_COUNT)

# X and Y interleaved as unsigned 16-bit values: the layout the DMA engine
# reads, one pair per point. Coordinates run -1..1, duty runs 0..65535.
frame = array.array("H", bytearray((len(path) * 4)))
for (i, (x, y)) in enumerate(path):
    frame[(i * 2)] = int((((x + 1.0) * 0.5) * 65535))
    frame[((i * 2) + 1)] = int((((y + 1.0) * 0.5) * 65535))

sample = audiocore.RawSample(frame, channel_count=2, sample_rate=SAMPLE_RATE)
audio = audiopwmio.PWMAudioOut(left_channel=board.GP2, right_channel=board.GP3)
audio.play(sample, loop=True)

# DMA draws in the background. This only stops code.py from exiting,
# which would switch the outputs off.
while True:
    pass

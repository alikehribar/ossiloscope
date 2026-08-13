import array
import math
import audiocore
import audiopwmio
import board

SAMPLE_RATE = 32000
POINT_COUNT = 320

X_POINTS = (
     43,   37,   21,   15,   15,   21,   37,   43,   43,   48,   76,   62,   62,   81,
     95,  102,   88,  102,  109,  120,  136,  142,  142,  130,  142,  142,  136,  120,
    114,  114,  120,  136,  142,  147,  147,  147,  173,  147,  173,  180,  180,  208,
    208,  213,  219,  235,  241,  235,  219,  213,  213,  219,  235,  241,  241,  229,
    247,  247,   43,
)

Y_POINTS = (
    180,  195,  195,  180,   75,   60,   60,   75,  180,  195,  195,  195,   60,   60,
    195,  127,  127,  127,   60,   60,   60,   75,  127,  127,  127,   75,   60,   60,
     75,  180,  195,  195,  180,  195,   60,  127,  195,  127,   60,   60,  195,   60,
    195,  180,  195,  195,  180,  195,  195,  180,   75,   60,   60,   75,  127,  127,
    127,   25,   25,
)



def even_spaced_path(count):
    corners = [(float(x), float(y)) for (x, y) in zip(X_POINTS, Y_POINTS)]
    corners.append(corners[0])

    # Distance travelled from the start up to each corner. This turns the
    # outline into a ruler we can measure positions along.
    walked = [0.0]
    for i in range(1, len(corners)):
        dx = (corners[i][0] - corners[(i - 1)][0])
        dy = (corners[i][1] - corners[(i - 1)][1])
        walked.append((walked[-1] + math.sqrt(((dx * dx) + (dy * dy)))))

    # The beam spends the same time on every point, so points spaced evenly
    # along the line make every stroke equally bright. Corner points alone
    # would leave long strokes 28x dimmer than short ones.
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


path = even_spaced_path(POINT_COUNT)

# X and Y interleaved as unsigned 16-bit values: the layout the DMA engine
# reads, one pair per point. Input is 0-255, output is 0-65535 (0 to 3.3 V).
frame = array.array("H", bytearray((len(path) * 4)))
for (i, (x, y)) in enumerate(path):
    frame[(i * 2)] = int(((x / 255.0) * 65535))
    frame[((i * 2) + 1)] = int(((y / 255.0) * 65535))

sample = audiocore.RawSample(frame, channel_count=2, sample_rate=SAMPLE_RATE)
audio = audiopwmio.PWMAudioOut(left_channel=board.GP2, right_channel=board.GP3)
audio.play(sample, loop=True)

# DMA draws in the background. This only stops code.py from exiting,
# which would switch the outputs off.
while True:
    pass

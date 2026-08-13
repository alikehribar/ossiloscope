import array
import math
import time
import analogio
import audiocore
import audiopwmio
import board

SAMPLE_RATE = 32000
MAX_DUTY = 65535
HEAD_R = 0.62


def polar(angle_deg, radius):
    a = math.radians(angle_deg)
    return ((radius * math.cos(a)), (radius * math.sin(a)))

def arc(a0, a1, radius, steps):
    points = []
    for i in range(steps + 1):
        points.append(polar((a0 + (((a1 - a0) * i) / steps)), radius))
    return points


def line(p0, p1, steps):
    points = []
    for i in range(steps + 1):
        t = (i / steps)
        points.append((
            (p0[0] + ((p1[0] - p0[0]) * t)),
            (p0[1] + ((p1[1] - p0[1]) * t)),
        ))
    return points


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

path = []
path += line(p25, EAR_TIP_R, 6)
path += line(EAR_TIP_R, p70, 6)
path += arc(70, 110, HEAD_R, 8)
path += line(p110, EAR_TIP_L, 6)
path += line(EAR_TIP_L, p155, 6)
path += arc(155, 385, HEAD_R, 46)

path += line(p25, EYE_R, 8)
path += circle(EYE_R[0], EYE_R[1], EYE_SIZE, 12)
path += line(EYE_R, EYE_L, 8)
path += circle(EYE_L[0], EYE_L[1], EYE_SIZE, 12)
path += line(EYE_L, NOSE_L, 6)
path += line(NOSE_L, NOSE_R, 4)
path += line(NOSE_R, NOSE_B, 4)
path += line(NOSE_B, NOSE_L, 4)

for (start, end) in WHISKERS:
    path += line(start, end, 8)
    path += line(end, start, 8)

path += line(path[-1], path[0], 8)


def to_duty(value):
    scaled = int((((value + 1.0) * 0.5) * MAX_DUTY))
    return min(max(scaled, 0), MAX_DUTY)


frame = array.array("H", bytearray((len(path) * 4)))
for (i, (x, y)) in enumerate(path):
    frame[(i * 2)] = to_duty(x)
    frame[((i * 2) + 1)] = to_duty(y)

sample = audiocore.RawSample(frame, channel_count=2, sample_rate=SAMPLE_RATE)
audio = audiopwmio.PWMAudioOut(left_channel=board.GP2, right_channel=board.GP3)
audio.play(sample, loop=True)

x_in = analogio.AnalogIn(board.GP26)
y_in = analogio.AnalogIn(board.GP27)

time.sleep(2.0)
print("BEGIN")
for _ in range(3000):
    print(x_in.value, y_in.value)
print("END")

while True:
    pass

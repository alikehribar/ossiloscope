import array
import math
import analogio
import usb_cdc
import audiocore
import audiopwmio
import board

SAMPLE_RATE = 512000
POINT_COUNT = 7200

X_POINTS = (
     167,  163,  158,  146,  136,  126,  115,  105,   93,   88,   84,   81,
      78,   74,   70,   65,   60,   56,   52,   50,   49,   49,   48,   48,
      47,   47,   46,   45,   44,   43,   43,   42,   41,   41,   40,   40,
      40,   41,   41,   42,   43,   44,   44,   45,   46,   47,   48,   48,
      49,   49,   49,   48,   47,   46,   44,   42,   40,   37,   32,   31,
      30,   29,   28,   27,   27,   27,   26,   26,   26,   26,   27,   27,
      30,   33,   38,   43,   49,   49,   56,   62,   67,   70,   72,   74,
      75,   77,   79,   82,   85,   89,   94,   97,  100,  103,  105,  108,
     111,  113,  116,  120,  123,  126,  128,  132,  135,  138,  140,  143,
     146,  148,  151,  154,  158,  162,  166,  169,  172,  174,  176,  177,
     179,  181,  185,  189,  195,  202,  208,  213,  218,  221,  224,  225,
     224,  224,  223,  222,  221,  220,  215,  211,  209,  207,  206,  204,
     203,  203,  202,  203,  203,  204,  204,  205,  206,  207,  208,  208,
     209,  210,  210,  211,  211,  211,  210,  210,  209,  209,  208,  207,
     206,  205,  205,  204,  203,  203,  202,  202,  201,  199,  195,  191,
     186,  181,  177,  173,  170,  167,  172,  174,  176,  179,  182,  185,
     188,  191,  195,  200,  204,  206,  209,  212,  214,  217,  219,  221,
     222,  223,  224,  225,  226,  226,  225,  224,  223,  223,  223,  223,
     223,  224,  224,  225,  226,  227,  229,  232,  236,  240,  242,  243,
     243,  243,  242,  240,  238,  236,  234,  231,  229,  227,  223,  219,
     213,  207,  201,  195,  189,  184,  181,  178,  177,  176,  175,  174,
     172,  169,  167,  164,  162,  159,  157,  155,  154,  151,  146,  140,
     134,  129,  126,  123,  117,  111,  105,  100,   97,   96,   94,   92,
      89,   87,   84,   82,   80,   78,   76,   75,   74,   73,   71,   67,
      62,   56,   50,   44,   38,   32,   28,   24,   22,   20,   17,   15,
      13,   11,    9,    9,    8,    8,    8,   10,   12,   16,   18,   21,
      23,   24,   26,   26,   27,   27,   27,   27,   27,   26,   26,   25,
      25,   26,   26,   27,   28,   29,   30,   32,   34,   37,   40,   42,
      45,   48,   51,   56,   60,   63,   66,   69,   72,   75,   77,   79,
      80,   82,   82,   83,   86,   92,  101,  110,  119,  126,  133,  141,
     150,  159,  165,  168,  169,  170,  171,  172,
)

Y_POINTS = (
      33,   32,   30,   26,   23,   23,   23,   26,   30,   32,   33,   35,
      38,   40,   44,   49,   55,   60,   65,   69,   72,   73,   74,   76,
      78,   80,   81,   84,   86,   89,   93,   96,   99,  103,  106,  109,
     112,  116,  120,  123,  127,  130,  133,  136,  138,  140,  143,  144,
     146,  148,  149,  151,  153,  154,  155,  155,  155,  155,  183,  190,
     197,  204,  209,  212,  214,  215,  216,  217,  217,  217,  218,  217,
     214,  211,  206,  200,  194,  194,  186,  180,  176,  173,  171,  171,
     171,  172,  173,  175,  178,  182,  186,  189,  191,  192,  193,  194,
     195,  195,  195,  196,  196,  196,  196,  196,  195,  195,  195,  194,
     193,  192,  191,  189,  186,  182,  178,  175,  173,  172,  171,  171,
     171,  173,  176,  180,  186,  194,  200,  206,  211,  214,  216,  217,
     216,  213,  208,  202,  194,  186,  155,  155,  155,  155,  154,  153,
     151,  149,  148,  146,  144,  143,  140,  138,  136,  133,  130,  127,
     123,  120,  116,  112,  109,  106,  103,   99,   96,   93,   89,   86,
      84,   81,   80,   78,   76,   74,   73,   72,   69,   65,   60,   55,
      49,   44,   40,   38,   35,   33,   21,   22,   23,   24,   26,   28,
      31,   34,   38,   43,   47,   50,   54,   59,   64,   70,   74,   79,
      83,   88,   94,  101,  106,  111,  116,  123,  131,  132,  133,  134,
     134,  134,  134,  134,  135,  139,  149,  167,  195,  214,  228,  236,
     241,  243,  245,  246,  247,  247,  246,  245,  243,  240,  237,  232,
     226,  220,  213,  207,  201,  196,  192,  189,  188,  188,  189,  190,
     192,  194,  196,  199,  201,  203,  204,  206,  206,  207,  208,  209,
     210,  210,  211,  210,  210,  209,  208,  207,  206,  206,  204,  203,
     201,  199,  196,  194,  192,  190,  189,  188,  188,  189,  192,  196,
     201,  207,  213,  220,  226,  232,  237,  240,  243,  245,  246,  247,
     247,  246,  245,  245,  243,  241,  235,  226,  210,  187,  173,  160,
     148,  139,  134,  131,  130,  129,  127,  125,  122,  119,  115,  111,
     107,  104,   99,   93,   87,   83,   78,   74,   70,   64,   59,   54,
      50,   47,   43,   38,   34,   31,   28,   26,   24,   23,   22,   21,
      20,   19,   19,   18,   16,   14,   12,   10,    9,    8,    9,   10,
      12,   14,   16,   18,   19,   19,   20,   21,
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
    # would leave long strokes 8.7x dimmer than typical ones: the longest run
    # in the table below is 31.4 units against a median of 3.61.
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

# The DMA carries on drawing while the CPU reads the outputs back through
# the ADC taps on GP26/GP27 and ships them to the Mac over USB.
BURST = 2048
MAGIC = b"\xab\xcd\xef\x01"

x_in = analogio.AnalogIn(board.GP26)
y_in = analogio.AnalogIn(board.GP27)
capture = array.array("H", bytearray((BURST * 4)))
serial = usb_cdc.console

while True:
    for i in range(BURST):
        capture[(i * 2)] = x_in.value
        capture[((i * 2) + 1)] = y_in.value
    # Serial has no message boundaries, so each burst is prefixed with
    # MAGIC and the Mac re-syncs by searching for it.
    serial.write(MAGIC)
    serial.write(capture)

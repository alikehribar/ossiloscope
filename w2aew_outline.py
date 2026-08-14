# The word W2AEW in Arial Bold, traced as one continuous stroke.
# The table below comes from `python3 textgen.py W2AEW` on the Mac: the letters
# are drawn overlapping so they fuse into a single shape, potrace traces that
# shape, and the two closed contours it returns (the word, and the hole in the
# A) are joined into one loop by a bridge along the baseline. The beam cannot
# be blanked, so that bridge is drawn; it hides on the bottom edge of the
# letters, and the climb into the A stays visible as a short vertical line.
import array
import math
import audiocore
import audiopwmio
import board

SAMPLE_RATE = 512000
POINT_COUNT = 7200

X_POINTS = (
      20,   20,   25,   31,   35,   37,   38,   39,   40,   40,   40,   41,
      43,   45,   48,   49,   50,   50,   51,   52,   53,   54,   55,   61,
      63,   63,   64,   65,   65,   66,   67,   68,   68,   69,   69,   69,
      70,   70,   70,   70,   70,   70,   70,   70,   70,   70,   71,   72,
      73,   74,   75,   76,   76,   77,   77,   78,   78,   79,   79,   79,
      79,   79,   79,   79,   79,   79,   79,   80,   81,   82,   83,   85,
      87,   88,   90,   91,   91,   92,   92,   92,   91,   91,   89,   86,
      82,   79,   76,   74,   72,   71,   70,   70,   69,   69,   69,   69,
      68,   69,   70,   73,   76,   82,   89,  109,  111,  113,  123,  133,
     135,  138,  161,  185,  185,  185,  171,  157,  157,  157,  170,  182,
     182,  182,  182,  182,  182,  182,  182,  182,  181,  179,  176,  173,
     170,  157,  157,  157,  171,  174,  177,  180,  182,  183,  184,  184,
     185,  186,  187,  188,  189,  190,  191,  192,  193,  194,  194,  194,
     200,  205,  210,  211,  212,  213,  214,  215,  215,  216,  217,  220,
     222,  224,  225,  225,  225,  226,  227,  228,  230,  231,  233,  234,
     235,  235,  235,  235,  236,  237,  238,  240,  241,  243,  244,  245,
     246,  247,  247,  247,  246,  246,  245,  244,  242,  237,  236,  235,
     235,  235,  234,  234,  234,  234,  234,  233,  233,  233,  232,  232,
     231,  231,  231,  230,  230,  230,  230,  229,  228,  227,  225,  221,
     215,  213,  211,  210,  209,  209,  209,  209,  208,  208,  207,  206,
     205,  204,  203,  202,  201,  201,  200,  200,  200,  200,  200,  199,
     199,  198,  198,  198,  198,  198,  197,  197,  197,  197,  197,  196,
     196,  195,  195,  195,  195,  194,  194,  194,  194,  194,  194,  194,
     193,  193,  170,  147,  147,  147,  147,  147,  147,  147,  147,  147,
     146,  144,  142,  140,  138,  129,  123,  118,  110,  108,  106,  104,
     103,  102,  102,  101,  101,  100,   98,   96,   92,   83,   83,   84,
      84,   86,   87,   89,   91,   94,   96,   98,   99,  100,  101,  101,
     101,  102,  101,  101,  100,   99,   98,   96,   95,   93,   90,   89,
      88,   86,   84,   83,   81,   79,   77,   75,   74,   72,   71,   71,
      71,   71,   71,   71,   71,   71,   71,   72,   72,   72,   73,   72,
      72,   71,   70,   69,   68,   63,   61,   61,   61,   60,   60,   60,
      60,   60,   59,   59,   59,   58,   58,   57,   57,   57,   56,   56,
      56,   56,   55,   55,   54,   53,   51,   47,   41,   38,   37,   36,
      35,   35,   34,   34,   34,   33,   32,   31,   30,   29,   28,   27,
      27,   26,   26,   26,   26,   25,   25,   25,   24,   24,   24,   23,
      23,   23,   23,   23,   23,   22,   22,   22,   21,   21,   21,   20,
      20,   20,   20,   20,   20,   20,   19,   19,   19,   18,   13,   12,
      11,    9,    9,    8,    8,    8,    9,   11,   14,   16,   18,   19,
      20,   20,  123,  123,  120,  118,  117,  117,  118,  120,  122,  123,
     123,  124,  124,  124,  125,  126,  127,  127,  128,  128,  129,  129,
     130,  130,  129,  127,  123,  123,
)

Y_POINTS = (
       8,    8,    8,    8,   26,   31,   36,   39,   42,   44,   45,   42,
      35,   26,   18,   11,    8,    8,    8,    8,    8,    8,    8,    8,
      16,   18,   21,   24,   27,   31,   33,   36,   38,   40,   42,   43,
      43,   44,   44,   44,   44,   43,   43,   43,   43,   43,   43,   43,
      42,   42,   42,   42,   42,   42,   42,   42,   42,   42,   42,   42,
      42,   42,   43,   43,   44,   44,   44,   46,   47,   48,   49,   49,
      49,   49,   48,   47,   46,   45,   43,   41,   40,   38,   36,   33,
      29,   26,   23,   20,   18,   17,   15,   14,   13,   11,   10,    9,
       8,    8,    8,    8,    8,    8,    8,    8,   14,   19,   19,   19,
      14,    8,    8,    8,   12,   16,   16,   16,   23,   30,   30,   30,
      34,   35,   36,   36,   37,   38,   38,   38,   38,   38,   38,   38,
      38,   38,   44,   49,   49,   49,   49,   49,   49,   49,   49,   49,
      47,   44,   40,   35,   30,   24,   20,   15,   12,   10,    9,    8,
       8,    8,   26,   31,   36,   39,   42,   44,   45,   42,   35,   26,
      18,   11,    8,    8,    8,    8,    8,    8,    8,    8,    8,    8,
       8,    8,    8,    9,   12,   15,   20,   26,   33,   39,   45,   50,
      54,   56,   57,   57,   57,   57,   57,   57,   57,   57,   51,   49,
      47,   46,   45,   44,   43,   43,   42,   41,   39,   37,   35,   33,
      31,   29,   28,   27,   26,   25,   24,   25,   28,   33,   40,   57,
      57,   57,   57,   57,   57,   57,   57,   56,   54,   52,   49,   45,
      41,   37,   33,   30,   28,   26,   25,   24,   24,   25,   25,   27,
      29,   30,   32,   33,   34,   35,   35,   36,   37,   38,   39,   41,
      42,   44,   46,   47,   48,   49,   49,   50,   50,   51,   52,   53,
      54,   57,   57,   57,   34,   28,   23,   18,   15,   12,   11,   12,
      15,   18,   23,   28,   34,   57,   57,   57,   36,   31,   26,   22,
      19,   17,   16,   16,   16,   17,   17,   17,   17,   17,   17,   18,
      19,   20,   21,   23,   25,   28,   31,   33,   35,   36,   38,   40,
      42,   44,   46,   48,   49,   51,   53,   54,   55,   56,   57,   57,
      57,   57,   57,   57,   57,   56,   56,   54,   53,   51,   50,   49,
      49,   49,   49,   48,   49,   50,   52,   54,   55,   57,   57,   57,
      57,   57,   57,   57,   57,   57,   51,   49,   47,   46,   45,   44,
      43,   43,   42,   41,   39,   37,   35,   33,   31,   29,   28,   27,
      26,   25,   24,   25,   28,   33,   40,   57,   57,   57,   57,   57,
      57,   57,   57,   56,   54,   52,   49,   45,   41,   37,   33,   30,
      28,   26,   25,   24,   24,   25,   25,   27,   29,   30,   32,   33,
      34,   35,   35,   36,   37,   38,   39,   41,   42,   44,   46,   47,
      48,   49,   49,   50,   50,   51,   52,   53,   54,   57,   57,   57,
      57,   57,   57,   57,   57,   57,   54,   45,   34,   23,   14,    9,
       8,    8,    8,   27,   27,   28,   28,   29,   33,   37,   41,   44,
      45,   45,   44,   43,   41,   39,   36,   36,   34,   32,   30,   29,
      28,   28,   27,   27,   27,    8,
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
    # would leave long strokes 51x dimmer than short ones: the longest run
    # here is 103 units against a median of 2.0.
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

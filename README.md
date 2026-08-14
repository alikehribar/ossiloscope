# Oscilloscope XY vector drawing on Raspberry Pi Pico 2

Draws a picture on an oscilloscope in XY mode using a Raspberry Pi Pico 2
(RP2350) running CircuitPython. Two PWM pins plus RC filters act as a two channel
DAC; the point stream is pushed by DMA, so the CPU is not involved in drawing.

I started this project to learn how to use an oscilloscope, how PWM works, how to
build and understand an RC circuit, and how to draw vector images on an
oscilloscope. By the end of the project, I had learned these topics to a level
that was sufficient to understand and complete this project successfully.

Verified on Adafruit CircuitPython 10.2.1, board id `raspberry_pi_pico2`, with an
Owon SmartDS5032E.

`REPORT.md` is the full write up: theory, circuit, method and results.

## Circuit

Both channels are identical: a 2.2 kohm resistor in series with the PWM pin and a
4.7 nF capacitor to ground, with the output taken between them. In terms of
physical Pico pins:

```
                    2.2 kohm            X node
   GP2  (pin 4)  ---[========]-------------+------------  scope CH1  (X)
                                           |
                                           +------------  GP26 (pin 31)  ADC tap
                                           |
                                          === 4.7 nF
                                           |
                                          GND

                    2.2 kohm            Y node
   GP3  (pin 5)  ---[========]-------------+------------  scope CH2  (Y)
                                           |
                                           +------------  GP27 (pin 32)  ADC tap
                                           |
                                          === 4.7 nF
                                           |
                                          GND

   GND (pin 38 or AGND pin 33)  ----------------------  scope ground clips
```

The scope and ADC taps connect to the node between the resistor and the
capacitor, never to the GPIO side of the resistor. The same circuit drawn as a
schematic:

<img src="schematic.png" alt="Two channel RC filter schematic" width="340">

Scope settings: XY mode, 1 Mohm input impedance, roughly 500 mV/div to
1 V/div. The ADC taps are optional. They are only needed by
the files marked "streams" in the table below.

The time base matters as much as the vertical scale, because the instrument has
to acquire fast enough to resolve consecutive points.

<img src="scope_output.jpg" alt="The arc built cat drawn on the instrument" width="340">

The arc built cat at 4.0 ms/div, where the instrument acquires at 125 kS/s and
the outline is continuous.

<img src="scope_undersampled.jpg" alt="The same board acquired at 125 S/s" width="340">

The same running board at 4 s/div, which drops acquisition to 125 S/s. The
instrument keeps roughly one pair in 256 and the outline breaks into dots. The
board is doing the same thing in both photographs.

## Values

| Quantity | Value | Source |
| --- | --- | --- |
| RC time constant, `R * C` | 10.34 us | derived |
| RC cutoff frequency | 15.4 kHz | derived |
| Time per point at 32 kHz | 31.25 us = 3.02 tau | derived |
| Settling per point at 32 kHz | 95.1 % | derived |
| Point budget at 50 Hz and 32 kHz | 640 points | derived |
| X output, mean / min / max | 1.696 / 0.426 / 2.850 V | measured |
| Y output, mean / min / max | 1.725 / 0.562 / 3.226 V | measured |

Voltages were measured by the Pico reading its own outputs through GP26 and GP27.
The means are the reliable numbers: repeat runs give the same means within 2 mV,
while the minimum and maximum are single samples and move by tens of millivolts
depending on which instants are caught.

The voltage rows were taken from the arc built 231 point path at 32 kHz, which
redraws at (32000 / 231) = 138.5 Hz. That path is still what `livescope_fw.py`
and `selftest_adc.py` run.

`REPORT.md` section 6 covers the 512 kHz outline mode, where the readback sits
15.0 mV from the intended path, the same order as the 16.1 mV predicted from the
time constant. Section 6.3 explains why that comparison is good for an order of
magnitude and not for a third figure: the readback reads X and Y one after the
other, which can displace a pair by up to 34.7 mV on its own.

## Files

Firmware, one at a time as `code.py` on the Pico:

| File | Sample rate | Points | Purpose |
| --- | --- | --- | --- |
| `cat_outline.py` | 512000 | 7200 | Cat traced as a closed outline from a point table. |
| `cat_outline_livescope_fw.py` | 512000 | 7200 | `cat_outline.py` that also streams. |
| `w2aew_outline.py` | 512000 | 7200 | The word W2AEW as a closed outline from a point table. |
| `w2aew_outline_livescope_fw.py` | 512000 | 7200 | `w2aew_outline.py` that also streams. |
| `livescope_fw.py` | 32000 | 231 | The arc built cat, streaming. Not resampled, so the count is whatever the arcs produce. |
| `selftest_adc.py` | 32000 | 231 | Same arc built cat, with a check of how fast the ADC can be read. |
| `cat_xy_pwm_legacy.py` | n/a | 231 | The first version, a `pwmio` loop with no DMA. Kept because the 20 to 40 Hz it manages is what motivated the DMA route. |

The streaming firmware sends its ADC measurements to the computer over USB.

Host tools, run on the Mac:

| File | Purpose |
| --- | --- |
| `livescope.py` | Live viewer for the USB stream. `--headless` saves `live_capture.npy` instead of opening a window. |
| `outline_compare.py` | Measures a capture against the path the firmware meant to draw and writes the two panel figure: `python3 outline_compare.py w2aew_outline.py w2aew_capture.npy`. |
| `scope_sim.py` | Simulates the RC filter to preview a path before flashing it. Takes a firmware file as an argument, defaulting to `cat_outline.py`. |

`schematic.kicad_sch` is the KiCad source for the figure above. Only the
schematic is kept, since the circuit is built on a breadboard and there is no
board layout.

## Usage

Copy any firmware file to the board as `code.py`:

```
cp cat_outline.py /Volumes/CIRCUITPY/code.py
```

The board starts drawing as soon as it restarts, and keeps drawing without a
computer attached. USB is only needed for power, or to receive the stream from
one of the three `_livescope_fw.py` files.

The host tools need numpy and matplotlib.

To watch the output live, flash a streaming firmware and run:

```
python3 livescope.py
```

## How the drawing works

An oscilloscope in XY mode positions a single dot from two voltages. There is no
frame buffer, so a picture must be a single ordered list of points that the dot
visits in sequence. The dot cannot be switched off without a Z axis input, so
moves between disconnected shapes are drawn as visible lines. Paths are therefore
built as one closed circuit, and detours such as the whiskers are retraced along
the same line so the return stroke overlaps the outgoing one.

For the second test, a closed path with a different shape was created from the
word W2AEW. It runs along a shared baseline between the letters, so the travel
line sits on the bottom edge and stays invisible; only the climb into the A
shows, as the short vertical line under it.

CircuitPython's audio output is used to send the X and Y values continuously
using DMA. It is chosen because it is DMA driven rather than for sound: left
channel is X, right channel is Y, and `RawSample` holds the interleaved uint16
duty values. CircuitPython exposes no direct DMA API; this is the available route
to it.

`cat_outline.py` resamples its path to evenly spaced points with
`even_spaced_path()` before playing it. The drawing point spends the same time on
every point, so equal spacing keeps a long stroke from appearing dimmer than a
short one.

The older arc built cat in `livescope_fw.py`, `selftest_adc.py` and
`cat_xy_pwm_legacy.py` does not do this. Its 231 points come straight from the
arc and line builders, and their spacing is uneven: the longest gap is 3.8 times
the median and a few points are exact duplicates. Those files are kept for the
measurements and the DMA comparison, not because they draw well.

## Limits

- Point budget is set by the flicker threshold, not by memory. At 32 kHz, 640
  points is the maximum that stays above 50 Hz.
- Raising the point budget means raising the sample rate, which is what the
  512 kHz mode does.
- At 512 kHz each point lasts 0.19 tau and the filter settles only 17.2 % of the
  way to it. That mode works because 7200 points sit close together along the
  path, so the filter averages neighbours instead of chasing a step. The cost is
  the rounding measured in `REPORT.md` section 6.
- Resampling equalises brightness within one path but not between drawings, since
  each has its own ratio of path length to point count.

## Checking the output

A capture can be compared against the path the firmware meant to draw. In the
figure below, left is what was sent to GP2 and GP3 and right is what came back
through GP26 and GP27. The photograph beside it is the oscilloscope output:

<img src="outline_compare.png" alt="Intended path beside the readback" width="460"> <img src="cat_outline_scope.jpg" alt="cat_outline.py on the instrument" width="330">

All three are the same firmware, `cat_outline.py`: 7200 points at 512 kHz. The
photograph was taken at 500 mV/div on both channels, in XY mode with dot
display.

The steps on the plot are the ADC, not the circuit: it keeps about one point in
(7200 / 630) = 11.4 and the viewer joins those with straight lines. The blunted
ear tips are the RC filter. `REPORT.md` section 6 works through both.

The same check on `w2aew_outline.py`, a different drawing through the same
circuit:

<img src="w2aew_outline_compare.png" alt="W2AEW as sent and as read back" width="460"> <img src="w2aew_scope.jpg" alt="w2aew_outline.py on the instrument" width="330">

| Distance from the intended path | W2AEW | Cat outline |
| --- | --- | --- |
| mean | 14.3 mV | 14.3 mV |

Both drawings were measured the same way, with `outline_compare.py` over one lap
of a fresh capture, and both run at 512 kHz with 7200 points. Their
perimeters are close enough that the drawing point moves almost the same distance
per point, 0.2315 units for the word against 0.2343 for the cat. The two means
landing on the same 14.3 mV suggests that the measured error mainly comes from
the signal path rather than from the particular drawing.

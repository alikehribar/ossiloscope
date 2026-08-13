# Oscilloscope XY vector drawing on Raspberry Pi Pico 2

Draws a picture on an oscilloscope in XY mode using a Raspberry Pi Pico 2
(RP2350) running CircuitPython. Two PWM pins plus RC filters act as a two channel
DAC; the point stream is pushed by DMA, so the CPU is not involved in drawing.

Verified on Adafruit CircuitPython 10.2.1, board id `raspberry_pi_pico2`, with an
Owon SmartDS5032E.

`REPORT.md` is the full write up: theory, circuit, method and results.

## Circuit

![Two channel RC filter schematic](schematic.png)

Both channels are identical: a 2.2 kohm resistor in series with the PWM pin and a
4.7 nF capacitor to ground, with the output taken between them. The same circuit
in terms of physical Pico pins:

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
capacitor, never to the GPIO side of the resistor.

Scope settings: XY mode, both channels DC coupled, 1 Mohm input impedance,
roughly 500 mV/div to 1 V/div. The ADC taps are optional. They are only needed by
the files marked "streams" in the table below.

The time base matters as much as the vertical scale, because the instrument has
to acquire fast enough to resolve consecutive points.

![cat_xy.py drawn on the instrument](scope_output.jpg)

`cat_xy.py` at 4.0 ms/div, where the instrument acquires at 125 kS/s and the
outline is continuous.

![The same board acquired at 125 S/s](scope_undersampled.jpg)

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
| ADC rate, list comprehension benchmark | 52206 pairs/s | measured |
| ADC rate, streaming firmware in practice | 43900 pairs/s | measured |
| USB streaming throughput | about 144 kB/s, 18 frames/s | measured |

Voltages were measured by the Pico reading its own outputs through GP26 and GP27.

The voltage and rate rows were taken from the arc built 231 point path at 32 kHz,
which redraws at (32000 / 231) = 138.5 Hz. That path is still what
`livescope_fw.py` and `selftest_adc.py` run. `cat_xy.py` is a different drawing
and resamples to 400 points, giving (32000 / 400) = 80 Hz.

`REPORT.md` section 6 covers the 512 kHz outline mode, where the readback sits
15.0 mV from the intended path against 16.1 mV predicted from the time constant.

## Files

Firmware, one at a time as `code.py` on the Pico:

| File | Sample rate | Points | Purpose |
| --- | --- | --- | --- |
| `cat_xy.py` | 32000 | 400 | Cat drawn from arcs and lines built in code. |
| `cat_outline.py` | 512000 | 7200 | Cat traced as a closed outline from a point table. |
| `text_outline.py` | 512000 | 7200 | Word traced as outlines from a font. |
| `text_xy.py` | 32000 | 320 | Word from a point table, at the lower sample rate. |
| `cat_outline_livescope_fw.py` | 512000 | 7200 | `cat_outline.py` that also streams. |
| `text_outline_livescope_fw.py` | 512000 | 7200 | `text_outline.py` that also streams. |
| `text_livescope_fw.py` | 32000 | 320 | `text_xy.py` that also streams. |
| `livescope_fw.py` | 32000 | 231 | The arc built cat, streaming. Not resampled, so the count is whatever the arcs produce. |
| `selftest_adc.py` | 32000 | 231 | Same arc built cat, then benchmarks the ADC read rate. |
| `cat_xy_pwm_legacy.py` | n/a | 231 | The first version, a `pwmio` loop with no DMA. Kept because the 20 to 40 Hz it manages is what motivated the DMA route. |

The files that stream sample GP26 and GP27 and push 2048 pair bursts over USB CDC
behind the marker `\xab\xcd\xef\x01`.

Host tools, run on the Mac:

| File | Purpose |
| --- | --- |
| `livescope.py` | Live viewer for the USB stream. `--headless` saves `live_capture.npy` instead of opening a window. |
| `outline_compare.py` | Measures a saved capture against the outline `cat_outline.py` intended to draw, and writes `outline_compare.png`. |
| `textgen.py` | Turns a word into the outline point tables, using PIL and potrace. |
| `scope_sim.py` | Simulates the RC filter to preview a path before flashing it. |

## Usage

Copy any firmware file to the board as `code.py`:

```
cp cat_xy.py /Volumes/CIRCUITPY/code.py
```

The board starts drawing as soon as it restarts, and keeps drawing without a
computer attached. USB is only needed for power, or for the stream produced by
`text_outline_livescope_fw.py`.

## How the drawing works

An oscilloscope in XY mode positions a single dot from two voltages. There is no
frame buffer, so a picture must be a single ordered list of points that the dot
visits in sequence. The dot cannot be blanked without a Z axis input, so moves
between disconnected shapes are drawn as visible lines. Paths are therefore built
as one closed circuit, and detours such as the whiskers are retraced along the
same line so the return stroke overlaps the outgoing one.

`audiopwmio.PWMAudioOut` is used as a DMA engine rather than for audio. Left
channel is X, right channel is Y, and `RawSample` holds the interleaved uint16
duty values. CircuitPython exposes no direct DMA API; this is the available route
to it.

Each path is resampled to evenly spaced points by `even_spaced_path()` before it
is played. The beam spends the same time on every point, so equal spacing keeps a
long stroke from appearing dimmer than a short one.

## Limits

- Point budget is set by the flicker threshold, not by memory. At 32 kHz, 640
  points is the maximum that stays above 50 Hz.
- Raising the sample rate requires a smaller capacitor. At 2.2 nF the filter
  supports 64 kHz, which doubles the point budget to 1280.
- At 512 kHz each point lasts 0.19 tau and the filter settles only 17.2 % of the
  way to it. That mode works because 7200 points sit close together along the
  path, not because the output reaches each coordinate.
- Resampling equalises brightness within one path but not between drawings, since
  each has its own ratio of path length to point count.
- `even_spaced_path()` is copied into every firmware that resamples, because each
  one has to run standalone as `code.py` with no shared module to import.

## Checking the output

`outline_compare.py` compares a capture against the path the firmware meant to
draw. Left is what was sent to GP2 and GP3, right is what came back through GP26
and GP27:

![Intended path beside the readback](outline_compare.png)

The steps on the right are the ADC, not the circuit: it keeps about one point in
(7200 / 630) = 11.4 and the viewer joins those with straight lines. The blunted
ear tips are the RC filter. `REPORT.md` section 6 works through both.

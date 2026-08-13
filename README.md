# Oscilloscope XY vector drawing on Raspberry Pi Pico 2

Draws a picture on an oscilloscope in XY mode using a Raspberry Pi Pico 2
(RP2350) running CircuitPython. Two PWM pins plus RC filters act as a two channel
DAC; the point stream is pushed by DMA, so the CPU is not involved in drawing.

Verified on Adafruit CircuitPython 10.2.1, board id `raspberry_pi_pico2`, with an
Owon SmartDS5032E.

`REPORT.md` is the full write up: theory, circuit, method and results.

## Circuit

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
roughly 500 mV/div to 1 V/div. The time base matters as much as the vertical
scale, because the instrument has to acquire fast enough to resolve consecutive
points; see `scope_undersampled.jpg` for what happens when it does not. The ADC
taps are optional and only used by `text_outline_livescope_fw.py`.

## Measured values

| Quantity | Value |
| --- | --- |
| RC time constant, `R * C` | 10.34 us |
| RC cutoff frequency | 15.4 kHz |
| Sample rate | 32000 points/s |
| Time per point | 31.25 us = 3.02 tau |
| Settling per point | 95.1 % |
| Path length | 231 points |
| Frame rate | 138.5 Hz |
| Point budget at 50 Hz | 640 points |
| X output, mean / min / max | 1.696 / 0.426 / 2.850 V |
| Y output, mean / min / max | 1.725 / 0.562 / 3.226 V |
| ADC sampling rate, list comprehension benchmark | 52206 pairs/s |
| ADC sampling rate, streaming firmware in practice | 43900 pairs/s |
| USB streaming throughput | about 144 kB/s, 18 frames/s |

Voltages were measured by the Pico reading its own outputs through GP26 and GP27.

These figures come from a 231 point path at 32 kHz. `cat_xy.py` as it stands
resamples to 400 points, which gives (32000 / 400) = 80 Hz at the same sample
rate.

## Files

| File | Sample rate | Output points | Purpose |
| --- | --- | --- | --- |
| `cat_xy.py` | 32000 | 400 | Cat drawn from arcs and lines built in code. |
| `cat_outline.py` | 512000 | 7200 | Cat traced as a closed outline from a point table. |
| `text_outline.py` | 512000 | 7200 | Word traced as outlines from a font. |
| `text_outline_livescope_fw.py` | 512000 | 7200 | Same as `text_outline.py`, plus it samples GP26/GP27 and streams 2048 pair bursts over USB CDC behind the marker `\xab\xcd\xef\x01`. |

All four run on the Pico. The Mac side tools that generated the point tables and
received the USB stream are not in this repository.

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
- `even_spaced_path()` is duplicated in every firmware file, because each has to
  run standalone on the board with no shared module to import.

## Images

| File | Shows |
| --- | --- |
| `schematic.png` | The two channel RC filter. |
| `scope_output.jpg` | `cat_xy.py` on the instrument at 125 kS/s. |
| `scope_undersampled.jpg` | The same board at 125 S/s, where the instrument keeps roughly one pair in 256 and the outline breaks into dots. |

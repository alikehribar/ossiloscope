# Oscilloscope XY vector drawing on Raspberry Pi Pico 2

Draws a picture on an analog oscilloscope in XY mode using a Raspberry Pi Pico 2
(RP2350) running CircuitPython. Two PWM pins plus RC filters act as a two channel
DAC; the point stream is pushed by DMA, so the CPU is not involved in drawing.

Verified on Adafruit CircuitPython 10.2.1, board id `raspberry_pi_pico2`.

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

The scope and ADC taps connect to the node between the resistor and the capacitor,
never to the GPIO side of the resistor.

Scope settings: XY mode, both channels DC coupled, 1 Mohm input impedance,
roughly 500 mV/div. The ADC taps are optional and only needed for the self test
and the live viewer.

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

## Files

| File | Runs on | Purpose |
| --- | --- | --- |
| `cat_xy.py` | Pico | Main firmware. Builds the path, plays it through DMA. Copy to `CIRCUITPY` as `code.py`. |
| `cat_xy_pwm_legacy.py` | Pico | Earlier version driving PWM from a Python loop. Kept for comparison; flickers at 20-40 Hz. |
| `selftest_adc.py` | Pico | Draws and prints 3000 ADC pairs as text. Used to verify wiring. |
| `livescope_fw.py` | Pico | Draws and streams ADC bursts as binary over USB for the live viewer. |
| `livescope.py` | Mac | Live matplotlib window fed by `livescope_fw.py`. `--headless` saves `live_capture.npy` instead. |
| `scope_sim.py` | Mac | Renders what the scope will show, including RC filter blur. Writes `sim_ideal.png` and `sim_filtered.png`. |

## Usage

Normal drawing:

```
cp cat_xy.py /Volumes/CIRCUITPY/code.py
```

Preview a shape before flashing:

```
python3 scope_sim.py
```

Live viewer, requires the GP26/GP27 taps:

```
cp livescope_fw.py /Volumes/CIRCUITPY/code.py
python3 livescope.py
```

`livescope.py` finds the serial port itself by globbing `/dev/cu.usbmodem*`.
macOS derives that name from the USB address the board enumerates on, so it
changes when the board is replugged or moved to another socket.

## How the drawing works

An oscilloscope in XY mode positions a single dot from two voltages. There is no
frame buffer, so a picture must be a single ordered list of points that the dot
visits in sequence. The dot cannot be blanked without a Z axis input, so moves
between disconnected shapes are drawn as visible lines. Paths are therefore built
as one closed circuit, and detours such as the whiskers are retraced along the same
line so the return stroke overlaps the outgoing one.

`audiopwmio.PWMAudioOut` is used as a DMA engine rather than for audio. Left channel
is X, right channel is Y, and `RawSample` holds the interleaved uint16 duty values.
CircuitPython exposes no direct DMA API; this is the available route to it.

## Limits

- Point budget is set by the flicker threshold, not by memory. At 32 kHz, 640 points
  is the maximum that stays above 50 Hz.
- Raising the sample rate requires a smaller capacitor. At 2.2 nF the filter supports
  64 kHz, which doubles the point budget to 1280.
- Point spacing is not uniform, so line brightness varies along the path. Resampling
  by arc length would correct this.
- The live viewer samples X and Y sequentially, about 9.6 us apart, which shears each
  reading by roughly 0.3 of a point.
# ossiloscope

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Headless: the plot is written to a PNG instead of shown
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(sys.path[0], '..', 'src')))

from PyQa40x.analyzer import Analyzer
from PyQa40x.wave_sine import WaveSine

#
# Hardware sanity check. Plays a different tone on each output and reports what
# arrives on each input, so you can tell at a glance whether the loopback cables
# are connected, whether left/right are swapped, and whether levels are calibrated.
#
# Expected wiring: L OUT -> L IN and R OUT -> R IN (single-ended BNC is fine).
#

LEFT_FREQ = 1000    # Hz, played on the left output
RIGHT_FREQ = 4500   # Hz, played on the right output. Not a harmonic of LEFT_FREQ, so crosstalk and distortion stay distinguishable
LEVEL_DBV = -10     # Level of both tones

analyzer = Analyzer()
params = analyzer.init(sample_rate=48000, max_input_level=6, max_output_level=8, fft_size=2**14, window_type="flattop")

left_dac = WaveSine(params).gen_sine_dbv(LEFT_FREQ, LEVEL_DBV)
right_dac = WaveSine(params).gen_sine_dbv(RIGHT_FREQ, LEVEL_DBV)

left_adc, right_adc = analyzer.send_receive(left_dac, right_dac)
analyzer.cleanup()


def dbv(volts_rms: float) -> float:
    return 20 * np.log10(max(volts_rms, 1e-12))


print()
print(f"Played {LEFT_FREQ} Hz on LEFT out and {RIGHT_FREQ} Hz on RIGHT out, both at {LEVEL_DBV} dBV")
print(f"{'Input':<7}{'RMS (time)':>12}{'Peak':>12}{f'@{LEFT_FREQ} Hz':>12}{f'@{RIGHT_FREQ} Hz':>12}")
results = {}
for name, wave in (("LEFT", left_adc), ("RIGHT", right_adc)):
    buf = wave.get_main_buffer()
    buf = buf - np.mean(buf)
    rms = dbv(np.sqrt(np.mean(buf ** 2)))
    peak = dbv(np.max(np.abs(buf)))
    at_left = wave.compute_rms_freq(LEFT_FREQ * 0.9, LEFT_FREQ * 1.1)
    at_right = wave.compute_rms_freq(RIGHT_FREQ * 0.9, RIGHT_FREQ * 1.1)
    results[name] = (at_left, at_right)
    print(f"{name:<7}{rms:>8.2f} dBV{peak:>8.2f} dBV{at_left:>8.2f} dBV{at_right:>8.2f} dBV")

print()
tol = 1.0  # dB
left_ok = abs(results["LEFT"][0] - LEVEL_DBV) < tol
right_ok = abs(results["RIGHT"][1] - LEVEL_DBV) < tol
left_swapped = abs(results["LEFT"][1] - LEVEL_DBV) < tol
right_swapped = abs(results["RIGHT"][0] - LEVEL_DBV) < tol
if left_ok and right_ok:
    print("PASS: both channels loop back at the expected level")
elif left_swapped and right_swapped:
    print("FAIL: channels are swapped (cables crossed, or the library has L/R reversed)")
elif max(max(v) for v in results.values()) < -80:
    print("FAIL: no signal on either input. Check the loopback cables, then suspect the output path")
else:
    print(f"FAIL: LEFT {'ok' if left_ok else 'bad'}, RIGHT {'ok' if right_ok else 'bad'}. See the table above")

fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for row, (name, wave) in enumerate((("LEFT", left_adc), ("RIGHT", right_adc))):
    axes[row][0].plot(wave.get_main_buffer()[:480])
    axes[row][0].set_title(f"{name} input, first 10 ms (V)")
    axes[row][0].grid(True)
    axes[row][1].semilogx(wave.get_frequency_array()[1:], wave.get_amplitude_array()[1:])
    axes[row][1].set_title(f"{name} input spectrum (dBV)")
    axes[row][1].set_xlim(20, 20000)
    axes[row][1].grid(True, which="both")
fig.tight_layout()
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loopback_check.png")
fig.savefig(out_path, dpi=100)
print(f"Plot written to {out_path}")

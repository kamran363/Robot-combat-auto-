#!/usr/bin/env python3
"""Build per-video SFX bed + commentary mix, normalized LOUD (peak -1 dB).
Usage: python3 build_audio.py v1|v2|v3
"""
import numpy as np, os, subprocess, sys
from scipy.signal import fftconvolve
from scipy.io import wavfile

SR = 44100
VID = '/home/hatch/workspace/robot-combat-auto/staging/2026-10-05/vid'
rng = np.random.default_rng(7)

def env(n, d):
    return np.exp(-np.arange(n) / (SR * d))

def crash(dur=1.6, g=1.0):
    n = int(SR * dur); tt = np.arange(n) / SR; y = np.zeros(n)
    for i, f in enumerate([523, 774, 1092, 1537, 2145, 3011]):
        y += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6.28)) * env(n, 0.25 + 0.12 * i) / (i + 1)
    nz = np.diff(rng.standard_normal(n), prepend=0) * env(n, 0.18)
    y = y + nz * 0.8
    m = int(SR * 0.08)
    y[:m] += np.sin(2 * np.pi * 90 * tt[:m]) * env(m, 0.03) * 1.5
    return y * g

def grind(dur=2.0, g=0.5):
    n = int(SR * dur); nz = rng.standard_normal(n)
    k = np.ones(int(SR * 0.02)) / int(SR * 0.02)
    sm = fftconvolve(nz, k, mode='same')
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * 13 * np.arange(n) / SR + 1)
    return sm * mod * env(n, dur * 0.7) * g

def boom(dur=2.5, g=1.2):
    n = int(SR * dur); nz = rng.standard_normal(n)
    k = np.ones(int(SR * 0.08)) / int(SR * 0.08)
    low = fftconvolve(nz, k, mode='same'); tt = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (70 - 40 * tt / dur) * tt) * env(n, 0.9)
    return (low * 1.2 + sub * 1.5) * env(n, 0.8) * g

def whir(dur=8.0, g=0.35):
    n = int(SR * dur); tt = np.arange(n) / SR
    f = 150 + (700 - 150) * (tt / dur) ** 1.5; ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) * 0.6 + np.sin(2 * ph) * 0.25 + rng.standard_normal(n) * 0.15)
    return y * np.minimum(1, tt / 1.5) * g

def rumble(dur, g=0.25):
    nz = rng.standard_normal(int(SR * dur)); k = np.ones(int(SR * 0.15)) / int(SR * 0.15)
    return fftconvolve(nz, k, mode='same') * g

def put(bed, y, ts):
    i = int(ts * SR)
    if i >= len(bed):
        return
    j = min(len(bed), i + len(y))
    bed[i:j] += y[:j - i]

def decode_mp3(path):
    """Decode mp3 to mono float32 @44100."""
    p = subprocess.run(['/usr/bin/ffmpeg', '-hide_banner', '-loglevel', 'error',
                        '-i', path, '-ar', str(SR), '-ac', '1', '-f', 'f32le', '-'],
                       capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f'decode failed for {path}: {p.stderr.decode()[:200]}')
    return np.frombuffer(p.stdout, dtype=np.float32)

# Timelines: impacts (crash/boom), grinds, whir windows, commentary placement
PLANS = {
    'v1': dict(
        dur=24.0,
        crashes=[7.6, 13.8, 19.7],
        grinds=[(7.9, 0.5), (13.0, 0.45), (19.0, 0.4), (21.5, 0.35)],
        booms=[19.7],
        whir=(0.0, 10.0),
        vox=[('v1_l1.mp3', 0.6), ('v1_l2.mp3', 3.2), ('v1_l3.mp3', 6.8),
             ('v1_l4.mp3', 12.6), ('v1_l5.mp3', 18.8), ('v1_l6.mp3', 23.0)],
    ),
    'v2': dict(
        dur=24.0,
        crashes=[7.4, 13.2, 20.2],
        grinds=[(7.8, 0.45), (12.8, 0.4), (18.5, 0.5), (21.0, 0.35)],
        booms=[7.4, 20.2],
        whir=(0.0, 24.0),  # drum screaming throughout
        vox=[('v2_l1.mp3', 0.6), ('v2_l2.mp3', 3.2), ('v2_l3.mp3', 7.0),
             ('v2_l4.mp3', 13.0), ('v2_l5.mp3', 18.7), ('v2_l6.mp3', 22.7)],
    ),
    'v3': dict(
        dur=24.0,
        crashes=[7.6, 13.8, 19.6],
        grinds=[(7.0, 0.5), (13.0, 0.45), (18.9, 0.4), (21.5, 0.35)],
        booms=[19.6],
        whir=None,
        vox=[('v3_l1.mp3', 0.6), ('v3_l2.mp3', 3.2), ('v3_l3.mp3', 7.0),
             ('v3_l4.mp3', 12.6), ('v3_l5.mp3', 18.8)],
    ),
}

which = sys.argv[1]
plan = PLANS[which]
DUR = plan['dur']; N = int(SR * DUR)

# 1) SFX bed
bed = np.zeros(N, dtype=np.float64)
bed += rumble(DUR, 0.20)
if plan['whir']:
    s, e = plan['whir']; w = whir(e - s, 0.38); put(bed, w, s)
for ts in plan['crashes']:
    put(bed, crash(1.8, 1.05), ts)
for ts, g in plan['grinds']:
    put(bed, grind(1.7, g), ts)
    put(bed, crash(0.5, 0.35), ts)
for ts in plan['booms']:
    put(bed, boom(2.6, 1.15), ts)

# 2) Commentary track (mono), each line boosted
vox = np.zeros(N, dtype=np.float64)
for fname, ts in plan['vox']:
    y = decode_mp3(os.path.join(VID, fname)).astype(np.float64) * 1.9
    put(vox, y, ts)

# 3) Mix: commentary on top, SFX slightly ducked under voice is not needed
#    since bed peaks are brief; scale bed to 0.75 relative to voice
mix = vox + bed * 0.85

# 4) Loudness: normalize to peak -1 dB (0.891)
peak = np.abs(mix).max()
mix = mix / max(1e-6, peak) * 0.891

st = np.stack([mix, np.roll(mix, int(SR * 0.008))], axis=1)
wavfile.write(os.path.join(VID, f'{which}_final.wav'), SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print(f'{which}: vox lines={len(plan["vox"])}, mix peak={np.abs(mix).max():.3f}, wrote {which}_final.wav')

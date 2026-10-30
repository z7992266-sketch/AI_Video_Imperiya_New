#!/usr/bin/env python3
"""Taqqos #8 audio bed: drone + kick + SFX (whoosh on every whip transition, impact on the flag collision
and every round win, ticking while counters run, fanfare at the end).
If tools/taqqos/sfx/*.mp3 (ElevenLabs SFX) exist they are used, otherwise synthesized fallbacks."""
import numpy as np, wave, sys, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from taqqos08 import INTRO, ROUNDS, TOTAL, ROUND_STARTS, ROUND_LENS, OUTRO_START, T_COLLIDE, T_DECIDE, COUNT0, COUNT_D

SR = 44100
N = int(TOTAL * SR) + SR // 2
t = np.arange(N) / SR
out = np.zeros(N)
rng = np.random.default_rng(1)

def add(sig, start, g=1.0):
    i = int(start * SR)
    if i < 0: sig = sig[-i:]; i = 0
    j = min(N, i + len(sig)); out[i:j] += g * sig[: j - i]

def env(n, a=0.005, r=0.2):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    e *= np.exp(-np.arange(n) / (r * SR)); return e

def load_sfx(name):
    p = os.path.join(HERE, "sfx", name + ".mp3")
    if not os.path.exists(p): return None
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float) / 32768
    return x / (np.abs(x).max() + 1e-9) * 0.8

# ---- synthesized fallbacks ----
def s_whoosh(d=0.35):
    n = int(d * SR); x = rng.standard_normal(n)
    x = np.convolve(x, np.ones(18) / 18, mode="same")
    f = np.linspace(0, 1, n); e = np.sin(np.pi * f ** 0.7) ** 2
    return x * e * 0.9
def s_impact():
    n = int(1.1 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (32 + 90 * np.exp(-tt * 9)) * tt) * env(n, 0.001, 0.32)
    s += rng.standard_normal(n) * env(n, 0.0005, 0.04) * 0.5
    return s * 0.9
def s_tick():
    n = int(0.025 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 2600 * tt) * env(n, 0.0003, 0.005) * 0.5
def s_ticks(d):
    x = np.zeros(int(d * SR) + 2000); k = 0.0; step = 0.045
    while k < d:
        i = int(k * SR); tk = s_tick(); x[i:i + len(tk)] += tk * (1 - 0.5 * k / d); k += step; step *= 1.06
    return x
def s_win():
    n = int(0.9 * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for k, f in enumerate([1046.5, 1568.0, 2093.0]):
        o = int(k * 0.05 * SR); m = n - o; tm = tt[:m]
        s[o:] += (np.sin(2 * np.pi * f * tm) + 0.4 * np.sin(4 * np.pi * f * tm)) * env(m, 0.002, 0.25)
    return s * 0.35
def s_fanfare():
    n = int(2.6 * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    notes = [(0.0, 523.3, 0.18), (0.18, 659.3, 0.18), (0.36, 784.0, 0.18), (0.56, 1046.5, 1.6)]
    for st, f, d in notes:
        o = int(st * SR); m = min(n - o, int((d + 0.6) * SR)); tm = tt[:m]
        saw = sum(np.sin(2 * np.pi * f * h * tm) / h for h in range(1, 7))
        s[o:o + m] += saw * env(m, 0.01, d * 0.8) * 0.25
    return s

SFX = {k: (load_sfx(k) if load_sfx(k) is not None else fb) for k, fb in
       [("whoosh", s_whoosh()), ("impact", s_impact()), ("win", s_win()), ("fanfare", s_fanfare())]}
TICK = load_sfx("tick")

# ---- bed: drone + heartbeat kick 110 bpm + hats ----
beat = 60 / 110
drone = 0.05 * (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t) + 0.3 * np.sin(2 * np.pi * 110 * t))
drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * t); out += drone
kn = int(0.25 * SR); kt = np.arange(kn) / SR
kick = np.sin(2 * np.pi * (45 + 80 * np.exp(-kt * 30)) * kt) * env(kn, 0.001, 0.08) * 0.4
for k, s in enumerate(np.arange(0, OUTRO_START, beat)): add(kick * (0.6 if k % 2 else 1.0), s)
hn = int(0.05 * SR); hat = rng.standard_normal(hn) * env(hn, 0.001, 0.012) * 0.05
for s in np.arange(beat / 2, OUTRO_START, beat): add(hat, s)

# ---- cues ----
add(SFX["whoosh"], 0.0, 0.7)                       # flags flying in
add(SFX["impact"], T_COLLIDE - 0.02, 1.0)          # collision
add(SFX["whoosh"], INTRO - 0.25, 0.8)              # whip into round 1
for i, s0 in enumerate(ROUND_STARTS):
    if i > 0: add(SFX["whoosh"], s0 - 0.22, 0.8)   # whip between rounds
    if TICK is not None:
        reps = int(np.ceil(COUNT_D * SR / len(TICK)))
        add(np.tile(TICK, reps)[: int(COUNT_D * SR)] * np.linspace(1, 0.4, int(COUNT_D * SR)), s0 + COUNT0, 0.5)
    else:
        add(s_ticks(COUNT_D), s0 + COUNT0, 0.8)
    add(SFX["impact"], s0 + T_DECIDE - 0.02, 0.55); add(SFX["win"], s0 + T_DECIDE, 0.7)
add(SFX["whoosh"], OUTRO_START - 0.22, 0.8)
add(SFX["impact"], OUTRO_START + 0.73, 1.0)        # G'OLIB stamp
add(SFX["fanfare"], OUTRO_START + 0.8, 0.9)

fo = int(0.8 * SR); out[-fo:] *= np.linspace(1, 0, fo)
out = out / (np.abs(out).max() + 1e-9) * 0.9
with wave.open(os.environ.get("AUDIO_OUT", "audio.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", TOTAL)

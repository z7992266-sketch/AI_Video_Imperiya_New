#!/usr/bin/env python3
"""Synthesized soundtrack: tense pulse bed + whoosh/tick/ding cues synced to render.py timing."""
import numpy as np, wave, sys
sys.path.insert(0, ".")
from taqqos04 import INTRO, ROUNDS, TOTAL, ROUND_STARTS, ROUND_LENS

SR = 44100
N = int(TOTAL * SR) + SR // 2
t = np.arange(N) / SR
out = np.zeros(N)

def add(sig, start):
    i = int(start * SR); j = min(N, i + len(sig)); out[i:j] += sig[: j - i]

def env(n, a=0.005, r=0.2):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    e *= np.exp(-np.arange(n) / (r * SR)); return e

# bed: drone (A minor) + heartbeat kick at 100 bpm
bpm = 100; beat = 60 / bpm
drone = 0.05 * (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t) + 0.3 * np.sin(2 * np.pi * 110 * t))
drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * t)
out += drone
kn = int(0.25 * SR); kt = np.arange(kn) / SR
kick = np.sin(2 * np.pi * (45 + 80 * np.exp(-kt * 30)) * kt) * env(kn, 0.001, 0.08) * 0.45
for k, s in enumerate(np.arange(0, TOTAL, beat)):
    add(kick * (0.6 if k % 2 else 1.0), s)
# hats on offbeats
rng = np.random.default_rng(1)
hn = int(0.05 * SR); hat = rng.standard_normal(hn) * env(hn, 0.001, 0.012) * 0.05
for s in np.arange(beat / 2, TOTAL, beat): add(hat, s)

def whoosh(d=0.45):
    n = int(d * SR); x = rng.standard_normal(n)
    x = np.convolve(x, np.ones(30) / 30, mode="same")
    e = np.sin(np.linspace(0, np.pi, n)) ** 2; return x * e * 0.35

def ding(f=1318.5, d=1.2):
    n = int(d * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2 * tt) + 0.25 * np.sin(2 * np.pi * f * 3.01 * tt)
    return s * env(n, 0.002, 0.35) * 0.22

def tick():
    n = int(0.03 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 2200 * tt) * env(n, 0.0005, 0.006) * 0.12

def impact():
    n = int(1.0 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (35 + 60 * np.exp(-tt * 8)) * tt) * env(n, 0.002, 0.35) * 0.7
    s += rng.standard_normal(n) * env(n, 0.001, 0.05) * 0.2
    return s

add(impact(), 0.5)  # VS hit
for i in range(len(ROUNDS)):
    s0 = ROUND_STARTS[i]
    add(whoosh(), s0 - 0.15)
    for k in np.arange(0.45, 2.4, 0.09): add(tick() * (1 - (k - 0.45) / 2.2), s0 + k)
    add(ding(), s0 + 2.6); add(ding(1975.5, 0.9) * 0.5, s0 + 2.62)
o0 = INTRO + sum(ROUND_LENS)
add(whoosh(0.6), o0 - 0.2); add(impact(), o0 + 0.1)
for k, f in enumerate([1046.5, 1318.5, 1568]): add(ding(f, 1.5) * 0.8, o0 + 0.3 + k * 0.12)

# fade out
fo = int(1.5 * SR); out[-fo:] *= np.linspace(1, 0, fo)
out = out / (np.abs(out).max() + 1e-9) * 0.85
pcm = (out * 32767).astype(np.int16)
with wave.open("audio.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", TOTAL)

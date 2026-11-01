"""Synthesised sound design (whooshes, taps, pops, printer, impacts) from an event list."""
import numpy as np, wave
SR = 44100
rng = np.random.default_rng(5)

def env(n, a=0.004, r=0.2):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    return e * np.exp(-np.arange(n) / (r * SR))

def lp(x, k=20):
    return np.convolve(x, np.ones(k) / k, mode='same')

def whoosh(d=0.5, up=True):
    n = int(d * SR); x = rng.standard_normal(n)
    x = lp(x, 14) - lp(x, 120)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    if up: e *= np.linspace(0.6, 1.2, n)
    return x * e * 0.55

def impact(d=1.4):
    n = int(d * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (32 + 70 * np.exp(-t * 7)) * t) * env(n, 0.002, 0.45) * 0.9
    s += lp(rng.standard_normal(n), 6) * env(n, 0.001, 0.06) * 0.35
    return s

def riser(d=1.2):
    n = int(d * SR); t = np.arange(n) / SR
    x = lp(rng.standard_normal(n), 8) * (t / d) ** 2 * 0.35
    x += np.sin(2 * np.pi * (200 + 900 * (t / d) ** 2) * t) * (t / d) ** 2 * 0.08
    return x

def tap():
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1800 * t) * 0.3 + lp(rng.standard_normal(n), 3) * 0.4) * env(n, 0.0005, 0.012)

def pop(f=900):
    n = int(0.12 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (f + 600 * np.exp(-t * 60)) * t) * env(n, 0.001, 0.03) * 0.45

def tick():
    n = int(0.025 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2600 * t) * env(n, 0.0005, 0.005) * 0.18

def ding(f=1318.5, d=1.2, v=0.3):
    n = int(d * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3.01 * f * t)
    return s * env(n, 0.002, 0.3) * v

def success():
    out = np.zeros(int(1.4 * SR))
    for k, f in enumerate([1046.5, 1318.5, 1568.0]):
        s = ding(f, 1.0, 0.18); i = int(k * 0.07 * SR); out[i:i + len(s)] += s
    return out

def printer(d=1.6):
    n = int(d * SR); t = np.arange(n) / SR
    buzz = np.sign(np.sin(2 * np.pi * 95 * t)) * 0.08 + lp(rng.standard_normal(n), 4) * 0.12
    am = 0.6 + 0.4 * (np.sin(2 * np.pi * 22 * t) > 0)
    e = np.ones(n); e[:400] = np.linspace(0, 1, 400); e[-2000:] = np.linspace(1, 0, 2000)
    return buzz * am * e

def coin():
    return ding(2093, 0.5, 0.18) + np.pad(ding(2637, 0.45, 0.14), (int(0.06 * SR), 0))[:int(0.5 * SR)]

def thud():
    n = int(0.3 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (70 + 120 * np.exp(-t * 30)) * t) * env(n, 0.001, 0.08) * 0.6

def blip(f=1500):
    n = int(0.08 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * env(n, 0.002, 0.03) * 0.15

def shimmer(d=1.5):
    out = np.zeros(int(d * SR))
    for k in range(10):
        f = 1500 + 300 * k
        s = ding(f, 0.6, 0.05); i = int(k * 0.06 * SR); out[i:i + len(s)] += s[:len(out) - i]
    return out

def glitch():
    n = int(0.18 * SR)
    x = np.sign(rng.standard_normal(n)) * 0.12
    x *= (np.arange(n) // 600) % 2
    return x * env(n, 0.001, 0.1)

LIB = dict(whoosh=whoosh, impact=impact, riser=riser, tap=tap, pop=pop, tick=tick, ding=lambda: ding(),
           success=success, printer=printer, coin=coin, thud=thud, blip=blip, shimmer=shimmer, glitch=glitch)

def render(events, total, path):
    out = np.zeros(int((total + 1) * SR))
    cache = {}
    for t, name, vol in events:
        if t < 0: continue
        if name not in cache:
            cache[name] = LIB[name]()
        s = cache[name] * vol
        i = int(t * SR); j = min(len(out), i + len(s))
        out[i:j] += s[:j - i]
    out = out[:int(total * SR)]
    peak = np.abs(out).max() + 1e-9
    out = out / peak * 0.8
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

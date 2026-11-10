"""Exclusive Vibe — original generative ambient music (sleep / relax / study).

Writes 16-bit stereo PCM to stdout (or a WAV file) chunk by chunk, so 1-3 hour tracks
use little memory. Every track is unique (seeded), composed from:
  * warm pad chords (detuned sines, slow swells, slow chord changes)
  * sparse soft "felt piano" notes from the current chord / pentatonic scale
  * optional ambience: rain, fire crackle, ocean waves
  * a long feedback-delay reverb
Usage: python music.py --minutes 60 --mood rain --seed 7 --out track.wav
"""
import argparse
import math
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi

SR = 44100
CHUNK = SR * 20  # 20 s per chunk

KEYS = {  # root midi notes
    'C': 48, 'D': 50, 'Eb': 51, 'F': 53, 'G': 55, 'A': 57, 'Bb': 58,
}
# progressions as scale-degree chords (semitones from root), gentle major/minor colours
PROGS = [
    [[0, 4, 7, 11], [9, 12, 16, 19], [2, 5, 9, 12], [5, 9, 12, 16]],      # I maj7 – vi – ii – IV
    [[0, 3, 7, 10], [5, 8, 12, 15], [-2, 2, 5, 9], [3, 7, 10, 14]],       # i m7 – iv – VII – III
    [[0, 4, 7, 14], [5, 9, 12, 16], [7, 11, 14, 17], [4, 7, 11, 14]],     # I add9 – IV – V – iii
    [[0, 7, 14, 16], [-3, 4, 9, 12], [5, 12, 16, 19], [2, 9, 14, 17]],    # open fifths, airy
]
PENTA_MAJ = [0, 2, 4, 7, 9]
PENTA_MIN = [0, 3, 5, 7, 10]


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


class Voice:
    def __init__(self, f, start, dur, amp, kind):
        self.f, self.start, self.dur, self.amp, self.kind = f, start, dur, amp, kind


def render(minutes, mood, seed, out):
    rng = np.random.default_rng(seed)
    total = int(minutes * 60 * SR)
    root = KEYS[rng.choice(list(KEYS))]
    prog = PROGS[rng.integers(len(PROGS))]
    minor = prog is PROGS[1]
    scale = PENTA_MIN if minor else PENTA_MAJ
    chord_len = float(rng.uniform(10, 16))  # seconds per chord
    bpm_gap = (2.2, 6.5)  # seconds between piano notes

    # --- schedule events for the whole track (cheap) ---
    pads = []
    t = 0.0
    i = 0
    while t < total / SR + chord_len:
        ch = prog[i % len(prog)]
        for k, iv in enumerate(ch):
            for octv, a in ((-12, 0.055), (0, 0.045), (12, 0.018)):
                pads.append(Voice(mtof(root + iv + octv), t - 2.0, chord_len + 4.0, a, 'pad'))
        t += chord_len
        i += 1
    notes = []
    t = float(rng.uniform(1, 4))
    while t < total / SR:
        ci = int(t // chord_len) % len(prog)
        pool = [root + 12 + x for x in prog[ci]] + [root + 24 + s for s in scale]
        m = int(rng.choice(pool))
        notes.append(Voice(mtof(m), t, 6.0, float(rng.uniform(0.06, 0.12)), 'pno'))
        if rng.random() < 0.25:  # soft two-note phrase
            m2 = int(rng.choice(pool))
            notes.append(Voice(mtof(m2), t + float(rng.uniform(0.4, 0.9)), 6.0, float(rng.uniform(0.04, 0.08)), 'pno'))
        t += float(rng.uniform(*bpm_gap))
    events = pads + notes
    events.sort(key=lambda v: v.start)

    # ambience filters (stateful across chunks)
    b_lp, a_lp = butter(2, 2800 / (SR / 2), 'low')
    b_hp, a_hp = butter(2, 350 / (SR / 2), 'high')
    zl = lfilter_zi(b_lp, a_lp) * 0
    zh = lfilter_zi(b_hp, a_hp) * 0
    b_pk, a_pk = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
    zp = np.zeros(3)
    b_lo, a_lo = butter(2, 400 / (SR / 2), 'low')
    zo = lfilter_zi(b_lo, a_lo) * 0

    # reverb: 4 feedback combs on a stereo bus (delay lines kept across chunks)
    comb_d = [int(SR * x) for x in (0.0297, 0.0371, 0.0411, 0.0437)]
    comb_g = 0.84
    hist = [np.zeros(d, dtype=np.float32) for d in comb_d]
    dly = int(SR * 0.37)
    echo = np.zeros(dly, dtype=np.float32)

    wf = wave.open(out, 'wb')
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)

    ei = 0
    active = []
    pos = 0
    while pos < total:
        n = min(CHUNK, total - pos)
        t0 = pos / SR
        tt = (np.arange(n) / SR + t0).astype(np.float64)
        dry = np.zeros(n, dtype=np.float64)
        while ei < len(events) and events[ei].start < t0 + n / SR:
            active.append(events[ei])
            ei += 1
        keep = []
        for v in active:
            s = max(v.start, t0)
            e = min(v.start + v.dur, t0 + n / SR)
            if e <= t0:
                continue
            keep.append(v)
            if s >= e:
                continue
            a = int((s - t0) * SR)
            b = int((e - t0) * SR)
            lt = tt[a:b] - v.start
            if v.kind == 'pad':
                env = np.sin(np.pi * np.clip(lt / v.dur, 0, 1)) ** 2
                lfo = 1 + 0.15 * np.sin(2 * np.pi * 0.07 * lt + v.f)
                sig = (np.sin(2 * np.pi * v.f * lt) + 0.6 * np.sin(2 * np.pi * v.f * 1.003 * lt)
                       + 0.4 * np.sin(2 * np.pi * v.f * 0.997 * lt))
                dry[a:b] += v.amp * env * lfo * sig
            else:
                env = np.exp(-lt / 1.6) * np.clip(lt / 0.012, 0, 1)
                sig = (np.sin(2 * np.pi * v.f * lt) + 0.35 * np.sin(2 * np.pi * 2 * v.f * lt) * np.exp(-lt / 0.6)
                       + 0.12 * np.sin(2 * np.pi * 3 * v.f * lt) * np.exp(-lt / 0.3))
                dry[a:b] += v.amp * env * sig
        active = [v for v in keep if v.start + v.dur > t0 + n / SR]

        # ambience
        amb = np.zeros(n)
        if mood in ('rain', 'storm'):
            noise = rng.standard_normal(n)
            r, zl = lfilter(b_lp, a_lp, noise, zi=zl)
            r, zh = lfilter(b_hp, a_hp, r, zi=zh)
            swell = 0.75 + 0.25 * np.sin(2 * np.pi * tt / 47.0)
            amb += 0.10 * r * swell
            drops = (rng.random(n) < 0.0009).astype(float) * rng.uniform(0.05, 0.2, n)
            amb += lfilter([1, -0.6], [1], drops) * 0.4
        if mood == 'fire':
            noise = rng.standard_normal(n)
            p, zp = lfilter(b_pk, a_pk, noise, zi=zp)
            amb += 0.12 * p
            cr = (rng.random(n) < 0.0004).astype(float) * rng.uniform(0.1, 0.5, n)
            amb += lfilter([1, -0.9], [1], cr) * 0.35
        if mood == 'ocean':
            noise = rng.standard_normal(n)
            o, zo = lfilter(b_lo, a_lo, noise, zi=zo)
            wave_env = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 9.0) ** 2
            amb += 0.35 * o * wave_env

        # reverb (combs) on music only
        wet = np.zeros(n, dtype=np.float32)
        x = dry.astype(np.float32)
        for ci2, d in enumerate(comb_d):
            buf = np.concatenate([hist[ci2], np.zeros(n, dtype=np.float32)])
            # y[k] = x[k] + g*y[k-d]  (block-recursive in steps of d)
            yv = np.zeros(n + d, dtype=np.float32)
            yv[:d] = buf[:d]
            for st in range(0, n, d):
                en = min(st + d, n)
                yv[d + st:d + en] = x[st:en] + comb_g * yv[st:en]
            hist[ci2] = yv[-d:].copy()
            wet += yv[d:]
        wet *= 0.12
        # long ping-pong echo
        ech = np.concatenate([echo, wet])
        left = dry + wet + 0.25 * ech[:n]
        right = dry + wet + 0.25 * ech[dly // 2: dly // 2 + n] if dly // 2 + n <= len(ech) else dry + wet
        echo = ech[-dly:].astype(np.float32)

        L = left + amb
        R = right + amb * 0.95
        # gentle fade in/out of the whole track
        fade = np.ones(n)
        fi = np.clip(tt / 8.0, 0, 1)
        fo = np.clip((total / SR - tt) / 10.0, 0, 1)
        fade = fi * fo
        st = np.stack([L * fade, R * fade], axis=1)
        st = np.tanh(st * 1.6) * 0.8  # soft limiter
        wf.writeframes((st * 32767).astype('<i2').tobytes())
        pos += n
        print(f'audio {pos / total * 100:5.1f}%', file=sys.stderr, flush=True)
    wf.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--minutes', type=float, default=60)
    ap.add_argument('--mood', default='rain', choices=['rain', 'storm', 'fire', 'ocean', 'none'])
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default='track.wav')
    a = ap.parse_args()
    render(a.minutes, a.mood, a.seed, a.out)

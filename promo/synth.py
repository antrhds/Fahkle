# Pure-python score for the 15s piece. 120 BPM, F minor. Writes audio.wav (48k stereo).
import math, random, struct, wave

SR = 48000
DUR = 15.0
N = int(SR * DUR)
L = [0.0] * N
Rr = [0.0] * N
SL = [0.0] * N  # reverb send
SR_ = [0.0] * N
rnd = random.Random(7)
TAU = math.tau
sin, exp = math.sin, math.exp


def add(i, l, r, send=0.0):
    if 0 <= i < N:
        L[i] += l; Rr[i] += r
        if send:
            SL[i] += l * send; SR_[i] += r * send


def note(f):  # midi -> hz
    return 440.0 * 2 ** ((f - 69) / 12)


def kick(t0, amp=1.0, low=42, top=150, dec=7.0, length=0.55):
    i0 = int(t0 * SR); ph = 0.0
    for k in range(int(length * SR)):
        t = k / SR
        f = low + top * exp(-t * 30)
        ph += TAU * f / SR
        v = sin(ph) * exp(-t * dec) * amp
        if k < 150:
            v += (rnd.random() * 2 - 1) * 0.5 * amp * (1 - k / 150)
        v = math.tanh(v * 1.6)
        add(i0 + k, v, v, 0.05)


def boom(t0, amp=1.0):
    kick(t0, amp * 1.1, low=30, top=90, dec=3.2, length=1.6)
    i0 = int(t0 * SR); lp = 0.0
    for k in range(int(1.2 * SR)):
        t = k / SR
        lp += (rnd.random() * 2 - 1 - lp) * 0.04
        v = lp * 2.2 * exp(-t * 4) * amp
        add(i0 + k, v, v, 0.5)


def clap(t0, amp=0.6, pan=0.0):
    i0 = int(t0 * SR); lp = 0.0
    for k in range(int(0.3 * SR)):
        t = k / SR
        n = rnd.random() * 2 - 1
        lp += (n - lp) * 0.25
        hp = n - lp
        env = exp(-t * 16) * (1.0 if t > 0.02 else (0.6 + 0.4 * ((k // 240) % 2)))
        v = (hp * 0.9 + sin(TAU * 185 * t) * 0.4 * exp(-t * 30)) * env * amp
        add(i0 + k, v * (1 - pan) , v * (1 + pan), 0.35)


def hat(t0, amp=0.18, pan=0.3, dec=70):
    i0 = int(t0 * SR); lp = 0.0
    for k in range(int(0.08 * SR)):
        t = k / SR
        n = rnd.random() * 2 - 1
        lp += (n - lp) * 0.5
        v = (n - lp) * exp(-t * dec) * amp
        add(i0 + k, v * (1 - pan), v * (1 + pan), 0.1)


def whoosh(t0, dur, amp=0.5, up=True, pan_from=-0.8, pan_to=0.8):
    i0 = int(t0 * SR); n_ = int(dur * SR); lp = 0.0; lp2 = 0.0
    for k in range(n_):
        x = k / n_
        c = (0.01 + 0.25 * x * x) if up else (0.26 - 0.25 * x)
        n = rnd.random() * 2 - 1
        lp += (n - lp) * c; lp2 += (lp - lp2) * c
        env = sin(math.pi * x) ** 2 if up is not None else 1
        env *= (x ** 1.5) if up else 1
        pan = pan_from + (pan_to - pan_from) * x
        v = lp2 * 3 * env * amp
        add(i0 + k, v * (1 - pan), v * (1 + pan), 0.4)


def riser(t0, dur, amp=0.35, f0=200, f1=1400):
    i0 = int(t0 * SR); n_ = int(dur * SR); ph = [0.0, 0.0, 0.0]; lp = 0.0
    for k in range(n_):
        x = k / n_
        f = f0 * (f1 / f0) ** (x ** 2)
        v = 0.0
        for j, dt in enumerate((1.0, 1.007, 0.993)):
            ph[j] += TAU * f * dt / SR
            v += ((ph[j] / TAU) % 1.0) * 2 - 1
        n = rnd.random() * 2 - 1
        lp += (n - lp) * (0.02 + 0.4 * x)
        v = (v * 0.18 + lp * 0.7) * (x ** 2.2) * amp
        s = sin(k / SR * TAU * 3) * 0.5
        add(i0 + k, v * (1 - s), v * (1 + s), 0.5)


def bell(t0, f, amp=0.25, pan=0.0, dec=2.2):
    i0 = int(t0 * SR)
    parts = ((1, 1.0, 1.0), (2.0, 0.5, 1.6), (2.76, 0.35, 2.3), (5.4, 0.18, 3.5), (8.93, 0.08, 5))
    for k in range(int(3.0 * SR)):
        t = k / SR
        v = 0.0
        for m, a, d in parts:
            v += sin(TAU * f * m * t) * a * exp(-t * dec * d)
        v *= amp * min(1.0, t * 800)
        add(i0 + k, v * (1 - pan), v * (1 + pan), 0.6)


def blip(t0, f, amp=0.22, pan=0.0):
    i0 = int(t0 * SR)
    for k in range(int(0.16 * SR)):
        t = k / SR
        ff = f if t < 0.05 else f * 1.335
        v = (sin(TAU * ff * t) + 0.3 * math.copysign(1, sin(TAU * ff * t))) * exp(-t * 18) * amp
        add(i0 + k, v * (1 - pan), v * (1 + pan), 0.3)


def saw_voice(f, t, detune=(1.0, 1.006, 0.994), harm=9):
    v = 0.0
    for d in detune:
        for h in range(1, harm + 1):
            v += sin(TAU * f * d * h * t + h) / h
    return v / len(detune)


def pad(t0, t1, notes, amp=0.08, att=0.3, rel=0.4, harm=7):
    i0 = int(t0 * SR); n_ = int((t1 - t0 + rel) * SR)
    fs = [note(m) for m in notes]
    for k in range(0, n_):
        t = k / SR
        env = min(1.0, t / att) * (1.0 if t < t1 - t0 else max(0.0, 1 - (t - (t1 - t0)) / rel))
        if env <= 0:
            continue
        v = 0.0
        for f in fs:
            v += saw_voice(f, t, harm=harm)
        v *= env * amp
        s = 0.25 * sin(t * 1.3)
        add(i0 + k, v * (1 - s), v * (1 + s), 0.45)


def bass(t0, m, dur=0.24, amp=0.34):
    i0 = int(t0 * SR); f = note(m)
    for k in range(int(dur * SR)):
        t = k / SR
        env = min(1.0, t * 400) * exp(-t * 5)
        v = sin(TAU * f * t) + 0.45 * sin(TAU * 2 * f * t) + 0.2 * sin(TAU * 3 * f * t)
        v = math.tanh(v * 1.4) * env * amp
        add(i0 + k, v, v)


def sad_trombone(t0):
    # descending, wobbling "fail" glide
    i0 = int(t0 * SR); ph = 0.0
    segs = [(0.0, 0.22, 64), (0.24, 0.46, 63), (0.48, 0.7, 62), (0.72, 1.3, 61)]
    for k in range(int(1.35 * SR)):
        t = k / SR
        m = None
        for a, b, mm in segs:
            if a <= t < b:
                m = mm; seg = (a, b)
        if m is None:
            continue
        f = note(m - 12)
        if m == 61:
            f *= 1 + 0.03 * sin(TAU * 7 * (t - 0.72)) * min(1, (t - 0.72) * 3)
            f *= 1 - 0.25 * max(0, (t - 1.0) / 0.3) ** 2
        ph += TAU * f / SR
        x = (t - seg[0]) / (seg[1] - seg[0])
        env = min(1, x * 20) * min(1, (1 - x) * 12)
        v = (((ph / TAU) % 1) * 2 - 1) * 0.5 + sin(ph) * 0.5
        v = math.tanh(v * 2) * env * 0.16
        add(i0 + k, v, v, 0.3)


def glitch(t0, t1, amp=0.2):
    i0 = int(t0 * SR); n_ = int((t1 - t0) * SR); f = 400; hold = 0; crush = 1
    for k in range(n_):
        if k % int(0.03 * SR) == 0:
            f = rnd.choice([110, 220, 330, 880, 1760, 60, 3520]); crush = rnd.choice([1, 8, 24, 60])
        if k % crush == 0:
            hold = (1 if sin(TAU * f * k / SR) > 0 else -1) * 0.5 + (rnd.random() * 2 - 1) * 0.5
        x = k / n_
        v = hold * amp * (1 - x) ** 0.5
        p = rnd.choice([-0.6, 0.6]) if k % 2400 == 0 else 0
        add(i0 + k, v, v * (0.7 if (k // 1200) % 2 else 1.0))


# ---------------- arrangement ----------------
B = 0.5  # beat
# intro: swell into the burst
pad(0.0, 1.0, [53, 60, 65], amp=0.035, att=0.8, rel=0.3)
riser(0.15, 0.85, amp=0.4, f0=120, f1=900)
blip(0.12, note(89), amp=0.08)
boom(1.0, 1.0); clap(1.0, 0.5); bell(1.0, note(84), 0.12, dec=1.5)
whoosh(1.0, 0.9, 0.35, up=False)

# section groove 2.0 - 7.5: F minor progression, 2s per chord
prog = [(41, [53, 56, 60]), (37, [49, 53, 56]), (44, [51, 56, 60]), (39, [51, 55, 58])]
for bar in range(3):
    t0 = 2.0 + bar * 2
    root, ch = prog[bar % 4]
    pad(t0, t0 + 2.0 if t0 + 2.0 <= 7.5 else 7.5, ch, amp=0.03, att=0.05, rel=0.2)
for i in range(int((7.5 - 2.0) / 0.25)):
    t = 2.0 + i * 0.25
    root = prog[int((t - 2.0) // 2) % 4][0]
    bass(t, root + (12 if i % 4 == 3 else 0), amp=0.26)
    if i % 2 == 1:
        hat(t, 0.13, pan=0.35 if i % 4 == 1 else -0.35)
for i in range(11):
    t = 2.0 + i * B
    if t < 7.5:
        kick(t, 0.9 if t != 2.0 else 1.0)
boom(2.0, 0.8)  # die lands
hat(2.0, 0.3, 0, 30)
# callout type-on ticks
for k in range(9):
    hat(2.4 + k * 0.035, 0.07, -0.5, 120); hat(2.65 + k * 0.035, 0.07, 0.5, 120)
blip(2.25, note(88), 0.07, -0.5); blip(2.5, note(91), 0.07, 0.5)
# split + ring
whoosh(3.05, 0.45, 0.4, up=True); clap(3.5, 0.55); bell(3.5, note(77), 0.1)
for i in range(6):
    blip(3.55 + i * 0.04, note(79 + [0, 3, 7, 10, 12, 15][i]), 0.07, -0.6 + i * 0.24)
clap(4.0, 0.35); clap(4.5, 0.45); clap(5.0, 0.35)
whoosh(4.95, 0.55, 0.55, up=True, pan_from=0.8, pan_to=-0.8)
# words
for t, ch in ((5.5, [65, 68, 72]), (6.0, [61, 65, 68]), (6.5, [63, 68, 72])):
    boom(t, 0.55); clap(t, 0.7)
    pad(t, t + 0.18, ch, amp=0.06, att=0.005, rel=0.15, harm=10)
    whoosh(t - 0.18, 0.2, 0.3, up=True)
for k in range(8):  # letter wave ticks on REPEAT
    hat(6.95 + k * 0.055, 0.1, -0.6 + k * 0.17, 90)
# pip transition
riser(7.2, 0.8, amp=0.45, f0=180, f1=2200)
whoosh(7.5, 0.5, 0.45, up=True)

# HOT DICE 8.0 - 10.0
kick(8.0, 1.0); boom(8.0, 0.5)
for i in range(6):
    tl = 8.0 + i * 0.09 + 0.32
    kick(tl, 0.35, low=70, top=200, dec=16, length=0.2)
    blip(tl, note(76 + [0, 2, 4, 7, 9, 12][i]), 0.13, -0.6 + i * 0.24)
for k in range(40):  # odometer rattle
    hat(8.4 + k * 0.018, 0.05, rnd.uniform(-0.4, 0.4), 150)
pad(8.0, 8.9, [53, 56, 60, 65], amp=0.03, att=0.1, rel=0.1)
riser(8.5, 0.5, amp=0.3, f0=300, f1=1800)
boom(9.0, 1.0); clap(9.0, 0.8)
pad(9.0, 9.95, [56, 60, 63, 68], amp=0.045, att=0.01, rel=0.05, harm=10)
bell(9.0, note(80), 0.12, -0.3); bell(9.08, note(84), 0.1, 0.3); bell(9.16, note(87), 0.09, 0)
for i in range(8):
    t = 9.0 + i * 0.125
    bass(t, 44 + (12 if i % 2 else 0), dur=0.12, amp=0.24)
    hat(t + 0.0625, 0.12, 0.3 if i % 2 else -0.3)
kick(9.5, 0.8); kick(9.75, 0.6)
riser(9.5, 0.5, amp=0.5, f0=400, f1=3000)

# FAHKLE 10.0
boom(10.0, 1.2); clap(10.0, 0.9)
glitch(10.0, 10.55, 0.22)
glitch(10.72, 10.8, 0.15)
kick(10.12, 1.0, low=36, top=80, dec=5, length=0.6)
sad_trombone(10.3)

# resolve
whoosh(10.75, 1.4, 0.35, up=True, pan_from=-0.9, pan_to=0.9)
riser(11.3, 1.2, amp=0.35, f0=150, f1=1600)
# particle sparkle arpeggio as the dots land
arp = [65, 68, 72, 77, 80, 84, 89]
for i in range(14):
    blip(11.35 + i * 0.07, note(arp[i % 7] + (12 if i >= 7 else 0)), 0.05, -0.8 + i * 0.12)
# logo hit
boom(12.5, 1.1); clap(12.5, 0.5)
pad(12.5, 14.6, [41, 53, 60, 65, 68, 72], amp=0.035, att=0.02, rel=0.5, harm=8)
bell(12.5, note(77), 0.16, -0.2, dec=0.9); bell(12.5, note(84), 0.12, 0.2, dec=0.9)
bell(13.0, note(80), 0.08, -0.4, dec=1.1); bell(13.12, note(84), 0.08, 0.0, dec=1.1); bell(13.24, note(89), 0.08, 0.4, dec=1.1)
blip(13.45, note(96), 0.05)
kick(14.2, 0.35, low=80, top=220, dec=18, length=0.2); blip(14.62, note(89), 0.08); bell(14.62, note(96), 0.05)

# ---------------- reverb (Schroeder) ----------------
def reverb(x, combs, aps):
    out = [0.0] * N
    for d, g in combs:
        buf = [0.0] * d; j = 0; lp = 0.0
        for i in range(N):
            y = buf[j]
            lp = y * 0.6 + lp * 0.4
            buf[j] = x[i] + lp * g
            out[i] += y
            j += 1
            if j == d: j = 0
    for d, g in aps:
        buf = [0.0] * d; j = 0
        for i in range(N):
            b = buf[j]; v = out[i]
            y = -g * v + b
            buf[j] = v + g * y
            out[i] = y
            j += 1
            if j == d: j = 0
    return out

revL = reverb(SL, [(1557, .84), (1617, .84), (1491, .84), (1422, .84)], [(225, .5), (556, .5)])
revR = reverb(SR_, [(1580, .84), (1640, .84), (1514, .84), (1445, .84)], [(248, .5), (579, .5)])

# ---------------- master ----------------
fade_i = int(14.75 * SR)
peak = 0.0
outL = [0.0] * N; outR = [0.0] * N
for i in range(N):
    l = L[i] + revL[i] * 0.22
    r = Rr[i] + revR[i] * 0.22
    g = 1.0
    if i > fade_i:
        g = max(0.0, 1 - (i - fade_i) / (N - fade_i)) ** 1.5
    if i < 400:
        g *= i / 400
    l = math.tanh(l * 1.1) * g; r = math.tanh(r * 1.1) * g
    outL[i] = l; outR[i] = r
    peak = max(peak, abs(l), abs(r))
norm = 0.89 / peak
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    frames = bytearray()
    for i in range(N):
        frames += struct.pack('<hh', int(outL[i] * norm * 32767), int(outR[i] * norm * 32767))
    w.writeframes(bytes(frames))
print('peak', peak)

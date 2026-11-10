#!/usr/bin/env python3
"""JOSEPH PONNAR intro: beat-synced 16:9 montage + fire reveal + title.
Usage: make_intro.py OUT.mp4 [scale]   (scale 1.0 = 3840x2160)"""
import sys, glob, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

U = '/root/.claude/uploads/ac76fd70-c0d5-563d-85d6-06df4815d492/'
SCR = '/tmp/claude-0/-home-user-SUNIE-T-SUNNY/ac76fd70-c0d5-563d-85d6-06df4815d492/scratchpad/'
SRC = {k: glob.glob(U + k + '*')[0] for k in ['002a', 'f47c', 'c953', '8e0a']}
SONG = glob.glob(U + '6f521d79*')[0]
OUT = sys.argv[1]
SCALE = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
W, H = int(3840 * SCALE) // 2 * 2, int(2160 * SCALE) // 2 * 2
FPS = 30
END = 48.75

# ---- beat grid (114 BPM, measured from the song) ----
P = 60 / 114.0
PH = 0.29
def beat(k): return PH + k * P
def bar(n): return beat(2 + 4 * n)       # downbeats: 1.34, 3.44, 5.55 ...

def ease(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)

# Shot list: (src, out_start, out_end, src_start, speed, box0, box1, trans)
# box = (cx, cy, w) in source pixels; height = w*9/16. trans: 'flash' | 'fade' | 'none'
shots = []
def S(src, a, b, ss, box0, box1, trans='flash', speed=1.0):
    shots.append(dict(src=src, a=a, b=b, ss=ss, sp=speed, b0=box0, b1=box1, tr=trans))

# Intro (energetic)
S('f47c', 0.0, bar(1), 0.0, (360, 420, 720), (380, 760, 640), 'none', 0.95)   # comet -> tilt down to lion
S('f47c', bar(1), bar(2), 4.0, (470, 700, 460), (500, 660, 380))             # lion head push-in
S('002a', bar(2), bar(3), 0.2, (360, 830, 720), (360, 820, 640))             # walking wide
S('002a', bar(3), bar(4), 4.0, (360, 640, 720), (380, 640, 600))             # charge
S('002a', bar(4), bar(5), 7.0, (360, 650, 720), (340, 650, 620))             # running close
S('002a', bar(5), bar(6), 10.0, (360, 760, 720), (360, 760, 620))            # low run
# Calm section (2-bar shots, soft crossfades)
S('002a', bar(6), bar(8), 14.0, (360, 330, 720), (360, 780, 720), 'fade')    # aurora tilt down to lion
S('002a', bar(8), bar(10), 19.9, (360, 860, 720), (360, 860, 600), 'fade')   # running through trees
S('002a', bar(10), bar(12), 23.7, (360, 860, 720), (380, 860, 620), 'fade')
S('002a', bar(12), bar(14), 28.4, (360, 560, 720), (360, 600, 460), 'fade')  # lion on branch push-in
S('c953', bar(14), bar(15), 0.0, (360, 470, 640), (360, 470, 520), 'fade')   # lion face (crop above caption)
# Drop: cut on every beat
t0 = bar(15)
S('c953', t0, beat(63), 4.5, (360, 450, 470), (360, 450, 420))
S('002a', beat(63), beat(64), 5.0, (380, 640, 560), (380, 640, 500))
S('f47c', beat(64), beat(65), 8.0, (500, 680, 420), (500, 680, 380))
S('002a', beat(65), bar(16), 33.0, (360, 480, 560), (360, 480, 470))
# Fire reveal (logo template, only the part before its placeholder text)
FIRE_A = bar(16)            # 35.02
FIRE_SP = 0.88
FIRE_SRC_END = 4.4   # placeholder logo starts appearing at ~4.6s
FIRE_FREEZE = FIRE_A + FIRE_SRC_END / FIRE_SP
S('8e0a', FIRE_A, END + 0.1, 0.0, (368, 207, 736), (368, 207, 736), 'none', FIRE_SP)
T_JOSEPH = bar(19)          # 41.33  title hit 1
T_PONNAR = beat(80)         # 42.38  title hit 2
T_SWEEP = bar(20)           # 43.44  light sweep
FADE_OUT = 47.3

cuts_flash = [s['a'] for s in shots if s['tr'] == 'flash']
cuts_fade = [s['a'] for s in shots if s['tr'] == 'fade']
XF = 0.35  # crossfade length (ends on the beat)

# ---- source frame loading ----
_cache = {}
def load(src, t_from, t_to):
    key = (src, round(t_from, 3), round(t_to, 3))
    if key in _cache: return _cache[key]
    info = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                           'stream=width,height,r_frame_rate', '-of', 'csv=p=0', SRC[src]],
                          capture_output=True, text=True).stdout.strip().split(',')
    w, h = int(info[0]), int(info[1]); num, den = map(int, info[2].split('/')); fr = num / den
    a = max(0, t_from - 0.2)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{a:.3f}', '-i', SRC[src], '-t', f'{t_to - a + 0.4:.3f}',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    arr = np.frombuffer(raw[:n * w * h * 3], np.uint8).reshape(n, h, w, 3)
    frames = [Image.fromarray(f) for f in arr]
    if len(_cache) >= 3: _cache.pop(next(iter(_cache)))
    _cache[key] = (frames, a, fr)
    return _cache[key]

def shot_frame(s, t, extra_zoom=1.0):
    src_t = s['ss'] + (t - s['a']) * s['sp']
    if s['src'] == '8e0a': src_t = min(src_t, FIRE_SRC_END)
    dur = (s['b'] - s['a']) * s['sp']
    frames, a, fr = load(s['src'], s['ss'], s['ss'] + dur + 0.1)
    i = int(round((src_t - a) * fr)); i = min(max(i, 0), len(frames) - 1)
    img = frames[i]
    u = ease((t - s['a']) / max(s['b'] - s['a'], 1e-6))
    if s['src'] == '8e0a':
        # after freeze: slow push-in on the clean smoke frame
        u = 0; fz = max(0, t - FIRE_FREEZE)
        extra_zoom *= 1.0 + 0.012 * fz
    cx = s['b0'][0] + (s['b1'][0] - s['b0'][0]) * u
    cy = s['b0'][1] + (s['b1'][1] - s['b0'][1]) * u
    bw = (s['b0'][2] + (s['b1'][2] - s['b0'][2]) * u) / extra_zoom
    bh = bw * 9 / 16
    sw, sh = img.size
    cx = min(max(cx, bw / 2), sw - bw / 2); cy = min(max(cy, bh / 2), sh - bh / 2)
    # keep away from bottom watermarks / captions
    limit = {'002a': 1120, 'f47c': 1090, 'c953': 672, '8e0a': sh}[s['src']]
    cy = min(cy, limit - bh / 2)
    box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    return img.resize((W, H), Image.LANCZOS, box=box)

# ---- title layer ----
def make_title():
    font = ImageFont.truetype(SCR + 'fonts/Anton.ttf', int(500 * SCALE))
    words = ['JOSEPH', 'PONNAR']
    gap = int(110 * SCALE)
    tmp = ImageDraw.Draw(Image.new('L', (10, 10)))
    bbs = [tmp.textbbox((0, 0), w, font=font) for w in words]
    ws = [b[2] - b[0] for b in bbs]
    total = sum(ws) + gap
    x0 = (W - total) // 2
    th = max(b[3] - b[1] for b in bbs)
    y0 = (H - th) // 2 - bbs[0][1]
    layers = []
    x = x0
    for word, bb, ww in zip(words, bbs, ws):
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).text((x - bb[0], y0), word, font=font, fill=255)
        layers.append(m); x += ww + gap
    # metallic gold gradient fill
    ys = np.linspace(0, 1, H)[:, None]
    top, mid, bot = np.array([255, 246, 220]), np.array([255, 205, 120]), np.array([170, 96, 30])
    tb = (y0 + bbs[0][1]) / H; bt = (y0 + bbs[0][1] + th) / H
    v = np.clip((ys - tb) / (bt - tb), 0, 1)
    col = np.where(v < 0.5, top + (mid - top) * (v / 0.5), mid + (bot - mid) * ((v - 0.5) / 0.5))
    col = np.repeat(col[:, None, :], W, 1).reshape(H, W, 3).astype(np.uint8)
    grad = Image.fromarray(col)
    out = []
    for m in layers:
        edge = m.filter(ImageFilter.MaxFilter(5)) if SCALE >= 0.5 else m
        rgba = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        # glow
        glow = m.filter(ImageFilter.GaussianBlur(40 * SCALE))
        g = Image.new('RGBA', (W, H), (255, 120, 20, 0)); g.putalpha(glow.point(lambda p: int(p * 0.85)))
        rgba = Image.alpha_composite(rgba, g)
        # shadow/outline
        o = Image.new('RGBA', (W, H), (25, 10, 0, 0)); o.putalpha(edge)
        rgba = Image.alpha_composite(rgba, o)
        f = grad.convert('RGBA'); f.putalpha(m)
        rgba = Image.alpha_composite(rgba, f)
        out.append((rgba, m))
    bbox = (x0, y0 + bbs[0][1], x0 + total, y0 + bbs[0][1] + th)
    return out, bbox

TITLE, TBOX = make_title()

def scaled(layer, s):
    if abs(s - 1) < 1e-3: return layer
    nw, nh = int(W * s), int(H * s)
    big = layer.resize((nw, nh), Image.BILINEAR)
    l = (nw - W) // 2; t = (nh - H) // 2
    if s >= 1: return big.crop((l, t, l + W, t + H))
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0)); c.paste(big, (-l, -t)); return c

def title_comp(frame, t):
    hits = [T_JOSEPH, T_PONNAR]
    img = frame.convert('RGBA')
    for (layer, mask), th in zip(TITLE, hits):
        if t < th: continue
        d = t - th
        u = ease(d / 0.22)
        s = 1.35 - 0.35 * u + 0.008 * max(0, t - T_PONNAR)   # slam + slow push-in
        a = min(1.0, d / 0.12)
        L = scaled(layer, s)
        if a < 1: L.putalpha(L.getchannel('A').point(lambda p: int(p * a)))
        img = Image.alpha_composite(img, L)
    # light sweep across the letters
    if T_SWEEP <= t <= T_SWEEP + 1.2:
        u = (t - T_SWEEP) / 1.2
        x0, y0, x1, y1 = TBOX
        cx = x0 - 400 * SCALE + (x1 - x0 + 800 * SCALE) * u
        band = Image.new('L', (W, H), 0)
        bw = 160 * SCALE
        ImageDraw.Draw(band).polygon([(cx - bw, y1), (cx, y1), (cx + 300 * SCALE, y0), (cx + 300 * SCALE - bw, y0)], fill=230)
        band = band.filter(ImageFilter.GaussianBlur(30 * SCALE))
        mask = ImageChops.lighter(TITLE[0][1], TITLE[1][1])
        band = ImageChops.multiply(band, mask)
        wl = Image.new('RGBA', (W, H), (255, 255, 255, 0)); wl.putalpha(band)
        img = Image.alpha_composite(img, wl)
    return img.convert('RGB')

# drifting embers so the held smoke frame stays alive
_rng = np.random.default_rng(7)
EMB = [(_rng.uniform(0, 1), _rng.uniform(0, 1), _rng.uniform(0.02, 0.07), _rng.uniform(1.5, 5), _rng.uniform(0, 6.28))
       for _ in range(140)]
def embers(img, t):
    d = t - (FIRE_FREEZE - 0.3)
    a = min(1, d / 0.6)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    for x, y, v, r, ph in EMB:
        yy = (y - v * d) % 1.0
        xx = x + 0.01 * math.sin(ph + d * 1.3)
        rr = r * SCALE * 2
        al = int(255 * a * (0.5 + 0.5 * math.sin(ph + d * 4)) * min(1, yy * 3))
        dr.ellipse([xx * W - rr, yy * H - rr, xx * W + rr, yy * H + rr], fill=(255, 170, 70, al))
    lay = Image.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3 * SCALE)), lay)
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

# ---- render loop ----
def active(t):
    for s in shots:
        if s['a'] <= t < s['b']: return s
    return shots[-1]

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y',
    '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-i', SONG,
    '-filter_complex',
    f"[0:v]unsharp=5:5:0.6:5:5:0.0,eq=contrast=1.06:saturation=1.08:gamma=0.98,vignette=angle=PI/5,"
    f"noise=alls=5:allf=t,format=yuv420p[v];"
    f"[1:a]atrim=0:{END},afade=t=in:st=0:d=0.3,afade=t=out:st={FADE_OUT - 0.3}:d={END - FADE_OUT + 0.3}[a]",
    '-map', '[v]', '-map', '[a]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-profile:v', 'high', '-level', '5.2',
    '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', '-shortest', OUT], stdin=subprocess.PIPE)

N = int(END * FPS)
for fi in range(N):
    t = fi / FPS
    s = active(t)
    # zoom punch after hard cuts / title hits
    punch = 1.0
    for c in cuts_flash + [T_JOSEPH, T_PONNAR]:
        if 0 <= t - c < 0.3: punch = max(punch, 1.0 + 0.06 * (1 - ease((t - c) / 0.3)))
    img = shot_frame(s, t, punch)
    # crossfade into 'fade' shots (prev shot continues past its end)
    idx = shots.index(s)
    if idx + 1 < len(shots) and shots[idx + 1]['tr'] == 'fade' and t > shots[idx + 1]['a'] - XF:
        nxt = shots[idx + 1]
        al = ease((t - (nxt['a'] - XF)) / XF)
        img = Image.blend(img, shot_frame(nxt, max(t, nxt['a']), 1.0), al)
    if s['src'] == '8e0a' and t > FIRE_FREEZE - 0.5:
        # darken the smoke a bit so the title pops
        k = 1 - 0.25 * ease((t - FIRE_FREEZE + 0.5) / 1.0)
        img = Image.eval(img, lambda p, k=k: int(p * k))
    if s['src'] == '8e0a' and t > FIRE_FREEZE - 0.3:
        img = embers(img, t)
    if t >= T_JOSEPH:
        img = title_comp(img, t)
    arr = np.asarray(img)
    # white flash on beat cuts and title hits
    fl = 0.0
    for c in cuts_flash:
        if 0 <= t - c < 0.2: fl = max(fl, 0.45 * (1 - (t - c) / 0.2))
    for c in [T_JOSEPH, T_PONNAR]:
        if 0 <= t - c < 0.35: fl = max(fl, 0.8 * (1 - (t - c) / 0.35))
    fade = 1.0
    if t < 0.6: fade = ease(t / 0.6)
    if t > FADE_OUT: fade = 1 - ease((t - FADE_OUT) / (END - FADE_OUT))
    if fl > 0 or fade < 1:
        a = arr.astype(np.float32)
        a = a + (255 - a) * fl
        a *= fade
        arr = a.clip(0, 255).astype(np.uint8)
    enc.stdin.write(arr.tobytes())
    if fi % 60 == 0: print(f'{t:5.1f}s / {END}', flush=True)
enc.stdin.close(); enc.wait()
print('done', OUT)

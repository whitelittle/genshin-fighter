"""Pixel-art -> client rectangles.

The client can only draw pooled image controls (rect / ellipse / triangle ...), so every
sprite becomes a list of axis-aligned rectangles drawn back to front. Two steps:

1. quantize(): k-means in OKLab with per-pixel weights (alpha, local contrast) so small
   but important colours (eyes, outlines, element glow) survive; palettes can be shared
   by all poses of one character, which keeps colour writes equal between poses.
2. painter(): colours are layered from most to least common; a layer's rectangles may
   cover pixels of layers drawn later (they get painted over) but never transparent
   pixels. Greedy: from the first uncovered pixel, try several maximal expansions and
   keep the one that covers the most uncovered pixels of that colour.

Everything here is offline (numpy + Pillow); nothing in this file runs in the game.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

# ------------------------------------------------------------------ colour space

def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255.0


def rgb_to_oklab(rgb):
    lin = srgb_to_linear(np.asarray(rgb, dtype=np.float64))
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(np.maximum(lin @ m1.T, 0))
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return lms @ m2.T


def oklab_to_rgb(lab):
    m2i = np.array([[1.0, 0.3963377774, 0.2158037573],
                    [1.0, -0.1055613458, -0.0638541728],
                    [1.0, -0.0894841775, -1.2914855480]])
    lms = (np.asarray(lab) @ m2i.T) ** 3
    m1i = np.array([[4.0767416621, -3.3077115913, 0.2309699292],
                    [-1.2684380046, 2.6097574011, -0.3413193965],
                    [-0.0041960863, -0.7034186147, 1.7076147010]])
    return linear_to_srgb(lms @ m1i.T)


# ------------------------------------------------------------------ resampling

def load_rgba(path):
    return Image.open(path).convert('RGBA')


def downscale(im: Image.Image, scale: float) -> Image.Image:
    """Area-average downscale on premultiplied colour, then re-threshold alpha."""
    if abs(scale - 1.0) < 1e-6:
        return im
    w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    a = np.asarray(im, dtype=np.float64)
    pm = a.copy()
    pm[..., :3] *= pm[..., 3:4] / 255.0
    pim = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), 'RGBA')
    small = np.asarray(pim.resize((w, h), Image.BOX), dtype=np.float64)
    alpha = small[..., 3:4]
    rgb = np.where(alpha > 0, small[..., :3] * 255.0 / np.maximum(alpha, 1), 0)
    out = np.concatenate([rgb, alpha], axis=2)
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), 'RGBA')


# ------------------------------------------------------------------ quantization

def _weights(rgba):
    """Per-pixel importance: opaque pixels, boosted where local contrast is high (edges,
    eyes, highlights) so k-means spends colours there instead of on large gradients."""
    a = rgba[..., 3] / 255.0
    lab = rgb_to_oklab(rgba[..., :3].reshape(-1, 3)).reshape(rgba.shape[0], rgba.shape[1], 3)
    L = lab[..., 0]
    pad = np.pad(L, 1, mode='edge')
    g = np.zeros_like(L)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                g = np.maximum(g, np.abs(pad[1 + dy:1 + dy + L.shape[0], 1 + dx:1 + dx + L.shape[1]] - L))
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    w = a * (1.0 + 6.0 * g + 2.0 * chroma)
    return lab, w


def kmeans_palette(samples_lab, weights, k, iters=24, seed=1):
    """Weighted k-means++ in OKLab. Returns k centres (Lab)."""
    rng = np.random.default_rng(seed)
    X, W = samples_lab, weights
    if len(X) <= k:
        return X.copy()
    p = W / W.sum()
    centres = [X[rng.choice(len(X), p=p)]]
    d2 = ((X - centres[0]) ** 2).sum(1)
    for _ in range(1, k):
        q = W * d2
        if q.sum() <= 0:
            break
        centres.append(X[rng.choice(len(X), p=q / q.sum())])
        d2 = np.minimum(d2, ((X - centres[-1]) ** 2).sum(1))
    C = np.array(centres)
    for _ in range(iters):
        lab_d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(2)
        lab_i = lab_d.argmin(1)
        newC = C.copy()
        for j in range(len(C)):
            m = lab_i == j
            if m.any():
                newC[j] = (X[m] * W[m, None]).sum(0) / W[m].sum()
        if np.allclose(newC, C, atol=1e-5):
            C = newC
            break
        C = newC
    return C


def build_palette(images, k, seed=1):
    """One palette for several RGBA images (all poses of a character)."""
    labs, ws = [], []
    for im in images:
        rgba = np.asarray(im, dtype=np.float64)
        lab, w = _weights(rgba)
        m = rgba[..., 3] >= 128
        labs.append(lab[m])
        ws.append(w[m])
    X = np.concatenate(labs)
    W = np.concatenate(ws)
    # sub-sample for speed; weights keep the important pixels
    if len(X) > 40000:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(X), 40000, replace=False, p=W / W.sum())
        X, W = X[idx], np.ones(40000)
    C = kmeans_palette(X, W, k, seed=seed)
    rgb = np.clip(np.round(oklab_to_rgb(C)), 0, 255).astype(int)
    # merge duplicates after rounding
    uniq = []
    for c in rgb.tolist():
        if c not in uniq:
            uniq.append(c)
    return uniq


def apply_palette(im, palette, alpha_cut=128):
    rgba = np.asarray(im, dtype=np.float64)
    lab = rgb_to_oklab(rgba[..., :3].reshape(-1, 3))
    P = rgb_to_oklab(np.array(palette, dtype=np.float64))
    d = ((lab[:, None, :] - P[None, :, :]) ** 2).sum(2)
    idx = d.argmin(1).reshape(rgba.shape[0], rgba.shape[1]).astype(np.int32)
    idx[rgba[..., 3] < alpha_cut] = -1
    return idx


def despeckle(idx, passes=1):
    """Replace single pixels whose 4 neighbours agree on another colour (dither noise)."""
    out = idx.copy()
    H, W = idx.shape
    for _ in range(passes):
        p = np.pad(out, 1, constant_values=-2)
        up, dn, lf, rt = p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]
        same = (up == dn) & (dn == lf) & (lf == rt) & (up >= 0) & (out >= 0) & (out != up)
        out = np.where(same, up, out)
    return out


# ------------------------------------------------------------------ rectangles

def painter(idx, order=None):
    """idx: HxW palette indices (-1 transparent). Returns [(x, y, w, h, colour)] back to front.
    order: colour layering bottom -> top (default: by pixel count in this image). Sharing one
    order between the poses of a character keeps rect i's colour mostly equal across poses."""
    H, W = idx.shape
    cols, counts = np.unique(idx[idx >= 0], return_counts=True)
    if order is None:
        order = cols[np.argsort(-counts, kind='stable')]
    else:
        present = set(cols.tolist())
        order = [c for c in order if c in present]
    rank = np.full(idx.shape, -1, dtype=np.int32)
    for i, c in enumerate(order):
        rank[idx == c] = i
    rects = []
    for li, c in enumerate(order):
        allowed = rank >= li
        need = rank == li
        while True:
            ys, xs = np.nonzero(need)
            if len(ys) == 0:
                break
            y, x = int(ys[0]), int(xs[0])
            best = None
            for mode in range(4):
                if mode in (0, 2):              # grow right then down (mode 2 also left)
                    x0 = x
                    if mode == 2:
                        while x0 - 1 >= 0 and allowed[y, x0 - 1]:
                            x0 -= 1
                    x1 = x
                    while x1 + 1 < W and allowed[y, x1 + 1]:
                        x1 += 1
                    y1 = y
                    while y1 + 1 < H and allowed[y1 + 1, x0:x1 + 1].all():
                        y1 += 1
                    y0 = y
                else:                           # grow down then right (mode 3 also left)
                    y1 = y
                    while y1 + 1 < H and allowed[y1 + 1, x]:
                        y1 += 1
                    x0 = x
                    if mode == 3:
                        while x0 - 1 >= 0 and allowed[y:y1 + 1, x0 - 1].all():
                            x0 -= 1
                    x1 = x
                    while x1 + 1 < W and allowed[y:y1 + 1, x1 + 1].all():
                        x1 += 1
                    y0 = y
                gain = int(need[y0:y1 + 1, x0:x1 + 1].sum())
                if best is None or gain > best[0]:
                    best = (gain, x0, y0, x1, y1)
            _, x0, y0, x1, y1 = best
            need[y0:y1 + 1, x0:x1 + 1] = False
            rects.append((x0, y0, x1 - x0 + 1, y1 - y0 + 1, int(c)))
    return rects


def silhouette(idx, cell):
    """Coarse one-colour mask (cell x cell blocks with >= half coverage) as rectangles in
    source pixels, for afterimages and hit flashes."""
    H, W = idx.shape
    h, w = (H + cell - 1) // cell, (W + cell - 1) // cell
    m = np.zeros((h, w), dtype=np.int32) - 1
    for j in range(h):
        for i in range(w):
            blk = idx[j * cell:(j + 1) * cell, i * cell:(i + 1) * cell]
            if (blk >= 0).mean() >= 0.45:
                m[j, i] = 0
    return [(x * cell, y * cell, ww * cell, hh * cell, 0) for x, y, ww, hh, _ in painter(m)]


def render(rects, palette, w, h, unit=1):
    from PIL import ImageDraw
    im = Image.new('RGBA', (w * unit, h * unit), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    for x, y, rw, rh, c in rects:
        col = tuple(palette[c][:3]) + (255,)
        dr.rectangle([x * unit, y * unit, (x + rw) * unit - 1, (y + rh) * unit - 1], fill=col)
    return im


# ------------------------------------------------------------------ encoding

B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'


def b64(data: bytes) -> str:
    out = []
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3] + b'\0' * (3 - len(data[i:i + 3]))
        n = (chunk[0] << 16) | (chunk[1] << 8) | chunk[2]
        out.append(B64[(n >> 18) & 63] + B64[(n >> 12) & 63] + B64[(n >> 6) & 63] + B64[n & 63])
    return ''.join(out)


def pack_rects16(rects):
    """9 bytes per rect: x, y, w, h as big-endian uint16, colour byte (pictures wider than 255 px)."""
    b = bytearray()
    for x, y, w, h, c in rects:
        for v in (x, y, w, h):
            b += int(v).to_bytes(2, 'big')
        b.append(int(c))
    return bytes(b)


def pack_rects(rects):
    """5 bytes per rect: x, y, w, h, colour (all < 256)."""
    b = bytearray()
    for x, y, w, h, c in rects:
        for v in (x, y, w, h, c):
            if not 0 <= v < 256:
                raise ValueError(f'rect field out of range: {v}')
        b += bytes((x, y, w, h, c))
    return bytes(b)

"""Sketch renderer for mock-client draw lists (tests / previews only, not UGUI-exact)."""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATHS = ['C:/Windows/Fonts/msyhbd.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf']


@lru_cache(maxsize=64)
def font(size):
    size = max(6, int(size))
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _shape_points(shape, x0, y0, x1, y1):
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    if shape == 100002 or shape == 100006:
        return [(cx + rx * math.cos(t * math.pi / 18), cy + ry * math.sin(t * math.pi / 18)) for t in range(36)]
    if shape == 100003:
        return [(cx, y1), (x1, y0), (x0, y0)]                       # apex up (local y up)
    if shape in (100004, 100005):
        n = 4 if shape == 100004 else 5
        inner = 0.32 if n == 4 else 0.42
        pts = []
        for i in range(n * 2):
            r = 1.0 if i % 2 == 0 else inner
            t = math.pi / 2 + i * math.pi / n
            pts.append((cx + rx * r * math.cos(t), cy + ry * r * math.sin(t)))
        return pts
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def render(items, size, scale=1.0):
    W, H = size
    im = Image.new('RGB', (int(W * scale), int(H * scale)), (0, 0, 0))
    dr = ImageDraw.Draw(im, 'RGBA')

    def tr(a, b, c, d, e, f, x, y):
        X = a * x + c * y + e
        Y = b * x + d * y + f
        return (X * scale, (H - Y) * scale)

    for it in items.values():
        kind = it[1]
        a, b, c, d, e, f, w, h, px, py = (it[i] for i in range(2, 12))
        x0, y0 = -px * w, -py * h
        x1, y1 = x0 + w, y0 + h
        col = (int(it[12]), int(it[13]), int(it[14]), int(it[15]))
        if kind == 'image':
            if col[3] == 0 or w <= 0 or h <= 0:
                continue
            shape = int(it[16])
            soft = float(it[17] or 0)
            ftype = it[18]
            amount = float(it[19])
            if ftype == 'Horizontal':
                if it[20] == 'Right':
                    x0 = x1 - w * amount
                else:
                    x1 = x0 + w * amount
                if amount <= 0:
                    continue
            if ftype == 'Radial360' and amount < 1:
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                pts = [(cx, cy)]
                steps = max(2, int(36 * amount))
                for i in range(steps + 1):
                    t = math.pi / 2 - (i / steps) * amount * 2 * math.pi
                    pts.append((cx + (w / 2) * math.cos(t), cy + (h / 2) * math.sin(t)))
                dr.polygon([tr(a, b, c, d, e, f, x, y) for x, y in pts], fill=col)
                continue
            if shape == 100006:
                pts = _shape_points(100002, x0, y0, x1, y1)
                k = max(1, int(min(w, h) * 0.06 * scale * math.hypot(a, b)))
                dr.line([tr(a, b, c, d, e, f, x, y) for x, y in pts + pts[:1]], fill=col, width=k)
                continue
            if soft > 0:
                pts = [tr(a, b, c, d, e, f, x, y) for x, y in _shape_points(shape, x0, y0, x1, y1)]
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                rad = max(1.0, soft * min(abs(w), abs(h)) * math.hypot(a, b) * scale * 0.35)
                pad = int(rad * 2) + 2
                bx0, by0 = int(min(xs)) - pad, int(min(ys)) - pad
                bx1, by1 = int(max(xs)) + pad, int(max(ys)) + pad
                if bx1 - bx0 > 1 and by1 - by0 > 1 and bx1 > 0 and by1 > 0 and bx0 < im.width and by0 < im.height:
                    mask = Image.new('L', (bx1 - bx0, by1 - by0), 0)
                    md = ImageDraw.Draw(mask)
                    k = 1 - soft * 0.5
                    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
                    md.polygon([((px - cx) * k + cx - bx0, (py - cy) * k + cy - by0) for px, py in pts], fill=col[3])
                    mask = mask.filter(ImageFilter.GaussianBlur(rad))
                    im.paste(col[:3], (bx0, by0, bx1, by1), mask)
                continue
            pts = _shape_points(shape, x0, y0, x1, y1)
            dr.polygon([tr(a, b, c, d, e, f, x, y) for x, y in pts], fill=col)
        else:
            bg = (int(it[24]), int(it[25]), int(it[26]), int(it[27]))
            if bg[3] > 0:
                dr.polygon([tr(a, b, c, d, e, f, x, y) for x, y in _shape_points(100001, x0, y0, x1, y1)], fill=bg)
            text = it[16] or ''
            if not text or col[3] == 0:
                continue
            import re
            text = re.sub(r'</?(color|b|i|size)[^>]*>', '', text)
            k = math.hypot(a, b)
            fs = float(it[17]) * k * scale
            fnt = font(fs)
            ox, oy = tr(a, b, c, d, e, f, x0, y1)        # top-left on screen
            bw, bh = w * k * scale, h * k * scale
            lines = text.split('\n')
            lh = fs * 1.25
            total = lh * len(lines)
            va = it[28]
            ty = oy + (0 if va == 'Top' else (bh - total) if va == 'Bottom' else (bh - total) / 2)
            ha = it[18]
            stroke = int(it[19]) == 1
            oc = (int(it[20]), int(it[21]), int(it[22]), int(it[23]))
            # the canvas is RGB, so translucent text goes through its own layer
            layer = None
            td = dr
            if col[3] < 250:
                layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
                td = ImageDraw.Draw(layer)
            for i, line in enumerate(lines):
                tw = td.textlength(line, font=fnt)
                tx = ox + (0 if ha == 'Left' else (bw - tw) if ha == 'Right' else (bw - tw) / 2)
                td.text((tx, ty + i * lh), line, font=fnt, fill=col[:3] + (255,) if layer else col,
                        stroke_width=max(1, int(fs / 14)) if stroke else 0,
                        stroke_fill=(oc[:3] + (255,) if layer else oc) if stroke else None)
            if layer:
                layer.putalpha(layer.getchannel('A').point(lambda v, k=col[3] / 255: int(v * k)))
                im.paste(layer, (0, 0), layer)
    return im

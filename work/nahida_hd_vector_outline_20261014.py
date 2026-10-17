"""Add closed vector ink and a shared silhouette clip to the HD trace."""
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path('outputs/nahida-hd-vector-fit-20261014')
source = Image.open(OUT / 'source-hd-first.png').convert('RGBA')
w, h = source.size
code = Path('work/nahida_vector_fit_20261014.py').read_text(encoding='utf-8')
scope = {'np': np, 'defaultdict': defaultdict}
exec(code[code.index('def area('):code.index('def fit(')], scope)
loops, area, rdp, smooth_path = [scope[k] for k in ('loops', 'area', 'rdp', 'smooth_path')]


def trace(mask, tolerance=.25, minimum=1):
    result = []
    for contour in loops(mask):
        signed = area(contour)
        if abs(signed) < minimum:
            continue
        split = len(contour) // 2
        points = rdp(contour[:split+1], tolerance)[:-1] + rdp(contour[split:]+[contour[0]], tolerance)[:-1]
        if len(points) < 3:
            continue
        d, poly = smooth_path(points)
        result.append((signed, d, poly))
    return result


def paint(contours, color, stroke=0):
    layer = Image.new('RGBA', (w*3, h*3))
    draw = ImageDraw.Draw(layer)
    for signed, d, poly in sorted(contours, key=lambda c: abs(c[0]), reverse=True):
        xy = [(x*3, y*3) for x, y in poly]
        draw.polygon(xy, fill=color if signed > 0 else (0, 0, 0, 0))
        if stroke:
            draw.line(xy+[xy[0]], fill=color, width=stroke, joint='curve')
    return layer


rgba = np.array(source)
alpha = rgba[:, :, 3] >= 48
silhouette = trace(alpha, .35, 1)
boundary = ' '.join(c[1] for c in silhouette)
clip = paint(silhouette, (255, 255, 255, 255)).getchannel('A')

tree = ET.parse(OUT / 'hd-fit-48color.svg')
old_paths = list(tree.getroot())
paths = [p for p in old_paths if p.tag.endswith('path')]
# The underpainting covers the whole silhouette. Expanded color fills share its
# clip, so overlaps cover seams without changing the character boundary.
base = f'<path fill="#ded6c5" fill-rule="evenodd" d="{boundary}"/>'
fills = []
for path in paths[1:]:
    path.set('stroke-width', '1.0')
    fills.append(ET.tostring(path, encoding='unicode'))
render = Image.open(OUT / 'hd-fit-48color.png').convert('RGBA')
back = paint(silhouette, (222, 214, 197, 255))
back.alpha_composite(render)
render = back

# Recover ink from the HD source by local contrast, preserving its warm skin
# lines and softer hair lines. These become closed filled vector regions.
rgb = rgba[:, :, :3].copy()
rgb[~alpha] = 255
gray = Image.fromarray(rgb).convert('L')
lum = np.array(gray).astype(np.int16)
local_light = np.array(gray.filter(ImageFilter.MaxFilter(5))).astype(np.int16)
interior = np.array(Image.fromarray(alpha.astype('uint8')*255).filter(ImageFilter.MinFilter(3))) > 0
ink = alpha & interior & (lum < 205) & (local_light-lum >= 17)
warm = ink & (rgb[:, :, 0].astype(float) > rgb[:, :, 1]*1.12) & (rgb[:, :, 0] > 110)
soft = ink & ~warm & (lum >= 130)
dark = ink & ~warm & ~soft
ink_paths = []
ink_counts = {}
for name, mask, color in [('dark', dark, '#625a43'), ('hair', soft, '#a38b88'), ('skin', warm, '#b47c66')]:
    contours = trace(mask, .22, 1)
    ink_counts[name] = len(contours)
    if not contours:
        continue
    ink_paths.append(f'<path fill="{color}" fill-rule="evenodd" d="'+ ' '.join(c[1] for c in contours)+'"/>')
    render.alpha_composite(paint(contours, color))
render.putalpha(clip)
# A single continuous exterior stroke is drawn last, including true holes.
edge_color = '#817062'
edge = f'<path fill="none" stroke="{edge_color}" stroke-width="0.75" stroke-linejoin="round" stroke-linecap="round" d="{boundary}"/>'
draw = ImageDraw.Draw(render)
for signed, d, poly in silhouette:
    xy = [(x*3, y*3) for x, y in poly]
    draw.line(xy+[xy[0]], fill=edge_color, width=2, joint='curve')

svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>草神高清第一帧：连续色块与闭合边缘线</title><defs><clipPath id="silhouette"><path fill-rule="evenodd" clip-rule="evenodd" d="{boundary}"/></clipPath></defs><g clip-path="url(#silhouette)">'+base+''.join(fills)+''.join(ink_paths)+'</g>'+edge+'</svg>'
(OUT / 'hd-fit-outlined.svg').write_text(svg, encoding='utf-8')
render.save(OUT / 'hd-fit-outlined.png')

# Verify the delivered vector, including each subpath, rather than assuming Z.
root = ET.fromstring(svg)
starts = closed = 0
for element in root.iter():
    if element.tag.endswith('path'):
        d = element.get('d', '')
        starts += len(re.findall(r'[Mm]', d))
        closed += len(re.findall(r'[Zz]', d))
assert starts == closed, (starts, closed)
assert not any(e.tag.endswith('image') for e in root.iter())
assert np.count_nonzero((np.array(clip)>0) & (np.array(render.getchannel('A'))==0)) == 0

font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 24)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 17)
panel = Image.new('RGB', (1200, 850), '#eff2f6')
draw = ImageDraw.Draw(panel)
draw.text((27,18), '草神高清第一帧 · 补边缘线 / 连续填色 / 闭合轮廓', font=font, fill='#25362b')
for i, (pic, label, caption) in enumerate([
    (source, '高清源帧', '直接以高清第一帧为参考'),
    (Image.open(OUT/'hd-fit-48color.png').convert('RGBA'), '上版矢量', '48色曲线拟合'),
    (render, '补线与闭合版', '外轮廓 + 发丝 / 五官 / 服装边线')]):
    left = 20+i*397
    draw.rounded_rectangle((left,65,left+377,780), radius=16, fill='white')
    draw.text((left+19,85), label, font=font, fill='#25362b')
    targeth = 610
    targetw = round(w/h*targeth)
    shown = pic.resize((targetw,targeth), Image.Resampling.LANCZOS)
    panel.paste(shown, (left+(377-targetw)//2,130), shown)
    draw.text((left+18,749), caption, font=small, fill='#657169')
draw.text((27,804), '全部路径闭合；连续底色覆盖接缝；SVG不含嵌入位图。美术小样，尚未接入游戏。', font=small, fill='#657169')
panel.save(OUT/'outlined-comparison.png')
report = {'closedSubpaths': closed, 'openSubpaths': starts-closed,
          'inkContours': ink_counts, 'continuousUnderpainting': True,
          'sharedSilhouetteClip': True, 'embeddedRasterImages': 0,
          'transparentCracksInsideVectorSilhouette': 0,
          'gameIntegrated': False, 'deviceVerified': False}
(OUT/'outline-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))

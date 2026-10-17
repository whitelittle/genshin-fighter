"""Compare actual rendered SVGs against the same full-resolution source."""
import io
import json
import math
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path('work/vector-research-deps').resolve()))
import vtracer
import resvg_py
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path('outputs/nahida-vector-algorithm-20261014')
OUT.mkdir(parents=True, exist_ok=True)
OLD = Path('outputs/nahida-hd-vector-fit-20261014')
source = Image.open(OLD/'source-hd-first.png').convert('RGBA')
w,h = source.size
# Normalize the source's almost-opaque foreground, retaining the exact HD RGB.
src = np.array(source)
src[:,:,3] = np.where(src[:,:,3]>=48, 255, 0)
input_image = Image.fromarray(src)
input_image.save(OUT/'input-hd.png')

def white(pic):
    back = Image.new('RGBA', pic.size, 'white')
    back.alpha_composite(pic)
    return np.array(back.convert('RGB')).astype(float)

reference = white(input_image)
region = src[:,:,3]>0
face = region.copy()
face[:60] = False
face[150:] = False
face[:,:125] = False
face[:,235:] = False
rows = []
images = {}

def measure(name, svgfile, parameters=None, duration=None):
    markup = svgfile.read_text(encoding='utf-8')
    root = ET.fromstring(markup)
    paths = [e for e in root.iter() if e.tag.endswith('path')]
    commands = ''.join(e.get('d','') for e in paths)
    contours = len(re.findall('[Mm]', commands))
    # Geometry command counts include every contour, not just XML elements.
    segments = len(re.findall('[LlHhVvCcSsQqTtAa]', commands))
    pixels = resvg_py.svg_to_bytes(svg_string=markup, width=w*3, height=h*3, skip_system_fonts=True)
    pic = Image.open(io.BytesIO(pixels)).convert('RGBA')
    pic.save(OUT/(name+'.png'))
    images[name] = pic
    small = pic.resize((w,h), Image.Resampling.LANCZOS)
    raster = white(small)
    delta = raster-reference
    mse = float(np.mean(delta[region]**2))
    alpha = np.array(small)[:,:,3]>=128
    intersection = np.count_nonzero(alpha & region)
    union = np.count_nonzero(alpha | region)
    row = {'name':name, 'pathElements':len(paths), 'subpaths':contours,
           'curveOrLineCommands':segments, 'svgBytes':svgfile.stat().st_size,
           'rgbMAE':round(float(np.abs(delta[region]).mean()),3),
           'faceRGBMAE':round(float(np.abs(delta[face]).mean()),3),
           'foregroundPSNR':round(10*math.log10(255**2/max(mse,1e-12)),3),
           'silhouetteIoU':round(intersection/union,5),
           'embeddedImages':sum(e.tag.endswith('image') for e in root.iter()),
           'parameters':parameters, 'seconds':duration}
    rows.append(row)
    return row

for name in ['hd-fit-18color','hd-fit-48color','hd-fit-outlined']:
    measure(name, OLD/(name+'.svg'))

for name,speckle,precision,difference in [
    ('stacked-compact',8,5,32), ('stacked-balanced',4,6,16),
    ('stacked-detail',2,7,12), ('stacked-fine',1,8,8),
    ('stacked-ultrafine',1,8,4)]:
    parameters = dict(colormode='color', hierarchical='stacked', mode='spline',
                      filter_speckle=speckle, color_precision=precision,
                      layer_difference=difference, corner_threshold=60,
                      length_threshold=4.0, max_iterations=10,
                      splice_threshold=45, path_precision=2)
    start = time.perf_counter()
    target = OUT/(name+'.svg')
    vtracer.convert_image_to_svg_py(str(OUT/'input-hd.png'), str(target), **parameters)
    measure(name,target,parameters,round(time.perf_counter()-start,3))

baseline = next(r for r in rows if r['name']=='hd-fit-48color')
for row in rows:
    row['subpathReductionVs48colorPercent'] = round((1-row['subpaths']/baseline['subpaths'])*100,2)
    row['dominates48colorOnRGBAndSubpaths'] = row['rgbMAE']<baseline['rgbMAE'] and row['subpaths']<baseline['subpaths']
(OUT/'benchmark.json').write_text(json.dumps({'inputSize':[w,h],
    'inputDownscaled':False, 'libraryVersion':'vtracer 0.6.15',
    'reference':'HD RGB with alpha threshold 48; white composite; foreground metrics',
    'renderer':'resvg-py 0.5.0 at 3x, Lanczos downsample',
    'faceROI':[125,60,235,150], 'results':rows}, ensure_ascii=False, indent=2),encoding='utf-8')

font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
smallfont = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
selected = ['hd-fit-48color','stacked-balanced','stacked-detail','stacked-fine']
panel = Image.new('RGB',(1500,890),'#eff2f6')
draw = ImageDraw.Draw(panel)
draw.text((25,16),'同一高清第一帧 · 算法对比（实际 SVG 渲染）',font=font,fill='#25362b')
for i,name in enumerate(['source']+selected):
    left=15+i*297
    draw.rounded_rectangle((left,60,left+285,840),radius=12,fill='white')
    title={'source':'高清源帧','hd-fit-48color':'旧 48 色算法','stacked-balanced':'分层：均衡','stacked-detail':'分层：细节','stacked-fine':'分层：精细'}[name]
    draw.text((left+12,78),title,font=font,fill='#25362b')
    pic=input_image if name=='source' else images[name]
    th=610;tw=round(w/h*th)
    shown=pic.resize((tw,th),Image.Resampling.LANCZOS)
    panel.paste(shown,(left+(285-tw)//2,125),shown)
    if name!='source':
        row=next(r for r in rows if r['name']==name)
        draw.text((left+12,752),f'{row["subpaths"]} 轮廓 / {row["curveOrLineCommands"]} 段',font=smallfont,fill='#657169')
        draw.text((left+12,780),f'色彩误差 {row["rgbMAE"]} / {row["svgBytes"]/1024:.0f} KB',font=smallfont,fill='#657169')
draw.text((25,857),'误差越低越接近参考。轮廓与曲线段数分别统计；均未接入游戏或验证真机。',font=smallfont,fill='#657169')
panel.save(OUT/'algorithm-comparison.png')
print(json.dumps(rows,ensure_ascii=False))

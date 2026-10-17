"""Trace the archived HD first pose directly. Never reads a fitted pixel frame."""
import json, runpy
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw,ImageFont
import numpy as np

OUT=Path('outputs/nahida-hd-vector-fit-20261014')
SOURCE=Path('work/github-review-20261009/V3/assets/animation-source/nahida-basic.png')
im=Image.open(SOURCE).convert('RGBA').crop((0,0,384,512))
box=im.getchannel('A').point(lambda a:255 if a>=48 else 0).getbbox()
source=im.crop(box);source.save(OUT/'source-hd-first.png')
# Reuse only the contour math definitions, not the old low-resolution input or output code.
code=Path('work/nahida_vector_fit_20261014.py').read_text(encoding='utf-8')
defs=code[code.index('def area('):code.index('def fit(')]
scope={'np':np,'defaultdict':__import__('collections').defaultdict}
exec(defs,scope)
loops,area,rdp,smooth_path=[scope[k] for k in ('loops','area','rdp','smooth_path')]
w,h=source.size

def fit(colors,eps,minarea,name):
    rgba=np.array(source);alpha=rgba[:,:,3]>=48
    rgb=rgba[:,:,:3].copy();rgb[~alpha]=[255,255,255]
    # Full HD input is smoothed slightly to merge shading islands, never downsized.
    image=Image.fromarray(rgb)
    if colors<=18:image=image.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(.65))
    else:image=image.filter(ImageFilter.GaussianBlur(.15))
    q=image.quantize(colors=colors,method=Image.Quantize.MEDIANCUT)
    ids=np.array(q);palette=np.array(q.getpalette()).reshape(-1,3)
    render=Image.new('RGBA',(w*3,h*3));svgs=[];regions=points=discarded=0
    # One continuous vector underpainting prevents transparent cracks between color regions.
    base=[];drawbase=ImageDraw.Draw(render)
    for contour in loops(alpha):
        if abs(area(contour))<3:continue
        split=len(contour)//2
        p=rdp(contour[:split+1],.55)[:-1]+rdp(contour[split:]+[contour[0]],.55)[:-1]
        if len(p)<3:continue
        d,poly=smooth_path(p);base.append(d)
        if area(contour)>0:drawbase.polygon([(x*3,y*3) for x,y in poly],fill='#DED6C5')
    svgs.append('<path fill="#DED6C5" stroke="#786C5C" stroke-width="0.65" fill-rule="evenodd" d="'+' '.join(base)+'"/>')
    for k in sorted(range(colors),key=lambda i:float(palette[i].mean()),reverse=True):
        contours=loops((ids==k)&alpha);kept=[]
        for p in contours:
            a=area(p)
            # Face/eye and the gold head ornament retain smaller regions.
            cy=sum(v[1] for v in p)/len(p);cx=sum(v[0] for v in p)/len(p)
            # Preserve ink lines and small face features instead of deleting them as noise.
            dark=float(palette[k].mean())<112
            threshold=1 if dark or (cy<145 and cx>125) else minarea
            if abs(a)<threshold:discarded+=1;continue
            split=len(p)//2
            simple=rdp(p[:split+1],eps)[:-1]+rdp(p[split:]+[p[0]],eps)[:-1]
            if len(simple)<3:continue
            d,poly=smooth_path(simple);kept.append((a,d,poly));regions+=1;points+=len(simple)
        if not kept:continue
        color=tuple(palette[k].tolist());hexcol='#'+''.join(f'{v:02x}' for v in color)
        svgs.append(f'<path fill="{hexcol}" stroke="{hexcol}" stroke-width="0.7" stroke-linejoin="round" fill-rule="evenodd" d="'+' '.join(t[1] for t in kept)+'"/>')
        layer=Image.new('RGBA',render.size);draw=ImageDraw.Draw(layer)
        for a,d,p in sorted(kept,key=lambda t:abs(t[0]),reverse=True):
            xy=[(x*3,y*3) for x,y in p]
            draw.polygon(xy,fill=color+(255,) if a>0 else (0,0,0,0))
            draw.line(xy+[xy[0]],fill=color+(255,),width=2,joint='curve')
        render.alpha_composite(layer)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>纳西妲高清第一帧直接矢量拟合</title>'+''.join(svgs)+'</svg>'
    (OUT/(name+'.svg')).write_text(svg,encoding='utf-8');render.save(OUT/(name+'.png'))
    return render,{'inputSize':[w,h],'colors':colors,'colorPaths':len(svgs),'closedContours':regions,'controlPoints':points,'removedTinyRegions':discarded,'tolerance':eps,'inputDownscaled':False}

simple,sr=fit(18,.8,10,'hd-fit-18color')
detail,dr=fit(48,.35,2,'hd-fit-48color')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
panel=Image.new('RGB',(1200,850),'#EFF2F6');draw=ImageDraw.Draw(panel)
draw.text((27,18),'草神高清第一帧 → 直接矢量拟合',fill='#25362B',font=font)
for i,(pic,label,caption) in enumerate([(source,'高清源帧','251 × 462 原图裁切'),(simple,'18色矢量拟合',f'{sr["closedContours"]}个闭合轮廓'),(detail,'48色细节拟合',f'{dr["closedContours"]}个闭合轮廓')]):
    left=20+i*397;draw.rounded_rectangle((left,65,left+377,780),radius=16,fill='white')
    draw.text((left+19,85),label,fill='#25362B',font=font)
    targeth=610;targetw=round(w/h*targeth)
    shown=pic.resize((targetw,targeth),Image.Resampling.LANCZOS)
    panel.paste(shown,(left+(377-targetw)//2,130),shown)
    draw.text((left+18,749),caption,fill='#657169',font=small)
draw.text((27,804),'输入为高清源帧；SVG曲线路径，未转为千星原生图元，未验证真机性能。',fill='#657169',font=small)
panel.save(OUT/'hd-comparison.png')
report={'source':SOURCE.as_posix(),'sheetSize':[1536,1024],'cell':[0,0,384,512],'alphaCrop':box,'inputSize':[w,h],'inputPixelFit':False,'variants':{'18color':sr,'48color':dr},'nativePrimitiveCount':None,'gameSourceChanged':False,'deviceVerified':False}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report['variants'],ensure_ascii=False))

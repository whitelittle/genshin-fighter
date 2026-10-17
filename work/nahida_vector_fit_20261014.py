import json, math
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path('outputs/v4-one-character-20261010/baseline-actions/nahida')
OUT=Path('outputs/nahida-first-frame-vector-20261014');OUT.mkdir(parents=True,exist_ok=True)
source=Image.open(ROOT/'basic_0.png').convert('RGBA')
w,h=source.size;crop=[0,0,w,h]
source.save(OUT/'source-idle.png')

def area(p):return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))/2
def rdp(points,eps):
    if len(points)<3:return points
    a,b=np.array(points[0],float),np.array(points[-1],float)
    v=b-a;den=float(np.dot(v,v))
    arr=np.array(points[1:-1],float)
    t=np.clip(((arr-a)@v)/(den or 1),0,1)
    dist=np.linalg.norm(arr-(a+t[:,None]*v),axis=1)
    k=int(np.argmax(dist))+1
    if dist[k-1]>eps:return rdp(points[:k+1],eps)[:-1]+rdp(points[k:],eps)
    return [points[0],points[-1]]
def loops(mask):
    edges=defaultdict(list)
    H,W=mask.shape
    ys,xs=np.where(mask)
    for yy,xx in zip(ys.tolist(),xs.tolist()):
        if yy==0 or not mask[yy-1,xx]:edges[(xx,yy)].append((xx+1,yy))
        if xx==W-1 or not mask[yy,xx+1]:edges[(xx+1,yy)].append((xx+1,yy+1))
        if yy==H-1 or not mask[yy+1,xx]:edges[(xx+1,yy+1)].append((xx,yy+1))
        if xx==0 or not mask[yy,xx-1]:edges[(xx,yy+1)].append((xx,yy))
    result=[]
    while edges:
        start=next(iter(edges));p=[start];current=start
        while current in edges:
            nxt=edges[current].pop()
            if not edges[current]:del edges[current]
            if nxt==start:break
            p.append(nxt);current=nxt
        if len(p)>=4:result.append(p)
    return result

def smooth_path(points):
    mid=[((a[0]+b[0])/2,(a[1]+b[1])/2) for a,b in zip(points,points[1:]+points[:1])]
    d=f'M {mid[-1][0]:.2f} {mid[-1][1]:.2f}'
    poly=[]
    for i,p in enumerate(points):
        a=mid[i-1];b=mid[i]
        d+=f' Q {p[0]} {p[1]} {b[0]:.2f} {b[1]:.2f}'
        for t in np.linspace(0,1,7,endpoint=False):
            poly.append(((1-t)**2*a[0]+2*(1-t)*t*p[0]+t*t*b[0],(1-t)**2*a[1]+2*(1-t)*t*p[1]+t*t*b[1]))
    return d+' Z',poly

def fit(colors,eps,minarea,label):
    arr=np.array(source)
    alpha=arr[:,:,3]>=180
    rgb=Image.fromarray(arr[:,:,:3]).filter(ImageFilter.GaussianBlur(.45))
    q=rgb.quantize(colors=colors,method=Image.Quantize.MEDIANCUT)
    ids=np.array(q);palette=np.array(q.getpalette()).reshape(-1,3)
    groups=[];render=Image.new('RGBA',(w*10,h*10))
    paths=0;vertices=0;removed=0
    for k in range(colors):
        traced=loops((ids==k)&alpha)
        retained=[]
        for p in traced:
            a=area(p)
            if abs(a)<minarea:removed+=1;continue
            # Split at opposite contour point to avoid a closed line with identical endpoints.
            n=len(p)//2
            simple=rdp(p[:n+1],eps)[:-1]+rdp(p[n:]+[p[0]],eps)[:-1]
            if len(simple)<3:continue
            d,poly=smooth_path(simple)
            retained.append((a,d,poly));vertices+=len(simple);paths+=1
        if not retained:continue
        color=tuple(palette[k].tolist())
        hexcol='#'+''.join(f'{v:02x}' for v in color)
        groups.append(f'<path fill="{hexcol}" stroke="{hexcol}" stroke-width="0.6" stroke-linejoin="round" fill-rule="evenodd" d="'+ ' '.join(v[1] for v in retained)+'"/>')
        layer=Image.new('RGBA',render.size);draw=ImageDraw.Draw(layer)
        for a,d,p in sorted(retained,key=lambda v:abs(v[0]),reverse=True):
            pts=[(xx*10,yy*10) for xx,yy in p]
            draw.polygon(pts,fill=color+(255,) if a>0 else (0,0,0,0))
            draw.line(pts+[pts[0]],fill=color+(255,),width=6,joint='curve')
        render.alpha_composite(layer)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>纳西妲原始基础大图矢量拟合</title>'+''.join(groups)+'</svg>'
    (OUT/f'{label}.svg').write_text(svg,encoding='utf-8')
    render.save(OUT/f'{label}.png')
    return render,dict(colors=colors,colorPaths=len(groups),closedContours=paths,controlPoints=vertices,discardedTinyContours=removed,curveTolerance=eps,minRegionArea=minarea)

light,lr=fit(14,.5,1,'fit-14color')
detail,dr=fit(24,.3,.5,'fit-24color')
fontpath='C:/Windows/Fonts/msyh.ttc'
font=ImageFont.truetype(fontpath,23);small=ImageFont.truetype(fontpath,16)
panel=Image.new('RGB',(1120,740),'#EEF1F5');draw=ImageDraw.Draw(panel)
draw.text((30,20),'小草神第一帧 · 矢量轮廓拟合对照',fill='#253729',font=font)
for i,(im,title,sub) in enumerate([(source,'原始第一帧',f'{w} × {h}，最近邻放大'),(light,'14色简化拟合',f'{lr["closedContours"]} 个闭合轮廓'),(detail,'24色细节拟合',f'{dr["closedContours"]} 个闭合轮廓')]):
    left=25+i*368
    draw.rounded_rectangle((left,70,left+348,660),15,fill='#FFFFFF')
    draw.text((left+18,86),title,fill='#253729',font=font)
    enlarged=im.resize((round(w/h*456),456),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS)
    panel.paste(enlarged,(left+23,135),enlarged)
    draw.text((left+16,613),sub,fill='#657064',font=small)
draw.text((30,682),'曲线路径 SVG 实验；路径数不是千星图元数，尚未转成原生图元或验证真机性能。',fill='#657064',font=small)
panel.save(OUT/'comparison.png')
report={'source':'outputs/v4-one-character-20261010/baseline-actions/nahida/basic_0.png','sourceCrop':crop,'sourceSize':[w,h],'inputIsOriginalLargeCrop':False,'variants':{'14color':lr,'24color':dr},'status':'vector-contour-study','nativeGenshinPrimitiveCount':None,'deviceVerified':False,'gameSourceChanged':False}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report['variants'],ensure_ascii=False))

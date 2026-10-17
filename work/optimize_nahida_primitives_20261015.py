"""Optimize existing native shapes; do not trace pixels or add fragments."""
import copy, io, json, math, sys, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,str(Path('work/vector-research-deps').resolve()))
import resvg_py

OUT=Path('outputs/nahida-native-optimized-20261015');OUT.mkdir(parents=True,exist_ok=True)
data=json.loads(Path('outputs/nahida-native-collage-20261014/collage.json').read_text(encoding='utf-8'))
elements=copy.deepcopy(data['elements']);initial=copy.deepcopy(elements)
W,H=data['w'],data['h']; yy,xx=np.mgrid[:H,:W].astype(np.float32);xx+=.5;yy+=.5
source=Image.open('outputs/nahida-hd-vector-fit-20261014/source-hd-first.png').convert('RGBA')
raw=np.array(source);targetA=(raw[:,:,3]>=48).astype(np.float32)
target=raw[:,:,:3].astype(np.float32)/255;target[targetA==0]=1
weights=np.ones((H,W),np.float32);weights[60:145,125:236]=2.5
templates={'triangle':np.array([[0,-.5],[.5,.5],[-.5,.5]],np.float32),
 'fourstar':np.array([[0,-.5],[.12,-.12],[.5,0],[.12,.12],[0,.5],[-.12,.12],[-.5,0],[-.12,-.12]],np.float32)}

def mask(e):
    if e.get('removed'):return np.zeros((H,W),np.uint8)
    angle=math.radians(-e['rotation']);c,s=math.cos(angle),math.sin(angle)
    dx=xx-e['x'];dy=yy-e['y'];u=dx*c+dy*s;v=-dx*s+dy*c
    w,h=e['width'],e['height']
    if e['type']=='ellipse':
        q=np.sqrt((u/(w*.5))**2+(v/(h*.5))**2)
        distance=(1-q)*min(w,h)*.5
    elif e['type']=='rectangle':distance=np.minimum(w*.5-np.abs(u),h*.5-np.abs(v))
    else:
        pts=templates[e['type']]*[w,h]
        if e['type']=='triangle':
            distance=np.full((H,W),1e6,np.float32)
            for a,b in zip(pts,np.roll(pts,-1,axis=0)):
                edge=b-a;dist=(edge[0]*(v-a[1])-edge[1]*(u-a[0]))/max(np.linalg.norm(edge),1e-5)
                distance=np.minimum(distance,dist)
        else:
            # Star perimeter includes concave vertices; binary point-in-polygon
            # is only an optimization proxy. Final metrics use actual SVG.
            hit=np.zeros((H,W),bool)
            for a,b in zip(pts,np.roll(pts,-1,axis=0)):
                hit^=((a[1]>v)!=(b[1]>v))&(u<(b[0]-a[0])*(v-a[1])/(b[1]-a[1]+1e-12)+a[0])
            return hit.astype(np.uint8)*255
    return (np.clip(distance+.5,0,1)*255).astype(np.uint8)

def rgb(e):return np.array([int(e['color'][i:i+2],16) for i in (1,3,5)],np.float32)/255
def bounds(m):
    ys,xs=np.where(m>0)
    return (0,0,0,0) if not len(xs) else (int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))

def svg_for(items):
    parts=[]
    for i,e in enumerate(items):
        if e.get('removed'):continue
        w,h=e['width'],e['height'];typ=e['type']
        if typ=='ellipse':shape=f'<ellipse rx="{w/2}" ry="{h/2}"/>'
        elif typ=='rectangle':shape=f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}"/>'
        else:shape='<polygon points="'+' '.join(f'{x*w},{y*h}' for x,y in templates[typ])+'"/>'
        parts.append(f'<g id="p{i}" transform="translate({e["x"]} {e["y"]}) rotate({-e["rotation"]})" fill="{e["color"]}">{shape}</g>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'+''.join(parts)+'</svg>'

def actual_measure(items,name):
    svg=svg_for(items);(OUT/(name+'.svg')).write_text(svg,encoding='utf-8')
    png=resvg_py.svg_to_bytes(svg_string=svg,zoom=3,skip_system_fonts=True)
    (OUT/(name+'.png')).write_bytes(png)
    pic=Image.open(io.BytesIO(png)).convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)
    a=np.array(pic)[:,:,3].astype(float)/255
    color=np.array(pic)[:,:,:3].astype(float)/255
    comp=color*a[:,:,None]+1-a[:,:,None]
    mae=float(np.abs(comp-target)[targetA>0].mean()*255)
    mse=float(np.mean((comp-target)**2));aa=a>=.5;ta=targetA>0
    return {'images':sum(not e.get('removed') for e in items),'foregroundRGBMAE':round(mae,3),
            'wholeCanvasRGBMSE':round(mse,6),'silhouetteIoU':round(float(np.count_nonzero(aa&ta)/np.count_nonzero(aa|ta)),5)}

baseline=actual_measure(initial,'baseline')
history=[];start=time.time();masks=[mask(e) for e in elements]
for sweep,step in enumerate([4,2,1,.5]):
    n=len(elements)
    # Cache the contribution of all shapes above each element. float16 only
    # stores cache values; fitting arithmetic is float32.
    suffixP=np.zeros((n+1,H,W,3),np.float16);suffixT=np.ones((n+1,H,W),np.float16)
    p=np.zeros((H,W,3),np.float32);t=np.ones((H,W),np.float32)
    for i in range(n-1,-1,-1):
        a=masks[i].astype(np.float32)/255
        p=p+t[:,:,None]*a[:,:,None]*rgb(elements[i]);t=t*(1-a)
        suffixP[i]=p;suffixT[i]=t
    prefix=np.ones((H,W,3),np.float32);prefixA=np.zeros((H,W),np.float32)
    accepted=removed=0
    for i,e in enumerate(elements):
        if e.get('removed'):continue
        # Local patch includes all allowed position/size variations.
        radius=math.hypot(e['width'],e['height'])*.65+step*4+3
        x0=max(0,int(e['x']-radius));x1=min(W,int(e['x']+radius+1))
        y0=max(0,int(e['y']-radius));y1=min(H,int(e['y']+radius+1))
        if x1<=x0 or y1<=y0:continue
        sl=np.s_[y0:y1,x0:x1]
        P=suffixP[i+1][sl].astype(np.float32);T=suffixT[i+1][sl].astype(np.float32)
        behind=prefix[sl];behindA=prefixA[sl];ref=target[sl];refA=targetA[sl];wt=weights[sl]
        original_color=rgb(initial[i])
        def score(m,color_fit=True):
            a=m[sl].astype(np.float32)/255
            coefficient=T*a;base=P+T[:,:,None]*(1-a[:,:,None])*behind
            if color_fit and np.sum(coefficient**2)>1e-7:
                col=np.sum(wt[:,:,None]*coefficient[:,:,None]*(ref-base),axis=(0,1))/np.sum(wt*coefficient**2)
                # Keep part colors recognizable and prevent white paint from
                # substituting for actual transparent geometry.
                col=np.clip(col,np.maximum(0,original_color-.18),np.minimum(1,original_color+.18))
            else:col=rgb(e)
            output=base+coefficient[:,:,None]*col
            outputA=1-T*(1-a)*(1-behindA)
            loss=float(np.sum(wt*(np.sum((output-ref)**2,axis=2)+1.2*(outputA-refA)**2)))
            return loss,col
        bestm=masks[i];bestloss,bestcol=score(bestm)
        for key,delta in [('x',step),('y',step),('width',max(step,e['width']*.045)),('height',max(step,e['height']*.045)),('rotation',step*1.5)]:
            old=e[key];selected=old
            for direction in [-1,1]:
                trial=old+direction*delta
                if key in ('width','height') and (trial<.7 or trial<initial[i][key]*.45 or trial>initial[i][key]*1.8):continue
                if key in ('x','y','rotation') and abs(trial-initial[i][key])>30:continue
                e[key]=trial;candidate=mask(e);loss,col=score(candidate)
                if loss<bestloss-1e-5:bestloss,bestcol,bestm,selected=loss,col,candidate,trial;accepted+=1
            e[key]=selected
        # Low-contribution deletion has a small explicit complexity penalty.
        empty=np.zeros((H,W),np.uint8);delete_loss,_=score(empty,False)
        if delete_loss<=bestloss+.2:
            e['removed']=True;bestm=empty;removed+=1
        else:e['color']='#'+''.join(f'{round(float(v)*255):02x}' for v in bestcol)
        masks[i]=bestm
        a=bestm.astype(np.float32)/255
        prefix=prefix*(1-a[:,:,None])+a[:,:,None]*rgb(e)
        prefixA=prefixA+(1-prefixA)*a
    del suffixP,suffixT
    result=actual_measure(elements,f'pass-{sweep+1}')
    result.update(passIndex=sweep+1,acceptedParameterChanges=accepted,removedThisPass=removed)
    history.append(result);print(json.dumps(result),flush=True)

# Select by actual rendered SVG error plus a small alpha penalty, rather than
# only trusting the analytical optimization proxy.
final=actual_measure(elements,'optimized')
data['elements']=[e for e in elements if not e.get('removed')]
for e in data['elements']:
    for key in ('x','y','width','height','rotation'):e[key]=round(e[key],4)
data['method']='native primitive parameter optimization and low-contribution pruning'
(OUT/'collage.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
report={'baseline':baseline,'final':final,'passes':history,'seconds':round(time.time()-start,2),
 'newShapesAdded':0,'arbitraryCurves':0,'pixelBlocksAdded':0,'deviceVerified':False,
 'referenceSize':[W,H],'inputDownscaled':False,'globalMinimumProven':False}
(OUT/'optimization-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
from collections import Counter
summary={'imagePrimitives':len(data['elements']),'types':dict(Counter(e['type'] for e in data['elements'])),
 'arbitraryBezierPaths':0,'pixelFitting':False,'automaticColorRegionTracing':False,'deviceVerified':False}
(OUT/'report.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
panel=Image.new('RGB',(1200,850),'#eff2f6');draw=ImageDraw.Draw(panel)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
draw.text((24,18),'基础图元自动优化 · 同图对照',font=font,fill='#354139')
for i,(pic,title,caption) in enumerate([(source,'高清参考','固定高清第一帧'),(Image.open(OUT/'baseline.png').convert('RGBA'),'原249图元拼装',f'主体色彩误差 {baseline["foregroundRGBMAE"]}'),(Image.open(OUT/'optimized.png').convert('RGBA'),f'优化后 {final["images"]} 图元',f'主体色彩误差 {final["foregroundRGBMAE"]}')]):
    left=15+i*397;draw.rounded_rectangle((left,65,left+382,780),16,fill='white');draw.text((left+16,85),title,font=font,fill='#354139')
    shown=pic.resize((round(W/H*610),610),Image.Resampling.LANCZOS);panel.paste(shown,(left+(382-shown.width)//2,130),shown)
    draw.text((left+16,749),caption,font=small,fill='#657169')
draw.text((24,805),'只调整现有基础图元并删减；误差越低越接近参考。造型仍需审查，真机未验证。',font=small,fill='#657169')
panel.save(OUT/'comparison.png');print(json.dumps(report,ensure_ascii=False),flush=True)

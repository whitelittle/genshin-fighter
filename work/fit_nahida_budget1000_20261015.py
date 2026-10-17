"""One higher-precision tier: bounded native shape additions, edge-weighted fitting."""
import copy, json, math, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

code=Path('work/optimize_nahida_primitives_20261015.py').read_text(encoding='utf-8')
exec(code[:code.index("baseline=actual_measure")],globals())
OUT=Path('outputs/nahida-native-budget1000-20261015');OUT.mkdir(parents=True,exist_ok=True)
data=json.loads(Path('outputs/nahida-native-budget500-20261015/collage.json').read_text(encoding='utf-8'))
elements=copy.deepcopy(data['elements']);initial=copy.deepcopy(elements)
lum=target.mean(axis=2)
gy,gx=np.gradient(lum)
edgeweight=np.clip(np.hypot(gx,gy)*8,0,2)
weights=1+edgeweight
weights[65:145,125:236]*=2
baseline=actual_measure(elements,'baseline')

# Addition candidates are elongated native shapes of useful part scale,
# not one-pixel squares or contours traced from segmented colors.
regions=[('发束细节',(12,20,230,160)),('五官细节',(151,78,223,132)),
         ('衣片细节',(115,150,216,296)),('披带细节',(0,205,128,325)),
         ('手臂细节',(82,173,247,290)),('腿部细节',(117,297,205,458))]
sizes=[(1.5,12),(3,6),(4,10),(6,16),(8,24),(12,36),(20,50),(36,18),(12,6),(28,8)]
rng=np.random.default_rng(20261016)
addition_history=[]
start=time.time()
for addition in range(1000-len(elements)):
    # Re-render current whole SVG for scoring, including all real occlusion.
    markup=svg_for(elements)
    png=resvg_py.svg_to_bytes(svg_string=markup,width=W*2,height=H*2,skip_system_fonts=True)
    picture=Image.open(io.BytesIO(png)).convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)
    rawpic=np.array(picture).astype(np.float32)/255
    currentA=rawpic[:,:,3];current=rawpic[:,:,:3]*currentA[:,:,None]+1-currentA[:,:,None]
    residual=weights*(np.sum((target-current)**2,axis=2)+.8*(targetA-currentA)**2)
    # Spread candidate centers across semantic regions and concentrated error.
    centers=[]
    for part,(lx,ly,hx,hy) in regions:
        roi=residual[ly:hy,lx:hx].copy();roi*=targetA[ly:hy,lx:hx]
        for j in range(5):
            mass=roi.ravel();total=float(mass.sum())
            if total<=1e-6:break
            pos=int(rng.choice(len(mass),p=mass/total));ry,rx=np.unravel_index(pos,roi.shape)
            if roi[ry,rx]<.005:continue
            centers.append((part,float(rx+lx),float(ry+ly)))
            roi[max(0,ry-9):ry+10,max(0,rx-9):rx+10]=0
    best=None;bestgain=.025
    for part,cx,cy in centers:
        for width,height in sizes:
            for angle in [-60,-30,0,30,60,90]:
                radius=math.hypot(width,height)*.55+2
                x0=max(0,int(cx-radius));x1=min(W,int(cx+radius+1));y0=max(0,int(cy-radius));y1=min(H,int(cy+radius+1))
                sl=np.s_[y0:y1,x0:x1]
                dx=xx[sl]-cx;dy=yy[sl]-cy;r=math.radians(-angle);c,s=math.cos(r),math.sin(r)
                u=dx*c+dy*s;v=-dx*s+dy*c
                a=np.clip((1-np.sqrt((u/(width*.5))**2+(v/(height*.5))**2))*min(width,height)*.5+.5,0,1)
                if np.sum(a*targetA[sl])/max(np.sum(a),1e-7)<.93:continue
                wt=weights[sl];old=current[sl];ref=target[sl]
                denominator=float(np.sum(wt*a*a))
                if denominator<1e-6:continue
                col=np.clip(np.sum(wt[:,:,None]*a[:,:,None]*(ref-old*(1-a[:,:,None])),axis=(0,1))/denominator,0,1)
                predicted=old*(1-a[:,:,None])+a[:,:,None]*col
                predictedA=currentA[sl]+(1-currentA[sl])*a
                after=weights[sl]*(np.sum((target[sl]-predicted)**2,axis=2)+.8*(targetA[sl]-predictedA)**2)
                gain=float(np.sum(residual[sl]-after))
                if gain>bestgain:
                    bestgain=gain;best={'type':'ellipse','name':part+str(addition+1),'part':part,
                        'x':cx,'y':cy,'width':width,'height':height,'rotation':angle,
                        'color':'#'+''.join(f'{round(float(v)*255):02x}' for v in col),'fill':1}
    if best is None:
        continue
    elements.append(best)
    if (addition+1)%40==0:
        row=actual_measure(elements,f'added-{addition+1}');addition_history.append(row);print(json.dumps(row),flush=True)

initial=copy.deepcopy(elements)
# Preserve thin line and eye details with smaller steps and a lower pruning
# penalty. The same basic-primitive coordinate fitting remains in use.
history=[];masks=[mask(e) for e in elements]
loop=code[code.index('for sweep,step in enumerate'):code.index('# Select by actual rendered SVG')]
loop=loop.replace('[4,2,1,.5]','[.8,.35]' ).replace('bestloss+.2','bestloss+.01')
exec(loop,globals())
final=actual_measure(elements,'optimized')
data['elements']=[e for e in elements if not e.get('removed')]
for e in data['elements']:
    for key in ('x','y','width','height','rotation'):e[key]=round(e[key],4)
data['method']='native shape budget 1000: regional residual-guided ellipse placement and joint optimization'
(OUT/'collage.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
from collections import Counter
report={'baseline':baseline,'final':final,'addedBeforePruning':len(initial)-497,'additionHistory':addition_history,
 'passes':history,'seconds':round(time.time()-start,2),'arbitraryCurves':0,'pixelBlocksAdded':0,
 'inputSize':[W,H],'inputDownscaled':False,'globalMinimumProven':False,'deviceVerified':False}
(OUT/'optimization-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
summary={'imagePrimitives':len(data['elements']),'types':dict(Counter(e['type'] for e in data['elements'])),
 'arbitraryBezierPaths':0,'pixelFitting':False,'automaticColorRegionTracing':False,'deviceVerified':False}
(OUT/'report.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
panel=Image.new('RGB',(1200,850),'#eff2f6');draw=ImageDraw.Draw(panel)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
draw.text((24,18),'基础图元 · 1000图元预算试验',font=font,fill='#354139')
for i,(pic,title,caption) in enumerate([(source,'高清参考','固定高清第一帧'),(Image.open(OUT/'baseline.png').convert('RGBA'),'上一档 497图元',f'主体误差 {baseline["foregroundRGBMAE"]}'),(Image.open(OUT/'optimized.png').convert('RGBA'),f'1000预算候选 {final["images"]}图元',f'主体误差 {final["foregroundRGBMAE"]}')]):
    left=15+i*397;draw.rounded_rectangle((left,65,left+382,780),16,fill='white');draw.text((left+16,85),title,font=font,fill='#354139')
    shown=pic.resize((round(W/H*610),610),Image.Resampling.LANCZOS);panel.paste(shown,(left+(382-shown.width)//2,130),shown)
    draw.text((left+16,749),caption,font=small,fill='#657169')
draw.text((24,805),'仍使用原生基础形状；保留上一档。数值误差与美术还原分别评估，真机未验证。',font=small,fill='#657169')
panel.save(OUT/'comparison.png');print(json.dumps(report,ensure_ascii=False),flush=True)

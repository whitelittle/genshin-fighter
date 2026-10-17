"""Image-local landmark proposals for review, not human anatomy acceptance.

No image is repainted. Face, coat and tights measurements independently screen a
uniform display scale; conflicts are recorded, never averaged into a 'pass'.
"""
from pathlib import Path
import math,json,heapq
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from clorinde_assets import O,components,area,bounds,canonical_fit

def center(g):
    a=area(g);return [sum((x0+x1-1)*(x1-x0)/2 for y,x0,x1 in g)/a,sum(y*(x1-x0) for y,x0,x1 in g)/a]
def points(g):return np.array([(x,y) for y,x0,x1 in g for x in range(x0,x1)])
def principal(g):
    p=points(g);c=p.mean(axis=0);vals,vec=np.linalg.eigh(np.cov(p.T));axis=vec[:,np.argmax(vals)];z=(p-c)@axis
    lo,hi=np.percentile(z,[2,98]);return float(hi-lo),c.tolist(),(c+axis*lo).tolist(),(c+axis*hi).tolist()
def mask_for(groups,size):
    a=np.zeros(size,dtype='uint8')
    for g in groups:
        for y,x0,x1 in g:a[y,x0:x1]=1
    return a
def thin(a):
    a=np.pad(a.astype(bool),1)
    for _ in range(90):
        changes=0
        for step in [0,1]:
            p=a[1:-1,1:-1];ns=[a[:-2,1:-1],a[:-2,2:],a[1:-1,2:],a[2:,2:],a[2:,1:-1],a[2:,:-2],a[1:-1,:-2],a[:-2,:-2]]
            count=sum(x.astype('uint8') for x in ns)
            transitions=sum((~ns[i]&ns[(i+1)%8]).astype('uint8') for i in range(8))
            if step==0:rule=~(ns[0]&ns[2]&ns[4])&~(ns[2]&ns[4]&ns[6])
            else:rule=~(ns[0]&ns[2]&ns[6])&~(ns[0]&ns[4]&ns[6])
            remove=p&(count>=2)&(count<=6)&(transitions==1)&rule
            changes+=int(remove.sum());p[remove]=False
        if not changes:break
    return a[1:-1,1:-1]
def leg_paths(mask,hip,cuffs):
    if not cuffs:return []
    sk=thin(mask);yy,xx=np.where(sk)
    if len(xx)<12:return []
    nodes=set(zip(xx.tolist(),yy.tolist()));start=min(nodes,key=lambda p:(p[0]-hip[0])**2+(p[1]-hip[1])**2)
    dist={start:0};parent={};queue=[(0,start)]
    while queue:
        d,p=heapq.heappop(queue)
        if d!=dist[p]:continue
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                q=(p[0]+dx,p[1]+dy)
                if not(dx or dy) or q not in nodes:continue
                nd=d+math.hypot(dx,dy)
                if nd<dist.get(q,1e9):dist[q]=nd;parent[q]=p;heapq.heappush(queue,(nd,q))
    result=[]
    for cuff in cuffs:
        end=min(dist,key=lambda p:(p[0]-cuff[0])**2+(p[1]-cuff[1])**2)
        gap=math.dist(end,cuff)
        if gap>30 or dist[end]<20:continue
        path=[end]
        while path[-1]!=start:path.append(parent[path[-1]])
        path.reverse();result.append({'length':dist[end]+math.dist(start,hip)+gap,'chain':[hip,list(path[len(path)//2]),cuff],
            'method':'tights medial path, not measured joint centers','gap':gap})
    return result

def measure(im):
    a=np.asarray(im.convert('RGBA')).astype(float);r,g,b,al=[a[:,:,i] for i in range(4)]
    skin=(al>180)&(r>150)&(g>120)&(b>110)&(r-g>=2)&(r-g<=40)&(r-b>=5)&(r-b<=65)&(g-b>=-10)&(g-b<=32)
    upper=.60 if im.width>im.height*1.4 else .38
    candidates=[q for q in components(skin) if area(q)>20 and (bounds(q)[1]+bounds(q)[3])/2<im.height*upper]
    if not candidates:return {'reason':'face occluded/rotated or skin segmentation unavailable'}
    f=max(candidates,key=area);span,fc,fp0,fp1=principal(f)
    if span<8:return {'reason':'small face fragment, not calibrated'}
    # Colored tights indicate the body's longitudinal direction even in a
    # horizontal lunge. They do not establish approved joint positions.
    Y,X=np.indices(al.shape)
    preliminary=(al>180)&(r>=60)&(r<=175)&(g>=35)&(g<=130)&(b>=50)&(b<=155)&(r-g>=10)&(b-g>=7)&(r>=b-4)
    preliminary_parts=[q for q in components(preliminary) if area(q)>span*span*.15 and math.dist(center(q),fc)>span*2][:4]
    if preliminary_parts:
        lp=np.concatenate([points(q) for q in preliminary_parts]);lc=lp.mean(axis=0);axis=lc-np.array(fc);axis=axis/max(1,np.linalg.norm(axis))
        xmin=min(fc[0]-span*2,lc[0]-span*2);xmax=max(fc[0]+span*2,lc[0]+span*2)
    else:axis=np.array([0.,1.]);xmin=fc[0]-span*2.5;xmax=fc[0]+span*2.5
    longitudinal=(X-fc[0])*axis[0]+(Y-fc[1])*axis[1]
    coat=(al>180)&(r>=20)&(r<=85)&(g<=75)&(b>=20)&(b<=105)&(b-r<50)&(X>xmin)&(X<xmax)&(longitudinal>span*.45)&(longitudinal<span*7.0)
    coats=[q for q in components(coat) if area(q)>span*span*.10]
    neck=[fc[0]-span*.25,fc[1]+span*.65]
    hip=None
    if coats:
        c=max(coats,key=area);p=points(c);z=(p-np.array(fc))@axis;end=np.percentile(z,94);q=p[z>=end-span*.10]
        hip=[float(np.median(q[:,0])),float(np.median(q[:,1]))]
    parts=preliminary_parts
    lm=mask_for(parts,al.shape)
    lm=np.asarray(Image.fromarray(lm*255).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7)))>0
    if hip is None and parts:
        p=np.concatenate([points(q) for q in parts]);nearest=p[np.argsort(((p-np.array(neck))**2).sum(axis=1))[:max(1,len(p)//20)]]
        hip=nearest.mean(axis=0).tolist()
    white=(al>180)&(np.minimum(np.minimum(r,g),b)>175)&((np.maximum(np.maximum(r,g),b)-np.minimum(np.minimum(r,g),b))<55)
    whites=[q for q in components(white) if area(q)>span*span*.04]
    legs=[];grips=[];cuffs=[]
    legpoints=np.column_stack(np.where(lm))[:,::-1] if lm.any() else np.zeros((0,2))
    for q in whites:
        c=center(q);bb=bounds(q)
        if hip is not None and len(legpoints) and math.dist(c,hip)>span*1.6:
            near=float(np.sqrt(((legpoints-np.array(c))**2).sum(axis=1)).min())
            if near<span*.75 and bb[3]-bb[1]>span*.12:cuffs.append(c)
        if hip is not None and fc[1]+span*.3<c[1]<hip[1]+span*.7:
            xline=neck[0]+(hip[0]-neck[0])*(c[1]-neck[1])/max(1,hip[1]-neck[1])
            if abs(c[0]-xline)>span*.45:grips.append({'point':c,'area':area(q)})
    if hip is not None:
        cuffs=sorted(cuffs,key=lambda c:math.dist(c,hip),reverse=True)[:2]
        legs=leg_paths(lm,hip,cuffs)
    return {'faceSpan':span,'face':fc,'faceAxis':[fp0,fp1],'neck':neck,'hip':hip,
        'torso':math.dist(neck,hip) if hip else None,'legs':legs,'cuffs':cuffs,
        'hands':sorted(grips,key=lambda x:x['area'],reverse=True)[:2],
        'confidence':'automatic image-region proposals; source-local human review required'}

def main():
    data=json.loads((O/'actions.json').read_text(encoding='utf-8'));palette=json.loads((O/'palette.json').read_text(encoding='utf-8'))
    mother=data['idle']['sourceFrames'][0];m=measure(Image.open(O/mother['file']))
    target={'face':m['faceSpan']*mother['scale'],'torso':m['torso']*mother['scale'] if m.get('torso') else None,
        'leg':max([q['length'] for q in m.get('legs',[])],default=0)*mother['scale'] or None}
    report={'method':'independent image-region scale intervals, not face-only or canvas-height calibration; no averaging conflicts',
        'mother':m,'targets':target,'measurements':{},'conflicts':[],'artAccepted':False}
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14);seen={}
    for key,d in data.items():
        for i,sf in enumerate(d['sourceFrames']):
            name=sf['file']
            if name in seen:
                d['sourceFrames'][i],d['frames'][i]=[dict(x) for x in seen[name]];continue
            im=Image.open(O/name).convert('RGBA');p=measure(im);old=sf['scale'];scale=old;constraints=[]
            if p.get('faceSpan'):constraints.append(('face',target['face']/p['faceSpan'],.10))
            if p.get('torso') and target.get('torso') and span_ratio_valid(p):constraints.append(('torso',target['torso']/p['torso'],.16))
            if p.get('legs') and target.get('leg'):
                leg=max(q['length'] for q in p['legs'])
                if leg>p['faceSpan']*1.5:constraints.append(('leg',target['leg']/leg,.18))
            intervals=[(ratio*(1-tol),ratio*(1+tol)) for part,ratio,tol in constraints]
            conflict=False
            if intervals:
                low=max(a for a,b in intervals);high=min(b for a,b in intervals)
                if low<=high:scale=min(high,max(low,constraints[0][1]))
                else:
                    conflict=True
                    # Pick one explicit primary estimate and preserve the
                    # rejection; never average disparate anatomical cues.
                    primary=constraints[0][1];scale=primary
                scale=min(old*1.6,max(old*.5,scale))
            if key=='idle':scale=.25
            floor=sf['anchor'][1]
            anchor=list(sf['anchor'])
            if p.get('hip'):
                anchor[0]=p['hip'][0]
                if key in ['airlight','airheavy'] or (key=='jump' and i in [2,3,4]):
                    hipfloor=(mother['anchor'][1]-m['hip'][1])*.25
                    anchor[1]=p['hip'][1]+hipfloor/scale
                elif p.get('cuffs'):
                    # Preserve existing ground level; cuffs are ankle regions,
                    # not sole coordinates. No weapon bbox drives the root.
                    anchor[1]=floor
            sf.update(scale=scale,anchor=anchor,landmarkProposal=p,
                calibrationStatus='source conflict retained' if conflict else 'scale interval candidate, not art acceptance')
            fit,meta=canonical_fit(im,anchor,scale,palette,Path(d['frames'][i]['file']).stem)
            d['sourceFrames'][i]=sf;d['frames'][i]=fit;seen[name]=(sf,fit)
            row={'action':key,'frame':i,'file':name,'oldScale':old,'scale':scale,'constraints':constraints,'conflict':conflict,'landmarks':p}
            report['measurements'][name]=row
            if conflict:report['conflicts'].append({'action':key,'frame':i,'file':name,'reason':'image-region estimates conflict; source/manual review, not averaged'})
    (O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (O/'pose-calibration-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # Bone/region markers stay diagnostic and separate from delivered source.
    for batch in range((len(report['measurements'])+11)//12):
        sheet=Image.new('RGB',(1200,960),(234,237,244));draw=ImageDraw.Draw(sheet)
        for j,row in enumerate(list(report['measurements'].values())[batch*12:(batch+1)*12]):
            im=Image.open(O/row['file']).convert('RGBA');z=min(270/im.width,245/im.height);im=im.resize((max(1,round(im.width*z)),max(1,round(im.height*z))))
            x=(j%4)*300+(300-im.width)//2;y=(j//4)*320+38;sheet.paste(im,(x,y),im)
            draw.text(((j%4)*300+5,(j//4)*320+5),f"{row['action']} {row['frame']+1}  {row['scale']:.3f}"+(' 待复核' if row['conflict'] else ''),fill=(25,30,50),font=font)
            p=row['landmarks']
            for k,col in [('face',(225,95,100)),('neck',(80,150,210)),('hip',(80,170,110))]:
                if p.get(k):cx=x+p[k][0]*z;cy=y+p[k][1]*z;draw.ellipse((cx-3,cy-3,cx+3,cy+3),fill=col)
        sheet.save(O/f'evidence/calibration-v2-{batch}.jpg')
    print(json.dumps({'registered':len(seen),'conflicts':len(report['conflicts']),'targets':target,'artAccepted':False},ensure_ascii=False))

def span_ratio_valid(p):return 2.0<=p['torso']/max(1,p['faceSpan'])<=8.0

if __name__=='__main__':main()

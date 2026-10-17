"""Free-object extraction and diagnostic uniform-grid fitting; originals unchanged."""
from pathlib import Path
import math,json,sys,hashlib
from collections import deque
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
O=R/'outputs/clorinde-actions-20261011'
sys.path.insert(0,str(R/'game/tools'))
import artlib
from clorinde_action_specs import SPECS

def components(mask):
    runs=[];parents=[];prev=[]
    def find(n):
        while parents[n]!=n:parents[n]=parents[parents[n]];n=parents[n]
        return n
    for y,row in enumerate(mask):
        edges=np.diff(np.pad(row.astype('int8'),(1,1)))
        cur=[]
        for x0,x1 in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
            i=len(runs);parents.append(i);runs.append((y,int(x0),int(x1)));cur.append(i)
            for p in prev:
                _,px0,px1=runs[p]
                if x0<=px1 and x1>=px0:parents[find(i)]=find(p)
        prev=cur
    groups={}
    for i,run in enumerate(runs):groups.setdefault(find(i),[]).append(run)
    return sorted(groups.values(),key=area,reverse=True)

def area(g):return sum(x1-x0 for y,x0,x1 in g)
def bounds(g):return [min(x0 for y,x0,x1 in g),min(y for y,x0,x1 in g),max(x1 for y,x0,x1 in g),max(y for y,x0,x1 in g)+1]

def extract(path,n):
    im=Image.open(path).convert('RGBA');raw=np.asarray(im);alpha=raw[:,:,3]
    mask=alpha>=64
    groups=components(mask);large=[g for g in groups if area(g)>1500]
    method='alpha64 connected support'
    if path.stem=='airlight-v1':
        # Explicit source-local body seeds from visual review. This atlas has
        # two touching right-column bodies and a detached tassel, not six cores.
        seeds=[(350,240),(820,240),(370,725),(846,781),(360,1233),(820,1230)]
        owner=np.zeros(mask.shape,dtype='uint8');q=deque()
        for i,(x,y) in enumerate(seeds,1):
            if alpha[y,x]<32:raise ValueError('manual body seed outside alpha support')
            owner[y,x]=i;q.append((x,y,i))
        while q:
            x,y,i=q.popleft()
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=nx<im.width and 0<=ny<im.height and alpha[ny,nx]>=32 and owner[ny,nx]==0:
                    owner[ny,nx]=i;q.append((nx,ny,i))
        provisional=[]
        for i in range(1,n+1):
            yy,xx=np.where(owner==i);provisional.append([xx.min(),yy.min(),xx.max()+1,yy.max()+1])
        for g in components((alpha>=32)&(owner==0)):
            bb=bounds(g);cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2
            def distance(i):
                b=provisional[i];return math.hypot(max(b[0]-cx,0,cx-b[2]),max(b[1]-cy,0,cy-b[3]))
            i=min(range(n),key=distance)
            if distance(i)<=40:
                for y,x0,x1 in g:owner[y,x0:x1]=i+1
        large=[]
        for i in range(1,n+1):
            g=[]
            for y,row in enumerate(owner==i):
                e=np.diff(np.pad(row.astype('int8'),(1,1)))
                g.extend((y,int(a),int(b)) for a,b in zip(np.flatnonzero(e==1),np.flatnonzero(e==-1)))
            large.append(g)
        groups=large;method='manual six body seeds, original alpha32 connected ownership; RGBA unchanged'
    if len(large)!=n:
        # Antialiased fringe may join two otherwise complete opaque characters.
        # Seed each genuine opaque body, then deterministically grow ownership
        # through its original alpha pixels. Preserve RGBA; never split a cell.
        groups=components(alpha>=250);large=[g for g in groups if area(g)>1500]
        if len(large)!=n:raise ValueError(f'{path.name}: expected {n}, found {len(large)} opaque body cores')
        owner=np.zeros(mask.shape,dtype='uint8')
        for i,g in enumerate(large,1):
            for y,x0,x1 in g:owner[y,x0:x1]=i
        for _ in range(12):
            empty=owner==0;changed=0
            for i in range(1,n+1):
                expanded=np.asarray(Image.fromarray((owner==i).astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
                add=expanded&empty&(alpha>=32)&(owner==0)
                changed+=int(add.sum());owner[add]=i
            if not changed:break
        large=[]
        for i in range(1,n+1):
            g=[]
            for y,row in enumerate(owner==i):
                edges=np.diff(np.pad(row.astype('int8'),(1,1)))
                g.extend((y,int(a),int(b)) for a,b in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)))
            large.append(g)
        groups=large;method='alpha250 body cores, 12-step original alpha32 ownership growth; no RGB repaint'
    fragments=[]
    for g in groups:
        if area(g)>1500:continue
        gb=bounds(g);cx=(gb[0]+gb[2])/2;cy=(gb[1]+gb[3])/2
        def dist(target):
            b=bounds(target);return math.hypot(max(b[0]-cx,0,cx-b[2]),max(b[1]-cy,0,cy-b[3]))
        target=min(large,key=dist);d=dist(target)
        fragments.append({'bbox':gb,'area':area(g),'distance':d,'attached':d<=12})
        if d<=12:target.extend(g)
    # Row grouping uses actual object centers, no fixed equal cells.
    ys=sorted(large,key=lambda g:(bounds(g)[1]+bounds(g)[3])/2)
    height=float(np.median([bounds(g)[3]-bounds(g)[1] for g in large]))
    row=0;last=None;rows={}
    for g in ys:
        center=(bounds(g)[1]+bounds(g)[3])/2
        if last is not None and center-last>height*.35:row+=1
        rows[id(g)]=row;last=center
    large.sort(key=lambda g:(rows[id(g)],bounds(g)[0]))
    result=[]
    for g in large:
        layer=np.zeros(mask.shape,dtype='uint8')
        for y,x0,x1 in g:layer[y,x0:x1]=255
        keep=(layer>0) if method.startswith(('alpha250','manual')) else (np.asarray(Image.fromarray(layer).filter(ImageFilter.MaxFilter(3)))>0)
        isolated=raw.copy();isolated[~keep]=0
        b=bounds(g);box=[max(0,b[0]-4),max(0,b[1]-4),min(im.width,b[2]+4),min(im.height,b[3]+4)]
        crop=Image.fromarray(isolated).crop(box)
        result.append((crop,{'roi':box,'opaqueBounds':b,'sourceOrigin':box[:2],'extractionMethod':method,
            'fullCanvasContact':b[0]<=1 or b[1]<=1 or b[2]>=im.width-1 or b[3]>=im.height-1}))
    return result,fragments

def face_box(im):
    a=np.asarray(im.convert('RGBA')).astype(float);r,g,b,alpha=a[:,:,0],a[:,:,1],a[:,:,2],a[:,:,3]
    skin=(alpha>180)&(r>155)&(g>95)&(r-g>18)&(b>g*.80)&(b<r)
    groups=components(skin)
    choices=[p for p in groups if area(p)>18 and (bounds(p)[1]+bounds(p)[3])/2<im.height*.45]
    if not choices:return None
    return bounds(max(choices,key=area))

def canonical_fit(im,anchor,scale,palette,base):
    cell=4.5;q=scale/cell;ax,ay=anchor
    left=math.floor(-ax*q)-2;top=math.floor(-ay*q)-2
    right=math.ceil((im.width-ax)*q)+2;bottom=math.ceil((im.height-ay)*q)+2
    w,h=right-left,bottom-top;k=4
    a=np.asarray(im,dtype=float);a[:,:,:3]*=a[:,:,3:4]/255
    pm=Image.fromarray(np.clip(a,0,255).astype('uint8'),'RGBA')
    sample=pm.transform((w*k,h*k),Image.Transform.AFFINE,(1/(q*k),0,ax+left/q,0,1/(q*k),ay+top/q),resample=Image.Resampling.BILINEAR).resize((w,h),Image.Resampling.BOX)
    a=np.asarray(sample,dtype=float);al=a[:,:,3:4]
    a[:,:,:3]=np.where(al>0,a[:,:,:3]*255/np.maximum(1,al),0)
    small=Image.fromarray(np.clip(a+.5,0,255).astype('uint8'),'RGBA')
    idx=artlib.apply_palette(small,palette[:-1]);mask=idx>=0
    edge=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
    idx[edge&~mask]=len(palette)-1
    rects=artlib.painter(idx);target=np.zeros((h,w,4),dtype='uint8');rebuilt=np.zeros_like(target)
    for c,color in enumerate(palette):target[idx==c]=color+[255]
    for x,y,rw,rh,c in rects:rebuilt[y:y+rh,x:x+rw]=palette[c]+[255]
    assert np.array_equal(target,rebuilt)
    png=O/'fit'/f'{base}.png';png.parent.mkdir(exist_ok=True)
    Image.fromarray(rebuilt).save(png)
    meta={'file':png.relative_to(O).as_posix(),'anchor':[-left,-top],'scale':cell,
        'palette':palette,'rects':rects,'reconstruction':'exact quantized target',
        'sourceSampling':'uniform premultiplied affine; no independent X/Y scaling',
        'outline':'one external logical cell; interiors unchanged','runtimeIntegrated':False}
    jf=png.with_suffix('.json');jf.write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')
    return {'file':meta['file'],'anchor':meta['anchor'],'scale':cell,'rectData':jf.relative_to(O).as_posix(),'rectangles':len(rects)},meta

def main():
    (O/'frames').mkdir(exist_ok=True);(O/'fit').mkdir(exist_ok=True)
    mother=Image.open(O/'source/master-v2.png').convert('RGBA')
    mf=face_box(mother)
    if mf is None:raise ValueError('mother visible face measure not found')
    mheight=mf[3]-mf[1];scale=.25;target=mheight*scale
    # For comparison only: a visible-face proxy is not skull/body anatomy approval.
    palette=artlib.build_palette([artlib.downscale(mother,.055)],16,seed=31)+[[246,213,197],[239,237,245],[16,22,37]]
    (O/'palette.json').write_text(json.dumps(palette),encoding='utf-8')
    data={};report={'measurementPolicy':'Face skin regions are diagnostic only and do not drive scale. Declared source drawing units are provisional, uniform per sheet; no per-pose silhouette normalization or X/Y warping. Anatomy, body build, contact and final world scale require visual review.',
        'motherFaceBox':mf,'motherWorldScale':scale,'groups':{},'errors':{},'runtimeIntegrated':False}
    plans={'idle':('待机',2,[30,30],['呼气','吸气']),
        'light1':('轻攻一',4,[3,3,3,12],['准备','出手','有效','恢复'])}
    plans.update({k:(v[0],v[1],v[2],v[3]) for k,v in SPECS.items()})
    for key,(label,n,durations,phases) in plans.items():
        file=O/'source'/('light1-v2.png' if key=='light1' else f'{key}-v1.png')
        if key=='airheavy' and (O/'source/airheavy-v2.png').exists():file=O/'source/airheavy-v2.png'
        if key=='idle':
            paths=[O/'source/master-v2.png',O/'source/idle-single-v1.png']
            if not all(p.exists() for p in paths):continue
            items=[(Image.open(p).convert('RGBA'),{'roi':[0,0,*Image.open(p).size],'sourceOrigin':[0,0],'sourceFile':p.name,'fullCanvasContact':False}) for p in paths];fragments=[]
        else:
            if not file.exists():continue
            try:items,fragments=extract(file,n)
            except Exception as e:report['errors'][key]=str(e);continue
        faces=[face_box(im) for im,info in items]
        # Face skin regions fragment under hats/cool lighting and must not
        # determine actor scale. Declared source drawing units are provisional,
        # fixed for the entire sheet; never normalize each pose's silhouette.
        atlas_h=1448 if key=='idle' else Image.open(file).height
        rows=1 if key=='idle' else (3 if n==6 and Image.open(file).height>Image.open(file).width*1.15 else 2)
        sheet_scale=1448*.25/(atlas_h/rows)
        first_h=next((fb[3]-fb[1] for fb in faces if fb),mheight)
        source_frames=[];fitted=[];metrics=[]
        for i,((im,info),fb) in enumerate(zip(items,faces)):
            frame_scale=sheet_scale
            if key=='airheavy' and i in [3,5] and (O/f'source/airheavy-single-{i}-v1.png').exists():
                repair=O/f'source/airheavy-single-{i}-v1.png'
                im=Image.open(repair).convert('RGBA');fb=face_box(im)
                frame_scale=.33 if i==3 else .32
                rb=im.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
                info={'roi':[0,0,im.width,im.height],'sourceOrigin':[0,0],
                    'fullCanvasContact':rb[0]==0 or rb[1]==0 or rb[2]==im.width or rb[3]==im.height,'sourceFile':repair.name,
                    'objectReview':'sword tip now visibly complete; perimeter contact is not automatically crop acceptance',
                    'extractionMethod':'independent imagegen sword-tip repair; manual provisional unit'}
            # Contact-based provisional floor; never crop-box center. Hair/weapon
            # extents do not select horizontal root. Manual pivots remain required.
            opaque=np.asarray(im)[:,:,3]>=128;ys,xs=np.where(opaque)
            floor=int(ys.max());bottom_x=xs[ys>=floor-4]
            anchor=[float(np.median(bottom_x)),float(floor)]
            if key in ['airlight','airheavy','jump'] and fb:
                anchor=[(fb[0]+fb[2])/2-10/frame_scale,(fb[1]+fb[3])/2+260/frame_scale]
                if key=='airheavy' and i==len(items)-1:anchor=[float(np.median(bottom_x)),float(floor)]
            name=f'frames/{key}-{i}.png';im.save(O/name)
            sf={'file':name,'anchor':anchor,'scale':frame_scale,'source':('source/'+info['sourceFile']) if info.get('sourceFile') else file.relative_to(O).as_posix(),**info,'anchorStatus':'provisional support/virtual floor; manual pose/contact review required'}
            ff,meta=canonical_fit(im,anchor,frame_scale,palette,f'{key}-{i}')
            sf['sourceHash']=hashlib.sha256((O/name).read_bytes()).hexdigest()
            source_frames.append(sf);fitted.append(ff)
            metrics.append({'frame':i,'visibleFaceBox':fb,'faceRatio':((fb[3]-fb[1])/first_h) if fb else None,'rectangles':ff['rectangles'],'canvasContact':info['fullCanvasContact']})
        d={'actionId':'clorinde.'+key,'frames':fitted,'sourceFrames':source_frames,'durations':durations,'phases':phases,
            'events':[],'status':'新源图与拟合候选；体型/挂点/播放待逐项复核','runtimeIntegrated':False,
            'sourceScalePolicy':'one declared provisional source drawing unit per sheet; no face-only or per-pose bbox scaling; anatomy still requires visual review'}
        if key in ['forwarddash','backdash','victory'] and 'idle' in data:
            for field in ['frames','sourceFrames']:d[field]=[dict(data['idle'][field][0])]+d[field]+[dict(data['idle'][field][0])]
            d['durations']=[4]+durations+[4];d['phases']=['待机']+phases+['待机']
        data[key]=d;report['groups'][key]={'sourcePoses':n,'displayPoses':len(d['frames']),'scale':sheet_scale,'frames':metrics,'fragments':fragments,'visualAccepted':False}
    if 'hit_knockdown' in data and 'wakeup' in data:
        for field in ['frames','sourceFrames']:data['hit_knockdown'][field][-1]=dict(data['wakeup'][field][0])
        data['hit_knockdown']['continuation']={'next':'wakeup','sharedPose':True}
    if 'wakeup' in data and 'idle' in data:
        for field in ['frames','sourceFrames']:data['wakeup'][field].append(dict(data['idle'][field][0]))
        data['wakeup']['durations'].append(4);data['wakeup']['phases'].append('待机')
    (O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (O/'fit-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # Contact sheets keep each sheet's uniform world scale; no per-frame boxes.
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
    for key,d in data.items():
        card=Image.new('RGBA',(1200,340),(245,247,250,255));draw=ImageDraw.Draw(card)
        for i,f in enumerate(d['frames']):
            im=Image.open(O/f['file']).convert('RGBA');s=f['scale']*.58
            resized=im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))),Image.Resampling.NEAREST)
            x=int(80+i*1200/len(d['frames'])-f['anchor'][0]*s);y=int(310-f['anchor'][1]*s)
            card.alpha_composite(resized,(x,y));draw.text((i*1200/len(d['frames'])+5,5),str(i+1),font=font,fill=(20,25,40))
        card.convert('RGB').save(O/f'evidence/{key}-fit-review.jpg')
    print(json.dumps({'groups':len(data),'errors':report['errors'],'displayPoses':sum(len(d['frames']) for d in data.values())},ensure_ascii=False))

if __name__=='__main__':main()

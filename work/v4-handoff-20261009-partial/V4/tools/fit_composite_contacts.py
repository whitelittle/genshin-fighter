"""Offline diagnostic fitting for integrated E contact candidates.

Uses the character's existing E palette and source cell height. This is a
candidate inspection tool; it does not claim the original V3 encoder or runtime.
"""
from pathlib import Path
from PIL import Image, ImageFilter
import hashlib
import json
import numpy as np

V = Path(__file__).resolve().parents[1]
jobs = json.loads((V / 'design/ROSTER_JOBS.json').read_text())

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def oklab(rgb):
    a = np.asarray(rgb, dtype=np.float32) / 255.0
    a = np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)
    l = np.cbrt(.41222147*a[...,0] + .53633254*a[...,1] + .05144599*a[...,2])
    m = np.cbrt(.21190350*a[...,0] + .68069955*a[...,1] + .10739696*a[...,2])
    s = np.cbrt(.08830246*a[...,0] + .28171884*a[...,1] + .62997870*a[...,2])
    return np.stack([.21045426*l+.79361779*m-.00407205*s,
                     1.97799850*l-2.42859221*m+.45059371*s,
                     .02590404*l+.78277177*m-.80867577*s], axis=-1)

def painter(idx):
    rects = []
    open_rects = {}
    for y, row in enumerate(idx):
        runs = []
        x = 0
        while x < len(row):
            color = int(row[x]); begin = x
            while x < len(row) and int(row[x]) == color: x += 1
            if color >= 0: runs.append((begin,x-begin,color))
        next_open = {}
        for run in runs:
            if run in open_rects:
                r = open_rects.pop(run); r[3] += 1
            else:
                r = [run[0],y,run[1],1,run[2]]
            next_open[run] = r
        rects.extend(open_rects.values()); open_rects = next_open
    rects.extend(open_rects.values())
    return rects

summary = []
for job in jobs['jobs']:
    record = job.get('E_integrated_candidate')
    if not record: continue
    key = job['character']; source = V.parent / record['output']
    body_fit = json.loads((V / 'evidence' / f'{key}-E-review/fit.json').read_text())
    palette = np.asarray(body_fit['palette'], dtype=np.uint8)
    pal_lab = oklab(palette[:-1]); height = body_fit['height']
    im = Image.open(source).convert('RGBA'); w,h=im.size
    dest=V/'evidence'/f'{key}-E-composite-review'; dest.mkdir(exist_ok=True)
    frames=[];pairs=[]
    for n in range(4):
        crop=im.crop(((n%2)*w//2,(n//2)*h//2,(n%2+1)*w//2,(n//2+1)*h//2))
        sp=dest/f'source-cell-{n}.png'; crop.save(sp)
        alpha=np.asarray(crop.getchannel('A'))
        edge={side: bool((a>=32).any()) for side,a in {
            'left':alpha[:,0], 'right':alpha[:,-1],
            'top':alpha[0,:], 'bottom':alpha[-1,:]}.items()}
        # Pillow RGBa downsamples premultiplied RGB and alpha together.
        pre=crop.convert('RGBa'); resized=pre.resize((round(crop.width*height/crop.height),height),Image.Resampling.BOX).convert('RGBA')
        rgba=np.asarray(resized);mask=rgba[:,:,3]>=32
        rgb=oklab(rgba[:,:,:3]).reshape(-1,3)
        dist=np.sum((rgb[:,None,:]-pal_lab[None,:,:])**2*np.array([1.2,1.,1.])[None,None,:],axis=2)
        idx=np.argmin(dist,axis=1).reshape(rgba.shape[:2]).astype(np.int16);idx[~mask]=-1
        border=Image.fromarray((mask.astype('uint8')*255)).filter(ImageFilter.MaxFilter(3))
        outline=(np.asarray(border)>0)&(~mask);idx[outline]=len(palette)-1
        rects=painter(idx)
        output=np.zeros((*idx.shape,4),dtype=np.uint8);valid=idx>=0;output[valid,:3]=palette[idx[valid]];output[valid,3]=255
        reconstructed=np.zeros_like(output)
        for x,y,rw,rh,color in rects: reconstructed[y:y+rh,x:x+rw]=[*palette[color],255]
        assert np.array_equal(output,reconstructed)
        fp=dest/f'optimized-{n}.png';Image.fromarray(output).save(fp)
        panel=Image.new('RGB',(720,270),'#242936')
        for side,pic in enumerate([crop,Image.fromarray(output)]):
            scale=min(340/pic.width,250/pic.height)
            t=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.LANCZOS if side==0 else Image.Resampling.NEAREST)
            panel.paste(t,(side*360+(360-t.width)//2,(270-t.height)//2),t)
        pairs.append(panel)
        frames.append({'source_sha256':digest(sp),'fit_sha256':digest(fp),'edge_alpha32':edge,'rect_count':len(rects),'rect_reconstruction_exact':True,'anchor_status':'未人工逐像素标定'})
    pairs[0].save(dest/'playback.gif',save_all=True,append_images=pairs[1:],duration=[210,160,200,270],loop=0)
    sheet=Image.new('RGB',(720,1080))
    for n,pair in enumerate(pairs):sheet.paste(pair,(0,n*270))
    sheet.save(dest/'comparison.png')
    r={'character':key,'source':record['output'],'source_sha256':digest(source),'height':height,'palette_scope':'复用该角色E身体19色调色板，车与武器细节可能损失','method':'premultiplied BOX to existing body height; weighted OKLab nearest of existing palette; 1px outline; exact rectangle reconstruction','rect_counts':[f['rect_count'] for f in frames],'max_rects':max(f['rect_count'] for f in frames),'budget760':all(f['rect_count']<=760 for f in frames),'frames':frames,'status':'offline_diagnostic_candidate_not_V3_encoder_not_runtime'}
    (dest/'fit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    record['fitting']={'report':str((dest/'fit.json').relative_to(V.parent)),'max_rects':r['max_rects'],'budget760':r['budget760'],'status':r['status']}
    summary.append({'character':key,'rect_counts':r['rect_counts'],'max_rects':r['max_rects'],'budget760':r['budget760'],'edge_alpha32':[f['edge_alpha32'] for f in frames]})
    print(key,r['rect_counts'],[f['edge_alpha32'] for f in frames],flush=True)
(V/'evidence/E-composite-fit-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(V/'design/ROSTER_JOBS.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2))

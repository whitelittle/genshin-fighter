"""Offline 32px member diagnostics and static-slot composite, not V3 encoder/runtime."""
from pathlib import Path
from PIL import Image
import hashlib,json,numpy as np

V=Path(__file__).resolve().parents[1]
Q=V/'design/ROSTER_JOBS.json'
jobs=json.loads(Q.read_text())
job=next(j for j in jobs['jobs'] if j['character']=='furina')
out=V/'evidence'/job.get('E_assistant_evidence_batch','furina-salon-refinement-v2');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rects(idx):
    done=[];opened={}
    for y,row in enumerate(idx):
        spans=[];x=0
        while x<len(row):
            start=x;c=int(row[x])
            while x<len(row) and int(row[x])==c:x+=1
            if c>=0:spans.append((start,x-start,c))
        nxt={}
        for s in spans:
            r=opened.pop(s,[s[0],y,s[1],0,s[2]]);r[3]+=1;nxt[s]=r
        done.extend(opened.values());opened=nxt
    return done+list(opened.values())
prepared=[];samples=[]
for rec in job['E_individual_assistants']:
    im=Image.open(V.parent/rec['output']).convert('RGBA');w,h=im.size
    cols,rows=rec.get('grid',[2,2])
    cuts=rec.get('source_cuts_x',[round(i*w/cols) for i in range(cols+1)])
    cells=[im.crop((cuts[n%cols],n//cols*h//rows,cuts[n%cols+1],(n//cols+1)*h//rows)) for n in range(4)]
    roots_x=[(n%cols+.5)*w/cols-cuts[n%cols] for n in range(4)]
    # One transform per member for all four poses; never recenter each pose.
    # Opaque extent measures inspection scale only, not a gameplay contact anchor.
    heights=[]
    for c in cells:
        ys=np.where(np.asarray(c)[:,:,3]>=224)[0]
        heights.append(int(ys.max()-ys.min()+1) if len(ys) else 1)
    scale=28/max(heights)
    small=[]
    for n,c in enumerate(cells):
        s=c.convert('RGBa').resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.BOX).convert('RGBA')
        canvas=Image.new('RGBA',(48,48))
        canvas.alpha_composite(s,(24-round(roots_x[n]*scale),40-round(c.height*.9*scale)))
        small.append(canvas)
    rec['inspection_transform']={'scale':scale,'canvas':[48,48],'root_candidate':[24,40],'source_roots_x':roots_x,'source_root_y_fraction':.9,'opaque_height_target':28,'constant_across_poses':True,'anchor_measured':False}
    for s in small:
        a=np.asarray(s);samples.append(a[:,:,:3][a[:,:,3]>=32])
    prepared.append((rec,cells,small))
samples=np.concatenate(samples)
pim=Image.fromarray(samples.reshape(1,len(samples),3).astype('uint8'),'RGB').quantize(colors=16,method=Image.Quantize.MEDIANCUT)
raw=pim.getpalette();rgb=np.array([raw[i*3:i*3+3] for i in range(16)],dtype='uint8')
colors=np.array([list(map(int,p))+[a] for a in (64,128,255) for p in rgb],dtype='uint8')
all_frames={};summary=[]
for rec,cells,small in prepared:
    folder=out/rec['member'];folder.mkdir(exist_ok=True);frames=[];panels=[];fits=[]
    for n,(c,s) in enumerate(zip(cells,small)):
        sc=folder/f'source-cell-{n}.png';c.save(sc)
        pix=np.asarray(s);alpha=pix[:,:,3]
        delta=pix[:,:,:3].astype('int32')[:,:,None,:]-rgb.astype('int32')[None,None,:,:]
        idx=np.argmin((delta*delta).sum(axis=3),axis=2).astype('int16')
        idx+=np.where(alpha<=85,0,np.where(alpha<=170,1,2))*16;idx[alpha<32]=-1
        rr=rects(idx);fit=np.zeros((*idx.shape,4),dtype='uint8');mask=idx>=0;fit[mask]=colors[idx[mask]]
        rebuilt=np.zeros_like(fit)
        for x,y,w,h,k in rr:rebuilt[y:y+h,x:x+w]=colors[k]
        assert np.array_equal(fit,rebuilt)
        fp=folder/f'optimized-{n}.png';fi=Image.fromarray(fit);fi.save(fp);fits.append(fi)
        a=np.asarray(c)[:,:,3];edges={'left':bool((a[:,0]>=32).any()),'right':bool((a[:,-1]>=32).any()),'top':bool((a[0,:]>=32).any()),'bottom':bool((a[-1,:]>=32).any())}
        panel=Image.new('RGBA',(640,240),'#232936')
        for side,im in enumerate((c,fi)):
            scale=min(300/im.width,220/im.height);thumb=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS if side==0 else Image.Resampling.NEAREST)
            panel.alpha_composite(thumb,(side*320+(320-thumb.width)//2,(240-thumb.height)//2))
        panels.append(panel.convert('RGB'));frames.append({'rects':len(rr),'source_sha256':sha(sc),'fit_sha256':sha(fp),'edge_alpha32':edges,'reconstruction_exact':True})
    panels[0].save(folder/'playback.gif',save_all=True,append_images=panels[1:],duration=[240,160,180,260],loop=0)
    sheet=Image.new('RGB',(640,960));[sheet.paste(p,(0,n*240)) for n,p in enumerate(panels)];sheet.save(folder/'comparison.png')
    meta={'member':rec['member'],'canvas':[48,48],'inspection_transform':rec['inspection_transform'],'palette':colors.tolist(),'frames':frames,'rect_counts':[f['rects'] for f in frames],'status':'offline_palette_diagnostic_not_V3_encoder_not_runtime','anchors_measured':False}
    (folder/'fit.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));summary.append(meta);all_frames[rec['member']]=fits
    rec['fitting']={'report':str((folder/'fit.json').relative_to(V.parent)),'rect_counts':meta['rect_counts'],'status':meta['status']}
    print(rec['member'],meta['rect_counts'],[f['edge_alpha32'] for f in frames])
# Composite evidence uses explicit illustrative slots; no measured contacts or game logic.
scene=[]
for n in range(4):
    canvas=Image.new('RGBA',(340,180),'#232936')
    body=Image.open(V/'evidence/furina-E-review'/f'optimized-{n}.png').convert('RGBA')
    canvas.alpha_composite(body,(30,160-body.height))
    for key,x,y in [('usher',130,100),('chevalmarin',190,105),('crabaletta',250,128)]:
        canvas.alpha_composite(all_frames[key][n],(x,y))
    scene.append(canvas.convert('RGB').resize((1020,540),Image.Resampling.NEAREST))
scene[0].save(out/'scene-playback.gif',save_all=True,append_images=scene[1:],duration=[240,160,180,260],loop=0)
scene[2].save(out/'scene-active.png')
(out/'summary.json').write_text(json.dumps({'members':summary,'scene_status':'illustrative_static_slots_unmeasured_not_runtime'},ensure_ascii=False,indent=2))
Q.write_text(json.dumps(jobs,ensure_ascii=False,indent=2))

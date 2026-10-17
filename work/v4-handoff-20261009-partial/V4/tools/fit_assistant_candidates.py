"""Source/fit/playback evidence for independent E assistant candidates."""
from pathlib import Path
from PIL import Image
import hashlib,json,numpy as np

V=Path(__file__).resolve().parents[1]
jobs=json.loads((V/'design/ROSTER_JOBS.json').read_text())

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rectangles(idx):
    result=[];open_rows={}
    for y,row in enumerate(idx):
        spans=[];x=0
        while x<len(row):
            c=int(row[x]);start=x
            while x<len(row) and int(row[x])==c:x+=1
            if c>=0:spans.append((start,x-start,c))
        next_rows={}
        for span in spans:
            r=open_rows.pop(span,[span[0],y,span[1],0,span[2]]);r[3]+=1;next_rows[span]=r
        result.extend(open_rows.values());open_rows=next_rows
    result.extend(open_rows.values());return result

summary=[]
for job in jobs['jobs']:
    layer='assistant' if job.get('E_assistant_candidate') else 'prop'
    record=job.get('E_assistant_candidate') or job.get('E_prop_candidate')
    if not record:continue
    key=job['character'];source=V.parent/record['output'];im=Image.open(source).convert('RGBA');w,h=im.size
    cells=[im.crop(((n%2)*w//2,(n//2)*h//2,(n%2+1)*w//2,(n//2+1)*h//2)) for n in range(4)]
    # One assistant palette for all phases; selected from their joint source,
    # independent of the body palette. 64px cells are an inspection size.
    height=64;small=[c.convert('RGBa').resize((round(c.width*height/c.height),height),Image.Resampling.BOX).convert('RGBA') for c in cells]
    samples=np.concatenate([np.asarray(s)[:,:,:3][np.asarray(s)[:,:,3]>=32] for s in small],axis=0)
    palette_image=Image.fromarray(samples.reshape(1,len(samples),3).astype('uint8'),'RGB').quantize(colors=16,method=Image.Quantize.MEDIANCUT)
    raw=palette_image.getpalette();rgb=np.asarray([raw[i*3:i*3+3] for i in range(16)],dtype='uint8')
    colors=np.asarray([[int(c) for c in p]+[a] for a in (64,128,255) for p in rgb],dtype='uint8')
    out=V/'evidence'/f'{key}-E-{layer}-review';out.mkdir(exist_ok=True)
    frames=[];panels=[]
    for n,(c,s) in enumerate(zip(cells,small)):
        sc=out/f'source-cell-{n}.png';c.save(sc)
        pixels=np.asarray(s);alpha=pixels[:,:,3];d=((pixels[:,:,:3].astype('int16')[:,:,None,:]-rgb.astype('int16')[None,None,:,:])**2).sum(axis=3)
        index=np.argmin(d,axis=2).astype('int16');bucket=np.where(alpha<=85,0,np.where(alpha<=170,1,2));index+=bucket*16;index[alpha<32]=-1
        rects=rectangles(index);fitted=np.zeros((*index.shape,4),dtype='uint8');mask=index>=0;fitted[mask]=colors[index[mask]]
        rebuilt=np.zeros_like(fitted)
        for x,y,rw,rh,pal in rects:rebuilt[y:y+rh,x:x+rw]=colors[pal]
        assert np.array_equal(fitted,rebuilt)
        fp=out/f'optimized-{n}.png';Image.fromarray(fitted).save(fp)
        a=np.asarray(c)[:,:,3];edge=bool((a[0,:]>=32).any() or (a[-1,:]>=32).any() or (a[:,0]>=32).any() or (a[:,-1]>=32).any())
        panel=Image.new('RGBA',(720,260),'#242936')
        for side,pic in enumerate([c,Image.fromarray(fitted)]):
            scale=min(345/pic.width,240/pic.height);res=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.LANCZOS if side==0 else Image.Resampling.NEAREST)
            panel.alpha_composite(res,(side*360+(360-res.width)//2,(260-res.height)//2))
        panels.append(panel.convert('RGB'));frames.append({'rect_count':len(rects),'source_sha256':sha(sc),'fit_sha256':sha(fp),'edge_alpha32':edge,'rect_reconstruction_exact':True,'contact_anchor':None})
    panels[0].save(out/'playback.gif',save_all=True,append_images=panels[1:],duration=[200,170,200,260],loop=0)
    sheet=Image.new('RGB',(720,1040));[sheet.paste(p,(0,i*260)) for i,p in enumerate(panels)];sheet.save(out/'comparison.png')
    result={'character':key,'layer':'E_'+layer,'source_sha256':sha(source),'palette':colors.tolist(),'height':height,'rect_counts':[f['rect_count'] for f in frames],'max_rects':max(f['rect_count'] for f in frames),'legacy850_reference':max(f['rect_count'] for f in frames)<=850,'frames':frames,'status':'offline_independent_'+layer+'_candidate_unaligned_not_runtime'}
    (out/'fit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    record['fitting']={'report':str((out/'fit.json').relative_to(V.parent)),'max_rects':result['max_rects'],'status':result['status'],'anchor_measured':False}
    summary.append({'character':key,'rect_counts':result['rect_counts'],'max_rects':result['max_rects'],'edge':[f['edge_alpha32'] for f in frames]})
    print(key,summary[-1],flush=True)
(V/'evidence/E-assistant-fit-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(V/'design/ROSTER_JOBS.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2))

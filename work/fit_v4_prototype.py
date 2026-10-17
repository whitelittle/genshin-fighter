"""Use restored V3 artlib on four-frame candidates; preserve fixed nominal grid roots."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageFilter,ImageDraw

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work/github-review-20261009/game/tools'))
import artlib
V=ROOT/'work/v4-handoff-20261009-partial/V4'

def scan_rects(idx):
    rows=[]
    for y,row in enumerate(idx):
        x=0
        while x<len(row):
            c=int(row[x]);start=x;x+=1
            while x<len(row) and row[x]==c:x+=1
            if c>=0:rows.append((start,y,x-start,1,c))
    # Non-overlapping vertical merge of equal row spans.
    rects=[];active={}
    for y in range(idx.shape[0]):
        next_active={}
        for x,yy,w,h,c in (r for r in rows if r[1]==y):
            key=(x,w,c)
            if key in active:
                i=active[key];a=list(rects[i]);a[3]+=1;rects[i]=tuple(a)
            else:i=len(rects);rects.append((x,yy,w,h,c))
            next_active[key]=i
        active=next_active
    return rects

def bounded_rects(idx, original, max_ratio=2.0):
    remaining={int(c):idx==c for c in np.unique(idx[idx>=0])}
    result=[]
    for x,y,w,h,c in original:
        need=remaining[c][y:y+h,x:x+w]
        gain=int(need.sum())
        if not gain:continue
        if w*h<=max_ratio*gain:result.append((x,y,w,h,c))
        else:
            local=np.where(need,c,-1)
            result.extend((x+xx,y+yy,ww,hh,cc) for xx,yy,ww,hh,cc in scan_rects(local))
        remaining[c][y:y+h,x:x+w]=False
    assert all(not n.any() for n in remaining.values())
    return result

def run(name,character):
    source=V/'assets/codex-batch-20261009'/f'{name}.png'
    out=V/'evidence/codex-batch-20261009'/name;out.mkdir(parents=True,exist_ok=True)
    im=Image.open(source).convert('RGBA');w,h=im.size
    ref=json.loads((V/f'evidence/{character}-idle-review/fit.json').read_text(encoding='utf-8'))
    palette=ref['palette'];height=ref['optimized_height'];scale=height/(h/2)
    frames=[];panels=[];source_rgba=np.asarray(im)
    for n in range(4):
        box=(n%2*w//2,n//2*h//2,(n%2+1)*w//2,(n//2+1)*h//2)
        c=im.crop(box);c.save(out/f'source-{n}.png')
        alpha=np.asarray(c)[:,:,3];ys,xs=np.nonzero(alpha>=128)
        bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
        small=artlib.downscale(c,scale)
        idx=artlib.apply_palette(small,palette[:-1])
        mask=idx>=0
        outline=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
        idx[outline&~mask]=len(palette)-1
        rr=artlib.painter(idx);scan=scan_rects(idx);bounded=bounded_rects(idx,rr)
        fit=artlib.render(rr,palette,idx.shape[1],idx.shape[0])
        baseline=artlib.render(scan,palette,idx.shape[1],idx.shape[0])
        assert np.array_equal(np.asarray(fit),np.asarray(baseline)),'rectangle reconstruction differs'
        bounded_image=artlib.render(bounded,palette,idx.shape[1],idx.shape[0])
        assert np.array_equal(np.asarray(bounded_image),np.asarray(baseline)),'bounded reconstruction differs'
        bounded_area=sum(r[2]*r[3] for r in bounded)
        assert bounded_area<=2*int((idx>=0).sum())
        bounded_image.save(out/f'fit-bounded-{n}.png')
        fit.save(out/f'fit-{n}.png')
        opaque=int(mask.sum());outlined=int((idx>=0).sum());area=sum(r[2]*r[3] for r in rr)
        frames.append({'frame':n,'source_bbox':bounds,'source_boundary_touched':any([bounds[0]==0,bounds[1]==0,bounds[2]==c.width,bounds[3]==c.height]),
                       'rect_count':len(rr),'nonoverlapping_rect_count':len(scan),'rect_area':area,
                       'opaque_pixels':opaque,'outlined_pixels':outlined,'overlap_ratio':area/outlined,
                       'bounded_rect_count':len(bounded),'bounded_overlap_ratio':bounded_area/outlined,'bounded_rects':bounded,
                       'exact_reconstruction':True,'rects':rr,'fixed_nominal_root':[idx.shape[1]/2,height*0.92],
                       'root_manually_measured':False,'source_sha256':hashlib.sha256((out/f'source-{n}.png').read_bytes()).hexdigest()})
        panel=Image.new('RGB',(900,360),'#dddfe4')
        for i,(img,bg,title) in enumerate([(c,'#dddfe4','SOURCE'),(fit,'#202733','V3 PAINTER DARK'),(fit,'#dddfe4','V3 PAINTER LIGHT')]):
            cell=Image.new('RGB',(300,360),bg);factor=min(270/img.width,320/img.height)
            thumb=img.resize((round(img.width*factor),round(img.height*factor)),Image.Resampling.LANCZOS if i==0 else Image.Resampling.NEAREST)
            cell.paste(thumb,((300-thumb.width)//2,8),thumb)
            ImageDraw.Draw(cell).text((8,340),title,fill='#888');panel.paste(cell,(i*300,0))
        panels.append(panel)
    panels[0].save(out/'playback.gif',save_all=True,append_images=panels[1:],duration=[160,110,150,220],loop=0)
    sheet=Image.new('RGB',(900,1440))
    for i,p in enumerate(panels):sheet.paste(p,(0,i*360))
    sheet.save(out/'comparison.png')
    report={'source':source.relative_to(V.parent).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'tool':'restored V3 game/tools/artlib.py downscale/apply_palette/painter/render',
            'artlib_sha256':hashlib.sha256(Path(artlib.__file__).read_bytes()).hexdigest(),
            'palette_source':f'V4/evidence/{character}-idle-review/fit.json','palette':palette,
            'frame_size':[round(w/2*scale),height],'fixed_scale':scale,'frames':frames,
            'body_shared_pool_peak':max(x['rect_count'] for x in frames),
            'two_actor_double_body_buffer_images_only':4*max(x['rect_count'] for x in frames),
            'budget_status':'not approved; excludes weapons/assistants/fx/HUD and native controls',
            'visual_review':'pending','runtime':False,'accepted':False}
    (out/'fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'candidate':name,'rects':[f['rect_count'] for f in frames],
                      'scan_rects':[f['nonoverlapping_rect_count'] for f in frames],
                      'overlap':[round(f['overlap_ratio'],3) for f in frames],
                      'bounded_rects':[f['bounded_rect_count'] for f in frames],
                      'bounded_overlap':[round(f['bounded_overlap_ratio'],3) for f in frames],
                      'boundary_touched':[f['source_boundary_touched'] for f in frames]}),flush=True)

if __name__=='__main__':run(sys.argv[1],sys.argv[2])

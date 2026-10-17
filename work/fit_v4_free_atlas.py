"""Extract independent fox poses from a free atlas, preserving recorded source origins."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work/github-review-20261009/game/tools'))
sys.path.insert(0,str(ROOT/'work'))
import artlib
from fit_v4_prototype import scan_rects,bounded_rects
V=ROOT/'work/v4-handoff-20261009-partial/V4'
NAME=sys.argv[1] if len(sys.argv)>1 else 'yaemiko-crouchheavy-fox-pink-v1'
EXPECTED=int(sys.argv[2]) if len(sys.argv)>2 else 4
CHARACTER=sys.argv[3] if len(sys.argv)>3 else None
CALIBRATION_FRAME=int(sys.argv[4]) if len(sys.argv)>4 else 0
SOURCE=V/'assets/codex-batch-20261009'/f'{NAME}.png'
OUT=V/'evidence/codex-batch-20261009'/NAME
OUT.mkdir(parents=True,exist_ok=True)

def components(mask):
    runs=[];parents=[];previous=[]
    def find(n):
        while parents[n]!=n:parents[n]=parents[parents[n]];n=parents[n]
        return n
    for y,row in enumerate(mask):
        changes=np.diff(np.pad(row.astype('int8'),(1,1)))
        starts=np.flatnonzero(changes==1);ends=np.flatnonzero(changes==-1)
        current=[]
        for x0,x1 in zip(starts,ends):
            i=len(runs);parents.append(i);runs.append((y,int(x0),int(x1)));current.append(i)
            for p in previous:
                _,px0,px1=runs[p]
                if x0<=px1 and x1>=px0:parents[find(i)]=find(p)
        previous=current
    groups={}
    for i,run in enumerate(runs):groups.setdefault(find(i),[]).append(run)
    return sorted(groups.values(),key=lambda g:sum(x1-x0 for _,x0,x1 in g),reverse=True)

im=Image.open(SOURCE).convert('RGBA');raw=np.asarray(im);mask=raw[:,:,3]>=128
groups=components(mask);large=[g for g in groups if sum(x1-x0 for _,x0,x1 in g)>1000]
assert len(large)==EXPECTED,f'Expected {EXPECTED} connected poses; found {len(large)}'
def box(g):return [min(x0 for y,x0,x1 in g),min(y for y,x0,x1 in g),max(x1 for y,x0,x1 in g),max(y for y,x0,x1 in g)+1]
assigned_fragments=[]
for g in groups:
    if sum(x1-x0 for y,x0,x1 in g)>1000:continue
    x0,y0,x1,y1=box(g);cx=(x0+x1)/2;cy=(y0+y1)/2
    def distance(target):
        return min((y-cy)**2+max(x0-cx,0,cx-x1)**2 for y,x0,x1 in target)
    target=min(large,key=distance)
    assigned_fragments.append({'source_bbox':box(g),'area':sum(x1-x0 for y,x0,x1 in g),'method':'nearest actual opaque run support, not fixed cell'})
    target.extend(g)
centred=sorted(large,key=lambda g:(box(g)[1]+box(g)[3])/2)
height=float(np.median([box(g)[3]-box(g)[1] for g in large]))
row=0;last=None;row_ids={}
for g in centred:
    centre=(box(g)[1]+box(g)[3])/2
    if last is not None and centre-last>height*0.4:row+=1
    row_ids[id(g)]=row;last=centre
large.sort(key=lambda g:(row_ids[id(g)],box(g)[0]))
frames=[];selected=np.zeros(mask.shape,dtype=bool);crops=[]
for n,g in enumerate(large):
    region=np.zeros(mask.shape,dtype='uint8')
    for y,x0,x1 in g:region[y,x0:x1]=255;selected[y,x0:x1]=True
    keep=np.asarray(Image.fromarray(region).filter(ImageFilter.MaxFilter(7)))>0
    isolated=raw.copy();isolated[~keep,3]=0
    bounds=box(g);x0,y0,x1,y1=bounds
    padded=[max(0,x0-4),max(0,y0-4),min(im.width,x1+4),min(im.height,y1+4)]
    crop=Image.fromarray(isolated).crop(padded);crop.save(OUT/f'source-{n}.png')
    crops.append(crop)
    frames.append({'frame':n,'source_bbox':bounds,'crop_box':padded,'source_origin':padded[:2],
                   'full_canvas_boundary_contact':bounds[0]<=0 or bounds[1]<=0 or bounds[2]>=im.width or bounds[3]>=im.height,
                   'opaque_area':sum(x1-x0 for _,x0,x1 in g),'mask_method':'connected opaque support at alpha128, preserve original alpha within 3px neighborhood',
                   'source_root':'not manually measured','accepted':False})
unassigned=int((mask&~selected).sum())
assert unassigned<200,'Unexpected disconnected visible objects'
if CHARACTER:
    reference=V/f'evidence/{CHARACTER}-idle-review'
    ref=json.loads((reference/'fit.json').read_text(encoding='utf-8'))
    reference_bounds=Image.open(reference/'optimized-0.png').getbbox()
    target_height=reference_bounds[3]-reference_bounds[1]
    assert 0<=CALIBRATION_FRAME<len(crops)
    scale=target_height/crops[CALIBRATION_FRAME].height
else:scale=28/max(c.height for c in crops)
small=[artlib.downscale(c,scale) for c in crops]
palette=ref['palette'] if CHARACTER else artlib.build_palette(small,12,seed=24)+[[88,20,52]]
panels=[]
source_zoom=min(225/max(c.width for c in crops),225/max(c.height for c in crops))
fit_zoom=min(225/max(c.width for c in small),225/max(c.height for c in small))
for n,c in enumerate(small):
    idx=artlib.apply_palette(c,palette[:-1]);opaque=idx>=0
    edge=np.asarray(Image.fromarray(opaque.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
    idx[edge&~opaque]=len(palette)-1
    rr=artlib.painter(idx);scan=scan_rects(idx);bounded=bounded_rects(idx,rr)
    fit=artlib.render(rr,palette,idx.shape[1],idx.shape[0]);control=artlib.render(scan,palette,idx.shape[1],idx.shape[0])
    assert np.array_equal(np.asarray(fit),np.asarray(control))
    assert np.array_equal(np.asarray(artlib.render(bounded,palette,idx.shape[1],idx.shape[0])),np.asarray(control))
    fit.save(OUT/f'fit-{n}.png')
    frames[n].update(rect_count=len(rr),bounded_rect_count=len(bounded),rects=rr,bounded_rects=bounded,
                     rect_area=sum(r[2]*r[3] for r in rr),outlined_pixels=int((idx>=0).sum()),
                     fit_size=list(fit.size),exact_reconstruction=True,
                     source_sha256=hashlib.sha256((OUT/f'source-{n}.png').read_bytes()).hexdigest())
    panel=Image.new('RGB',(720,260))
    for col,(img,bg,label) in enumerate([(crops[n],'#e5e8ec','SOURCE'),(fit,'#202733','PAINTER DARK'),(fit,'#e5e8ec','PAINTER LIGHT')]):
        p=Image.new('RGB',(240,260),bg);factor=source_zoom if col==0 else fit_zoom
        thumb=img.resize((round(img.width*factor),round(img.height*factor)),Image.Resampling.LANCZOS if col==0 else Image.Resampling.NEAREST)
        p.paste(thumb,((240-thumb.width)//2,(240-thumb.height)//2),thumb);ImageDraw.Draw(p).text((8,242),label,fill='#888');panel.paste(p,(col*240,0))
    panels.append(panel)
duration=130 if EXPECTED==6 else [180,100,160,200] if EXPECTED==4 else 160
panels[0].save(OUT/'playback.gif',save_all=True,append_images=panels[1:],duration=duration,loop=0)
comparison=Image.new('RGB',(720,260*EXPECTED))
for n,p in enumerate(panels):comparison.paste(p,(0,n*260))
comparison.save(OUT/'comparison.png')
report={'source':SOURCE.relative_to(V.parent).as_posix(),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'source_image_size':list(im.size),'pixel_reconstruction_scope':'quantized outlined target, not lossless original source',
        'scale_calibration_frame':CALIBRATION_FRAME,'preview_zoom_fixed_across_frames':True,
        'free_atlas':True,'fixed_scale_all_poses':scale,'palette':palette,'frames':frames,
        'unassigned_opaque_pixels':unassigned,'runtime':False,'accepted':False,
        'attached_small_fragments':assigned_fragments,
        'animation_note':'Crops are for inspection; world anchors still pending. Do not render by independently centered crop bounds.'}
(OUT/'fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'rects':[f['rect_count'] for f in frames],'bounded':[f['bounded_rect_count'] for f in frames],
                  'source_boxes':[f['source_bbox'] for f in frames],'unassigned_opaque_pixels':unassigned}))

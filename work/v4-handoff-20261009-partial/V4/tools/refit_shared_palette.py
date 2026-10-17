from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageFilter
V=Path(__file__).resolve().parents[1];R=V.parent;sys.path.insert(0,str(R/'game/tools'));import artlib
summary=[]
for j in json.load(open(V/'design/ROSTER_JOBS.json'))['jobs']:
 key=j['character'];groups={}
 for kind in ['idle','walk']:
  d=V/'evidence'/f'{key}-{kind}-review';cells=[Image.open(p).convert('RGBA') for p in sorted(d.glob('source-cell-*.png'))];assert cells;groups[kind]=(d,cells)
 originals=[c for _,cells in groups.values() for c in cells];normalized=[artlib.downscale(c,80/c.height) for c in originals]
 p24=artlib.build_palette(normalized,24);p18=artlib.build_palette(normalized,18);oc=(18,32,27) if key=='venti' else ((37,18,34) if key in ['yaemiko','arlecchino'] else (16,22,37))
 def fit(height,p):
  p=p+[oc];res=[]
  for c in originals:
   im=artlib.downscale(c,height/c.height);idx=artlib.apply_palette(im,p[:-1]);mask=Image.fromarray((idx>=0).astype('uint8')*255);dil=np.asarray(mask.filter(ImageFilter.MaxFilter(3)))>0;idx[dil&(idx<0)]=len(p)-1;rr=artlib.painter(idx);a=np.zeros((*idx.shape,4),dtype='uint8');m=idx>=0;a[m,:3]=np.asarray(p,dtype='uint8')[idx[m]];a[m,3]=255;res.append((Image.fromarray(a),rr))
  return res,p
 initial,pi=fit(80,p24);height=80
 while True:
  optimized,po=fit(height,p18)
  if max(len(rr) for _,rr in optimized)<=760:break
  height-=4;assert height>=28
 offset=0;palsha=hashlib.sha256(json.dumps(po).encode()).hexdigest()
 for kind,(d,cells) in groups.items():
  report=json.load(open(d/'fit.json'));count=[];seq=[];compare=Image.new('RGB',(960,len(cells)*240),'#242936');frames=[];bottom=[]
  for n,c in enumerate(cells):
   ini,_=initial[offset+n];opt,rr=optimized[offset+n];ini.save(d/f'initial-{n}.png');opt.save(d/f'optimized-{n}.png');count.append(len(rr));frames.append({'rects':rr});ys,xs=np.where(np.asarray(opt)[:,:,3]>0);bottom.append(int(ys.max()))
   for col,img in enumerate([artlib.downscale(c,80/c.height),ini,opt]):
    frame=Image.new('RGB',(320,240),'#ddd9cd');scaled=img.resize((round(img.width*220/img.height),220),Image.Resampling.NEAREST);frame.paste(scaled,((320-scaled.width)//2,10),scaled);compare.paste(frame,(col*320,n*240))
   pair=Image.new('RGB',(640,240));scaled=opt.resize((round(opt.width*220/opt.height),220),Image.Resampling.NEAREST)
   for b,bg in enumerate(['#242936','#dfdbcd']):
    frame=Image.new('RGB',(320,240),bg);frame.paste(scaled,((320-scaled.width)//2,10),scaled);pair.paste(frame,(b*320,0))
   seq.append(pair)
  seq[0].save(d/'playback.gif',save_all=True,append_images=seq[1:],duration=350 if kind=='idle' else 120,loop=0);compare.save(d/'source-initial-optimized.png');offset+=len(cells)
  report.update(palette=po,palette_sha256=palsha,palette_scope='同角色待机与前走全部8帧共享；未来新增组须重新统一校准',optimized_height=height,rect_counts=count,mean_rects=sum(count)/len(count),max_rects=max(count),budget760=max(count)<=760,frames=frames,silhouette_bottom_y=bottom,fit_method='premult alpha BOX, importance weighted OKLab,shared character palette,1px external colored outline; provisional anchors')
  (d/'fit.json').write_text(json.dumps(report,ensure_ascii=False));summary.append({k:report[k] for k in ['character','group','palette_sha256','optimized_height','rect_counts','mean_rects','max_rects','budget760','silhouette_bottom_y','status']})
 print(key,height,max(len(rr) for _,rr in optimized),flush=True)
(V/'evidence/basics-fit-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))

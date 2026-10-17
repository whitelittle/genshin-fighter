"""Offline SD encoding, anatomical contact annotations and unmodified originals."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
import artlib
root=Path(__file__).resolve().parents[1];assets=root/'dist/assets'
specs={'idle':(2,1,.24,'mavuika-idle-source-v5.png',535),'walk':(3,2,.408,'mavuika-walk-source-v6.png',300),'backwalk':(3,2,.408,'mavuika-backwalk-source-v6.png',300),'light1':(2,2,.4,'mavuika-light1-source-v6.png',None)}
groups={};small={};report=[]
for key,(cols,rows,scale,file,rootx) in specs.items():
 path=assets/file;im=Image.open(path).convert('RGBA');rgba=np.array(im);poses=[]
 original_hash=hashlib.sha256(path.read_bytes()).hexdigest()
 if key=='light1':
  lab,n=ndimage.label(rgba[:,:,3]>64);size=np.bincount(lab.ravel());ids=list(np.argsort(size[1:])[::-1][:4]+1)
  centers={i:ndimage.center_of_mass(rgba[:,:,3]>64,lab,int(i)) for i in ids}
  top=sorted(sorted(ids,key=lambda i:centers[i][0])[:2],key=lambda i:centers[i][1]);bottom=sorted([i for i in ids if i not in top],key=lambda i:centers[i][1]);ids=top+bottom
  rois=[[90,0,900,640],[830,0,900,640],[40,550,900,640],[870,540,900,640]]
  contacts=[[520,552],[1200,567],[340,997],[1170,1003]]
  source=Image.new('RGBA',(1800,1280));crops=[]
  for i,(identity,roi,contact) in enumerate(zip(ids,rois,contacts)):
   mask=ndimage.binary_dilation(lab==identity,iterations=2);isolated=rgba.copy();isolated[:,:,3]=np.where(mask,rgba[:,:,3],0)
   x,y,w,h=roi;crop=Image.fromarray(isolated,'RGBA').crop((x,y,x+w,y+h));crops.append(crop)
   ox,oy=(i%cols)*900,(i//cols)*640;source.paste(crop,(ox,oy));poses.append({'sourceRect':[ox,oy,900,640],'sourceAnchor':[contact[0]-x,contact[1]-y],'originalROI':roi,'componentID':int(identity),'contactKind':'manual boot support midpoint, provisional'})
  file='mavuika-light1-extracted-v6.png';tmp=assets/(file+'.tmp');source.save(tmp,format='PNG');check=Image.open(tmp);check.load();tmp.replace(assets/file)
 else:
  w,h=im.width//cols,im.height//rows;crops=[]
  for i in range(cols*rows):
   x,y=(i%cols)*w,(i//cols)*h;crop=im.crop((x,y,x+w,y+h));crops.append(crop)
   alpha=np.array(crop)[:,:,3];foot=(alpha>128);foot[:int(h*.75)]=False
   yy,xx=np.where(foot);sole=int(yy.max()+1)
   poses.append({'sourceRect':[x,y,w,h],'sourceAnchor':[rootx,sole],'footBaselineAdjustment':round((sole-h*.965)*scale,2),'contactKind':'lower boot-region sole edge, manual X pelvis column, provisional'})
  source=im
 for i,(crop,p) in enumerate(zip(crops,poses)):
  scaled=artlib.downscale(crop,scale/4)
  padded=Image.new('RGBA',(scaled.width+2,scaled.height+2));padded.paste(scaled,(1,1));small[key,i]=padded
  p['anchor']=[v*scale/4+1 for v in p['sourceAnchor']];p['atlasRect']=[(i%cols)*128,(i//cols)*80,padded.width,padded.height]
 groups[key]={'source':file,'originalSource':path.name,'originalSHA256':original_hash,'sourceSHA256':hashlib.sha256((assets/file).read_bytes()).hexdigest(),'displayScale':scale,'columns':cols,'rows':rows,'poses':poses,'alphaZeroFraction':float((rgba[:,:,3]==0).mean())}
palette=artlib.build_palette(list(small.values()),20,seed=11)+[[68,38,35]]
for key,(cols,rows,scale,file,rootx) in specs.items():
 for mode in ['initial','optimized']:
  atlas=Image.new('RGBA',(cols*128,rows*80));records=[]
  for i,p in enumerate(groups[key]['poses']):
   im=small[key,i];base=artlib.apply_palette(im,palette);idx=base.copy();mask=base>=0
   if mode=='optimized':
    outline=ndimage.binary_dilation(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]))&~mask
    idx[outline]=len(palette)-1
    assert np.array_equal(idx[mask],base[mask]),'outline overwrote interior features'
   rects=artlib.painter(idx);restored=np.full(idx.shape,-1,dtype=int)
   for x,y,w,h,c in rects:restored[y:y+h,x:x+w]=c
   assert np.array_equal(restored,idx),'rect reconstruction failed'
   assert im.width<=128 and im.height<=80
   atlas.paste(artlib.render(rects,palette,im.width,im.height),tuple(p['atlasRect'][:2]))
   p[mode+'Rectangles']=len(rects);records.append({'pose':i,'width':im.width,'height':im.height,'rects':rects,'anchor':p['anchor'],'scale':4})
   report.append({'group':key,'pose':i,'mode':mode,'rectangles':len(rects),'interiorPreserved':True})
  filename=f'mavuika-{key}-{mode}-v6.png';atlas.save(assets/filename);groups[key][mode]=filename
  (assets/f'{key}-{mode}-rects-v6.json').write_text(json.dumps({'palette':palette,'poses':records,'sourceSHA256':groups[key]['sourceSHA256'],'status':'candidate; not formal combat or device accepted'},separators=(',',':'))+'\n')
data={'groups':groups,'palette':palette,'status':'18 display poses / 4 groups; full 25 pending','anchorPolicy':'boot support Y and annotated pelvis X; no per-pose hair-bounds recentering; common body scale per group','issues':['Retreat passing poses and cycle transitions need further visual acceptance.','Light1 grip, body displacement and sword reach are candidates.','Extracted light1 source is isolated by connected alpha components; original RGBA preserved.','Formal combat integration, simulator, device and user acceptance pending.']}
(assets/'neutral-rig-v6.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
optimized=[r['rectangles'] for r in report if r['mode']=='optimized']
summary={'poses':len(small),'reconstructions':len(report),'optimizedMax':max(optimized),'optimizedMean':round(float(np.mean(optimized)),2),'outline':'one-pixel 4-neighbor outward dark red contour; all original interior indices invariant','scope':'offline pixel encoding and extraction; not game/device validation','records':report}
(root/'production/fit-report-v6.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='records'}))

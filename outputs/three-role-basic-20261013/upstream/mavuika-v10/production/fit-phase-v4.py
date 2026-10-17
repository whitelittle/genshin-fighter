"""Encode retained generated PNG into SD rectangles; never modify source alpha."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy import ndimage
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
import artlib
root=Path(__file__).resolve().parents[1];assets=root/'dist/assets'
source=assets/'mavuika-phase-sheet-v4.png';sheet=Image.open(source).convert('RGBA')
poses={
 'ride':{'rect':[0,0,790,515],'anchor':[280,496],'scale':.42,'rootKind':'rear-wheel contact candidate'},
 'brake':{'rect':[790,0,746,520],'anchor':[645,500],'scale':.42,'rootKind':'front-wheel contact candidate'},
 'windup':{'rect':[0,515,790,509],'anchor':[500,476],'scale':.42,'rootKind':'airborne foot reference candidate'},
 'slash':{'rect':[790,520,746,504],'anchor':[407,478],'scale':.42,'rootKind':'boot support candidate'},
 'idle':{'rect':[0,0,225,300],'anchor':[151,289],'scale':2/3,'rootKind':'boot support candidate','file':'mavuika-idle-original.png'}
}
prepared={key:sheet.crop((p['rect'][0],p['rect'][1],p['rect'][0]+p['rect'][2],p['rect'][1]+p['rect'][3])) for key,p in poses.items() if key!='idle'}
prepared['idle']=Image.open(assets/'mavuika-idle-original.png').convert('RGBA')
# One shared palette for identity consistency, with coordinated dark red outline.
small={key:artlib.downscale(im,poses[key]['scale']/4) for key,im in prepared.items()}
palette=artlib.build_palette(list(small.values()),20,seed=11)+[[43,25,27]]
materials={'source':{'file':source.name,'poses':poses}};report=[]
for mode in ['initial','optimized']:
 atlas=Image.new('RGBA',(200,240));records={}
 for i,(key,im) in enumerate(small.items()):
  idx=artlib.apply_palette(im,palette)
  if mode=='optimized':
   mask=idx>=0;edge=mask&~ndimage.binary_erosion(mask,np.ones((3,3)),border_value=0)
   a=np.array(im);bright=(a[:,:,:3].max(2)>210)&(a[:,:,:3].min(2)>130)
   idx[edge&~bright]=len(palette)-1
  rects=artlib.painter(idx);encoded=artlib.render(rects,palette,im.width,im.height)
  restored=np.full(idx.shape,-1,dtype=int)
  for x,y,w,h,c in rects:restored[y:y+h,x:x+w]=c
  assert np.array_equal(restored,idx),'painter reconstruction mismatch'
  offset=[(i%2)*100,(i//2)*80];assert im.width<=100 and im.height<=80
  atlas.paste(encoded,tuple(offset))
  p=poses[key];anchor=[v*p['scale']/4 for v in p['anchor']]
  records[key]={'rect':[*offset,im.width,im.height],'anchor':anchor,'scale':4,'rootKind':p['rootKind']}
  data={'palette':palette,'width':im.width,'height':im.height,'rects':rects,'anchor':anchor,'scale':4,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceROI':p['rect'],'status':'encoding checked; visual and runtime acceptance pending'}
  (assets/f'{key}-{mode}-rects-v4.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
  report.append({'pose':key,'mode':mode,'rectangles':len(rects),'size':[im.width,im.height],'support':'manual provisional, not accepted'})
 file=f'mavuika-phase-{mode}-v4.png';atlas.save(assets/file);materials[mode]={'file':file,'poses':records}
rig={'scale':.42,'sheetSize':list(sheet.size),'poses':poses,'materials':materials,'status':'four key pose candidates; scale, anatomy, grip and alpha edges need visual acceptance'}
(assets/'rig.json').write_text(json.dumps(rig,ensure_ascii=False,indent=2)+'\n')
(root/'production/fit-report-v4.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'palette':palette,'pipeline':'premultiplied BOX / weighted OKLab / shared palette / one-pixel coordinated inner outline / painter','records':report,'scope':'offline SD encoding only; no browser, formal game or device acceptance'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report))

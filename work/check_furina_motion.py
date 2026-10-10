"""File, rectangle and spatial correspondence checks, not visual acceptance."""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
data=json.loads((O/'actions.json').read_text(encoding='utf-8'))
baseline=json.loads((O/'actions-before-missing-20261011.json').read_text(encoding='utf-8'))
assert len(data)==25
assert data['待机']==baseline['待机']
assert data['空重']==baseline['空重']
refs=0
for name,d in data.items():
 assert len(d['frames'])==len(d['sourceFrames'])==len(d['durations'])==len(d['phases']),name
 for group in [d['frames'],d['sourceFrames']]:
  for f in group:
   assert f['scale']>0
   path=O/f['file'];assert path.is_file(),path.name
   with Image.open(path) as im:im.verify()
   refs+=1
assert sum(data['前冲']['durations'])==14
assert sum(data['后撤']['durations'])==18
for label in ['前冲','后撤']:
 for field in ['frames','sourceFrames']:
  assert data[label][field][0]==data['待机'][field][0]
  assert data[label][field][-1]==data['待机'][field][0]
assert data['前冲']['motion'][-1][0]>0 and data['后撤']['motion'][-1][0]<0
rectangles=0;peak=0
for key,label in [('forwarddash','前冲'),('backdash','后撤'),('jump','跳跃'),('defeat','败北')]:
 d=data[label]
 for s,f in zip(d['sourceFrames'],d['frames']):
  if not f['file'].startswith(key):continue
  p=O/(Path(f['file']).stem+'-rects.json');r=json.loads(p.read_text(encoding='utf-8'))
  arr=np.asarray(Image.open(O/f['file']).convert('RGBA'));rebuilt=np.zeros_like(arr)
  for x,y,w,h,c in r['rects']:rebuilt[y:y+h,x:x+w]=r['palette'][c][:3]+[255]
  assert np.array_equal(arr,rebuilt),f['file']
  source=Image.open(O/s['file']);fit=Image.open(O/f['file']);rx=(fit.width-2)/source.width;ry=(fit.height-2)/source.height
  for q in s['anatomy']['headPoints']+s['anatomy']['torsoPoints']:
   old=[(q[i]-s['anchor'][i])*s['scale'] for i in range(2)]
   new=[(q[0]*rx+1-f['anchor'][0])*f['scaleX'],(q[1]*ry+1-f['anchor'][1])*f['scaleY']]
   assert all(abs(a-b)<1e-6 for a,b in zip(old,new)),(s['file'],old,new)
  rectangles+=1;peak=max(peak,len(r['rects']))
report={'actions':len(data),'bodyDisplayPoses':sum(len(d['frames']) for d in data.values()),'bodyFileReferences':refs,'newUniquePosesReconstructionChecked':rectangles,'newBodyRectanglePeak':peak,'idleSourceAndFitBankPreserved':True,'airheavyBankPreserved':True,'sourceFitLandmarkWorldPositionsMatch':True,'simulation':'not run','device':'not observed','visualAcceptance':'pending user','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*source-v[35].png') if p.name.startswith(('forwarddash','backdash','jump','defeat'))}}
(O/'移动补齐文件检查_20261011.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))

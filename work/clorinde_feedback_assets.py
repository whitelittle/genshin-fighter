"""Explicit source units after world-size review; preserve automatic conflicts."""
from clorinde_assets import O,extract,canonical_fit
from clorinde_pose_profiles import measure
from PIL import Image
from pathlib import Path
import json,hashlib,shutil,numpy as np
data=json.loads((O/'actions.json').read_text(encoding='utf-8'))
backup=O/'actions-before-feedback-v2.json'
if not backup.exists():shutil.copy2(O/'actions.json',backup)
else:data=json.loads(backup.read_text(encoding='utf-8'))
palette=json.loads((O/'palette.json').read_text())
# Manually reviewed source drawing units. These are not acceptance measurements.
# Hat/weapon/canvas extents never select a scale; no nonuniform body deformation.
units={'light1':[.54,.54,.56,.56],'walk':[.63]*6,'backwalk':[.66]*6,
 'jump':[.65]*6,'forwarddash':[.25,.56,.56,.56,.56,.25],
 'backdash':[.25,.56,.56,.56,.56,.25],'crouch':[.51]*4,
 'standguard':[.50]*4,'crouchguard':[.50]*4,'light2':[.68]*6,
 'light3':[.68]*6,'heavy':[.67]*6,'crouchlight':[.61]*6,
 'crouchheavy':[.60]*6,'airlight':[.61]*6,'airheavy':[.62,.68,.64,.32,.58,.30],
 'E':[.70]*6,'Q':[.69]*6,'throw':[.65]*6,
 'victory':[.25,.46,.46,.46,.46,.25],'defeat':[.50]*4}
seen={}
def fit_source(sf,base):
 im=Image.open(O/sf['file']).convert('RGBA')
 ff,_=canonical_fit(im,sf['anchor'],sf['scale'],palette,base)
 return ff
for key,scales in units.items():
 d=data[key]
 for i,s in enumerate(scales):
  sf=d['sourceFrames'][i]
  if sf['file'].startswith('frames/idle-'):continue
  old=sf['scale'];sf['scale']=s
  p=sf.get('landmarkProposal',{})
  if key in ['airlight','airheavy'] or (key=='jump' and i in [2,3,4]):
   if p.get('hip'):sf['anchor'][1]=p['hip'][1]+(sf['anchor'][1]-p['hip'][1])*old/s
  sf['calibrationStatus']='explicit source unit after world-scale visual review; art candidate'
  d['frames'][i]=fit_source(sf,Path(d['frames'][i]['file']).stem)
 d['sourceScalePolicy']='explicit reviewed source units, uniform XY; source proportions retained; no silhouette-height normalization'
def build(source,n,key,scales):
 items,_=extract(O/source,n);sf=[];ff=[]
 for i,((im,info),s) in enumerate(zip(items,scales)):
  name=f'frames/{key}-direction-v2-{i}.png';im.save(O/name);p=measure(im)
  ys,xs=np.where(np.asarray(im)[:,:,3]>=128);floor=float(ys.max())
  anchor=[p['hip'][0] if p.get('hip') else im.width*.55,floor]
  f={'file':name,'source':source,'scale':s,'anchor':anchor,**info,
   'landmarkProposal':p,'anchorStatus':'source-local support anchor reviewed in direction chain; candidate',
   'sourceHash':hashlib.sha256((O/name).read_bytes()).hexdigest()}
  sf.append(f);ff.append(fit_source(f,f'{key}-direction-v2-{i}'))
 return sf,ff
k=build('source/hit-knockdown-direction-v2.png',4,'knockdown',[.48,.48,.48,.48])
w=build('source/wakeup-direction-v2.png',3,'wakeup',[.36,.38,.48])
v=build('source/victim-direction-v2.png',4,'victim',[.59,.59,.59,.59])
# Correct rejected automatic distal-coat anchors on horizontal bodies.
for pair,index,x in [(k,3,390),(w,0,542),(w,2,365)]:
 pair[0][index]['anchor'][0]=x
 pair[1][index]=fit_source(pair[0][index],Path(pair[1][index]['file']).stem)
for field,j in [('sourceFrames',0),('frames',1)]:
 data['hit_knockdown'][field]=k[j]
 data['wakeup'][field]=[k[j][-1]]+w[j]+[data['idle'][field][0]]
 data['victim'][field]=v[j]+[k[j][-1],w[j][0]]
data['hit_knockdown']['durations']=[4,6,8,18]
data['wakeup']['durations']=[6,8,10,8,4]
data['victim']['durations']=data['throw']['durations']=[4,4,8,8,8,18]
for key in ['hit_knockdown','wakeup','victim']:
 data[key]['directionPolicy']='single world fall: head-left, boots-right; mirror whole scene only; shared landing and support'
# Reuse approved candidate body states across the five-stage full cinematic.
q=data['Q'];base={field:q[field][:6] for field in ['frames','sourceFrames']}
indices=[0,1,1,2,3,3,4,2,5]
for field in base:q[field]=[base[field][i] for i in indices]+[data['idle'][field][0]]
q['durations']=[6,6,30,10,18,24,24,14,10,20]
q['cinematic']={'confirmationTick':6,'cutin':[12,42],'charge':[42,52],
 'releaseTick':52,'sustain':[70,132],'hitTicks':[70,94,118],
 'fade':[132,142],'recover':[142,162],'fullStageRequires':'confirmed hit',
 'bodyReuse':'six drawn Q source poses plus idle; holds are explicit, not additional drawings'}
(O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('Revised source units, shared directional fall and 162-tick Q saved; visual candidate.')

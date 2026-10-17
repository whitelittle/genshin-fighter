from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013';results=[];missing=[];checked=0
for role in ['neuvillette','mavuika','zhongli']:
 D=O/role;bank=json.loads((D/'actions.json').read_text(encoding='utf8'))
 for k,g in bank.items():
  assert len(g['frames'])==len(g['sourceFrames'])==len(g['durations'])==len(g['phases']),(role,k)
  assert all(isinstance(n,int) and n>0 for n in g['durations'])
  for field in ['frames','sourceFrames','initialFrames']:
   for f in g.get(field,[]):
    p=D/f['file'];checked+=1
    if not p.exists():missing.append((role,k,f['file']))
  units=[f['scale'] for f in g['sourceFrames']]
  results.append({'role':role,'action':g.get('actionId',k),'states':len(g['frames']),'minSourceUnit':min(units),'maxSourceUnit':max(units),'unitRatio':max(units)/min(units),'artAccepted':False})
assert not missing,missing
rebuilds=[]
for role in ['neuvillette','mavuika','zhongli']:
 D=O/role
 for metaFile in (D/'fit').glob('*strict-20261014-*.json'):
  d=json.loads(metaFile.read_text(encoding='utf8'));target=np.array(Image.open(D/d['file']).convert('RGBA'));out=np.zeros_like(target)
  for x,y,w,h,c in d['rects']:out[y:y+h,x:x+w]=d['palette'][c]+[255]
  assert np.array_equal(target,out),metaFile
  rebuilds.append({'role':role,'file':metaFile.relative_to(O).as_posix(),'rectangles':len(d['rects']),'exact':True})
assert len(rebuilds)==20
Z=O/'zhongli';history=Z/'history/strict-review-20261014'
restored={name:hashlib.sha256((Z/name).read_bytes()).hexdigest()==hashlib.sha256((history/name).read_bytes()).hexdigest() for name in ['actions.json','offline.html','size-review.html','index.html']}
assert all(restored.values()),restored
browser=[]
for name in ['browser-dash-strict-20261014.json','browser-jump-white-20261014.json','browser-jump-dark-20261014.json']:
 items=json.loads((O/'evidence'/name).read_text(encoding='utf8'));browser.extend(items)
assert len(browser)==76
for c in browser:
 assert c['ready'] and c['selected'] in ['jump','forwarddash','backdash']
 if c['selected']=='jump' and c['phase'] in [0,1,5,6]:assert c['root'][1]==550,c
report={'scope':'independent assets and display only','activeActions':len(results),'activeReferenceChecks':checked,'missing':missing,'bodyReconstructionChecks':rebuilds,'browserPhaseStartChecks':len(browser),'zhongliRestoredExactly':restored,'sourceUnitInventory':results,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False}
(O/'checks/strict-review-20261014.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
files=[O/'index.html',R/'docs/current/三角色动作严格审查与续作_20261014.md',R/'outputs/role-design-reference-20261014/index.html',R/'outputs/role-design-reference-20261014/manifest.json']
for role in ['neuvillette','mavuika','zhongli']:
 files.append(O/role/'actions.json');files.append(O/role/'current-status.json')
manifest={'date':'2026-10-14','scope':'independent three-character art review batch','checks':'checks/strict-review-20261014.json','historicalDeliveryManifest':'delivery.json applies to 2026-10-13 snapshot only; use this revision manifest for changed entries','artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False,'files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(O/'delivery-strict-review-20261014.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'actions':len(results),'references':checked,'rebuilds':len(rebuilds),'browserChecks':len(browser),'restored':restored},ensure_ascii=False))

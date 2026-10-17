from pathlib import Path
import json,hashlib,re,zipfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'outputs/zhongli-design-20261011/full-actions';S=Path('/workspace/sites/zhongli-action-review/dist')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((F/'actions.json').read_text());assert len(a)==25
foe=json.loads((F/'foe-fitted.json').read_text())
for group,indices in {'basic':[0],'hurt':[2,3],'guard':[0,1,2],'victim':[0,1,2,3],'throw':[0,1,2,3]}.items():
 for i in indices:assert (F/foe[f'{group}_{i}']['file']).exists()
for key,d in a.items():
 assert len(d['durations'])==len(d['frames'])==len(d['phases'])==len(d['sourceFrames'])==len(d['initialFrames']),key
 assert all(isinstance(v,int) and v>0 for v in d['durations'])
 for kind in ('sourceFrames','frames','initialFrames'):
  for f in d[kind]:assert (F/f['file']).is_file(),f
 for e in d['events']:assert 0<=e['tick']<sum(d['durations']),e
assert a['E · 地心']['combatDesign']['passiveDamage'] is False
e=a['E · 地心'];assert e['bodyActionTicks']==36 and sum(e['durations'])>=e['effects']['startTick']+e['effects']['duration'];assert sum(x.get('damageSegments',0) for x in e['events'])==1
q=a['Q · 天星'];assert q['branches']['hit']['damageSegments']==1;assert q['events'][0]['damageSegments']==0
for k in ('whiff','block'):assert q['branches'][k]['cinematic'] is False and q['branches'][k]['damageSegments']==0
pair=a['投技']['pairing'];assert pair['lockTicks'][1]==pair['releaseTick']<pair['landingTick'];assert pair['noFX']
reconstructed=0
for p in (F/'rects').glob('*.json'):
 d=json.loads(p.read_text());im=Image.open(F/('ultimate-portrait-fit.png' if p.stem=='portrait' else 'fitted/'+p.stem+'.png')).convert('RGBA');arr=np.array(im);out=np.zeros_like(arr)
 for x,y,w,h,c in d['rects']:
  assert 0<=x<x+w<=d['width'] and 0<=y<y+h<=d['height'];out[y:y+h,x:x+w,:3]=d['palette'][c];out[y:y+h,x:x+w,3]=255
 assert np.array_equal(arr,out),p
 assert digest(F/('ultimate-portrait-fit.png' if p.stem=='portrait' else 'fitted/'+p.stem+'.png'))==d['fittedSHA256']
 reconstructed+=1
errors=[]
for p in S.rglob('*'):
 if not p.is_file() or 'material-assets' in p.relative_to(S).parts:continue
 if p.suffix=='.png':Image.open(p).load()
 if p.suffix=='.html':
  txt=p.read_text()
  for src in re.findall(r'(?:src|href)="([^"]+)"',txt):
   if src.startswith(('http','data:','#')):continue
   dst=(p.parent/src.split('#')[0].split('?')[0]);dst=dst/'index.html' if src.endswith('/') else dst
   if not dst.exists():errors.append([str(p.relative_to(S)),src])
  for embedded in re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',txt,re.S):
   data=json.loads(embedded)
   def refs(v):
    if isinstance(v,dict):
     for k,x in v.items():
      if k in ('file','source') and isinstance(x,str) and x.endswith('.png') and not (p.parent/x).exists():errors.append([str(p.relative_to(S)),x])
      refs(x)
    elif isinstance(v,list):
     for x in v:refs(x)
   refs(data)
vol=json.loads((S/'downloads/volumes.json').read_text());n=0
for v in vol:
 assert v['bytes']<=18*1024**2
 for f in v['files']:
  path=S/f['url'];assert path.stat().st_size==f['bytes'];assert digest(path)==f['sha256'];n+=1
assert not errors,errors[:30]
report={'actionGroups':len(a),'displayPoses':sum(len(d['frames']) for d in a.values()),'painterRasterRoundTrips':reconstructed,'downloadVolumes':len(vol),'downloadSourceHashesVerified':n,'staticAndEmbeddedLinks':'passed','allSitePNGsDecode':'passed','browserQA':'not available / not performed','gameRuntime':'not integrated','device':'not observed'}
(F/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))

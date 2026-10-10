"""Small reproducible delivery audit; no aesthetic or combat acceptance."""
from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/v4-one-character-20261010/ayaka-armed-v2'
d=json.loads((O/'actions.json').read_text(encoding='utf-8'))
assert len(d)==25
manifest=[]
for name,a in d.items():
 assert len(a['frames'])==len(a['durations'])==len(a['phases'])
 source=a.get('sourceFrames') or a['frames'];assert len(source)==len(a['frames'])
 lists=[a['frames'],source]
 if a.get('effects'):lists += [a['effects']['sourceFrames'],a['effects']['fitFrames']]
 for group in lists:
  for f in group:
   p=O/f['file'];assert p.exists(),p.name
   with Image.open(p) as im:im.verify()
   assert len(f['anchor'])==2 and f['scale']>0
 manifest.append({'action':name,'poses':len(a['frames']),'duration':sum(a['durations']),'sourceFiles':[f['file'] for f in source],'fitFiles':[f['file'] for f in a['frames']],'effects':bool(a.get('effects')),'runtimeIntegrated':False})
assert d['站立格挡']['frames'][0]['file']!=d['站立格挡']['sourceFrames'][0]['file']
assert len(d['投技']['events'])==1 and d['投技']['events'][0]['tick']==44
assert d['被投']['continuation']['atTick']==44
for name in ['ultimate-portrait.png','ultimate-portrait-fit.png']:assert (O/name).exists()
report={'actions':manifest,'bodyPoses':sum(a['poses'] for a in manifest),'verification':'file/PNG/shape only','simulation':'not run','device':'not observed','nextCharacter':'not started','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.suffix in ['.png','.js','.json','.html','.css'] and p.name!='交付核查.json'}}
(O/'交付核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'actions':len(d),'bodyPoses':report['bodyPoses'],'fileChecks':'passed','runtimeIntegrated':False},ensure_ascii=False))

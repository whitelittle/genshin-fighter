from pathlib import Path
import json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
r=json.loads((O/'light3-consistency-report.json').read_text(encoding='utf-8'));a=r['before'];b=r['after']
assert a['durations']==b['durations'] and a['phases']==b['phases']
for key in ['combatDesign','effects','events']:assert a.get(key)==b.get(key)
for i in range(4):
 for key in ['frames','sourceFrames']:assert a[key][i]==b[key][i]
assert r['changedFrames']==[4,5]
for i in [4,5]:
 f=b['sourceFrames'][i];assert 'scaleX' not in f and 'scaleY' not in f
 deviations=f['proportionTrial']['segmentDeviation']
 assert all(abs(d)<=t+1e-8 for d,t in zip(deviations,r['tolerances']))
assert b['sourceFrames'][4]['file']==a['sourceFrames'][4]['file']
assert b['sourceFrames'][5]['file']!=a['sourceFrames'][5]['file']
source=Image.open(O/b['sourceFrames'][5]['file']);assert source.mode=='RGBA' and source.getchannel('A').getextrema()==(0,255)
f=b['frames'][5];meta=json.loads((O/f['file']).with_suffix('.rects.json').read_text(encoding='utf-8'))
bottom=(meta['bodyBoundingBox'][3]+1-f['anchor'][1])*f['scale'];assert abs(bottom)<=4.5,(bottom,'boot contact')
print(json.dumps({'trialChecks':'pass','changedDisplayFrames':[5,6],'recoveryContactErrorWorld':bottom,'visualAcceptance':False}))

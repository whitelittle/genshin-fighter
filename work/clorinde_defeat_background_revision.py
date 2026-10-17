from pathlib import Path
import json
from PIL import Image
from clorinde_assets import O,canonical_fit
p=O/'player.js'
s=p.read_text(encoding='utf-8')
if " ctx.strokeStyle='#aab8ea';" in s:
 start=s.index(" ctx.strokeStyle='#aab8ea';")
 end=s.index('ctx.restore()}',start)+len('ctx.restore()}')
 s=s[:start]+" const glow=ctx.createRadialGradient(840,190,0,840,190,380);glow.addColorStop(0,'#7774aa30');glow.addColorStop(1,'#7774aa00');ctx.fillStyle=glow;ctx.fillRect(0,0,1200,545);ctx.restore()}"+s[end:]
# Cut-in bars are also background decoration; use its solid panel without border lines.
s=s.replace("ctx.fillStyle='#7976b3';ctx.fillRect(0,100,1200,3);ctx.fillRect(0,317,1200,3);",'')
p.write_text(s,encoding='utf-8')
d=json.loads((O/'actions.json').read_text(encoding='utf-8'));pal=json.loads((O/'palette.json').read_text())
for i,sf in enumerate(d['defeat']['sourceFrames']):
 sf['scale']=.50
 sf['calibrationStatus']='mother-unit comparison: first-pose torso 95.19 vs mother 94.24; face span 15.54 vs mother 15.65; uniform source unit for all four poses; candidate'
 ff,_=canonical_fit(Image.open(O/sf['file']).convert('RGBA'),sf['anchor'],sf['scale'],pal,Path(d['defeat']['frames'][i]['file']).stem)
 d['defeat']['frames'][i]=ff
(O/'actions.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('Q decorative background lines removed; defeat source units .57 -> .50')

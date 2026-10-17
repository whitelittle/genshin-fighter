from pathlib import Path
from PIL import Image
import json,numpy as np
p=Path('outputs/arlecchino-actions-20261011');d=json.loads((p/'actions.json').read_text(encoding='utf-8'));b={}
for key,index,hint in [('E',1,(1175,100)),('Q',3,(446,664))]:
 f=d[key]['sourceFrames'][index];a=np.array(Image.open(p/f['file']).convert('RGBA'));x=hint[0]-f['sourceOrigin'][0];y=hint[1]-f['sourceOrigin'][1];yy,xx=np.where((a[:,:,3]>=180)&(a[:,:,:3].max(axis=2)<135));mask=(abs(xx-x)<35)&(abs(yy-y)<35);xx=xx[mask];yy=yy[mask];assert len(xx);i=np.argmin((xx-x)**2+(yy-y)**2);b[key]={'frameIndex':index,'point':[int(xx[i]),int(yy[i])],'binding':'actual dark palm source pixels'}
(p/'fx-bindings.json').write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding='utf-8');(p/'fx-binding-data.js').write_text('window.ARLECCHINO_FX_BINDINGS='+json.dumps(b)+';',encoding='utf-8')
p=p/'player-v2.js';s=p.read_text(encoding='utf-8');s=s.replace("if(time>=4&&time<16)effect('guide',x+90,y-240,Math.sin((time-4)/12*Math.PI));", "if(time>=4&&time<10){const b=window.ARLECCHINO_FX_BINDINGS.E,q=point(b.point,active.sourceFrames[b.frameIndex],actor);effect('guide',...q,Math.sin((time-4)/6*Math.PI))}")
s=s.replace("effect('mark',foe.x,foe.y-290,.9)", "effect('mark',foe.x,Math.max(30,foe.y-active.foeData[foe.key].ay*active.foeData[foe.key].scale-25),.9)")
s=s.replace("if(time>=42&&time<52)effect('guide',x+30,y-240,(time-42)/10);", "if(time>=42&&time<52){const b=window.ARLECCHINO_FX_BINDINGS.Q,q=point(b.point,active.sourceFrames[b.frameIndex],actor);effect('guide',...q,(time-42)/10)}")
p.write_text(s,encoding='utf-8')
for f in [p.parent/'player.html',p.parent/'index.html']:
 s=f.read_text(encoding='utf-8')
 if '<script src="fx-binding-data.js"></script>' not in s:s=s.replace('<script src="player-v2.js">','<script src="fx-binding-data.js"></script><script src="player-v2.js">')
 f.write_text(s,encoding='utf-8')
print(json.dumps(b))

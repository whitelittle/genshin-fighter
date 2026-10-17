from pathlib import Path
from PIL import Image
import numpy as np,json
p=Path('outputs/arlecchino-actions-20261011');d=json.loads((p/'actions.json').read_text(encoding='utf-8'));seen=set();occupied={};issues=[]
for action in [a for main in d.values() for a in [main]+[{**main,**v} for v in main.get('variants',{}).values()]]:
 for f in action['sourceFrames']:
  if f['file'] in seen:continue
  seen.add(f['file']);raw=Image.open(p/f['source']);counts=occupied.setdefault(f['source'],np.zeros((raw.height,raw.width),dtype='uint16'));mask=np.array(Image.open(p/f['file']))[:,:,3]>=250;x0,y0,x1,y1=f['roi'];area=counts[y0:y1,x0:x1];over=int(((area>0)&mask).sum())
  if over:issues.append({'file':f['file'],'overlappingOpaquePixels':over})
  area[mask]+=1
report={'uniqueObjects':len(seen),'sourceSheets':len(occupied),'opaqueOwnershipOverlap':issues,'status':'passed' if not issues else 'failed'};(p/'extraction-ownership-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))

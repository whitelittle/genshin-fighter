from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('work/video-deps').resolve()))
import cv2
import numpy as np
from PIL import Image
root=Path(sys.argv[1] if len(sys.argv)>1 else 'outputs/motion-production')
result={}
for p in root.glob('*.png'):
    a=np.array(Image.open(p).convert('RGBA'))[:,:,3]
    n,labels,stats,centers=cv2.connectedComponentsWithStats((a>=220).astype('uint8'),8)
    components=[]
    for i in range(1,n):
        x,y,w,h,area=map(int,stats[i])
        if area>700:components.append({'box':[x,y,w,h],'area':area,'center':centers[i].tolist()})
    result[p.name]={'size':[int(a.shape[1]),int(a.shape[0])],'transparent':int((a==0).sum()),'partial':int(((a>0)&(a<220)).sum()),'components':components}
(root/'source-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for name,data in result.items():
    print(name,len(data['components']),[c['box'] for c in data['components']])

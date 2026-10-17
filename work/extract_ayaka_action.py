"""Extract separated sprite objects, retaining ROI and one action scale."""
from pathlib import Path
from collections import deque
import json
import sys
from PIL import Image

root=Path(__file__).resolve().parents[1]/'outputs/v4-one-character-20261010/ayaka-armed-v2'
key,count,scale=sys.argv[1],int(sys.argv[2]),float(sys.argv[3])
source=f'{key}-source-v4.png' if (root/f'{key}-source-v4.png').exists() else f'{key}-source-clean-v3.png' if (root/f'{key}-source-clean-v3.png').exists() else f'{key}-source-v3.png'
im=Image.open(root/source).convert('RGBA');w,h=im.size
a=im.getchannel('A').tobytes();seen=bytearray(w*h);objects=[]
for p in range(w*h):
    if seen[p] or a[p]<64:continue
    q=deque([p]);seen[p]=1;pts=[]
    while q:
        v=q.popleft();pts.append(v);x=v%w;y=v//w
        for z in (v-1 if x else -1,v+1 if x<w-1 else -1,v-w if y else -1,v+w if y<h-1 else -1):
            if z>=0 and not seen[z] and a[z]>=64:seen[z]=1;q.append(z)
    if len(pts)>1500:objects.append(pts)
objects=sorted(objects,key=len,reverse=True)[:count]
if len(objects)!=count:raise RuntimeError(f'Need {count} separate poses, found {len(objects)}')
boxes=[(min(v%w for v in p),min(v//w for v in p),max(v%w for v in p)+1,max(v//w for v in p)+1) for p in objects]
rows=2 if count==6 or w/h<2 else 1
order=sorted(range(count),key=lambda i:((boxes[i][1]+boxes[i][3])//2//(h//2) if rows==2 else 0,boxes[i][0]))
frames=[]
for n,i in enumerate(order):
    b=boxes[i];mask=Image.new('L',im.size);mp=mask.load()
    for v in objects[i]:mp[v%w,v//w]=a[v]
    f=im.copy();f.putalpha(mask);f=f.crop(b);name=f'{key}-{n}.png';f.save(root/name)
    if key=='victim' and n in [1,2,3]:anchor=[f.width/2,f.height/2]
    else:anchor=[f.width/2,f.height-1]
    frames.append({'file':name,'anchor':anchor,'scale':scale,'roi':list(b),'source':source})
config={'crouchguard':('蹲防',[10,24,10,24],['进入','保持','受力','恢复']),
        'throw':('投技',[10,14,10,10,6,22],['抓取','上挑','腾空','下砸','落地','恢复']),
        'victim':('被投',[10,14,10,10,6,22],['被抓','上升','腾空','下落','落地','倒地'])}
label,durations,phases=config[key]
data={'frames':frames,'sourceFrames':frames,'durations':durations,'phases':phases,'status':'',
      'events':[{'tick':44,'kind':'slam','damageSegments':1}] if key in ['throw','victim'] else [],'previewOnly':True}
target=root/'new-actions.json';all_data=json.loads(target.read_text(encoding='utf-8')) if target.exists() else {};all_data[label]=data
target.write_text(json.dumps(all_data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'action':label,'boxes':[boxes[i] for i in order],'counts':[len(objects[i]) for i in order]},ensure_ascii=False))

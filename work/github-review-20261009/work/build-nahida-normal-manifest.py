from pathlib import Path
import json
import numpy as np
from PIL import Image
root=Path('outputs/motion-production/nahida-normal-v2')
audit=json.loads((root/'source-audit.json').read_text(encoding='utf-8'))
role={'key':'nahida','name':'纳西妲 · 正常比例','height':150,'variant':'normal-v2','frames':[],'notes':['以正常比例待机母版重制整套姿势，儿童身高150不变。','48张姿势：基础16、攻击16、普攻/E连接16。普攻与E各8帧，其他状态仍以关键姿势为主。','脚底自动初估，服饰、手指、比例与锚点为美术候选，不代表真机验收。']}
for kind in ['basic','attack','connections']:
    source=kind+'-v1.png'; data=audit[source]; W,H=data['size']; ordered=[]
    for row in range(4):
        cs=[c for c in data['components'] if int(c['center'][1]*4/H)==row]
        cs.sort(key=lambda c:c['center'][0]); assert len(cs)==4,(kind,row,len(cs));ordered.extend(cs)
    ref=ordered[15 if kind=='attack' else 0]['box'][3]
    arr=np.array(Image.open(root/source).convert('RGBA'))
    for i,c in enumerate(ordered):
        x,y,w,h=c['box']; box=[max(0,x-3),max(0,y-3),min(W,x+w+3)-max(0,x-3),min(H,y+h+3)-max(0,y-3)]
        center=c['center'][0]; l=max(x,int(center-w*.22)); r=min(x+w,int(center+w*.22)+1)
        ys,xs=np.where(arr[y:y+h,l:r,3]>=220); foot=y+int(ys.max())+1
        yy,xx=np.where(arr[max(y,foot-8):foot,l:r,3]>=220); ax=l+float(xx.mean()) if len(xx) else center
        if kind=='attack' and i in [6,7]:foot=y+h
        actual=ordered[8]['box'][3] if kind=='connections' and i>=8 else ref
        role['frames'].append({'id':kind+str(i),'source':source,'sourceIndex':i,'crop':box,'anchor':[ax-box[0],foot-box[1]],'unit':150/actual,'review':'candidate','edgeRisk':x==0 or y==0 or x+w>=W or y+h>=H})
out={'version':'nahida-normal-v2','status':'normal_proportion_action_candidate','deviceVerified':False,'productionCombatChanged':False,'roles':[role]}
(root/'source-manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('NAHIDA_NORMAL_MANIFEST',len(role['frames']))

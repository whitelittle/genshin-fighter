from pathlib import Path
import json
from PIL import Image
import numpy as np
root=Path('outputs/motion-production')
audit=json.loads((root/'source-audit.json').read_text(encoding='utf-8'))
plan=json.loads((root/'batch-plan.json').read_text(encoding='utf-8'))
out={'version':1,'status':'keyframe_playback_candidate','deviceVerified':False,'productionCombatChanged':False,'roles':[]}
for key,name in plan['samples']:
    role={'key':key,'name':name,'height':150 if key=='nahida' else 232,'frames':[],'notes':[]}
    for kind,version in [('basic',1),('attack',2 if key in ['keqing','kamisatoayaka'] else 1),('connections',1)]:
        source=f'{key}-{kind}-v{version}.png'; data=audit[source]; W,H=data['size']; rows=[]
        for row in range(4):
            cs=[c for c in data['components'] if int(c['center'][1]*4/H)==row]
            cs.sort(key=lambda c:c['center'][0]); assert len(cs)==4,(source,row,len(cs));rows.extend(cs)
        reference=rows[15 if kind=='attack' else 0]['box'][3]
        for i,comp in enumerate(rows):
            x,y,w,h=comp['box']; box=[max(0,x-3),max(0,y-3),min(W,x+w+3)-max(0,x-3),min(H,y+h+3)-max(0,y-3)]
            arr=np.array(Image.open(root/source).convert('RGBA'))
            # Estimate support from opaque pixels in the body's central band; reviewable metadata, not image edits.
            center=comp['center'][0]; l=max(x,int(center-w*.22)); r=min(x+w,int(center+w*.22)+1)
            ys,xs=np.where(arr[y:y+h,l:r,3]>=220)
            foot=y+int(ys.max())+1
            bottom=arr[max(y,foot-8):foot,l:r,3]>=220
            by,bx=np.where(bottom); anchorx=l+float(bx.mean()) if len(bx) else center
            if kind=='attack' and i in [6,7]:foot=y+h
            actual_reference=rows[8]['box'][3] if kind=='connections' and i>=8 else reference
            f={'id':kind+str(i),'source':source,'crop':box,'anchor':[anchorx-box[0],foot-box[1]],'unit':role['height']/actual_reference,'sourceIndex':i,'review':'candidate','edgeRisk':x==0 or y==0 or x+w>=W or y+h>=H}
            role['frames'].append(f)
    if key=='diluc':
        source='diluc-overhead-v1.png'; c=max(audit[source]['components'],key=lambda c:c['area']); x,y,w,h=c['box']
        f=next(f for f in role['frames'] if f['id']=='attack1')
        f.update(source=source,crop=[x,y,w,h],anchor=[w*.68,h],unit=203/(h*.65),edgeRisk=False,review='single_pose_repair_candidate')
    role['notes'].append('基础16张、攻击16张、普攻与特殊技连接16张；连接帧真实生成，其他短动作仍为关键姿势。锚点自动初估，需逐帧复核。')
    out['roles'].append(role)
(root/'source-manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('MANIFEST',len(out['roles']),sum(len(r['frames']) for r in out['roles']))

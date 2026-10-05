"""Read-only source image audit/crop metadata; fitting is delegated to existing native tool."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
root=Path(sys.argv[1]); config=json.loads((root/'role-design.json').read_text(encoding='utf-8-sig'))
audit=json.loads((root/'source-audit.json').read_text(encoding='utf-8'))
suffix=config.get('sourceVersion','v2')
role=dict(key=config['key'],name=config['name']+' · 第一组',height=config['height'],variant='group1-'+suffix,design=config['design'],frames=[],notes=config['notes'])
for kind in ['basic','attack','connections']:
    source=kind+'-'+suffix+'.png'; data=audit[source]; W,H=data['size']
    components=data['components']
    if config['key'] in ['ganyu','yaemiko'] and kind=='connections' and len(components)>16:
        # One thin bow is alpha-disconnected from its hand. Preserve it in the same actor crop.
        ranked=sorted(components,key=lambda c:c['area'],reverse=True)
        assert all(c['area']<ranked[15]['area']/4 for c in ranked[16:]),'extra actor-sized figure cannot be discarded'
        bodies=ranked[:16]
        for extra in ranked[16:]:
            ex,ey,ew,eh=extra['box']
            def gap(c):
                x,y,w,h=c['box'];return max(x-(ex+ew),ex-(x+w),0)**2+max(y-(ey+eh),ey-(y+h),0)**2
            owner=min(bodies,key=gap);assert gap(owner)<70**2,'detached bow too far from its actor'
            x,y,w,h=owner.get('cropUnion',owner['box']);left=min(x,ex);top=min(y,ey)
            owner['cropUnion']=[left,top,max(x+w,ex+ew)-left,max(y+h,ey+eh)-top]
        role.setdefault('preservedDisconnectedWeapons',{})[source]=ranked[16:]
        components=bodies
    if config['key'] in ['klee','kirara'] and len(components)>16:
        # Detached thrown bombs / courier boxes belong to independent projectile visuals.
        ranked=sorted(components,key=lambda c:c['area'],reverse=True)
        assert all(c['area']<ranked[15]['area']/4 for c in ranked[16:]),'unexpected extra actor-sized component'
        role.setdefault('externalProjectileComponents',{})[source]=ranked[16:]
        components=ranked[:16]
    cs=sorted(components,key=lambda c:c['center'][1])
    assert len(cs)==16,(source,'expected 16 separate figures',len(cs))
    ordered=[]
    for row in range(4):
        group=cs[row*4:row*4+4];group.sort(key=lambda c:c['center'][0]);ordered.extend(group)
    arr=np.array(Image.open(root/source).convert('RGBA'))
    ref=ordered[15 if kind=='attack' else 0]['box'][3]
    for i,c in enumerate(ordered):
        x,y,w,h=c['box'];cx,cy,cw,ch=c.get('cropUnion',c['box']);bx=max(0,cx-3);by=max(0,cy-3)
        edge=cx==0 or cy==0 or cx+cw>=W or cy+ch>=H
        assert not edge,(source,i,'source clipped at edge')
        center=c['center'][0];l=max(x,int(center-w*.22));r=min(x+w,int(center+w*.22)+1)
        ys,xs=np.where(arr[y:y+h,l:r,3]>=220);foot=y+int(ys.max())+1
        yy,xx=np.where(arr[max(y,foot-8):foot,l:r,3]>=220)
        ax=l+float(xx.mean()) if len(xx) else center
        actual=ordered[8]['box'][3] if kind=='connections' and i>=8 else ref
        role['frames'].append(dict(id=kind+str(i),source=source,sourceIndex=i,crop=[bx,by,min(W,cx+cw+3)-bx,min(H,cy+ch+3)-by],anchor=[ax-bx,foot-by],unit=config['height']/actual,review='candidate',edgeRisk=edge))
(root/'source-manifest.json').write_text(json.dumps(dict(version='group1-v2',status='art_candidate',deviceVerified=False,productionCombatChanged=False,roles=[role]),ensure_ascii=False,indent=2),encoding='utf-8')
print(config['key'],'48 pose metadata prepared; anchors require visual review')

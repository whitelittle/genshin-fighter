from pathlib import Path
import json
import numpy as np
from PIL import Image
root=Path('outputs/motion-group1/kaeya')
audit=json.loads((root/'source-audit.json').read_text(encoding='utf-8'))
def move(name,startup,active,recovery,reach,damage,fx,notes):
    return dict(name=name,startup=startup,active=active,recovery=recovery,reach=reach,damage=damage,fx=fx,notes=notes,height='mid',hitCount=1,blockstun=12,hitstun=20,effectExtent=reach+22)
design={'key':'kaeya','name':'凯亚','weapon':'sword','color':'#87cdf0','identity':'冰系单手剑中距离控制；不以大光团掩盖剑路。','evidence':'旧项目造型参考；原作E冰霜前放、Q冰棱环绕改编为演出候选，数值非正式战斗。','moves':{'A':move('仪典剑术 · 前横斩',9,4,18,145,9,'slash','肩肘与重心先带动刀路，不把图像旋转当动画。'),'E':move('霜袭 · 前方冰霜',16,5,25,210,15,'icecone','角色先出掌；冰霜主体另建，不画入动作源板。'),'Q':move('凛冽轮舞 · 冰棱终击',27,5,30,240,32,'iceorbit','首击成功后冰棱围绕对手短演出，终击结算；非持续状态版。')}}
role={'key':'kaeya','name':'凯亚 · 第一组','height':226,'variant':'group1-v1','design':design,'frames':[],'notes':['第一组首位48张姿势候选，正常成年比例。','普攻/E各8张，其他状态主要是关键姿势。','特效独立预览，具体冰霜与冰棱视觉待讨论；暂未接入正式战斗。']}
for kind in ['basic','attack','connections']:
    source=kind+'-v1.png';data=audit[source];W,H=data['size'];ordered=[]
    for row in range(4):
        cs=[c for c in data['components'] if int(c['center'][1]*4/H)==row];cs.sort(key=lambda c:c['center'][0]);assert len(cs)==4,(kind,row,len(cs));ordered.extend(cs)
    arr=np.array(Image.open(root/source).convert('RGBA'));ref=ordered[15 if kind=='attack' else 0]['box'][3]
    for i,c in enumerate(ordered):
        x,y,w,h=c['box'];bx=max(0,x-3);by=max(0,y-3);box=[bx,by,min(W,x+w+3)-bx,min(H,y+h+3)-by]
        center=c['center'][0];l=max(x,int(center-w*.22));r=min(x+w,int(center+w*.22)+1);ys,xs=np.where(arr[y:y+h,l:r,3]>=220);foot=y+int(ys.max())+1
        yy,xx=np.where(arr[max(y,foot-8):foot,l:r,3]>=220);ax=l+float(xx.mean()) if len(xx) else center
        actual=ordered[8]['box'][3] if kind=='connections' and i>=8 else ref
        role['frames'].append({'id':kind+str(i),'source':source,'sourceIndex':i,'crop':box,'anchor':[ax-bx,foot-by],'unit':226/actual,'review':'candidate','edgeRisk':x==0 or y==0 or x+w>=W or y+h>=H})
(root/'source-manifest.json').write_text(json.dumps({'version':'group1-kaeya-v1','status':'art_candidate','deviceVerified':False,'productionCombatChanged':False,'roles':[role]},ensure_ascii=False,indent=2),encoding='utf-8')
print('KAEYA_MANIFEST',len(role['frames']))

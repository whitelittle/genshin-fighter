"""Import delivered idle/portrait rectangles without altering original candidate art."""
from pathlib import Path
import json,struct,hashlib
from export_furina import lua
ROOT=Path(__file__).resolve().parents[2]
data={};receipt={}
for key in ('clorinde','arlecchino'):
    src=ROOT/f'outputs/{key}-actions-20261011'
    frames=json.loads((src/'actions.json').read_text(encoding='utf-8'))['idle']['frames']
    idle=frames[0]
    def image(frame,portrait=False):
        meta=src/frame['rectData'];obj=json.loads(meta.read_text(encoding='utf-8'))
        path=src/frame['file'];w,h=struct.unpack('>II',path.read_bytes()[16:24])
        crop=[8,0,32,32] if portrait else [0,0,w,h]
        cx,cy,cw,ch=crop
        scale=32/cw if portrait else frame['scale']
        clipped=[]
        for x,y,rw,rh,c in obj['rects']:
            x0,y0=max(x,cx),max(y,cy);x1,y1=min(x+rw,cx+cw),min(y+rh,cy+ch)
            if x1>x0 and y1>y0:clipped.append([x0-cx,y0-cy,x1-x0,y1-y0,c])
        rects=[v*scale if i<4 else v for r in clipped for i,v in enumerate(r)]
        return {'n':len(clipped),'bytes':rects,'pal':[c[:3]+[c[3] if len(c)>3 else 255] for c in obj['palette']],
                'ax':cw*scale/2 if portrait else frame['anchor'][0]*scale,
                'ay':ch*scale if portrait else frame['anchor'][1]*scale,
                'u':1,'w':cw*scale,'h':ch*scale,'seam':.08*scale}, {'file':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rectSha256':hashlib.sha256(meta.read_bytes()).hexdigest(),'scale':scale,'anchor':frame['anchor'],'displayCrop':crop}
    portrait=json.loads((src/'portrait-fit.json').read_text(encoding='utf-8'))
    body,body_receipt=image(idle);face,face_receipt=image(portrait,True)
    data[key]={'idle':body,'face':face}
    receipt[key]={'idle':body_receipt,'face':face_receipt,'scope':'selection idle/portrait only; not battle integration'}
(ROOT/'runtime/source/assets/gf_selection_candidates.lua').write_text("__loaders['gf_selection_candidates']=function()return "+lua(data)+' end\n',encoding='utf-8')
(ROOT/'runtime/selection-candidate-import.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print('Clorinde and Arlecchino delivered idle/portraits imported')

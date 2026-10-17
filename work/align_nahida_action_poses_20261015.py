"""Use HD optical-flow correspondence to seed native geometry, then re-fit."""
import copy,json,math
from pathlib import Path
import numpy as np
from PIL import Image
code=Path('work/optimize_nahida_primitives_20261015.py').read_text(encoding='utf-8')
exec(code[:code.index('baseline=actual_measure')],globals())
import cv2
ROOT=Path('outputs/nahida-two-actions-20261015')
seed=json.loads(Path('outputs/nahida-native-budget1000-20261015/collage.json').read_text(encoding='utf-8'))
manifest=json.loads((ROOT/'animation.json').read_text(encoding='utf-8'))
W,H=384,512;yy,xx=np.mgrid[:H,:W].astype(np.float32);xx+=.5;yy+=.5
ref0=np.array(Image.open(ROOT/'idle/0/reference.png').convert('RGBA'))
ref0rgb=ref0[:,:,:3].copy();ref0rgb[ref0[:,:,3]==0]=255
rows=[]
for action in manifest['actions']:
    action['name']='基础姿势组' if action['key']=='idle' else '移动姿势组'
    for frame in action['frames']:
        OUT=ROOT/action['key']/str(frame['index'])
        source=Image.open(OUT/'reference.png').convert('RGBA');raw=np.array(source)
        targetA=(raw[:,:,3]>=48).astype(np.float32);target=raw[:,:,:3].astype(np.float32)/255;target[targetA==0]=1
        lum=target.mean(axis=2);gy,gx=np.gradient(lum);weights=1+np.clip(np.hypot(gx,gy)*8,0,2)
        old=json.loads((OUT/'collage.json').read_text(encoding='utf-8'))['elements']
        before=actual_measure(old,'before-alignment')
        lx,ly,hx,hy=source.getchannel('A').getbbox();sx=(hx-lx)/251;sy=(hy-ly)/462
        M=np.array([[sx,0,lx-59*sx],[0,sy,ly-19*sy]],np.float32)
        warped=cv2.warpAffine(ref0rgb,M,(W,H),borderValue=(255,255,255))
        goal=(target*255).astype(np.uint8)
        dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        flow=dis.calc(cv2.cvtColor(warped,cv2.COLOR_RGB2GRAY),cv2.cvtColor(goal,cv2.COLOR_RGB2GRAY),None)
        def mapping(x,y):
            ix=int(np.clip(round(x),0,W-1));iy=int(np.clip(round(y),0,H-1))
            dx,dy=flow[iy,ix];return np.array([x+float(dx),y+float(dy)])
        elements=copy.deepcopy(seed['elements'])
        for e in elements:
            x=lx+e['x']*sx;y=ly+e['y']*sy;w=e['width']*sx;h=e['height']*sy;r=math.radians(-e['rotation'])
            center=mapping(x,y);u=np.array([math.cos(r),math.sin(r)]);v=np.array([-math.sin(r),math.cos(r)])
            dw=min(max(w*.5,1),8);dh=min(max(h*.5,1),8)
            wu=(mapping(x+u[0]*dw,y+u[1]*dw)-mapping(x-u[0]*dw,y-u[1]*dw))/(2*dw)
            hv=(mapping(x+v[0]*dh,y+v[1]*dh)-mapping(x-v[0]*dh,y-v[1]*dh))/(2*dh)
            e.update(x=float(center[0]),y=float(center[1]),width=w*float(np.clip(np.linalg.norm(wu),.55,1.7)),height=h*float(np.clip(np.linalg.norm(hv),.55,1.7)),rotation=-math.degrees(math.atan2(wu[1],wu[0])))
        aligned=actual_measure(elements,'flow-seed')
        chosen=aligned['foregroundRGBMAE']<before['foregroundRGBMAE'] and aligned['wholeCanvasRGBMSE']<before['wholeCanvasRGBMSE']
        if chosen:
            initial=copy.deepcopy(elements);history=[];masks=[mask(e) for e in elements]
            loop=code[code.index('for sweep,step in enumerate'):code.index('# Select by actual rendered SVG')]
            loop=loop.replace('[4,2,1,.5]','[2, .75]').replace('if delete_loss<=bestloss+.2:','if False:')
            exec(loop,globals());refined=actual_measure(elements,'flow-refined')
            chosen=refined['foregroundRGBMAE']<before['foregroundRGBMAE'] and refined['wholeCanvasRGBMSE']<before['wholeCanvasRGBMSE']
        if chosen:
            actual_measure(elements,'fitted');frame['elements']=elements
            (OUT/'collage.json').write_text(json.dumps({'w':W,'h':H,'elements':elements},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        else:elements=old;refined=before
        rows.append({'action':action['key'],'frame':frame['index'],'before':before,'flowSeed':aligned,'accepted':chosen,'final':refined})
        print('ALIGNMENT '+json.dumps(rows[-1]),flush=True)
(ROOT/'animation.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(ROOT/'alignment-report.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')

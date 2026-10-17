"""Fit two HD pose sequences with one fixed native shape dictionary."""
import copy,json,math,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
code=Path('work/optimize_nahida_primitives_20261015.py').read_text(encoding='utf-8')
exec(code[:code.index('baseline=actual_measure')],globals())
BASE=Path('outputs/nahida-native-budget1000-20261015')
OUTPUT=Path('outputs/nahida-two-actions-20261015');OUTPUT.mkdir(parents=True,exist_ok=True)
seed=json.loads((BASE/'collage.json').read_text(encoding='utf-8'))
W,H=384,512;yy,xx=np.mgrid[:H,:W].astype(np.float32);xx+=.5;yy+=.5
actions=[];allrows=[]
for action,sourcefile,indices in [('idle','nahida-basic.png',[0,2,4,6]),('move','nahida-move.png',[4,5,6,7])]:
    sheet=Image.open(Path('work/github-review-20261009/V3/assets/animation-source')/sourcefile).convert('RGBA')
    frames=[]
    for frameindex,cell in enumerate(indices):
        OUT=OUTPUT/action/str(frameindex);OUT.mkdir(parents=True,exist_ok=True)
        source=sheet.crop(((cell%4)*W,(cell//4)*H,(cell%4+1)*W,(cell//4+1)*H))
        raw=np.array(source);targetA=(raw[:,:,3]>=48).astype(np.float32)
        # Existing source transparency defines the background; zero its hidden
        # RGB to avoid accidentally exporting the original brown matte.
        cleaned=raw.copy();cleaned[:,:,3]=targetA.astype(np.uint8)*255;cleaned[targetA==0,:3]=0
        Image.fromarray(cleaned).save(OUT/'reference.png')
        target=raw[:,:,:3].astype(np.float32)/255;target[targetA==0]=1
        lum=target.mean(axis=2);gy,gx=np.gradient(lum)
        weights=1+np.clip(np.hypot(gx,gy)*8,0,2)
        box=Image.fromarray((targetA*255).astype(np.uint8)).getbbox()
        lx,ly,hx,hy=box;sx=(hx-lx)/251;sy=(hy-ly)/462
        elements=copy.deepcopy(seed['elements'])
        for e in elements:
            # Per-frame affine initialization keeps part IDs and layering
            # stable; independent parameter fitting then follows the HD pose.
            e['x']=lx+e['x']*sx;e['y']=ly+e['y']*sy
            e['width']*=sx;e['height']*=sy
        if action=='idle' and cell==0:
            for e,original in zip(elements,seed['elements']):
                e.update(x=original['x']+59,y=original['y']+19,width=original['width'],height=original['height'])
        initial=copy.deepcopy(elements);baseline=actual_measure(elements,'initial')
        history=[];masks=[mask(e) for e in elements]
        loop=code[code.index('for sweep,step in enumerate'):code.index('# Select by actual rendered SVG')]
        loop=loop.replace('[4,2,1,.5]','[4,1.5]').replace('if delete_loss<=bestloss+.2:','if False:')
        exec(loop,globals())
        final=actual_measure(elements,'fitted')
        data={'w':W,'h':H,'elements':elements,'method':'fixed native shape IDs; per-HD-pose coordinate fit'}
        (OUT/'collage.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        from collections import Counter
        (OUT/'report.json').write_text(json.dumps({'imagePrimitives':len(elements),'types':dict(Counter(e['type'] for e in elements)),
          'sourceCell':cell,'existingSourceAlphaUsed':True,'backgroundControls':0,'newPixelBlocks':0,'deviceVerified':False},ensure_ascii=False),encoding='utf-8')
        row={'frame':frameindex,'cell':cell,'source':sourcefile,'images':len(elements),'baseline':baseline,'final':final,'path':f'{action}/{frameindex}'}
        frames.append({'index':frameindex,'durationMs':180,'sourceCell':cell,'elements':elements,'svg':f'{action}/{frameindex}/fitted.svg','reference':f'{action}/{frameindex}/reference.png'})
        allrows.append(row);print('FRAME_DONE '+json.dumps(row,ensure_ascii=False),flush=True)
    actions.append({'key':action,'name':'待机' if action=='idle' else '移动姿势组','loop':True,'frames':frames})
OUTPUT.joinpath('animation.json').write_text(json.dumps({'w':W,'h':H,'imagePoolSize':994,'actions':actions,'background':'transparent','deviceVerified':False},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
OUTPUT.joinpath('fit-report.json').write_text(json.dumps({'frames':allrows,'inputDownscaled':False,'backgroundRemoved':True,'sameShapeIds':True,'pruningDisabledForCorrespondence':True,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf-8')
# Contact sheets verify every exported frame rather than just frame zero.
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
for action in ['idle','move']:
    panel=Image.new('RGB',(1200,510),'#e8ecef');draw=ImageDraw.Draw(panel)
    for i in range(4):
        draw.text((i*300+12,8),('待机' if action=='idle' else '移动')+f' · {i+1}',font=font,fill='#354139')
        for name,left in [('reference.png',i*300+3),('fitted.png',i*300+153)]:
            pic=Image.open(OUTPUT/action/str(i)/name).convert('RGBA').resize((144,192),Image.Resampling.LANCZOS)
            panel.paste(pic,(left,52),pic)
            draw.text((left,260),'参考' if name=='reference.png' else '拟合',font=font,fill='#354139')
    panel=panel.crop((0,0,1200,300));panel.save(OUTPUT/(action+'-contact.png'))
print('ALL_FRAMES_COMPLETE',flush=True)

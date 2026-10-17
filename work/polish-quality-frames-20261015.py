"""Restore approved facial construction and constrain stray native geometry."""
import json,copy,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
code=Path('work/optimize_nahida_primitives_20261015.py').read_text(encoding='utf-8')
exec(code[:code.index('baseline=actual_measure')],globals())
ROOT=Path('outputs/nahida-quality-frames-20261015')
manifest=json.loads((ROOT/'animation.json').read_text(encoding='utf-8'))
seed=json.loads(Path('outputs/nahida-native-budget1000-20261015/collage.json').read_text(encoding='utf-8'))['elements']
heads=[(235,112),(234,114),(239,112),(240,110),(348,244),(296,182),(293,194),(324,140)]
W,H=384,512;yy,xx=np.mgrid[:H,:W].astype(np.float32);xx+=.5;yy+=.5
helper=Path('work/refit-quality-animation-20261015.py').read_text(encoding='utf-8')
exec(helper[helper.index('def sparse_mask'):helper.index('actions=[];report=[]')],globals())
rows=[]
for ai,action in enumerate(manifest['actions']):
 for frame in action['frames']:
  index=frame['index'];OUT=ROOT/action['key']/str(index)
  source=Image.open(OUT/'reference.png').convert('RGBA');raw=np.array(source)
  targetA=(raw[:,:,3]>=48).astype(np.float32);target=raw[:,:,:3].astype(np.float32)/255;target[targetA==0]=1
  before=actual_measure(frame['elements'],'before-polish')
  if ai==0 and index==0:
   for old,e in zip(seed,frame['elements']):
    assert e['x']==old['x']+59 and e['y']==old['y']+19
    for key in ('type','width','height','rotation','color'):assert e[key]==old[key]
   rows.append({'action':action['key'],'frame':index,'approvedFirstFrameExact':True,'final':before});continue
  es=frame['elements'];core=[];body=[];head=heads[ai*4+index]
  for e in es:
   old=seed[e['poolId']];x=old['x']+59;y=old['y']+19
   is_core=(x>165 and y<175) or old.get('part') in ('eyes','face','head','head-ornament','front-hair')
   if is_core:
    restored=copy.deepcopy(old);restored.update(x=x+head[0]-235,y=y+head[1]-112,poolId=e['poolId'])
    core.append(restored)
   else:body.append(e)
  # Shape containment removes the obsolete silhouette outside the HD pose;
  # it does not cut a bitmap or create arbitrary contour paths.
  adjusted=0
  for e in body:
   m=mask(e).astype(np.float32)/255;total=float(m.sum())
   overlap=float((m*targetA).sum())/max(total,1e-9)
   if overlap>=.94:continue
   original=copy.deepcopy(e);best=e.copy();bestover=overlap
   for shift in [(0,0),(-5,0),(5,0),(0,-5),(0,5),(-10,0),(10,0),(0,-10),(0,10)]:
    for scale in (.9,.7,.5,.3):
     candidate={**original,'x':original['x']+shift[0],'y':original['y']+shift[1],'width':max(.2,original['width']*scale),'height':max(.2,original['height']*scale)}
     mm=mask(candidate).astype(np.float32)/255;n=float(mm.sum())
     ratio=float((mm*targetA).sum())/max(n,1e-9)
     score=ratio-.015*(1-scale)
     if score>bestover:bestover=score;best=candidate
     if ratio>.98:break
    if bestover>.975:break
   if bestover>overlap+.02:e.update(best);adjusted+=1
  # Native sibling order explicitly restores the facial detail over body
  # shapes, which can overlap its new location after large pose changes.
  frame['elements']=body+core
  final=actual_measure(frame['elements'],'fitted')
  (OUT/'collage.json').write_text(json.dumps({'w':W,'h':H,'elements':frame['elements']},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
  rows.append({'action':action['key'],'frame':index,'restoredCoreShapes':len(core),'containedShapes':adjusted,'before':before,'final':final})
  print(json.dumps(rows[-1]),flush=True)
(ROOT/'animation.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(ROOT/'polish-report.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for action in ('idle','move'):
 panel=Image.new('RGB',(1200,300),'#eef2f5');d=ImageDraw.Draw(panel)
 for i in range(4):
  d.text((i*300+8,8),f'{action} {i+1}  原图 / 混合图元',font=font,fill='#354139')
  for name,x in [('reference.png',i*300+3),('fitted.png',i*300+153)]:
   pic=Image.open(ROOT/action/str(i)/name).convert('RGBA').resize((144,192),Image.Resampling.LANCZOS);panel.paste(pic,(x,47),pic)
 panel.save(ROOT/(action+'-contact.png'))

"""Offline source extraction and rectangle reconstruction, not combat simulation."""
from pathlib import Path
from collections import deque
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/v4-one-character-20261010/ayaka-armed-v2'
sys.path.insert(0,str(ROOT/'game/tools'))
import artlib

# Proposed ticks/boxes, distinct from accepted runtime parameters.
# boxes use world coordinates: x forward, y upward from actor floor.
SPECS={
 'light1':('轻攻一',[3,3,2,1,5,5],.68,[50,140,180,70],20,'mid'),
 'light2':('轻攻二',[3,3,2,2,5,7],.72,[50,155,200,90],22,'mid'),
 'light3':('轻攻三',[4,4,3,2,7,9],.72,[45,100,210,150],28,'mid'),
 'heavy':('站重',[5,6,2,2,9,10],.74,[40,90,210,200],35,'mid'),
 'crouchlight':('蹲轻',[3,3,2,1,5,5],.72,[50,60,250,80],10,'low'),
 'crouchheavy':('蹲重',[5,5,2,2,11,12],.72,[45,0,220,70],20,'low'),
 'airlight':('空轻',[3,3,3,3,4,4],.64,[35,-30,160,110],12,'high'),
 'airheavy':('空重',[4,5,3,3,6,6],.66,[20,-110,190,190],18,'high'),
 'skillE':('E · 冰华',[6,6,3,5,10,8],.61,[60,0,220,230],0,'mid'),
 'skillQ':('Q · 霜灭',[7,7,4,8,12,14],.645,[90,50,230,260],0,'mid'),
}

def extract(path,count=6):
 im=Image.open(path).convert('RGBA');w,h=im.size
 alpha=np.asarray(im)[:,:,3];a=alpha.tobytes();seen=bytearray(w*h);parts=[]
 for start in range(w*h):
  if seen[start] or a[start]<64:continue
  q=deque([start]);seen[start]=1;pts=[]
  while q:
   p=q.popleft();pts.append(p);x=p%w;y=p//w
   for z in (p-1 if x else -1,p+1 if x<w-1 else -1,p-w if y else -1,p+w if y<h-1 else -1):
    if z>=0 and not seen[z] and a[z]>=64:seen[z]=1;q.append(z)
  if len(pts)>1500:parts.append(pts)
 parts=sorted(parts,key=len,reverse=True)[:count]
 if len(parts)!=count:raise ValueError(f'{path.name}: expected {count} connected full poses, found {len(parts)}')
 records=[]
 for pts in parts:
  xs=np.array(pts)%w;ys=np.array(pts)//w
  box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
  mask=Image.new('L',im.size);m=np.zeros((h,w),dtype=np.uint8);m[ys,xs]=alpha[ys,xs]
  mask=Image.fromarray(m);f=im.copy();f.putalpha(mask);f=f.crop(box)
  records.append((box,f,xs,ys))
 # Sort by foot/bottom row: large swords can extend across arbitrary cell borders.
 records.sort(key=lambda r:(int(np.median(r[3])//(h/2)),r[0][0]))
 return records

def main():
 target=OUT/'new-actions.json';data=json.loads(target.read_text(encoding='utf-8'))
 report={};prepared={};small=[]
 for key,(label,durations,scale,box,lunge,level) in SPECS.items():
  source=next((OUT/f'{key}-attack-source-v{v}.png' for v in [3,2,1] if (OUT/f'{key}-attack-source-v{v}.png').exists()),OUT/f'{key}-attack-source-v1.png')
  if not source.exists():continue
  records=extract(source);prepared[key]=records
  for _,im,_,_ in records:small.append(artlib.downscale(im,1/6))
 reference=json.loads((ROOT/'work/v4-handoff-20261009-partial/V4/evidence/kamisatoayaka-idle-review/fit.json').read_text(encoding='utf-8'))
 palette=reference['palette']
 for key,records in prepared.items():
  label,durations,scale,box,lunge,level=SPECS[key];originals=[];fits=[];counts=[];rois=[]
  source=next(OUT/f'{key}-attack-source-v{v}.png' for v in [3,2,1] if (OUT/f'{key}-attack-source-v{v}.png').exists())
  for i,(roi,im,xs,ys) in enumerate(records):
   if key.startswith('air'):
    # Hand-authored source pelvis pivot; row/column determined by ordered poses.
    anchor=[(i%3+.5)*512-roi[0],(i//3)*512+280-roi[1]]
   else:
    # Feet only: blade/hair extents must never shift the root.
    foot=xs[ys>=ys.max()-10];anchor=[float((foot.min()+foot.max())/2)-roi[0],roi[3]-roi[1]-1]
   name=f'{key}-attack-{i}.png';im.save(OUT/name)
   originals.append({'file':name,'anchor':anchor,'scale':scale,'roi':list(roi),'source':source.name})
   thumb=artlib.downscale(im,scale/4.5);idx=artlib.apply_palette(thumb,palette[:-1]);opaque=idx>=0
   edge=np.asarray(Image.fromarray(opaque.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
   idx[edge&~opaque]=len(palette)-1;rects=artlib.painter(idx)
   rebuilt=Image.new('RGBA',thumb.size);draw=ImageDraw.Draw(rebuilt)
   for x,y,w,h,c in rects:draw.rectangle((x,y,x+w-1,y+h-1),fill=tuple(palette[c])+ (255,))
   expected=np.zeros((thumb.height,thumb.width,4),dtype=np.uint8)
   for c,col in enumerate(palette):expected[idx==c]=col+[255]
   assert np.array_equal(np.asarray(rebuilt),expected),'rectangle reconstruction differs'
   fitname=f'{key}-attack-fit-{i}.png';rebuilt.save(OUT/fitname)
   ratio=[im.width/thumb.width,im.height/thumb.height]
   fits.append({'file':fitname,'anchor':[anchor[0]/ratio[0],anchor[1]/ratio[1]],'scale':4.5,'source':source.name})
   (OUT/f'{key}-attack-rects-{i}.json').write_text(json.dumps({'palette':palette,'rects':rects,'anchor':fits[-1]['anchor'],'sourceROI':roi,'previewOnly':True}),encoding='utf-8')
   counts.append(len(rects));rois.append(list(roi))
  startup=sum(durations[:2]);active=sum(durations[2:4]);total=sum(durations)
  meta={'startup':startup,'active':active,'recovery':sum(durations[4:]),'box':box,'lunge':lunge,'level':level,'damage':'待调','cancel':'命中/防御确认后；窗口待接入','branches':['空挥恢复','防御恢复','命中确认'],'status':'design-only'}
  event={'tick':startup,'kind':'hit','hitId':key+'-1','damageSegments':1}
  if key=='skillE':event['kind']='ground-release'
  if key=='skillQ':event['kind']='storm-release';meta['branches']=['空挥短恢复','防御短恢复','命中确认后完整冰风演出'];meta['confirmedHits']=[startup,startup+18,startup+36]
  data[label]={'frames':fits,'sourceFrames':originals,'durations':durations,'phases':['准备','出手','有效','随挥','回收','恢复'],'events':[event],'combatDesign':meta,'previewOnly':True,'status':'新持械攻击关键帧；未接战斗逻辑'}
  report[key]={'source':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rois':rois,'rectangles':counts,'scale':scale,'simulation':'not run','device':'not observed','anatomicalScale':'provisional fixed action scale, not per-frame bbox normalization'}
 fxsource=OUT/'skillFx-attack-source-v1.png'
 if fxsource.exists():
  fx=Image.open(fxsource).convert('RGBA')
  for kind,row in [('E',0),('Q',1)]:
   items=[]
   for i in range(3):
    cell=fx.crop((i*fx.width//3,row*fx.height//2,(i+1)*fx.width//3,(row+1)*fx.height//2));name=f'{kind}-attack-effect-{i}.png';cell.save(OUT/name)
    items.append({'file':name,'anchor':[cell.width/2,cell.height*.86 if row==0 else cell.height/2],'scale':.66})
   label='E · 冰华' if row==0 else 'Q · 霜灭'
   data[label]['effects']={'frames':items,'startTick':12 if row==0 else 14,'duration':18 if row==0 else 38,'worldOffset':[150,0] if row==0 else [180,-160],'independent':True}
 target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'攻击制作检查.json').write_text(json.dumps({'palette':palette,'actions':report,'validation':'source extraction / exact rectangle reconstruction only; not runtime budget acceptance'},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()

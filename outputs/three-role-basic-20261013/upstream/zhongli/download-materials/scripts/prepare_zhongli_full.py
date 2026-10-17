from pathlib import Path
import json,sys,io
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs/zhongli-design-20261011';F=O/'full-actions'
sys.path.insert(0,str(ROOT/'work'));from build_zhongli_delivery import LABELS
repair=set('light1 heavy crouchlight airlight throw victim hit_knockdown'.split()); pending=set('light3 crouchheavy airheavy wakeup victory defeat heavy'.split())
def save(im,path):
 b=io.BytesIO();im.save(b,format="PNG");path.write_bytes(b.getvalue());Image.open(path).load()
reg={}
for key in LABELS:
 src=(F/'sources'/f'{key}.png')
 if not src.exists():
  if key in pending:continue
  old=O/('history/repairs' if key in repair else 'sources')/f'{key}.png';src.write_bytes(old.read_bytes())
 im=Image.open(src).convert('RGBA');a=np.array(im);labs,n=ndimage.label(a[:,:,3]>=64);sizes=np.bincount(labs.ravel());count=2 if key=='idle' else 4 if key=='skillE' else 6
 ids=sorted(range(1,n+1),key=lambda x:sizes[x],reverse=True)[:count];rows=1 if count==2 else 2 if count==4 or key not in repair|pending else 3
 parts=[]
 for ident in ids:
  y,x=np.where(labs==ident);roi=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)];parts.append((int(np.median(y)//(im.height/rows)),float(np.median(x)),roi,ident))
 parts.sort();assert len(parts)==count and min(sizes[t[3]] for t in parts)>1000,(key,"pose extraction failed");rr=[]
 canvas=Image.new('RGB',(1800,520*((count+2)//3)),(48,54,63));d=ImageDraw.Draw(canvas)
 for i,(_,_,roi,ident) in enumerate(parts):
  arr=np.array(im.crop(roi));arr[:,:,3]=np.where(labs[roi[1]:roi[3],roi[0]:roi[2]]==ident,arr[:,:,3],0);frame=Image.fromarray(arr);source=f'sources/{key}.png'
  override=F/'sources'/f'{key}-{i}-single-repair.png'
  if (key,i) in [('crouchheavy',3),('light1',5)] and override.exists():
   repaired=Image.open(override).convert('RGBA');aa=np.array(repaired);yy,xx=np.where(aa[:,:,3]>=64);roi=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];frame=repaired.crop(roi);source=str(override.relative_to(F))
  file=F/'frames'/f'{key}-{i}.png';save(frame,file)
  # Display at original pixel scale where possible: coordinates are local crop.
  ratio=min(550/frame.width,450/frame.height);thumb=frame.resize((round(frame.width*ratio),round(frame.height*ratio)));xx=i%3*600;yy=i//3*520;canvas.paste(thumb,(xx+30,yy+40),thumb)
  for v in range(0,frame.width,100):d.text((xx+30+v*ratio,yy+20),str(v),fill='white')
  for v in range(0,frame.height,100):d.text((xx,yy+40+v*ratio),str(v),fill='white')
  d.text((xx+30,yy+495),f'{key}-{i} crop {frame.size}',fill='white');rr.append({'roi':roi,'file':f'frames/{key}-{i}.png','source':source,'edge':any([roi[0]==0,roi[1]==0,roi[2]==im.width,roi[3]==im.height]) if source==f'sources/{key}.png' else False})
 canvas.save(F/'checks'/f'{key}.jpg');reg[key]=rr
(F/'source-registrations.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2))
print({k:len(v) for k,v in reg.items()})

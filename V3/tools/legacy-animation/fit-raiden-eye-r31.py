from pathlib import Path
from PIL import Image
import json,numpy as np,shutil
R=Path(__file__).resolve().parents[1]
im=Image.open(R/'animation-source/raiden-eye-r31/eye.png').convert('RGBA')
assert im.getextrema()[3][0]==0
def rects(idx):
 out=[];last={}
 for y,row in enumerate(idx):
  now={};x=0
  while x<len(row):
   c=int(row[x]);e=x+1
   while e<len(row) and row[e]==c:e+=1
   if c>=0:
    k=(x,e-x,c)
    if k in last:r=last[k];r[3]+=1
    else:r=[x,y,e-x,1,c];out.append(r)
    now[k]=r
   x=e
  last=now
 return out
data={};report=[]
for tier,width,limit in [('hi',320,2400),('lo',192,800)]:
 data[tier]={}
 for i in range(4):
  cell=im.crop((i%2*im.width//2,i//2*im.height//2,(i%2+1)*im.width//2,(i//2+1)*im.height//2))
  size=width
  while True:
   a=cell.resize((size,round(size*cell.height/cell.width)),Image.Resampling.BOX)
   q=a.quantize(colors=24,method=Image.Quantize.FASTOCTREE);pal=q.getpalette('RGBA');idx=np.array(q).astype(int);idx[np.array(a)[:,:,3]<90]=-1;rr=rects(idx)
   if len(rr)<=limit:break
   size-=4;assert size>=64
  data[tier][str(i)]=dict(bytes=[v for r in rr for v in r],n=len(rr),pal=[pal[j:j+4] for j in range(0,96,4)],ax=a.width/2,ay=a.height/2,u=1,w=a.width,h=a.height)
  report.append(dict(tier=tier,frame=i,width=size,primitives=len(rr)))
def lua(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(a) for k,a in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(lua(a) for a in v)+'}'
 if isinstance(v,str):return json.dumps(v)
 return str(v)
(R/'project-inputs/gf_raiden_eye_r31.lua').write_text('return '+lua(data)+'\n')
for char in ['raiden','nahida']:
 d=R/'dist/actions'/char;shutil.copy2(R/'animation-source/raiden-eye-r31/eye.png',d/'assets/raiden-eye-r31.png')
 atlas=json.loads((d/'atlas.json').read_text());w,h=im.width//2,im.height//2;atlas['burst_eye']=dict(url='assets/raiden-eye-r31.png',height=h,frames=[dict(x=i%2*w,y=i//2*h,w=w,h=h,ax=w/2,ay=h/2) for i in range(4)])
 (d/'atlas.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
(R/'animation-tools/eye-fit-report-r31.json').write_text(json.dumps(report,indent=2));print(report)

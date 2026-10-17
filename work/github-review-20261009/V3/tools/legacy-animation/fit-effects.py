from pathlib import Path
from PIL import Image
import json,numpy as np
ROOT=Path(__file__).resolve().parents[1]
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
out={}
for char in ['raiden','nahida']:
 r=ROOT/'dist/actions'/char;s=json.loads((r/'atlas.json').read_text())['effects'];src=Image.open(r/s['url']).convert('RGBA');entries={}
 for i,f in enumerate(s['frames']):
  im=src.crop((f['x'],f['y'],f['x']+f['w'],f['y']+f['h']));size=120
  while True:
   ratio=size/max(im.size);a=im.resize((max(1,round(im.width*ratio)),max(1,round(im.height*ratio))),Image.Resampling.BOX);rgb=a.quantize(colors=48,method=Image.Quantize.FASTOCTREE);pal=rgb.getpalette('RGBA');idx=np.array(rgb).astype(int);idx[np.array(a)[:,:,3]<32]=-1;rs=rects(idx)
   if len(rs)<=850:break
   size-=4
  p=[pal[j:j+4] for j in range(0,192,4)];entries[str(i)]=dict(bytes=[v for q in rs for v in q],n=len(rs),pal=p,ax=a.width/2,ay=a.height,u=1,w=a.width,h=a.height)
 out[char]=entries
def lua(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(a) for k,a in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(lua(a) for a in v)+'}'
 return str(v)
(ROOT/'project-inputs/gf_animation_effects.lua').write_text('return '+lua(out)+'\n')
print('Fitted 24 independent effects, <=850 primitives each')

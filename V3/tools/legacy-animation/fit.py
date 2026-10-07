from pathlib import Path
from PIL import Image
import numpy as np,json
from scipy.cluster.vq import kmeans2
ROOT=Path(__file__).resolve().parents[1]

def oklab(rgb):
 c=rgb/255.;c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
 lms=c@np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]])
 return np.cbrt(lms)@np.array([[.2104542553,1.9779984951,.0259040371],[.793617785,-2.428592205,.7827717662],[-.0040720468,.4505937099,-.808675766]])
def rectangles(idx):
 out=[];prev={}
 for y,row in enumerate(idx):
  cur={};x=0
  while x<len(row):
   ci=int(row[x]);end=x+1
   while end<len(row) and row[end]==ci:end+=1
   if ci>=0:
    k=(x,end-x,ci)
    if k in prev:rect=prev[k];rect[3]+=1
    else:rect=[x,y,end-x,1,ci];out.append(rect)
    cur[k]=rect
   x=end
  prev=cur
 return out
rng=np.random.default_rng(21);data={};report={}
for char,world in [('raiden',336),('nahida',261)]:
 root=ROOT/'dist/actions'/char;atlas=json.loads((root/'atlas.json').read_text());poses={};samples=[]
 for sheet,s in atlas.items():
  im=Image.open(root/s['url']).convert('RGBA')
  for i,f in enumerate(s['frames']):
   crop=im.crop((f['x'],f['y'],f['x']+f['w'],f['y']+f['h']));poses[f'{sheet}_{i}']=(crop,f,s)
   if sheet!='effects':
    ar=np.array(crop.resize((max(1,int(crop.width*64/s['height'])),max(1,int(crop.height*64/s['height']))),Image.Resampling.BOX));pixels=ar[ar[:,:,3]>128,:3];samples.append(pixels)
 pixels=np.concatenate(samples);sample=pixels[rng.choice(len(pixels),min(18000,len(pixels)),replace=False)];data[char]={};report[char]={}
 for tier,ncol,limit,target in [('hi',24,1250,108),('lo',18,760,80)]:
  lab=oklab(sample.astype(float));centers,labels=kmeans2(lab,ncol,iter=15,minit='++',seed=11);pal=[]
  for k in range(ncol):
   cluster=sample[labels==k];pal.append((np.mean(cluster,axis=0) if len(cluster) else sample[k]).round().astype(int).tolist()+[255])
  plab=oklab(np.array(pal)[:,:3].astype(float));tierdata={'pal':pal};counts=[]
  for name,(im,f,s) in poses.items():
   if name.startswith('effects_'):continue
   height=target
   while True:
    ratio=height/s['height'];w=max(1,round(im.width*ratio));h=max(1,round(im.height*ratio));ar=np.array(im.resize((w,h),Image.Resampling.BOX));rgb=ar[:,:,:3];labs=oklab(rgb.reshape(-1,3).astype(float));dist=((labs[:,None,:]-plab[None,:,:])**2).sum(axis=2);idx=dist.argmin(axis=1).reshape(h,w);idx[ar[:,:,3]<110]=-1;rects=rectangles(idx)
    if len(rects)<=limit:break
    height-=4;assert height>28,(name,limit)
   b=[v for rect in rects for v in rect];tierdata[name]=dict(bytes=b,n=len(rects),ax=round(f['ax']*ratio),ay=round(f['ay']*ratio),u=world/height,w=w,h=h)
   counts.append(len(rects))
  data[char][tier]=tierdata;report[char][tier]={'palette':ncol,'limit':limit,'poses':len(counts),'maximum':max(counts),'mean':round(float(np.mean(counts)),1)}
 print(char,report[char],flush=True)
def lua(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(val) for k,val in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
 return str(v)
(ROOT/'project-inputs/gf_animation_data.lua').write_text('return '+lua(data)+'\n')
(ROOT/'animation-tools/fit-report.json').write_text(json.dumps(report,indent=2))

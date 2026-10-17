from pathlib import Path
from PIL import Image
from scipy.ndimage import label,binary_dilation
import numpy as np,json,re,shutil
R=Path(__file__).resolve().parents[1];manifest=json.loads((R/'animation-source/inbetween-r28-jobs.json').read_text());data={'nahida':{'hi':{},'lo':{}},'raiden':{'hi':{},'lo':{}}};report=[]
base=(R/'project-inputs/gf_animation_data.lua').read_text()
def palette(char,tier):
 a=base.index('["'+char+'"]={');b=base.find('["nahida"]={',a+1) if char=='raiden' else -1;text=base[a:b if b>=0 else len(base)]
 pals=re.findall(r'\["pal"\]=(\{\{.*?\}\})',text);return json.loads(pals[tier=='lo'].replace('{','[').replace('}',']'))
def rectangles(idx):
 out=[];last={}
 for y,row in enumerate(idx):
  now={};x=0
  while x<len(row):
   c=int(row[x]);end=x+1
   while end<len(row) and row[end]==c:end+=1
   if c>=0:
    k=(x,end-x,c)
    if k in last:r=last[k];r[3]+=1
    else:r=[x,y,end-x,1,c];out.append(r)
    now[k]=r
   x=end
  last=now
 return out
keys={'nahida':{},'raiden':{}}
for job in manifest:
 char,sheet=job['char'],job['sheet'];origPath=R/'dist/actions'/char/'atlas.json';atlas=json.loads(origPath.read_text());orig=atlas[sheet];dest=R/'dist/actions'/char/'assets/inbetweens-r28';dest.mkdir(parents=True,exist_ok=True)
 im=Image.open(R/job['path']).convert('RGBA');n=len(job['next']);cols=2 if n==4 else 3 if n==6 else 4;rows=2;pieces=[];ratios=[]
 for i in range(n):
  cell=im.crop((round(i%cols*im.width/cols),round(i//cols*im.height/rows),round((i%cols+1)*im.width/cols),round((i//cols+1)*im.height/rows)))
  rgba=np.array(cell);mask=rgba[:,:,3]>=100;lab,count=label(binary_dilation(mask,iterations=2));sizes=np.bincount(lab.ravel());sizes[0]=0;main=int(sizes.argmax());assert sizes[main]>500,(char,sheet,i,'empty frame')
  yy,xx=np.where(lab==main);box=(max(0,int(xx.min())-2),max(0,int(yy.min())-2),min(cell.width,int(xx.max())+3),min(cell.height,int(yy.max())+3))
  rgba[:,:,3]*=(lab==main);piece=Image.fromarray(rgba).crop(box);pieces.append(piece)
  j=job['next'][i];expected=(orig['frames'][i]['h']+orig['frames'][j]['h'])/2/orig['height'];ratios.append(piece.height/expected)
 nominal=float(np.median(ratios));cw=max(x.width for x in pieces)+32;ch=max(x.height for x in pieces)+32;out=Image.new('RGBA',(cw*cols,ch*rows));frames=[]
 for i,cell in enumerate(pieces):
  x=i%cols*cw+(cw-cell.width)//2;y=i//cols*ch+ch-16-cell.height;out.alpha_composite(cell,(x,y));frames.append(dict(x=x,y=y,w=cell.width,h=cell.height,ax=cell.width/2,ay=cell.height,isolated=True))
 out.save(dest/(sheet+'.png'));atlas[sheet+'_between']=dict(url='assets/inbetweens-r28/'+sheet+'.png',height=nominal,frames=frames,next=job['next']);origPath.write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
 for i,j in enumerate(job['next']):keys[char][sheet+'_'+str(i)+'_'+str(j)]=sheet+'_between_'+str(i)
 counts=[]
 for tier,target,limit in [('hi',108,1250),('lo',80,760)]:
  pal=palette(char,tier);rgbpal=np.array(pal)[:,:3].astype(float)
  for i,cell in enumerate(pieces):
   height=target
   while True:
    ratio=height/nominal;ar=np.array(cell.resize((max(1,round(cell.width*ratio)),max(1,round(cell.height*ratio))),Image.Resampling.BOX));rgb=ar[:,:,:3].astype(float);dist=((rgb[:,:,None,:]-rgbpal[None,None,:,:])**2).sum(axis=3);idx=dist.argmin(axis=2);idx[ar[:,:,3]<110]=-1;rr=rectangles(idx)
    if len(rr)<=limit:break
    height-=4;assert height>24,(char,sheet,i)
   name=sheet+'_between_'+str(i);data[char][tier][name]=dict(bytes=[v for r in rr for v in r],n=len(rr),ax=cell.width*ratio/2,ay=cell.height*ratio,u=(261 if char=='nahida' else 336)/height,w=ar.shape[1],h=ar.shape[0]);counts.append(len(rr))
 report.append(dict(character=char,sheet=sheet,newFrames=n,maximumPrimitives=max(counts),height=nominal))
def lua(v):
 if isinstance(v,str):return json.dumps(v)
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(a) for k,a in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(lua(a) for a in v)+'}'
 return str(v)
(R/'project-inputs/gf_inbetween_data.lua').write_text('return '+lua({'poses':data,'keys':keys})+'\n');(R/'animation-tools/inbetween-fit-report-r28.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('Prepared',sum(x['newFrames'] for x in report),'new poses; preserved all original keyframes and palettes')

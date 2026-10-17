from pathlib import Path
from PIL import Image
import numpy as np,json,re,struct,base64
R=Path(__file__).resolve().parents[1]
base=(R/'project-inputs/gf_animation_data.lua').read_text()
scope={'__file__':str(R/'animation-tools/fit-raiden-eye-r31.py')};exec((R/'animation-tools/fit-raiden-eye-r31.py').read_text().split('data={};report=[]')[0],scope)
rects=scope['rects'];data={};report=[]
for char,world in [('raiden',336),('nahida',261)]:
 a=base.index('["'+char+'"]={');b=base.find('["nahida"]={',a+1) if char=='raiden' else len(base)
 pal=json.loads(re.search(r'\["pal"\]=(\{\{.*?\}\})',base[a:b]).group(1).replace('{','[').replace('}',']'))
 rgbpal=np.array(pal)[:,:3].astype(float);bank={'pal':pal}
 root=R/'dist/actions'/char;atlas=json.loads((root/'atlas.json').read_text())
 for sheet,entry in atlas.items():
  if sheet in ['effects','burst_eye']:continue
  im=Image.open(root/entry['url']).convert('RGBA')
  for i,f in enumerate(entry['frames']):
   cell=im.crop((f['x'],f['y'],f['x']+f['w'],f['y']+f['h']));height=160
   while True:
    ratio=height/entry['height'];ar=np.array(cell.resize((max(1,round(cell.width*ratio)),max(1,round(cell.height*ratio))),Image.Resampling.BOX))
    rgb=ar[:,:,:3].astype(float);idx=((rgb[:,:,None,:]-rgbpal[None,None,:,:])**2).sum(axis=3).argmin(axis=2);idx[ar[:,:,3]<110]=-1;rr=rects(idx)
    if len(rr)<=2200:break
    height-=4;assert height>=48
   values=[v for r in rr for v in r];packed=struct.pack('<'+'H'*len(values),*values);packed+=b'\0'*((-len(packed))%3)
   name=sheet+'_'+str(i);bank[name]=dict(d=base64.b64encode(packed).decode(),n=len(rr),ax=f['ax']*ratio,ay=f['ay']*ratio,u=world/height,w=ar.shape[1],h=ar.shape[0])
   report.append(dict(character=char,pose=name,height=height,primitives=len(rr)))
 data[char]=bank;print(char,len(bank)-1,flush=True)
def lua(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(a) for k,a in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(lua(a) for a in v)+'}'
 return str(v)
(R/'project-inputs/gf_hd_r31.lua').write_text('return '+lua(data)+'\n')
(R/'animation-tools/hd-fit-report-r31.json').write_text(json.dumps(report,indent=2))

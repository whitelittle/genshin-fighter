from pathlib import Path
from PIL import Image
import json,shutil,numpy as np
from scipy.ndimage import label,binary_dilation
ROOT=Path(__file__).resolve().parents[1]
files=json.loads(Path('/workspace/scratch/59397218f32a/nahida-files.json').read_text())
ref=Path('/workspace/scratch/59397218f32a/.sites-checkout/dist')
shutil.copytree(ref,ROOT/'dist/actions/raiden',dirs_exist_ok=True)
for name in ['index.html','app.js']:shutil.copy(ref/name,ROOT/'dist/actions/nahida'/name)
na={}
for key,source in files.items():
 target=ROOT/'animation-source'/f'nahida-{key}.png';shutil.copy(source,target)
 im=Image.open(target).convert('RGBA');cols,rows=(2,2) if key=='throw' else (3,2) if key=='victim' else (4,3) if key=='effects' else (4,2)
 frames=[];edge=[]
 if key!='effects':
  rgba=np.array(im);mask=rgba[:,:,3]>=48;labs,n=label(binary_dilation(mask,iterations=3));sizes=np.bincount(labs.ravel());sizes[0]=0
  indices=np.argsort(sizes)[-(cols*rows):];assert all(sizes[i]>1200 for i in indices),(key,sorted(sizes[indices]))
  bodies=[]
  for idx in indices:
   ys,xs=np.where(labs==idx);bb=(max(0,int(xs.min())-3),max(0,int(ys.min())-3),min(im.width,int(xs.max())+4),min(im.height,int(ys.max())+4))
   piece=rgba[bb[1]:bb[3],bb[0]:bb[2]].copy();piece[:,:,3]*=(labs[bb[1]:bb[3],bb[0]:bb[2]]==idx)
   bodies.append((float(ys.mean()),float(xs.mean()),Image.fromarray(piece)))
  bodies.sort(key=lambda v:v[0]);ordered=[]
  for row in range(rows):ordered+=sorted(bodies[row*cols:(row+1)*cols],key=lambda v:v[1])
  cw=max(v[2].width for v in ordered)+64;ch=max(v[2].height for v in ordered)+64;atlas=Image.new('RGBA',(cw*cols,ch*rows))
  for i,(_,_,cell) in enumerate(ordered):
   x=i%cols*cw+(cw-cell.width)//2;y=i//cols*ch+ch-32-cell.height;atlas.alpha_composite(cell,(x,y));frames.append(dict(x=x,y=y,w=cell.width,h=cell.height,ax=cell.width//2,ay=cell.height,isolated=True))
 else:
  atlas=Image.new('RGBA',im.size)
  for i in range(cols*rows):
   x0=round(i%cols*im.width/cols);x1=round((i%cols+1)*im.width/cols);y0=round(i//cols*im.height/rows);y1=round((i//cols+1)*im.height/rows)
   cell=im.crop((x0,y0,x1,y1));bb=cell.getchannel('A').point(lambda a:255 if a>=48 else 0).getbbox();assert bb,(key,i)
   atlas.paste(cell,(x0,y0));frames.append(dict(x=x0+bb[0],y=y0+bb[1],w=bb[2]-bb[0],h=bb[3]-bb[1],ax=(bb[2]-bb[0])//2,ay=bb[3]-bb[1],isolated=True))
 dest=ROOT/'dist/actions/nahida/assets';dest.mkdir(exist_ok=True);atlas.save(dest/f'{key}.png')
 na[key]=dict(url=f'assets/{key}.png',height=450 if key not in ['throw','victim'] else 470,frames=frames)
 if any(edge):print('edge review',key,[i for i,v in enumerate(edge) if v])
(ROOT/'dist/actions/nahida/atlas.json').write_text(json.dumps(na,separators=(',',':')))
p=ROOT/'dist/actions/nahida/app.js';s=p.read_text().replace('雷眼释放','草印释放').replace("name:'Q · 胸口拔刀一闪',sheet:'qburst',frames:[0,1,2,3,3],dur:[9,7,4,3,9],phase:['聚雷','胸口拔刀','举刀蓄势','一闪 · 有效窗口3帧','收手']","name:'Q · 心景幻成',sheet:'skill',frames:[4,5,6,7],dur:[8,8,20,12],phase:['祈愿','展开','神殿绽放','收手']")
s=s.replace('32逻辑帧 · 一闪窗口3帧 · 收手9帧','48逻辑帧 · 神殿施法预览')
s=s.replace('Q 预览：聚雷9帧、拔刀7帧、蓄势4帧、一闪3帧、收手9帧。此页只播放动作和特效，不计算伤害；战斗判定待接入测试。','Q 身体、神殿与草光分层播放；本页不计算伤害。正式战斗请从模拟器进入。')
s=s.replace('if(p===0)effect(4,x,y-245,105,.55+u*.35);','if(p===0)effect(8,x,y-170,130,.55+u*.35);').replace('if(p===1){effect(5,x,y-245,150,.9);effect(8,x+25,y-250,235,.52);}','if(p===1){effect(8,x,y-190,250,.9);}')
s=s.replace('if(p===2){effect(8,x+115,y-245,450,.85);effect(2,x+35,y-280,130,.8);}','if(p===2){effectGround(9,x,y,480,.8);effect(10,x+245,y-170,430,.8);}')
s=s.replace("p===3||p===4","p===3").replace("const hit=p===3","const hit=false").replace("330,a.id==='victim'","261,a.id==='victim'").replace("ground+dy,330","ground+dy,261").replace("ground);else pose","ground,261);else pose")
p.write_text(s)
p=ROOT/'dist/actions/nahida/index.html';p.write_text(p.read_text().replace('雷电将军','纳西妲'))
(ROOT/'animation-source/manifest.json').write_text(json.dumps({'nahida':na,'raiden':json.loads((ref/'atlas.json').read_text())},ensure_ascii=False,indent=2))
print('Prepared Nahida 74 body poses + 12 effects; retained Raiden atlases')

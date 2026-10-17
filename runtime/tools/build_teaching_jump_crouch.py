"""Unify jump/crouch with the approved master and align visible Paimon pixels to panel bottom."""
from pathlib import Path
import json,sys,copy,shutil,hashlib,base64,struct
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-refine-v18-20261017'
OUT=ROOT/'outputs/tutorial-jump-v19-20261017'
ART=ROOT/'outputs/lumine-jump-crouch-20261017'
sys.path.insert(0,str(ROOT/'runtime/tools'))
import build_teaching_unified as U
from compact_assets import LuaRuntime,python_table
from export_furina import lua

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
 rt=LuaRuntime();rt.execute('__loaders={};'+(BASE/f'source/teaching/{name}.lua').read_text(encoding='utf-8'))
 return python_table(rt.globals().__loaders[name]())
def write(name,data):
 (OUT/f'source/teaching/{name}.lua').write_text(f"__loaders['{name}']=function() return "+lua(data)+' end\n',encoding='utf-8')

def objects(im):
 alpha=np.asarray(im)[:,:,3];mask=alpha>=128;parent=[];runs=[];prev=[]
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for y,row in enumerate(mask):
  edge=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)));cur=[]
  for a,b in zip(edge[::2],edge[1::2]):
   k=len(parent);parent.append(k)
   for x,z,j in prev:
    if x<b and z>a:parent[find(j)]=find(k)
   cur.append((int(a),int(b),k));runs.append((y,int(a),int(b),k))
  prev=cur
 area={};bounds={}
 for y,a,b,j in runs:
  k=find(j);area[k]=area.get(k,0)+b-a
  if k not in bounds:bounds[k]=[a,y,b,y+1]
  else:
   q=bounds[k];q[:]=[min(q[0],a),min(q[1],y),max(q[2],b),max(q[3],y+1)]
 ids=sorted(area,key=area.get,reverse=True)[:8]
 assert len(ids)==8 and min(area[k]for k in ids)>10000
 ids.sort(key=lambda k:(int((bounds[k][1]+bounds[k][3])/2//(im.height/3)),(bounds[k][0]+bounds[k][2])/2))
 result=[]
 for k in ids:
  owned=np.zeros(mask.shape,dtype=np.uint8)
  for y,a,b,j in runs:
   if find(j)==k:owned[y,a:b]=255
  fringe=np.asarray(Image.fromarray(owned).filter(ImageFilter.MaxFilter(3)))>0
  rgba=np.asarray(im).copy();rgba[:,:,3]=np.where(fringe,alpha,0)
  bb=bounds[k];result.append((Image.fromarray(rgba).crop(bb),bb,area[k]))
 return result

def board(path,keys,frames):
 image=Image.new('RGB',(520*len(keys),430),'#263454');draw=ImageDraw.Draw(image)
 for i,key in enumerate(keys):
  f=frames[key];v=struct.unpack('<'+'H'*(f['n']*5),base64.b64decode(f['d'])[:f['n']*10])
  draw.text((i*520+12,12),key,fill='white');draw.line((i*520,375,(i+1)*520,375),fill='#a2b5d2')
  for j in range(f['n']):
   x,y,w,h,c=v[j*5:j*5+5];px=i*520+170+(x-f['ax'])*f['u'];py=375+(y-f['ay'])*f['u']
   draw.rectangle((px,py,px+w*f['u']-.01,py+h*f['u']-.01),fill=tuple(f['pal'][c][:3]))
 image.save(path)

def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 (ART/'fit').mkdir(exist_ok=True);(ART/'extracted').mkdir(exist_ok=True)
 data=load('gf_lumine_training_data');old=copy.deepcopy(data)
 cal=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/report.json').read_text(encoding='utf-8'))
 contrast=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/fit/master-contrast.json').read_text(encoding='utf-8'))['palette']
 path=ART/'source/jump-crouch.png';im=Image.open(path).convert('RGBA');items=objects(im)
 neutral,bb,area=items[0];a=np.asarray(neutral);ys,xs=np.nonzero(a[:,:,3]>=128);feet=xs[ys>=ys.max()-3]
 unit=320/(bb[3]-bb[1]);neutralX=bb[0]+float((feet.min()+feet.max())/2);neutralY=bb[3]
 U.ART=ART;rows={}
 keys=[f'jump_{i}'for i in range(6)]+['cblock_0']
 for index,(key,(crop,bb,area))in enumerate(zip(keys,items[1:]),1):
  row,col=divmod(index,3)
  root=[neutralX+col*im.width/3-bb[0],neutralY+row*im.height/3-bb[1]]
  grounded=key in ('jump_0','jump_1','jump_5','cblock_0')
  if grounded:
   a=np.asarray(crop);ys,xs=np.nonzero(a[:,:,3]>=128);feet=xs[ys>=ys.max()-3]
   root=[float((feet.min()+feet.max())/2),int(ys.max()+1)]
  data['frames'][key],rows[key]=U.fit(crop,root,unit,key,cal,contrast)
  rows[key].update(source='source/jump-crouch.png',sourceSha256=sha(path),sourceRoi=bb,sourceComponentArea=area,commonSheetUnit=unit,neutralCalibrationBounds=items[0][1],grounded=grounded,virtualBaseline=neutralY,ownership='connected silhouette with 1-pixel alpha fringe')
  crop.save(ART/'extracted'/f'{key}.png')
 data['frames']['cblock_1']=copy.deepcopy(data['frames']['cblock_0'])
 data['groups']['crouch']={'frames':['cblock_0'],'durations':[60]}
 # Existing animation timing, movement physics and combat rules stay unchanged.
 assert all(data['frames'][k]==v for k,v in old['frames'].items()if k not in keys+['cblock_1'])
 for k,v in old['groups'].items():
  if k!='crouch':assert data['groups'][k]==v,k
 data['bodyPeak']=max(v['n']for v in data['frames'].values())
 unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()};mean=sum(v['n']for v in unique.values())/len(unique)
 assert mean<1000,mean
 write('gf_lumine_training_data',data)
 avatar=load('gf_paimon_training_avatar')
 v=struct.unpack('<'+'H'*(avatar['n']*5),base64.b64decode(avatar['d'])[:avatar['n']*10])
 contentBottom=max(v[i*5+1]+v[i*5+3]for i in range(avatar['n']))
 avatar['seam']=.08;avatar['visibleLocalBottom']=avatar['ay']-contentBottom-avatar['seam']/2
 write('gf_paimon_training_avatar',avatar)
 p=OUT/'source/teaching/gf_training_lesson.lua';code=p.read_text(encoding='utf-8')
 before='self.avatar.node:pos(avatarX,y-72):scale(avatarSize/self.avatarImage.w,avatarSize/self.avatarImage.w):on(self.avatarReady)'
 after='local avatarScale=avatarSize/self.avatarImage.w\n local avatarY=y-106-(self.avatarImage.visibleLocalBottom or 0)*avatarScale\n self.avatar.node:pos(avatarX,avatarY):scale(avatarScale,avatarScale):on(self.avatarReady)'
 assert code.count(before)==1;code=code.replace(before,after);p.write_text(code,encoding='utf-8')
 p=OUT/'source/teaching/gf_character_lumine_training.lua';code=p.read_text(encoding='utf-8')
 code=code.replace("if st=='jumpsq' then return 'jump_0' end","if st=='jumpsq' then return t<2 and 'jump_0' or 'jump_1' end")
 p.write_text(code,encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert set(changed)=={'source/teaching/gf_lumine_training_data.lua','source/teaching/gf_paimon_training_avatar.lua','source/teaching/gf_training_lesson.lua','source/teaching/gf_character_lumine_training.lua'},changed
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8') for p in order),encoding='utf-8');(OUT/'verification').mkdir(exist_ok=True)
 manifest={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'sourceFiles':{p:sha(OUT/p)for p in order},'frames':rows,'bodyUniqueMean':mean,'bodyPeak':data['bodyPeak'],'paimon':{'display':310,'sampleMax':96,'colors':20,'rectangles':avatar['n'],'preparationBudget':160,'visibleLocalBottom':avatar['visibleLocalBottom'],'visiblePanelGap':0},'crouchGuard':'same one drawn crouch reused as crouch and crouch-guard; not two original drawings'}
 (OUT/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(ART/'import.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 groups={g:data['groups'][g]for g in ['idle','walk','back','dash','jump','crouch','light1','light2','light3','heavy']}
 reviewkeys={k for g in groups.values()for k in g['frames']}
 (ART/'review-data.json').write_text(json.dumps({'frames':{k:data['frames'][k]for k in reviewkeys},'groups':groups},ensure_ascii=False),encoding='utf-8')
 for group in ['walk','dash','jump','crouch','light1','light2','light3','heavy']:board(ART/f'{group}-runtime-review.png',['teaching_master']+groups[group]['frames'],data['frames'])
 html=(ROOT/'outputs/lumine-unified-20261017/index.html').read_text(encoding='utf-8')
 html=html.replace('荧 · 同母版动作核对','荧 · 跳跃、蹲下与派蒙贴底').replace('荧 · 前后走、前冲、三轻与重击核对','荧 · 跳跃、蹲下与派蒙贴底')
 start=html.index('<p>');end=html.index('</p>',start)+4
 html=html[:start]+'<p>跳跃六姿与下蹲一姿按已选母版制作，同一源单位、已确认加深19色与外轮廓；下蹲和蹲防复用同一姿。空中继承虚拟地面根点。派蒙保持310显示和96像素／20色精度，本次按可见像素下沿贴到对话框底部。新观感待验。</p>'+html[end:]
 html=html.replace("heavy:'重击'","heavy:'重击',jump:'跳跃',crouch:'下蹲与蹲防'").replace("['dash','light1','light2','light3','heavy']","['jump','crouch','dash','light1','light2','light3','heavy']")
 start=html.index('<p>留档：');end=html.index('</p>',start)+4
 html=html[:start]+'<p>留档：<a href="source/jump-crouch.png">跳跃／下蹲源图</a> · <a href="prompts.json">生成提示词</a> · <a href="import.json">来源、拟合与保留项</a></p>'+html[end:]
 (ART/'index.html').write_text(html,encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items()if k not in ['frames','sourceFiles']},ensure_ascii=False))

if __name__=='__main__':build()

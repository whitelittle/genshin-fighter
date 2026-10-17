"""Isolated wind E prototype and confirmed-hit launcher/jump-cancel route."""
from pathlib import Path
import sys,json,hashlib,shutil,copy
import numpy as np
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runtime/tools'))
import build_teaching_unified as U
from compact_assets import LuaRuntime,python_table
from export_furina import lua
from build_teaching_jump_crouch import board
BASE=ROOT/'outputs/tutorial-guard-pacing-v25-20261017';OUT=ROOT/'outputs/tutorial-wind-combo-v26-20261017';ART=ROOT/'outputs/lumine-wind-skills-20261017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(im):
 a=np.asarray(im);mask=a[:,:,3]>=128;parent=[];runs=[];prev=[]
 def find(k):
  while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
  return k
 for y,row in enumerate(mask):
  edges=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)));cur=[]
  for x,z in zip(edges[::2],edges[1::2]):
   k=len(parent);parent.append(k)
   for px,pz,pk in prev:
    if px<z and pz>x:parent[find(pk)]=find(k)
   cur.append((int(x),int(z),k));runs.append((y,int(x),int(z),k))
  prev=cur
 areas={};bounds={}
 for y,x,z,k in runs:
  k=find(k);areas[k]=areas.get(k,0)+z-x
  b=bounds.setdefault(k,[x,y,z,y+1]);b[:]=[min(b[0],x),min(b[1],y),max(b[2],z),max(b[3],y+1)]
 ids=sorted(areas,key=areas.get,reverse=True)[:4];assert min(areas[k]for k in ids)>10000
 ids.sort(key=lambda k:(int((bounds[k][1]+bounds[k][3])/2//(im.height/2)),(bounds[k][0]+bounds[k][2])/2))
 for k in ids:
  own=np.zeros(mask.shape,dtype=np.uint8)
  for y,x,z,j in runs:
   if find(j)==k:own[y,x:z]=255
  fringe=np.asarray(Image.fromarray(own).filter(ImageFilter.MaxFilter(3)))>0
  rgba=a.copy();rgba[:,:,3]=np.where(fringe,a[:,:,3],0);b=bounds[k]
  assert b[0]>0 and b[1]>0 and b[2]<im.width and b[3]<im.height,('clipped',b)
  yield Image.fromarray(rgba).crop(b),b
def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True);(OUT/'verification').mkdir(exist_ok=True);(ART/'fit').mkdir(exist_ok=True);(ART/'extracted').mkdir(exist_ok=True)
 rt=LuaRuntime();rt.execute('__loaders={};'+(BASE/'source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']());old=copy.deepcopy(data)
 cal=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/report.json').read_text(encoding='utf-8'));pal=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/fit/master-contrast.json').read_text(encoding='utf-8'))['palette'];U.ART=ART;rows={}
 for g in ['skill','skillUp','skillDown']:
  im=Image.open(ART/'source'/f'{g}.png').convert('RGBA');factor=im.width/2048;assert im.height==3072*factor
  for i,(crop,b)in enumerate(extract(im)):
   key=f'{g}_{i}';crop.save(ART/'extracted'/f'{key}.png')
   # The tool returned the requested sheet at uniform half resolution. Restore
   # original master source units globally, never normalize individual poses.
   root=[(i%2*1024+520)*factor-b[0],(i//2*1536+1435)*factor-b[1]]
   if not(g=='skillUp' and i in [1,2]):root[1]=crop.height
   data['frames'][key],rows[key]=U.fit(crop,root,cal['sourceUnit']/factor,key,cal,pal)
   rows[key].update(source=f'source/{g}.png',bounds=b,sheetFactor=factor,ownership='actual connected silhouette; no rectangle cell clipping')
 assert all(data['frames'][k]==v for k,v in old['frames'].items()if k not in rows)
 unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()};mean=sum(v['n']for v in unique.values())/len(unique);assert mean<1000
 data['bodyPeak']=max(v['n']for v in data['frames'].values())
 (OUT/'source/teaching/gf_lumine_training_data.lua').write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 for g in ['skill','skillUp','skillDown']:board(ART/f'{g}-review.png',['teaching_master']+data['groups'][g]['frames'],data['frames'])
 (ART/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>风旅行者三向E候选</title><style>body{background:#263454;color:white}img{max-width:100%;image-rendering:pixelated}</style><h1>风旅行者三向E · 动作候选</h1><p>母版／准备／出手／跟随／收招，同尺度。特效在试玩中查看，美术待验。</p>'+''.join(f'<h2>{g}</h2><img src="{g}-review.png">'for g in ['skill','skillUp','skillDown'])+'<p><a href="prompts.json">内置image_gen提示词</a> · <a href="import.json">拟合记录</a></p>',encoding='utf-8')
 def edit(rel,before,after,count=1):
  p=OUT/'source'/rel;s=p.read_text(encoding='utf-8');assert s.count(before)==count,(rel,before);p.write_text(s.replace(before,after),encoding='utf-8')
 # Ground chain -> launcher -> confirmed jump cancel -> air light/heavy.
 edit('teaching/gf_lumine_training_rules.lua',"cancel={'light2'}","cancel={'light2','crouchHeavy','skill'}")
 edit('teaching/gf_lumine_training_rules.lua',"cancel={'light3'}","cancel={'light3','crouchHeavy','skill'}")
 edit('teaching/gf_lumine_training_rules.lua',"knockdown=true,box={x=10,y=10,w=240,h=105},energy=8,cancel={}","launch=26,knockdown=true,box={x=10,y=10,w=240,h=105},energy=8,cancel={'jump'}")
 edit('teaching/gf_lumine_training_rules.lua',"box={x=5,y=-40,w=215,h=185},energy=4,cancel={}","box={x=5,y=-40,w=215,h=185},energy=4,cancel={'airHeavy','skill'}")
 edit('characters/gf_character_registry.lua',"key='lumine',name='荧',element='anemo',weapon='sword',attack='轻击试作',skill='暂未开放'", "key='lumine',name='荧',element='anemo',weapon='sword',attack='轻击试作',skill='风球／风刃'")
 edit('teaching/gf_sim_lumine_training.lua','function T:startMove(p,id)', '''function T:tryCancel(p,m)
 if p.key=='lumine' and p.moveId=='crouchHeavy' and p.trainingLaunchHit and p.connected and p.t<=m.startup+m.active+8 and p.inPressed&1~=0 then
  local now=p.inNow;local forward=p.face>0 and 8 or 4;local back=p.face>0 and 4 or 8
  self:setState(p,'jumpsq');p.jumpDir=now&forward~=0 and 1 or now&back~=0 and -1 or 0;p.trainingChase=true
  self:emit({type='jumpCancel',p=p.id});return true
 end
 return Base.tryCancel(self,p,m)
end
function T:startMove(p,id)''')
 edit('teaching/gf_sim_lumine_training.lua','function T:startMove(p,id)\n local ok',"function T:startMove(p,id)\n if p.key=='lumine' then p.trainingLaunchHit=nil end\n local ok")
 edit('teaching/gf_sim_lumine_training.lua','add(p.trainingGuardPace)','add(p.trainingGuardPace);add(p.trainingChase and 1 or 0);add(p.trainingLaunchHit and 1 or 0)')
 edit('teaching/gf_sim_lumine_training.lua',' local a=self.assist;add(a and 1 or 0)'," for _,pr in ipairs(self.proj)do add(pr.owner);add(pr.x);add(pr.y);add(pr.vx);add(pr.vy);add(pr.t);add(pr.life);add(pr.hits);str(pr.style);str(pr.move and pr.move.branch)end\n local a=self.assist;add(a and 1 or 0)")
 edit('teaching/gf_sim_lumine_training.lua',' Base.fighterTick(self,p)\n if p.key', ''' Base.fighterTick(self,p)
 if p.trainingChase and p.state=='air' then p.vy=28*C;p.vx=(p.jumpDir or 0)*p.face*700;p.trainingChase=nil
 elseif p.trainingChase and p.state~='jumpsq' then p.trainingChase=nil end
 if p.key''')
 edit('teaching/gf_sim_lumine_training.lua',' Base.step(self,a,b)\n if self.phase', ''' Base.step(self,a,b)
 -- Air follow-ups pressed during hitstop must be accepted like ground cancels.
 local air=self.f[1]
 if air.key=='lumine' and air.state=='air' and air.airMove and air.hitstop>0 and air.inPressed~=0 then self:tryCancel(air,air.airMove) end
 if self.phase''')
 edit('teaching/gf_sim_lumine_training.lua'," local m=clone(K.skills.lumine);m.branch=branch;m.startup=branch=='skillDown' and 24 or branch=='skillUp' and 20 or 18", " local m=clone(K.skills.lumine);m.branch=branch;m.windProjectile=p.element=='anemo';m.startup=m.windProjectile and 24 or branch=='skillDown' and 24 or branch=='skillUp' and 20 or 18;m.dur=m.windProjectile and 8 or m.dur")
 edit('teaching/gf_sim_lumine_training.lua'," self:setState(p,'skill',m,branch);p.skillCd", " p.airMove=nil;p.airMoveId=nil;p.trainingChase=nil\n self:setState(p,'skill',m,branch);p.skillCd")
 edit('teaching/gf_sim_lumine_training.lua',' local m=p.move\n if p.t==m.startup then', ''' local m=p.move
 if m.windProjectile and m.branch=='skillUp' and p.t==8 and p.y==0 then p.vy=12*C;self:emit({type='jump',p=p.id}) end
 if p.t==m.startup then''')
 edit('teaching/gf_sim_lumine_training.lua',"  self:trainingStrike(p,m,'skill',x,y,w,h)", '''  if m.windProjectile then
   local hit=clone(m);hit.push=5;hit.blockstun=16;hit.level='mid';hit.energy=4
   local spec={x=105,y=180,speed=12,w=120,h=120,life=45,style='travelerWindBall'}
   if m.branch=='skillUp' then spec.y=160;spec.vy=-6;spec.style='travelerWindThrow';hit.launch=18
   elseif m.branch=='skillDown' then spec.y=55;spec.speed=20;spec.w=80;spec.h=110;spec.style='travelerWindBlade';hit.level='low' end
   self:spawnProj(p,spec,hit,'skill')
  else self:trainingStrike(p,m,'skill',x,y,w,h) end''')
 # Body provider owns limited code-native wind effects, independent of UI and damage.
 p=OUT/'source/teaching/gf_character_lumine_training.lua';s=p.read_text(encoding='utf-8');s=s.replace("local D=require('gf_lumine_training_data')","local D=require('gf_lumine_training_data')\nlocal G=require('gf_gfx')")
 s=s.replace('return P\nend',WIND_VIEW+'\nreturn P\nend');p.write_text(s,encoding='utf-8')
 edit('battle/gf_scene_fight.lua',"            if st == 'arrow' then", "            if st=='travelerWindBall' or st=='travelerWindThrow' or st=='travelerWindBlade' then\n                require('gf_character_lumine_training').drawWind(L,x,y,w,h,pr.t,pr.face,st=='travelerWindBlade')\n            elseif st == 'arrow' then")
 # Suppress the old generic cast star: the charging wind effect follows the hand.
 edit('battle/gf_battle_events.lua',"if p.key~='nahida' and p.key~='furina' and p.key~='kamisatoayaka' then", "if p.key~='nahida' and p.key~='furina' and p.key~='kamisatoayaka' and p.key~='lumine' then")
 # Projectile event identity must survive the caster returning to idle.
 edit('teaching/gf_sim_lumine_training.lua','function T:hit(a,d,m,kind,opts)', "function T:hit(a,d,m,kind,opts)\n local eventStart=#self.events;local actualMove=a.airMove==m and a.airMoveId or a.moveId")
 edit('teaching/gf_sim_lumine_training.lua'," if result~='hit' then return result end", " for i=eventStart+1,#self.events do local e=self.events[i];if (e.type=='hit' or e.type=='block') and e.by==a.id then e.move=m.windProjectile and m.branch or actualMove or e.move end end\n if a.key=='lumine' and actualMove=='crouchHeavy' then a.trainingLaunchHit=result=='hit' end\n if result~='hit' then return result end")
 edit('teaching/gf_training_extended.lua','向前的元素掌击','向前搓出并推出风球')
 edit('teaching/gf_training_extended.lua','这个扫击准备和收招都更长','这记低位挑斩准备和收招都更长，命中会把对手挑空')
 edit('teaching/gf_training_extended.lua','使用向上释放的战技','腾空后向前下方投出风球')
 edit('teaching/gf_training_extended.lua','使用对地释放的战技','挥剑放出贴近地面的风刃')
 edit('teaching/gf_training_lesson.lua'," local Extended=require('gf_training_extended')", " if self.course=='launcher' then local J=require('gf_training_juggle');self.lessons=J.steps;self.extended=J.new(self)end\n local Extended=require('gf_training_extended')")
 edit('teaching/gf_training_courses.lua',"  {id='guard',", "  {id='launcher',label='挑空与追跳',available=true,desc='命中确认、蹲重挑空、向前跳跃取消、空轻接空重；最后练完整五击路线。',status='可练习 · 4个目标 · 自己输入追跳'},\n  {id='guard',")
 shutil.copy2(ROOT/'runtime/tools/gf_training_juggle.lua',OUT/'source/teaching/gf_training_juggle.lua')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'));order.insert(len(order)-1,'source/teaching/gf_training_juggle.lua')
 (OUT/'source/order.json').write_text(json.dumps(order,indent=2),encoding='utf-8')
 changed=[p for p in order if not(BASE/p).exists() or sha(BASE/p)!=sha(OUT/p)]
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8')for p in order),encoding='utf-8')
 r={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'frames':rows,'bodyUniqueMean':mean,'bodyPeak':data['bodyPeak'],'artAcceptance':'pending','comboDesign':'J,J,down+K,confirmed jump cancel,J,K; wind skill cancel optional','scope':'Traveler only; new wind projectiles, timings and damage reach require verification'}
 for p in [OUT/'build-manifest.json',ART/'import.json']:p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in r.items()if k!='frames'},ensure_ascii=False))
WIND_VIEW='''
function P.drawWind(L,x,y,w,h,t,face,blade)
 local mint={96,236,192};local white={220,255,244}
 if blade then
  for i=1,6 do local q=i/6;L:shape(G.RING,x-face*q*22,y+(q-.5)*h*.5,w*(1-q*.55),h*(1-q*.1),i%2==0 and white or mint,.9-q*.4,face*(20+t*3)) end
  L:rect(x-face*35,y,w*.8,8,white,.9)
 else
  L:shape(G.ELLIPSE,x,y,w*.75,h*.75,mint,.45)
  for i=1,5 do L:shape(G.RING,x,y,w*(.55+i*.09),h*(.35+i*.11),i%2==0 and white or mint,.85,i*35+t*13)end
  for i=1,4 do local a=math.rad(i*90+t*16);L:rect(x+math.cos(a)*w*.28,y+math.sin(a)*h*.28,16,6,white,.95,t*16+i*90)end
 end
end
function P.drawExtras(v)
 v.windL=v.windL or G.layer(v.layers.fx);local L=v.windL;L:begin()
 local f=v.f;local m=f.move
 if f.state=='skill' and m and m.windProjectile then
  local t=f.t;local up=m.branch=='skillUp';local down=m.branch=='skillDown'
  if t<m.startup then
   local k=t/m.startup;local r=30+70*k
   P.drawWind(L,f.x/100+f.face*(down and 60 or 105),f.y/100+(down and 60 or up and 160 or 180),r,down and 100 or r,t,f.face,down)
  end
 end
 L:finish()
end
function P.freeView(v)if v.windL then v.windL:free();v.windL=nil end end
'''
if __name__=='__main__':build()

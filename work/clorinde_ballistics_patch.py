from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-ballistics-20261014';O.mkdir(exist_ok=True)
def edit(rel,fn):
 p=R/rel;h=O/'history'/rel;h.parent.mkdir(parents=True,exist_ok=True)
 assert not h.exists(),'patch is one-shot; use saved baseline for retries'
 shutil.copy2(p,h);p.write_text(fn(p.read_text(encoding='utf8')),encoding='utf8')
edit('runtime/source/characters/gf_clorinde_rules_data.lua',lambda s:s.replace('return {','return {["shot"]={duration=8,origin=170,speed=45,near=9,far=203},',1))
def sim(s):
 s=s.replace('oldThrow=S.startBurst,S.skillUpdate,S.burstUpdate,S.fighterTick,S.physics,S.tryThrow','oldThrow=S.startBurst,S.skillUpdate,S.burstUpdate,S.fighterTick,S.physics,S.tryThrow\n local oldAttack,oldAirAttack=S.attackUpdate,S.airAttackUpdate')
 a=s.index('  local t=p.t;local window=')
 b=s.index('  if p.t>=D.skillTotal',a)
 s=s[:a]+'''  local t=p.t;local window=(t>=8 and t<8+D.shot.duration and 1 or t>=18 and t<22 and 2 or 0)
  if window>0 and ((p.skillHitMask or 0)&(1<<window))==0 then
   local box={x=60,y=0,w=220,h=230}
   if window==1 then
    local age=t-8
    box={x=D.shot.origin+age*D.shot.speed+D.shot.near,y=0,w=D.shot.far-D.shot.near,h=230}
   end
   local x0,x1,y0,y1=ctx.boxOf(p,box,1);local a,b,c,d=self:hurtbox(p.foe)
   if a and ctx.overlap(x0,x1,y0,y1,a,b,c,d) then
    local result=self:hit(p,p.foe,{damage=window==1 and 35 or 50,hitstun=28,blockstun=16,push=8,level='mid',energy=8,shake=8},'skill')
    if result then p.skillHitMask=(p.skillHitMask or 0)|(1<<window) end
   end
  end
'''+s[b:]
 pos=s.index(' local oldStartSkill=S.startSkill')
 s=s[:pos]+''' -- The three firearm attacks keep damage, level, startup and total action length.
 -- Their visible bullet lives eight ticks; each tick checks its current horizontal span.
 local function firearm(self,p,m,t,kind)
  local age=t-m.startup
  if age<0 or age>=D.shot.duration or p.connected then return end
  local box={x=D.shot.origin+age*D.shot.speed+D.shot.near,
    y=m.box.y,w=D.shot.far-D.shot.near,h=m.box.h}
  local x0,x1,y0,y1=ctx.boxOf(p,box,1);local a,b,c,d=self:hurtbox(p.foe)
  if a and ctx.overlap(x0,x1,y0,y1,a,b,c,d) then self:hit(p,p.foe,m,kind) end
 end
 function S:attackUpdate(p)
  if p.key~='clorinde' or (p.moveId~='light2' and p.moveId~='heavy') then return oldAttack(self,p) end
  local m,t=p.move,p.t;local su,ac=m.startup,m.active
  if m.lunge and t<su then p.vx=p.face*math.floor(m.lunge*C/su)
  elseif t<su+ac then p.vx=p.vx*6//10 else p.vx=0 end
  if not m.whiff then firearm(self,p,m,t,p.moveId=='heavy' and 'heavy' or 'light') end
  if t>=su and self:tryCancel(p,m) then return end
  if t>=su+ac+m.recovery then self:setState(p,'idle') end
 end
 function S:airAttackUpdate(p)
  if p.key~='clorinde' or p.airMoveId~='airLight' then return oldAirAttack(self,p) end
  local m,t=p.airMove,p.airT;p.airT=t+1
  firearm(self,p,m,t,'light')
  if t>=m.startup and self:tryCancel(p,m) then return end
  if t>=m.startup+m.active+m.recovery then p.airMove=nil end
 end
'''+s[pos:]
 return s
edit('runtime/source/battle/gf_sim_clorinde.lua',sim)
def view(s):
 s=s.replace("local G=require('gf_gfx')","local G=require('gf_gfx')\nlocal Rules=require('gf_clorinde_rules_data')")
 s=s.replace("    if shot then add(2,'bullet',170+age*45,180,1-age/8) end", "    local spent=id=='skill' and ((f.skillHitMask or 0)&2~=0) or (id~='skill' and id~='burst' and f.connected)\n    if shot and not spent then add(2,'bullet',Rules.shot.origin+age*Rules.shot.speed,180,1-age/Rules.shot.duration) end")
 return s
edit('runtime/source/characters/gf_character_clorinde_view.lua',view)
edit('runtime/source/network/gf_online.lua',lambda s:s.replace('O.VERSION = 7','O.VERSION = 8'))
edit('runtime/tests/skill-feedback.lua',lambda s:s.replace(".VERSION==7", ".VERSION==8"))
edit('runtime/tests/run.py',lambda s:s.replace("'skill-feedback.lua']","'skill-feedback.lua','clorinde-ballistics.lua']").replace('Protocol 7','Protocol 8').replace('assert(O.VERSION==7)','assert(O.VERSION==8)').replace('lobby={version=6}','lobby={version=7}').replace('lobby.version=7','lobby.version=8'))
print('three firearm attacks and E bullet timeline aligned; protocol 8')

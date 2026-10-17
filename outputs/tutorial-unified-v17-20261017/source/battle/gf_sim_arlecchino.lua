__loaders['gf_sim_arlecchino']=function()
local K=require('gf_kits')
local D=require('gf_arlecchino_rules_data')
-- Only this character adapter owns the delivered action timeline. No view writes simulation.
return function(S,ctx)
 local C,WALL=ctx.C,ctx.WALL
 local oldBurst,oldSkillUpdate,oldBurstUpdate,oldFighter,oldPhysics,oldThrow=S.startBurst,S.skillUpdate,S.burstUpdate,S.fighterTick,S.physics,S.tryThrow
 local function locked(p)
  local a=p.foe
  return a.key=='arlecchino' and ((a.state=='throw' and a.t<42) or (a.state=='burst' and a.cinematicConfirmed and a.t<162))
 end
 function S:startBurst(p)
  if p.key~='arlecchino' then return oldBurst(self,p) end
  if p.energy<100 then return false end
  p.energy=0;p.coat=0;p.invul=6;p.castX=p.x;p.castFace=p.face
  self:setState(p,'burst',p.kit.burst,'burst');p.cinematicConfirmed=false;p.stats.bursts=p.stats.bursts+1
  self:emit({type='burstAttempt',p=p.id,fx='soumetsu',element=p.element,style='soumetsuCinematic'})
  return true
 end
 function S:tryThrow(p)
  oldThrow(self,p)
  if p.key=='arlecchino' and p.state=='throw' then
   p.x=math.max(-WALL+180*C,math.min(WALL-180*C,p.x))
  end
 end
 function S:skillUpdate(p)
  if p.key~='arlecchino' then return oldSkillUpdate(self,p) end
  p.vx=0
  local t=p.t;local window=(t>=18 and t<24 and 1 or 0)
  if window>0 and ((p.skillHitMask or 0)&(1<<window))==0 then
   local x0,x1,y0,y1=ctx.boxOf(p,{x=60,y=0,w=220,h=230},1);local a,b,c,d=self:hurtbox(p.foe)
   if a and ctx.overlap(x0,x1,y0,y1,a,b,c,d) then
    self:hit(p,p.foe,{damage=85,hitstun=28,blockstun=16,push=8,level='mid',energy=8,shake=8},'skill')
    p.skillHitMask=(p.skillHitMask or 0)|(1<<window)
   end
  end
  if p.t>=D.skillTotal then self:setState(p,p.y>0 and 'air' or 'idle') end
 end
 local oldStartSkill=S.startSkill
 function S:startSkill(p)
  local ok=oldStartSkill(self,p)
  if ok and p.key=='arlecchino' then p.skillHitMask=0 end
  return ok
 end
 function S:burstUpdate(p)
  if p.key~='arlecchino' then return oldBurstUpdate(self,p) end
  local t,d=p.t,p.foe;p.vx=0
  if t==6 then
   local dx=(d.x-p.x)*p.face
   if dx>=-40*C and self:burstTouches(p,d,410) and d.y<420*C then
    local st=d.state;local blocking=ctx.grounded(d) and (st=='idle' or st=='walk' or st=='back' or st=='crouch' or st=='block' or st=='cblock' or st=='land') and ((d.inNow or 0)&(p.x>d.x and 4 or 8)~=0)
    if blocking and d.invul==0 then
     self:setState(d,((d.inNow or 0)&2~=0) and 'cblock' or 'block');d.stun=18
     p.hitstop,d.hitstop=6,6
     self:emit({type='block',p=d.id,by=p.id,x=d.x,y=d.y+170*C,heavy=true,kind='burst'})
    elseif d.invul==0 and st~='down' and st~='getup' and st~='thrown' and st~='ko' then
     self:setState(d,'hit');d.stun=160;d.vx,d.vy=0,0
     p.cinematicConfirmed=true;p.invul=170
     p.x=math.max(-WALL+500*C,math.min(WALL-500*C,p.x));p.castX=p.x;p.castFace=p.face
     p.hitstop,d.hitstop=0,0
     self:emit({type='arlecchinoCinematic',p=p.id})
    end
   end
  end
  if p.cinematicConfirmed then
   if t==70 or t==94 or t==118 then
    self:hit(p,d,{damage=t==118 and 96 or 97,hitstun=160,blockstun=18,push=0,energy=0,level='mid',shake=9},'burst',{unblockable=true,ignoreInvul=true})
    p.hitstop,d.hitstop=0,0 -- delivered cinematic has one continuous clock
   end
   local root=D.burstRoots[math.min(163,t+1)]
   d.x=p.x+p.face*root[1];d.y=root[2];d.vx,d.vy=0,0
   if t>=162 then self:setState(d,'down');d.y=0;self:setState(p,'idle') end
  elseif t>=24 then self:setState(p,p.y>0 and 'air' or 'idle') end
 end
 local function throwTick(self,p)
  local t,d=p.t,p.foe;p.vx=0
  local root=D.throwRoots[math.min(51,t+1)]
  if t<42 then d.x=p.x+p.face*root[1];d.y=root[2];d.vx,d.vy=0,0;d.face=-p.face;d.t=t end
  if t==32 then
   local dmg=K.throw.damage;d.hp=math.max(0,d.hp-dmg);p.energy=math.min(100,p.energy+K.throw.energy)
   p.stats.damage=p.stats.damage+dmg;d.combo,d.comboDmg=1,dmg
   if d.hp<=0 then d.ko=true;self:emit({type='ko',p=d.id,by=p.id,x=d.x,y=d.y+170*C}) end
   self:emit({type='hit',p=d.id,by=p.id,kind='throw',dmg=dmg,combo=1,x=d.x,y=d.y+170*C,element=p.element,heavy=true,shake=9,weapon=p.weapon})
  end
  if t==42 then self:setState(d,'down');d.y=0;self:emit({type='land',p=d.id,x=d.x,hard=true}) end
  if t>=50 then self:setState(p,'idle') end
 end
 function S:fighterTick(p)
  if locked(p) then return end
  if p.key=='arlecchino' and p.state=='throw' then p.t=p.t+1;throwTick(self,p);return end
  oldFighter(self,p)
 end
 function S:physics(p)
  if locked(p) then return end
  return oldPhysics(self,p)
 end
end
end

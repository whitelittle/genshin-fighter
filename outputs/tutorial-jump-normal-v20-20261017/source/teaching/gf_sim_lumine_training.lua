__loaders['gf_sim_lumine_training']=function()
-- Isolated deterministic subclass: the V15 match simulator and other characters stay intact.
local Base=require('gf_sim');local K=require('gf_kits')
local T={};T.__index=function(_,k)return T[k] or Base[k]end
local C=100;local abs,min,max,floor=math.abs,math.min,math.max,math.floor
local function clone(t)local n={};for k,v in pairs(t)do n[k]=v end;return n end
local can={idle=true,walk=true,back=true,crouch=true,land=true}
function T.new(opts)
 local s=Base.new(opts);setmetatable(s,T);s.assistCd=0;s.assist=nil;s.cores={};s.crystals={};s.elementMode='anemo'
 return s
end
function T.copy(src)
 local s=Base.copy(src);setmetatable(s,T)
 s.assist=src.assist and clone(src.assist) or nil;s.cores={};s.crystals={}
 for i,v in ipairs(src.cores)do s.cores[i]=clone(v)end
 for i,v in ipairs(src.crystals)do s.crystals[i]=clone(v)end
 return s
end
T.snapshot=T.copy
function T:hash()
 local h=Base.hash(self)
 local function add(v)h=(h*31+(v or 0))&0x7fffffff end
 local function str(v)for i=1,#(v or '')do add(v:byte(i))end end
 str(self.elementMode);add(self.assistCd)
 for _,p in ipairs(self.f)do
  add(p.face);add(p.inPrev);add(p.releaseMask);add(p.skillCd);add(p.coat);add(p.frozen);add(p.shield);add(p.shieldT);add(p.quickened);add(p.techT);add(p.auraT);add(p.hitstop);add(p.invul);add(p.vuln);add(p.airT);add(p.lastFwd);add(p.lastBack)
  str(p.state);str(p.element);str(p.aura);str(p.moveId);str(p.airMoveId)
  for _,dot in ipairs(p.dots)do add(dot.by);add(dot.every);add(dot.left);add(dot.dmg);add(dot.t)end
 end
 for _,list in ipairs({self.cores,self.crystals})do add(#list);for _,o in ipairs(list)do add(o.x);add(o.t);str(o.element)end end
 local a=self.assist;add(a and 1 or 0);if a then add(a.t);add(a.x);add(a.face);add(a.connected and 1 or 0)end
 return h
end
function T:resetObjects()self.cores={};self.crystals={};self.assist=nil;self.assistCd=0 end
function T:setElement(element)self.elementMode=element;self.f[1].element=element end
-- Keep shared V15 rules unchanged; only Traveler forward-dash speed is amplified.
function T:neutral(p)
 Base.neutral(self,p)
 if p.key=='lumine' and p.state=='dash' and p.t==0 then p.vx=p.vx*22//10 end
end
function T:startSkill(p)
 if p.key~='lumine' then return Base.startSkill(self,p)end
 if p.skillCd>0 then return false end
 local branch=p.inNow&2~=0 and 'skillDown' or p.inNow&1~=0 and 'skillUp' or 'skill'
 local m=clone(K.skills.lumine);m.branch=branch;m.startup=branch=='skillDown' and 24 or branch=='skillUp' and 20 or 18
 self:setState(p,'skill',m,branch);p.skillCd=m.cd;p.coat=0;p.energy=min(100,p.energy+8);p.vx=0
 self:emit({type='skill',p=p.id,style=m.style,fx=m.fx,element=p.element,branch=branch});return true
end
function T:skillUpdate(p)
 if p.key~='lumine' then return Base.skillUpdate(self,p)end
 local m=p.move
 if p.t==m.startup then
  self:emit({type='skillActive',p=p.id,style=m.style,fx=m.fx,element=p.element})
  local x,y,w,h=10,70,320,200
  if m.branch=='skillUp' then x,y,w,h=-30,80,240,420 elseif m.branch=='skillDown' then x,y,w,h=0,0,370,170 end
  self:trainingStrike(p,m,'skill',x,y,w,h)
 end
 if p.t>=m.startup+m.dur+m.recovery then self:setState(p,p.y>0 and 'air' or 'idle')end
end
function T:startBurst(p)
 if p.key~='lumine' then return Base.startBurst(self,p)end
 if p.energy<100 then return false end
 p.energy=0;p.stats.bursts=p.stats.bursts+1;p.vx=0;p.coat=0
 self:setState(p,'burst',p.kit.burst,'burst');p.invul=12
 self:emit({type='burst',p=p.id,fx='wind',style='trainingBurst',element=p.element});return true
end
function T:burstUpdate(p)
 if p.key~='lumine' then return Base.burstUpdate(self,p)end
 if p.t==p.move.startup then
  self:emit({type='burstActive',p=p.id,fx='wind',style='trainingBurst',element=p.element})
  self:trainingStrike(p,p.move,'burst',-10,0,390,370)
 end
 if p.t>=p.move.startup+p.move.active+p.move.recovery then self:setState(p,'idle')end
end
function T:trainingStrike(p,m,kind,x,y,w,h)
 local d=p.foe;local a,b,c,e=self:hurtbox(d);if not a then return end
 local x0,x1=p.x+p.face*x*C,p.x+p.face*(x+w)*C;if x0>x1 then x0,x1=x1,x0 end
 local y0,y1=p.y+y*C,p.y+(y+h)*C
 -- Cores are real bounded world objects; lightning/fire must touch them, not only the monster.
 for i=#self.cores,1,-1 do local core=self.cores[i]
  if core.x>=x0 and core.x<=x1 and y0<=90*C and (p.element=='electro' or p.element=='pyro')then
   local r=p.element=='electro' and 'hyperbloom' or 'burgeon';table.remove(self.cores,i)
   self:reactionEvent(p,d,r);self:reactionDamage(p,d,90,r)
  end
 end
 if a<x1 and b>x0 and c<y1 and e>y0 then
  local move=clone(m);move.push=5;move.blockstun=16;move.level='mid';move.energy=kind=='burst' and 0 or 4
  return self:hit(p,d,move,kind)
 end
end
function T:reactionEvent(a,d,r)
 a.stats.reactions=a.stats.reactions+1
 self:emit({type='reaction',p=d.id,by=a.id,r=r,x=d.x,y=d.y+200*C})
end
function T:reactionDamage(a,d,damage,r)
 d.hp=max(1,d.hp-damage);a.stats.damage=a.stats.damage+damage
 self:emit({type='dot',p=d.id,by=a.id,dmg=damage,r=r,x=d.x,y=d.y+140*C})
end
local reactions={hydro={pyro='vaporize',cryo='frozen',electro='electro',dendro='bloom'},pyro={hydro='vaporize',cryo='melt',electro='overload',dendro='burning'},cryo={hydro='frozen',pyro='melt',electro='superconduct'},electro={hydro='electro',pyro='overload',cryo='superconduct',dendro='quicken'},dendro={hydro='bloom',electro='quicken',pyro='burning'}}
function T:hit(a,d,m,kind,opts)
 local elemental=a.key=='lumine' and (kind=='skill' or kind=='burst')
 local aura=d.aura;local r
 if elemental then
  if (d.quickened or 0)>0 and (a.element=='electro' or a.element=='dendro')then r=a.element=='electro' and 'aggravate' or 'spread'
  elseif (a.element=='anemo' or a.element=='geo') and (aura=='pyro' or aura=='hydro' or aura=='electro' or aura=='cryo')then r=a.element=='anemo' and 'swirl' or 'crystal'
  else r=reactions[a.element] and reactions[a.element][aura]end
 elseif d.frozen>0 and kind=='heavy' then r='shatter'end
 local move=clone(m)
 if r=='vaporize' then move.damage=move.damage*(a.element=='hydro' and 200 or 150)//100
 elseif r=='melt' then move.damage=move.damage*(a.element=='pyro' and 200 or 150)//100
 elseif r=='aggravate' or r=='spread' then move.damage=move.damage+24 end
 -- The old coat shortcut is not the teaching aura model, and physical attacks cannot consume an aura.
 local coat=d.coat;d.coat=0;local result=Base.hit(self,a,d,move,kind,opts);d.coat=coat
 if result~='hit' then return result end
 if elemental and not r then d.aura=a.element;d.auraT=600 end
 if r then
  self:reactionEvent(a,d,r)
  if r=='quicken' then d.quickened=600;d.aura=nil
  elseif r=='aggravate' or r=='spread' then -- preserve the existing Quicken state
  elseif r=='frozen' then d.frozen=90;d.stun=90;d.vx=0;d.aura='cryo';d.auraT=600
  elseif r=='bloom' then if #self.cores>=3 then table.remove(self.cores,1)end;self.cores[#self.cores+1]={x=d.x,t=300};d.aura=nil
  elseif r=='crystal' then if #self.crystals>=3 then table.remove(self.crystals,1)end;self.crystals[#self.crystals+1]={x=d.x-a.face*100*C,t=900,element=aura};d.aura=nil
  elseif r=='electro' or r=='burning' then d.dots[#d.dots+1]={by=a.id,every=r=='electro' and 20 or 15,left=r=='electro' and 3 or 6,dmg=12,t=0};d.aura=nil
  elseif r=='superconduct' then d.vuln=240;d.aura=nil;self:reactionDamage(a,d,24,r)
  elseif r=='overload' then self:reactionDamage(a,d,50,r);self:setState(d,'airhit');d.vy=1800;d.vx=a.face*500;d.aura=nil
  elseif r=='swirl' or r=='shatter' then self:reactionDamage(a,d,35,r);d.aura=nil
  else d.aura=nil end
 end
 return result
end
function T:tryThrow(p)
 if p.key~='lumine' and p.foe.key~='lumine' then return Base.tryThrow(self,p)end
 if abs(p.x-p.foe.x)>self:throwRange(p) or p.foe.y>0 then return Base.tryThrow(self,p)end
 self:setState(p,'attack',{pose='slash',startup=18,active=1,recovery=20,damage=0,whiff=true},'throwStart')
 self:emit({type='throwWindup',p=p.id})
end
function T:attackUpdate(p)
 if p.moveId~='throwStart' then return Base.attackUpdate(self,p)end
 p.vx=0;if p.t==18 then Base.tryThrow(self,p)end
end
function T:fighterTick(p)
 if p.techT and p.techT>0 then p.techT=p.techT-1 end
 if (p.quickened or 0)>0 then p.quickened=p.quickened-1 end
 if (p.auraT or 0)>0 then p.auraT=p.auraT-1;if p.auraT==0 then p.aura=nil end end
 if p.state=='thrown' and p.foe.state=='throw' and p.foe.t<=12 and p.inPressed&512~=0 then
  local a=p.foe;self:setState(a,'idle');self:setState(p,'idle');p.techT=20;a.techT=20
  a.x=a.x-a.face*6000;p.x=p.x+p.face*-6000;p.invul=20;a.invul=20
  self:emit({type='throwTech',p=p.id,by=a.id});return
 end
 return Base.fighterTick(self,p)
end
function T:callSupport()
 local p=self.f[1]
 if self.assistCd>0 or self.assist or not (can[p.state] or p.state=='attack' or p.state=='skill' or p.state=='air')then
  self:emit({type='supportDenied',p=1,code=self.assistCd>0 and 'cooldown' or 'state'});return false
 end
 self.assist={t=0,x=p.x-p.face*9000,face=p.face,connected=false};self.assistCd=360
 self:emit({type='supportCall',p=1,key='aether'});return true
end
function T:step(a,b)
 local oldTick=self.tick;local frozen=self.freeze>0
 Base.step(self,a,b)
 if self.phase~='fight' or frozen or self.tick==oldTick then return end
 if self.assistCd>0 then self.assistCd=self.assistCd-1 end
 local p=self.f[1]
 if p.inPressed&1024~=0 then self:callSupport()end
 local assist=self.assist
 if assist then
  assist.t=assist.t+1
  if assist.t==20 then
   local fake={id=1,key='aether',element='anemo',weapon='sword',face=assist.face,x=assist.x,y=0,size=1,energy=0,stats=p.stats,hitCount=0,shield=0,shieldT=0,moveId='assist'}
   local d=p.foe;local h0,h1=self:hurtbox(d);local x0,x1=assist.x+assist.face*4000,assist.x+assist.face*41000;if x0>x1 then x0,x1=x1,x0 end
   if h0 and h0<x1 and h1>x0 and d.y<28000 then
    local outcome=self:hit(fake,d,{damage=65,hitstun=24,blockstun=12,push=5,level='mid',energy=0},'assist')
    assist.connected=outcome=='hit';self:emit({type='supportContact',p=1,outcome=outcome})
   end
  end
  if assist.t>=64 then self.assist=nil end
 end
 for i=#self.cores,1,-1 do local core=self.cores[i];core.t=core.t-1
  if core.t<=0 then table.remove(self.cores,i);if abs(core.x-p.foe.x)<18000 then self:reactionDamage(p,p.foe,60,'bloom')end end
 end
 for i=#self.crystals,1,-1 do local crystal=self.crystals[i];crystal.t=crystal.t-1
  if abs(p.x-crystal.x)<6000 and p.y==0 then p.shield=120;p.shieldT=360;table.remove(self.crystals,i);self:emit({type='crystalPickup',p=1})
  elseif crystal.t<=0 then table.remove(self.crystals,i)end
 end
end
function T:separate()
 -- A jumping Traveler can pass above a grounded fighter. Grounded bodies still push apart.
 local a,b=self.f[1],self.f[2]
 if a.state=='thrown' or b.state=='thrown' then return end
 local need=floor(70*C*a.size)+floor(70*C*b.size);local dx=b.x-a.x
 if abs(a.y-b.y)<120*C and abs(dx)<need then
  local push=(need-abs(dx))//2+1;if dx==0 then dx=a.face end
  if dx>0 then a.x=a.x-push;b.x=b.x+push else a.x=a.x+push;b.x=b.x-push end
 end
 for _,p in ipairs(self.f)do p.x=max(-Base.WALL,min(Base.WALL,p.x))end
 if abs(b.x-a.x)>1250*C then local mid=(a.x+b.x)//2;if a.x<b.x then a.x,b.x=mid-625*C,mid+625*C else a.x,b.x=mid+625*C,mid-625*C end end
end
return T
end

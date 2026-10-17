__loaders['gf_sim_assist']=function()
local Rules=require('gf_assist_rules')
local Registry=require('gf_character_registry')
local K=require('gf_kits')
return function(S,ctx)
 local C,B=ctx.C,ctx.B
 local oldRound,oldCopy,oldHash=S.startRound,S.copy,S.hash
 function S:startRound(first)
  oldRound(self,first);self.assists={};self.assistCd={0,0}
  for _,p in ipairs(self.f)do p.jumpAttack=nil end
 end
 function S:assistPartner(side)
  local selected=self.opts.assistChars and self.opts.assistChars[side]
  local char=type(selected)=='string' and Registry.byKey[selected] or selected
  return char and Rules.profiles[char.key] and char or nil,self.teams and 4 or 2
 end
 local forbidden={intro=true,win=true,lose=true,ko=true,hit=true,block=true,cblock=true,
                  airhit=true,down=true,getup=true,thrown=true,throw=true,burst=true}
 function S:callAssist(side)
  local p=self.f[side]
  local function reject(code) self:emit({type='skillFeedback',p=side,skill='assist',code=code});return false end
  if self.phase~='fight' or self.freeze>0 or p.ko or forbidden[p.state] then return reject('assistState') end
  if self.assistCd[side]>0 or self.assists[side] then return reject('assistCooldown') end
  local char,slot=self:assistPartner(side)
  if not char then return reject('noPartner') end
  local x=math.max(-S.WALL+80*C,math.min(S.WALL-80*C,p.x-p.face*110*C))
  local profile=Rules.profiles[char.key]
  local target=x
  if profile.spot then target=x+p.face*math.max(100*C,math.min(520*C,(p.foe.x-x)*p.face)) end
  self.assists[side]={key=char.key,slot=slot,t=0,x=x,y=0,face=p.face,
      targetX=target,ownerKey=p.key,connected=false,ownerId=side}
  self.assistCd[side]=Rules.cooldown
  self:emit({type='assistCall',p=side,key=char.key,slot=slot,x=x,y=0})
  return true
 end
 function S:updateAssists()
  if self.phase~='fight' then self.assists={};return end
  for side=1,2 do
   local p=self.f[side];local a=self.assists[side]
   if self.assistCd[side]>0 then self.assistCd[side]=self.assistCd[side]-1 end
   if a then
    local profile=Rules.profiles[a.key]
    a.t=a.t+1
    local interrupted=a.t<profile.startup and (p.state=='hit' or p.state=='airhit' or p.state=='thrown' or p.ko)
    if p.key~=a.ownerKey or p.ko or interrupted or a.t>=profile.life then
     self.assists[side]=nil
     self:emit({type='assistEnd',p=side,key=a.key,cancelled=interrupted})
    elseif a.t>=profile.startup and a.t<profile.startup+profile.active and not a.connected then
     local box=profile.box;local x=profile.spot and a.targetX or a.x
     local x0=x+a.face*box.x*C;local x1=x+a.face*(box.x+box.w)*C
     if x0>x1 then x0,x1=x1,x0 end
     local h0,h1,v0,v1=self:hurtbox(p.foe)
     if h0 and ctx.overlap(x0,x1,box.y*C,(box.y+box.h)*C,h0,h1,v0,v1) then
      -- A transient source has its own connected/hitstop fields. An assist cannot
      -- award the active fighter a melee cancel or freeze its movement.
      local char=Registry.byKey[a.key]
      local attacker={id=side,char=char,key=a.key,element=char.element,weapon=char.weapon,
       x=a.x,y=0,face=a.face,size=(char.h or 335)/335,state='assist',moveId='assist',
       stats=p.stats,energy=p.energy,connected=false,hitCount=0,hitstop=0,shield=0,shieldT=0}
      local move={};for k,v in pairs(profile.move)do move[k]=v end
      -- The existing reaction system requires active elemental coating. This
      -- release uses base assist damage, without adding a new reaction layer.
      local coating=p.foe.coat;p.foe.coat=0
      local outcome=self:hit(attacker,p.foe,move,'assist')
      p.foe.coat=coating
      if outcome then a.connected=true;self:emit({type='assistContact',p=side,key=a.key,outcome=outcome}) end
     end
    end
   end
  end
 end
 function S.copy(src)
  local dst=oldCopy(src)
  dst.assistCd={src.assistCd[1],src.assistCd[2]};dst.assists={}
  for i,a in pairs(src.assists)do local c={};for k,v in pairs(a)do c[k]=v end;dst.assists[i]=c end
  return dst
 end
 S.snapshot=S.copy
 function S:hash()
  local h=oldHash(self)
  for side=1,2 do
   h=(h*31+self.assistCd[side])&0x7fffffff
   local a=self.assists[side]
   h=(h*31+(self.f[side].jumpAttack=='airHeavy' and 2 or self.f[side].jumpAttack=='airLight' and 1 or 0))&0x7fffffff
   if a then
    h=(h*31+Registry.byKey[a.key].index+a.t*7+a.slot*13+(a.connected and 1 or 0))&0x7fffffff
    h=(h*31+a.x+a.targetX*3+a.face)&0x7fffffff
   else h=(h*31)&0x7fffffff end
  end
  return h
 end
end
end

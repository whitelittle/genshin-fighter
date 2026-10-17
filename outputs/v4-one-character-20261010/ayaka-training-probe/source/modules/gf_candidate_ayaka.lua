__loaders['gf_candidate_ayaka'] = function()
local P={}
function P.install()
 local A=require('gf_art');local R=require('gf_roster');local U=require('gf_util')
 local V=require('gf_fview');local S=require('gf_sim');local D=require('gf_candidate_ayaka_data')
 local key='kamisatoayaka'
 local char={key=key,name='绫华·接入测试',element='cryo',weapon='sword',attack='待接入',skill='待接入',burst='待接入',h=335,index=#R+1}
 R[#R+1]=char;A.byKey[key]=char
 local function image(pose)
  local img=assert(D.frames[pose],'candidate pose not supplied: '..tostring(pose))
  assert(img.bytes,'candidate must finish preparation before rendering')
  return img
 end
 local oldPose,oldSil,oldPrep=A.pose,A.silhouette,A.prepare
 A.pose=function(k,t,p)if k==key then return image(p)end;return oldPose(k,t,p)end
 A.silhouette=function(k,p)if k==key then return image(p)end;return oldSil(k,p)end
 for _,name in ipairs({'face','round','portrait'})do
  local old=A[name]
  A[name]=function(k)if k==key then return image('portrait')end;return old(k)end
 end
 A.prepare=function(k,t)
  if k~=key then return oldPrep(k,t)end
  local list={};for p,img in pairs(D.frames)do if not img.bytes then list[#list+1]=p end end;table.sort(list)
  local job={i=1,total=#list,completed=0}
  function job:step(budget)
   local p=list[self.i];if not p then return true end
   local img=D.frames[p];self.decoder=self.decoder or U.decoder(img.d)
   if not self.decoder:step(math.min(9000,budget or 9000))then return false end
   img.bytes={};local raw=self.decoder.bytes
   for n=1,img.n*5,5 do
    for j=0,3 do img.bytes[n+j]=raw[n+j]*img.u end
    img.bytes[n+4]=raw[n+4]
   end
   img.ax=img.ax*img.u;img.ay=img.ay*img.u;img.w=img.w*img.u;img.h=img.h*img.u
   img.seam=0.08*img.u;img.u=1;img.d=nil
   self.decoder=nil;self.completed=self.i;self.i=self.i+1
   return self.i>self.total
  end
  return job
 end
 local oldReserve,oldFor,oldDraw=V.reserveBody,V.poseFor,V.draw
 V.reserveBody=function(self,budget)
  if self.key~=key then return oldReserve(self,budget)end
  self.bodyCapacity=D.body_peak
  for _,slot in ipairs(self.slots)do
   slot.pinned=true
   if #slot.kids<self.bodyCapacity then slot:ensure(math.min(self.bodyCapacity,#slot.kids+budget));return false end
  end
  return true
 end
 V.poseFor=function(self)
  if self.key~=key then return oldFor(self)end
  local f=self.f;local st,t=f.state,f.t
  if st=='walk' then return 'walk_'..(self.walkT//8%D.counts.walk)end
  if st=='back' then return 'back_'..(self.walkT//8%D.counts.back)end
  if st=='crouch' then return 'crouch_'..math.min(3,t//4)end
  if st=='jumpsq' then return 'jump_0' end
  if st=='land' then return 'jump_5' end
  if st=='air' then return f.vy>300 and 'jump_1' or f.vy>0 and 'jump_2' or f.vy>-300 and 'jump_3' or 'jump_4' end
  if st=='block' then return 'guard_1' end
  if st=='hit' then return 'hurt_0' end
  if st=='airhit' then return 'hurt_2' end
  if st=='down' then return 'hurt_3' end
  if st=='getup' then return 'getup_'..math.min(3,t//4)end
  -- Explicitly unimplemented defeat/win/cblock/thrown fallback, not completed animations.
  return 'idle_'..(t//40%D.counts.idle)
 end
 V.draw=function(self,budget)
  oldDraw(self,budget)
  if self.key==key then
   -- Candidate key poses already show body motion; no extra floating/squash overlays.
   self.root:pos(self.f.x/100,self.f.y/100):rot(0):scale(self.f.face,1)
  end
 end
 -- This first probe deliberately disables unfinished combat and dash/throw states.
 local oldMove,oldSkill,oldBurst,oldThrow,oldNeutral=S.startMove,S.startSkill,S.startBurst,S.tryThrow,S.neutral
 S.startMove=function(self,p,id)if p.key==key then return false end;return oldMove(self,p,id)end
 S.startSkill=function(self,p)if p.key==key then return false end;return oldSkill(self,p)end
 S.startBurst=function(self,p)if p.key==key then return false end;return oldBurst(self,p)end
 S.tryThrow=function(self,p)if p.key==key then return false end;return oldThrow(self,p)end
 S.neutral=function(self,p)
  if p.key==key then
   p.inPressed=p.inPressed & (~(256|512|16|32|64|128))
   p.lastFwd=-100000;p.lastBack=-100000
  end
  return oldNeutral(self,p)
 end
 P.character=char;P.data=D
 return P
end
return P
end

__loaders['gf_character_furina']=function()
local Asset=require('gf_character_assets')
local D=require('gf_furina_data')
-- Native-grid anatomy calibration against idle_0, inspected at equal world scale.
-- These are pose import units, not state/root squash or silhouette-height fits.
-- Reused poses are corrected once, so down/getup and dash/idle keep their joins.
local bodyUnits={
 walk_0=1.16,walk_1=1.16,walk_2=1.16,walk_3=1.16,walk_4=1.16,walk_5=1.16,
 back_0=1.12,back_1=1.12,back_2=1.12,back_3=1.12,back_4=1.12,back_5=1.12,
 hurt_0=1.16,hurt_1=1.12,hurt_2=1.08,hurt_3=1.08,
 getup_1=1.04,getup_2=1.04,
 jump_0=1.08,jump_1=1.08,jump_2=1.08,jump_3=1.08,jump_4=1.08,jump_5=1.08,
 dash_1=1.12,dash_2=1.12,dash_3=1.12,dash_4=1.12,
 backdash_1=1.08,backdash_2=1.08,backdash_3=1.08,backdash_4=1.08,
 crouch_0=1.12,crouch_1=1.12,crouch_2=1.12,crouch_3=1.12,
 block_0=1.08,block_1=1.08,block_2=1.08,block_3=1.08,block_4=1.08,block_5=1.08,
 cblock_0=1.22,
 light1_0=1.06,light1_1=1.06,light1_2=1.06,light1_3=1.06,
 light2_0=1.10,light2_3=1.10,light2_4=1.08,
 light3_0=1.08,light3_2=1.08,light3_3=1.10,
 crouchLight_0=1.10,crouchLight_1=1.10,crouchLight_2=1.10,crouchLight_3=1.10,crouchLight_4=1.10,crouchLight_5=1.10,
 crouchHeavy_0=1.12,crouchHeavy_1=1.12,crouchHeavy_2=1.12,
 airLight_0=1.12,airLight_1=1.12,airLight_2=1.16,airLight_3=1.16,airLight_5=1.12,
 airHeavy_0=1.10,airHeavy_1=1.10,airHeavy_2=1.10,airHeavy_3=1.10,airHeavy_4=1.10,airHeavy_5=1.10,
 thrown_0=1.12,thrown_1=1.12,thrown_3=1.12,thrown_4=1.12,thrown_5=1.12,
}
for id,k in pairs(bodyUnits) do
 local img=assert(D.frames[id],id)
 img.u=img.u*k;img.ux=(img.ux or img.u/k)*k;img.uy=(img.uy or img.u/k)*k
 img.bodyUnitCorrection=k
end
-- Actor-attached emitters and sword ribbons use the very same calibrated units.
-- Independent salon members, stage effects and portraits keep their own scale.
for _,g in pairs(D.groups) do
 if g.effects and g.effects.nozzles then
  for i,q in ipairs(g.effects.nozzles) do
   local k=bodyUnits[g.frames[i]] or 1;q[1]=q[1]*k;q[2]=q[2]*k
  end
 end
end
for phase,id in pairs(D.trails or {}) do
 local k=bodyUnits[D.groups.airLight.frames[tonumber(phase)]] or 1
 local img=D.frames[id]
 img.u=img.u*k;img.ux=(img.ux or img.u/k)*k;img.uy=(img.uy or img.u/k)*k
 img.bodyUnitCorrection=k
end
local P=Asset.new(D)
local moves={light1='light1',light2='light2',light3='light3',heavy='heavy',crouchLight='crouchLight',crouchHeavy='crouchHeavy',airLight='airLight',airHeavy='airHeavy'}
local function total(group)
 local n=0;for _,d in ipairs(group.durations) do n=n+d end;return n
end
local function sample(id,t,loop)
 local g=assert(D.groups[id],id)
 if loop then t=t%total(g) end
 for i,d in ipairs(g.durations) do
  if t<d then return g.frames[i],i end;t=t-d
 end
 return g.frames[#g.frames],#g.frames
end
-- Delivered animation time is preserved. The character rule adapter uses the same clock.
local function moveTime(id,t,m)
 return t
end
function P.poseFor(view)
 local f=view.f;local st,t=f.state,f.t
 if f.foe.key=='furina' and f.foe.state=='burst' and f.foe.cinematicConfirmed then
  return D.groups.hurt.frames[f.foe.t>=122 and 4 or f.foe.t>=56 and 3 or 1]
 end
 if f.foe.key=='kamisatoayaka' and f.foe.state=='burst' and f.foe.cinematicConfirmed then return D.groups.hurt.frames[f.foe.t>=144 and 4 or 3] end
 if f.airMove then local id=moves[f.airMoveId];return sample(id,moveTime(id,f.airT or 0,f.airMove)) end
 if st=='attack' then
  -- The legacy sim reports a failed grab as an attack, without a victim.
  if f.moveId=='throwWhiff' then return sample('throw',math.min(19,t)) end
  local id=assert(moves[f.moveId],f.moveId);return sample(id,moveTime(id,t,f.move))
 end
 if st=='walk' or st=='back' then return sample(st,view.walkT,true) end
 if st=='dash' or st=='backdash' then return sample(st,t) end
 if st=='crouch' then return sample('crouch',t) end
 if st=='jumpsq' then return D.groups.jump.frames[1] end
 if st=='land' then return D.groups.jump.frames[6] end
 if st=='air' then return sample('jump',f.flightT or t) end
 if st=='block' or st=='cblock' then return D.groups[st].frames[t<8 and 4 or 5] end
 if st=='hit' then return D.groups.hurt.frames[1] end
 if st=='airhit' then return D.groups.hurt.frames[3] end
 if st=='down' then return D.groups.hurt.frames[4] end
 if st=='getup' then return sample('getup',t) end
 if st=='skill' then return sample('skill',moveTime('skill',t,f.move)) end
 if st=='burst' then return sample('burst',t) end
 if st=='throw' then return sample('throw',t) end
 if st=='thrown' then return sample('thrown',f.foe.key=='furina' and f.foe.t or t/30*total(D.groups.thrown)) end
 if st=='win' then return sample('win',t) end
 if st=='lose' then return sample('lose',t) end
 return sample('idle',t,true)
end
P.groundedFrames=true
function P.displayScale(view) return 1 end
P.sample=sample
function P.nextLocomotion(view)
 local g=D.groups[view.f.state];if not g then return nil end
 local t=view.walkT%total(g)
 for i,d in ipairs(g.durations) do
  if t<d then return g.frames[i%#g.frames+1] end;t=t-d
 end
end
require('gf_character_furina_view')(P,D)
return P
end

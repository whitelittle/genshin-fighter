__loaders['gf_character_clorinde']=function()
local Asset=require('gf_character_assets')
local D=require('gf_clorinde_data')
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
 if f.foe.key=='clorinde' and f.foe.state=='burst' and f.foe.cinematicConfirmed then return D.groups.hurt.frames[f.foe.t>=144 and 4 or 3] end
 if f.airMove then local id=moves[f.airMoveId];return sample(id,moveTime(id,(f.airT or 0)-1,f.airMove)) end
 if st=='attack' then
  -- The legacy sim reports a failed grab as an attack, without a victim.
  if f.moveId=='throwWhiff' then return sample('throw',math.min(19,t)) end
  local id=assert(moves[f.moveId],f.moveId);return sample(id,moveTime(id,t,f.move))
 end
 if st=='walk' or st=='back' then return sample(st,view.walkT,true) end
 if st=='dash' or st=='backdash' then return sample(st,t/(st=='dash' and 14 or 18)*total(D.groups[st])) end
 if st=='crouch' then return sample('crouch',t) end
 if st=='jumpsq' then return D.groups.jump.frames[1] end
 if st=='land' then return D.groups.jump.frames[6] end
 if st=='air' then return sample('jump',t/32*total(D.groups.jump)) end
 if st=='block' or st=='cblock' then return D.groups[st].frames[t<8 and 3 or 2] end
 if st=='hit' then return D.groups.hurt.frames[1] end
 if st=='airhit' then return D.groups.hurt.frames[3] end
 if st=='down' then return D.groups.hurt.frames[4] end
 if st=='getup' then return sample('getup',t) end
 if st=='skill' then return sample('skill',moveTime('skill',t,f.move)) end
 if st=='burst' then if not f.cinematicConfirmed then return t<6 and D.groups.burst.frames[1] or t<12 and D.groups.burst.frames[2] or D.groups.idle.frames[1] end;return sample('burst',t) end
 if st=='throw' then local pose,phase=sample('throw',t);local low=D.groups.throw.variants and D.groups.throw.variants.nahida;return f.foe.key=='nahida' and low and low[phase] or pose end
 if st=='thrown' then local pose,phase=sample('thrown',f.foe.key=='clorinde' and f.foe.t or t/30*total(D.groups.thrown));local low=D.groups.thrown.variants and D.groups.thrown.variants.nahida;return f.foe.key=='nahida' and low and low[phase] or pose end
 if st=='win' then return sample('win',t) end
 if st=='lose' then return sample('lose',t) end
 return sample('idle',t,true)
end
function P.rootOffset(v) return 0 end
P.groundedFrames=true
P.sample=sample
function P.nextLocomotion(view)
 local g=D.groups[view.f.state];if not g then return nil end
 local t=view.walkT%total(g)
 for i,d in ipairs(g.durations) do
  if t<d then return g.frames[i%#g.frames+1] end;t=t-d
 end
end
require('gf_character_clorinde_view')(P,D)
return P
end

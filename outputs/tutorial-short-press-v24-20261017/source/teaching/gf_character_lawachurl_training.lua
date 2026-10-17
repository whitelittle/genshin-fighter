__loaders['gf_character_lawachurl_training']=function()
local D=require('gf_lawachurl_training_data')
D.frames.hud=D.icons
local P=require('gf_character_assets').new(D)
P.groundedFrames=true
local function sample(name,t,loop)
 local g=D.groups[name] or D.groups.idle
 local total=0;for _,d in ipairs(g.durations)do total=total+d end
 if loop then t=t%total end
 for i,d in ipairs(g.durations)do if t<d then return g.frames[i] end;t=t-d end
 return g.frames[#g.frames]
end
function P.poseFor(view)
 local f=view.f;local st,t=f.state,f.t
 if st=='thrown' then return 'lawThrown_0' end
 if f.moveId=='throwStart' then return 'lawGrab_0' end
 if st=='throw' then return f.t<30 and 'lawGrab_1' or 'lawGrab_2' end
 if st=='airhit' and f.foe.state=='throw' then return 'lawThrown_1' end
 if st=='down' then return 'lawThrown_2' end
 if st=='getup' then return 'lawThrown_3' end
 if st=='hit' or st=='airhit' then return 'hurt' end
 if st=='down' or st=='getup' or st=='lose' then return 'down' end
 if st=='block' then return 'guard' end
 if st=='cblock' then return 'crouchGuard' end
 if st=='crouch' then return 'crouch' end
 if st=='attack' and f.move then
  local low=f.moveId=='crouchHeavy';local m=f.move
  if t<12 then return 'crouch' end
  if t<m.startup then return low and 'crouchGuard' or 'guard' end
  if t<m.startup+m.active+10 then return low and 'strikeLow' or 'strikeHigh' end
  if t<m.startup+m.active+m.recovery-16 then return 'crouch' end
 end
 return 'idle'
end
function P.nextAttackPose(view)
 local f=view.f
 if f.state=='attack' and f.move then
  local low=f.moveId=='crouchHeavy';local m=f.move;local t=f.t
  if t<12 then return low and 'crouchGuard' or 'guard' end
  if t<m.startup then return low and 'strikeLow' or 'strikeHigh' end
  if t<m.startup+m.active+10 then return 'crouch' end
  return 'idle'
 end
end
function P.nextLocomotion(view)
 local g=D.groups[view.f.state];if not g then return nil end
 local n=0;for _,d in ipairs(g.durations)do n=n+d end
 local t=view.walkT%n
 for i,d in ipairs(g.durations)do if t<d then return g.frames[i%#g.frames+1] end;t=t-d end
end
return P
end

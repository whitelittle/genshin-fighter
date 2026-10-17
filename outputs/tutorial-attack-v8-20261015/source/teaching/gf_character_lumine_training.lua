__loaders['gf_character_lumine_training']=function()
local D=require('gf_lumine_training_data')
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
 if st=='walk' or st=='back' then return sample(st,view.walkT,true) end
 if st=='dash' or st=='backdash' then return sample(st,t,false) end
 if st=='crouch' then return 'cblock_0' end
 if st=='jumpsq' then return 'jump_0' end
 if st=='land' then return 'jump_5' end
 if st=='air' then return f.vy>900 and 'jump_2' or f.vy>0 and 'jump_3' or 'jump_4' end
 if st=='block' then return 'block_1' end
 if st=='cblock' then return 'cblock_1' end
 if st=='attack' and f.move then
  local m=f.move;local g=D.groups[f.moveId]
  if g then
   if t<m.startup then return g.frames[1] end
   if t<m.startup+m.active then return g.frames[2] end
   return g.frames[t<m.startup+m.active+math.ceil(m.recovery/2) and 3 or 4]
  end
 end
 return sample('idle',t,true)
end
function P.nextLocomotion(view)
 local g=D.groups[view.f.state];if not g then return nil end
 local n=0;for _,d in ipairs(g.durations)do n=n+d end
 local t=view.walkT%n
 for i,d in ipairs(g.durations)do if t<d then return g.frames[i%#g.frames+1] end;t=t-d end
end
function P.nextAttackPose(view)
 local f=view.f;local m=f.move;local g=D.groups[f.moveId];if not m or not g then return nil end
 if f.t<m.startup then return g.frames[2] end
 if f.t<m.startup+m.active then return g.frames[3] end
 return g.frames[4]
end
return P
end

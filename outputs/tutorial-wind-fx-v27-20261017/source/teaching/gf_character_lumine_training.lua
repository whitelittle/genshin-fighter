__loaders['gf_character_lumine_training']=function()
local D=require('gf_lumine_training_data')
local G=require('gf_gfx')
D.frames.hud=D.icons
local P=require('gf_character_assets').new(D)
P.groundedFrames=true
P.locomotionPrefetchBudget=320
local function sample(name,t,loop)
 local g=D.groups[name] or D.groups.idle
 local total=0;for _,d in ipairs(g.durations)do total=total+d end
 if loop then t=t%total end
 for i,d in ipairs(g.durations)do if t<d then return g.frames[i] end;t=t-d end
 return g.frames[#g.frames]
end
function P.poseFor(view)
 local f=view.f;local st,t=f.state,f.t
 if (f.techT or 0)>0 then return 'throwTech_3' end
 if st=='hit' then return 'lumineHurt_0' end
 if st=='airhit' then return 'lumineHurt_1' end
 if st=='down' then return 'lumineHurt_2' end
 if st=='getup' then return 'lumineHurt_3' end
 if st=='thrown' then return 'throwTech_2' end
 if st=='throw' then return f.t<30 and 'throwTech_0' or 'throwTech_1' end
 if f.moveId=='throwStart' or f.moveId=='throwWhiff' then return 'throwTech_0' end
 if f.airMove then local g=D.groups[f.airMoveId];if g then local m=f.airMove;local at=f.airT or 0;return g.frames[at<m.startup and 1 or at<m.startup+(m.active or m.dur or 6) and 2 or at<m.startup+(m.active or m.dur or 6)+math.ceil(m.recovery/2) and 3 or 4]end end
 if st=='walk' or st=='back' then return sample(st,view.walkT,true) end
 if st=='dash' or st=='backdash' then return sample(st,t,false) end
 if st=='crouch' then return 'cblock_0' end
 if st=='jumpsq' then return t<2 and 'jump_0' or 'jump_1' end
 if st=='land' then return 'jump_5' end
 if st=='air' then return f.vy>900 and 'jump_2' or f.vy>0 and 'jump_3' or 'jump_4' end
 if st=='block' then return 'block_1' end
 if st=='cblock' then return 'cblock_1' end
 if (st=='attack' or st=='skill' or st=='burst') and f.move then
  local m=f.move;local g=D.groups[f.moveId]
  if g then
   if t<m.startup then return g.frames[1] end
   if t<m.startup+(m.active or m.dur or 6) then return g.frames[2] end
   return g.frames[t<m.startup+(m.active or m.dur or 6)+math.ceil(m.recovery/2) and 3 or 4]
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
P.dashPrefetchBudget=520
function P.nextDashPose(view)
 local g=D.groups[view.f.state];local t=view.f.t
 if not g then return D.groups.idle.frames[1] end
 for i,d in ipairs(g.durations)do if t<d then return g.frames[i+1] or D.groups.idle.frames[1] end;t=t-d end
 return D.groups.idle.frames[1]
end
function P.nextAttackPose(view)
 local f=view.f;local m=f.move;local g=D.groups[f.moveId];if not m or not g then return nil end
 if f.t<m.startup then return g.frames[2] end
 if f.t<m.startup+(m.active or m.dur or 6) then return g.frames[3] end
 return g.frames[4]
end

local windFx
local function fxImage(key)
 if not windFx then windFx=require('gf_character_assets').new(require('gf_wind_skill_fx_data'))end
 return windFx.image(key)
end
function P.clearWind(L)
 if L and L.windPair then for _,b in ipairs(L.windPair)do b.node:on(false)end end
end
function P.freeWind(L)
 if L and L.windPair then for _,b in ipairs(L.windPair)do b:free()end;L.windPair=nil;L.windFront=nil end
end
function P.drawWindImage(L,key,x,y,w,h,face)
 if not L.windPair then L.windPair={G.bitmap(L.node),G.bitmap(L.node)};for _,b in ipairs(L.windPair)do b.node:on(false)end end
 local img=fxImage(key);local front=L.windFront
 if not front or front.key~=key then
  local back=front==L.windPair[1] and L.windPair[2] or L.windPair[1]
  if back.key~=key or back.job then
   if not back.job or back.job.key~=key then back:start(img,key)end
   back:step(160)
  end
  if not back.job and back.key==key then
   if front then front.node:on(false)end;front=back;L.windFront=back
  end
 end
 if front then
  local shown=fxImage(front.key);front.node:pos(x,y):scale(face*w/shown.w,h/shown.h):on(true)
 end
end
function P.drawWind(L,x,y,w,h,t,face,blade)
 local key=(blade and 'blade_' or 'orb_')..((t//3)%4)
 P.drawWindImage(L,key,x,y,w,h,face)
end
function P.drawExtras(v)
 v.windL=v.windL or G.layer(v.layers.fx);local L=v.windL;L:begin()
 local f=v.f;local m=f.move;local charging=false
 if f.state=='skill' and m and m.windProjectile and f.t<m.startup then
  local down=m.branch=='skillDown';local k=f.t/m.startup;local r=30+70*k
  P.drawWind(L,f.x/100+f.face*(down and 60 or 105),f.y/100+(down and 60 or m.branch=='skillUp' and 160 or 180),r,down and 100 or r,f.t,f.face,down);charging=true
 end
 if not charging then P.clearWind(L)end
 L:finish()
 if v.windImpact then
  v.windImpactL=v.windImpactL or G.layer(v.layers.fx);local I=v.windImpactL;local e=v.windImpact
  local age=(v.app.scene.sim.tick-e.at)
  if age<12 then P.drawWindImage(I,'impact_'..math.min(3,age//3),e.x,e.y,180,180,e.face)
  else P.clearWind(I);v.windImpact=nil end
 end
end
function P.freeView(v)
 for _,L in ipairs({v.windL,v.windImpactL})do if L then P.freeWind(L);L:free()end end
 v.windL=nil;v.windImpactL=nil
end

return P
end

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

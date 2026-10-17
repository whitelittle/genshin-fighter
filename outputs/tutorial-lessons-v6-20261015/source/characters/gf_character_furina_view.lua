__loaders['gf_character_furina_view']=function()
local G=require('gf_gfx')
return function(P,D)
 local function clamp(t)return math.max(0,math.min(1,t)) end
 local keys={'usher','chevalmarin','crabaletta'}
 function P.newView(v,layers)
  v.characterLayers={G.layer(layers.fx)};v.characterChannels={}
  for i=1,4 do
   local capacity=0
   if i<=3 then for _,id in ipairs(D.helpers[keys[i]].frames) do capacity=math.max(capacity,D.frames[id].n) end
   else capacity=D.auxPeak end
   local ch={slots={G.bitmap(layers.fx),G.bitmap(layers.fx)},capacity=capacity}
   for _,b in ipairs(ch.slots) do b.pinned=true;b.node:on(false) end
   v.characterChannels[i]=ch
  end
 end
 function P.reserveExtras(v,budget)
  for _,ch in ipairs(v.characterChannels) do for _,b in ipairs(ch.slots) do
   if #b.kids<ch.capacity then b:ensure(math.min(ch.capacity,#b.kids+budget));return false end
  end end
  return true
 end
 local publish=require('gf_character_effect_channel')(P)
 function P.extras(v)
  local f=v.f;local id,t=f.moveId,f.t
  if f.airMove then id,t=f.airMoveId,f.airT or 0
  elseif f.state=='skill' then id='skill'
  elseif f.state=='burst' then id='burst'
  elseif f.state=='throw' then id='throw'
  elseif f.state~='attack' then id=nil end
  local g=id and D.groups[id];local result={}
  local x,y,face=f.x/100,f.y/100,f.face
  local function helper(i,frame,dx,dy)
   result[i]={id=D.helpers[keys[i]].frames[frame+1],x=x+dx*face,y=dy,face=face,alpha=1}
  end
  if g then
   local _,phase=P.sample(id,t);local index=({0,1,2,2,3,0})[phase] or 0
   if id=='skill' then
    for i=1,3 do helper(i,index,70+(i-1)*70+math.min(1,t/18)*35,({150,220,0})[i]) end
   elseif id=='burst' then
    local hits={56,78,100};local targets={{270,85},{240,155},{320,0}};local bases={{-50,60},{40,180},{100,0}}
    for i=1,3 do
     local h=hits[i];local u=t<h-14 and 0 or t<h and clamp((t-h+14)/14) or t<h+14 and 1 or clamp(1-(t-h-14)/14)
     helper(i,t<h and (u>0 and 1 or 0) or t<h+14 and 2 or 3,bases[i][1]+(targets[i][1]-bases[i][1])*u,bases[i][2]+(targets[i][2]-bases[i][2])*u)
    end
   elseif id=='throw' then
    if t<30 then helper(1,t<8 and 0 or 2,90,110) end
    if t>=20 and t<50 then helper(3,t<30 and 1 or 2,70+math.min(1,(t-20)/10)*90+math.max(0,t-30)*6,0) end
   elseif id=='airHeavy' then
    local active=t>=g.combat.startup and t<g.combat.startup+g.combat.active
    index=active and 2 or t<g.combat.startup and 1 or 3
    local mouth=D.helpers.chevalmarin.mouths[index+1]
    helper(2,index,120,y+140+mouth[2])
    if active then
     local e=g.effects;local i=math.min(#e.frames,1+math.floor((t-g.combat.startup)/g.combat.active*#e.frames))
     local mx=x+(120+mouth[1])*face;local my=y+140
     -- Aim in the mirrored local space; positive UI y points upwards.
     local angle=math.deg(math.atan((f.foe.y/100+220)-my,(f.foe.x/100-mx)*face))
     result[4]={id=e.frames[i],x=mx,y=my,face=face,alpha=1,rotation=angle*face}
    end
   end
   local e=g.effects
   if id~='throw' and id~='airHeavy' and id~='airLight' and e and t>=e.startTick and t<e.startTick+e.duration then
    local age=t-e.startTick;local i=math.min(#e.frames,1+math.floor(age/e.duration*#e.frames))
    local offset=e.nozzles and e.nozzles[phase] or e.worldOffset;local factor,alpha=1,math.min(1,(e.duration-age)/5)
    if id=='skill' then i=t<18 and 1 or t<24 and 2 or t<30 and 3 or 4 end
    if id=='burst' then
     if t<12 then i=1;offset={50+(t-6)*50,-200};factor=.4
     elseif t<56 then offset=nil
     elseif t<78 then i=4;offset={380,-170};factor=.45;alpha=1-(t-56)/22
     elseif t<100 then i=5+math.min(2,math.floor((t-78)/22*3));offset={275,-212}
     elseif t<122 then i=3;offset={380,-65};factor=.6;alpha=1-(t-100)/22
     else i=4;offset={400,-130};alpha=(142-t)/20 end
    end
    if offset then result[4]={id=e.frames[i],x=x+face*offset[1],y=y-offset[2],face=face,scale=factor,alpha=clamp(alpha),rotation=-(e.rotation or 0)*180/math.pi*face} end
   end
   if id=='airLight' and t>=g.combat.startup and t<g.combat.startup+g.combat.active and D.trails then
    result[4]={id=D.trails[tostring(phase)],x=x,y=y,face=face,alpha=.7*math.sin(math.pi*math.min(.98,(t-g.combat.startup)/g.combat.active+.06))}
   end
  end
  return result
 end
 function P.drawExtras(v)
  local result=P.extras(v);local total=0
  for _,r in pairs(result) do total=total+P.image(r.id).n end
  for i,ch in ipairs(v.characterChannels) do
   local r=result[i]
   if r then publish(ch,r.id,r.x,r.y,r.face,r.scale,r.alpha,r.rotation,math.max(1,math.floor(320*P.image(r.id).n/math.max(1,total))))
   else publish(ch) end
  end
  local L=v.characterLayers[1];L:begin()
  if (v.f.state=='block' or v.f.state=='cblock') and v.f.t<8 then
   local x=v.f.x/100+v.f.face*90;local y=v.f.y/100+(v.f.state=='cblock' and 160 or 215)
   L:rect(x,y,30,3,{200,244,255},1,45);L:rect(x,y,30,3,{200,244,255},1,-45)
  end
  L:finish()
 end
 function P.freeView(v)
  for _,ch in ipairs(v.characterChannels) do for _,b in ipairs(ch.slots) do b:free() end end
  for _,L in ipairs(v.characterLayers) do L:free() end
 end
end
end

__loaders['gf_character_ayaka_view']=function()
local G=require('gf_gfx')
return function(P,D)
 local publish=require('gf_character_effect_channel')(P)
 function P.newView(v,layers)
  local ch={slots={G.bitmap(layers.fx),G.bitmap(layers.fx)},capacity=D.auxPeak}
  for _,b in ipairs(ch.slots) do b.pinned=true;b.node:on(false) end
  v.characterChannels={ch}
 end
 function P.reserveExtras(v,budget)
  for _,b in ipairs(v.characterChannels[1].slots) do
   if #b.kids<D.auxPeak then b:ensure(math.min(D.auxPeak,#b.kids+budget));return false end
  end
  return true
 end
 function P.extras(v)
  local f=v.f;local id,t=f.moveId,f.t
  if f.airMove then id,t=f.airMoveId,f.airT or 0
  elseif f.state=='skill' then id='skill'
  elseif f.state=='burst' then id='burst'
  elseif f.state~='attack' then id=nil end
  local e=id and D.groups[id] and D.groups[id].effects
  if not e or t<e.startTick or t>=e.startTick+e.duration then return {} end
  local age=t-e.startTick;local i=math.min(3,1+math.floor(age/e.duration*3))
  local x,y,face=f.x/100,f.y/100,f.face;local scale,alpha=1,1
  local dx,dy=e.worldOffset[1],-e.worldOffset[2]
  if id=='burst' then
   i=1+math.floor(age/10)%3;dx,dy=230+math.min(145,age*3),205;scale=1.4
   alpha=math.min(1,age/8,math.max(0,(e.duration-age)/14));y=0
  elseif not e.followActor then x=(f.actionX or f.x)/100;y=0 end
  return {{id=e.frames[i],x=x+face*dx,y=y+dy,face=face,scale=scale,alpha=alpha}}
 end
 function P.drawExtras(v)
  local a=P.extras(v)[1];local ch=v.characterChannels[1]
  if a then publish(ch,a.id,a.x,a.y,a.face,a.scale,a.alpha,0,320) else publish(ch) end
 end
 function P.freeView(v)for _,b in ipairs(v.characterChannels[1].slots) do b:free() end end
end
end

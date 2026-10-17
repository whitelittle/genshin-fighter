__loaders['gf_character_arlecchino_view']=function()
local G=require('gf_gfx')
return function(P,D)
 local publish=require('gf_character_effect_channel')(P)
 local function peak(exclude)local n=0;for name,id in pairs(D.effectIds)do if name~=exclude then n=math.max(n,D.frames[id].n) end end;return n end
 function P.newView(v,layers)
  v.characterChannels={}
  for i,capacity in ipairs({D.auxPeak,peak('wings'),D.frames[D.effectIds.impact].n})do
   -- Wings occupy channel 1 during burst and belong behind both fighters.
   -- Normal attack arcs using that channel must return to the foreground.
   local ch={slots={G.bitmap(layers.fx),G.bitmap(layers.fx)},capacity=capacity}
   for _,b in ipairs(ch.slots)do b.pinned=true;b.node:on(false) end;v.characterChannels[i]=ch
  end
 end
 function P.reserveExtras(v,budget)
  for _,ch in ipairs(v.characterChannels)do for _,b in ipairs(ch.slots)do
   if #b.kids<ch.capacity then b:ensure(math.min(ch.capacity,#b.kids+budget));return false end
  end end;return true
 end
 function P.extras(v)
  local f=v.f;local id,t=f.moveId,f.t
  if f.airMove then id,t=f.airMoveId,f.airT or 0 elseif f.state=='skill' then id='skill' elseif f.state=='burst' then id='burst' elseif f.state~='attack' then id=nil end
  local g=id and D.groups[id];local out={}
  if not g or (id=='burst' and not f.cinematicConfirmed) then return out end
  local x,y,face=f.x/100,f.y/100,f.face
  local function add(channel,name,dx,dy,alpha,scale)
   local image=D.effectIds[name];if image then out[channel]={id=image,x=x+face*dx,y=y+dy,face=face,alpha=math.max(0,math.min(1,alpha or 1)),scale=scale or 1} end
  end
  if id=='burst' and t>=42 and t<142 then add(1,'wings',0,220,t<52 and (t-42)/10 or t>=132 and (142-t)/10 or .55) end
  if id=='skill' and t>=4 and t<10 then add(2,'guide',90,240,math.sin((t-4)/6*math.pi)) end
  if id=='skill' and f.connected and t>=18 and t<40 then out[3]={id=D.effectIds.mark,x=f.foe.x/100,y=f.foe.y/100+290,face=face,alpha=.9,scale=1} end
  if id=='burst' and t>=42 and t<52 then add(2,'guide',30,240,(t-42)/10) end
  if id=='burst' and t>=52 and t<62 then add(2,'release',170,220,1-(t-52)/10) end
  for _,e in ipairs(g.events)do local age=t-e.tick
   if age>=0 and age<8 and e.kind~='grab' and e.kind~='release' then
    local ch=id=='burst' and 2 or 1
    add(ch,(id=='airHeavy' or id=='heavy') and 'down' or id=='light3' and 'up' or 'horizontal',205,185,1-age/8)
    if age>=3 and e.kind~='confirm' then out[3]={id=D.effectIds.impact,x=f.foe.x/100,y=f.foe.y/100+190,face=face,alpha=(8-age)/5,scale=1} end
   end
  end
  return out
 end
 function P.drawExtras(v)
  local out=P.extras(v);local total=0;for _,e in pairs(out)do total=total+P.image(e.id).n end
  for i,ch in ipairs(v.characterChannels)do local e=out[i]
   local parent=e and e.id==D.effectIds.wings and v.layers.ghost or v.layers.fx
   for _,b in ipairs(ch.slots) do if b.node.parent~=parent then b.node:parentTo(parent) end end
   if e then publish(ch,e.id,e.x,e.y,e.face,e.scale,e.alpha,0,math.max(1,math.floor(320*P.image(e.id).n/math.max(1,total)))) else publish(ch) end
  end
 end
 function P.freeView(v)for _,ch in ipairs(v.characterChannels)do for _,b in ipairs(ch.slots)do b:free() end end end
end
end

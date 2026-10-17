__loaders['gf_character_clorinde_view']=function()
local G=require('gf_gfx')
local Rules=require('gf_clorinde_rules_data')
return function(P,D)
 local publish=require('gf_character_effect_channel')(P)
 local function peak(exclude)local n=0;for name,id in pairs(D.effectIds)do if name~=exclude then n=math.max(n,D.frames[id].n) end end;return n end
 function P.newView(v,layers)
  v.characterChannels={}
  for i,capacity in ipairs({D.auxPeak,peak('wings'),D.frames[D.effectIds.impact].n})do
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
  if f.airMove then id,t=f.airMoveId,(f.airT or 0)-(f.airMoveId=='airLight' and 1 or 0) elseif f.state=='skill' then id='skill' elseif f.state=='burst' then id='burst' elseif f.state~='attack' then id=nil end
  local g=id and D.groups[id];local out={}
  local impact=v.confirmedImpact
  if impact and v.app.t<impact.untilTime then
   out[3]={id=D.effectIds.impact,x=impact.x,y=impact.y,face=impact.face,alpha=math.min(1,(impact.untilTime-v.app.t)/.12),scale=1}
  end
  if not g or (id=='burst' and not f.cinematicConfirmed) then return out end
  local x,y,face=f.x/100,f.y/100,f.face
  local function add(channel,name,dx,dy,alpha,scale)
   local image=D.effectIds[name];if image then out[channel]={id=image,x=x+face*dx,y=y+dy,face=face,alpha=math.max(0,math.min(1,alpha or 1)),scale=scale or 1} end
  end
  for _,e in ipairs(g.events)do local age=t-e.tick
   if age>=0 and age<8 then
    local shot=e.kind=='shot' or e.kind=='confirm-shot'
    add(1,shot and 'gun' or (id=='airHeavy' and 'down' or id=='heavy' and 'diagonal' or 'sword'),170,180,1-age/8)
    local spent=id=='skill' and ((f.skillHitMask or 0)&2~=0) or (id~='skill' and id~='burst' and f.connected)
    if shot and not spent then add(2,'bullet',Rules.shot.origin+age*Rules.shot.speed,180,1-age/Rules.shot.duration) end
   end
  end
  return out
 end
 function P.drawExtras(v)
  local out=P.extras(v);local total=0;for _,e in pairs(out)do total=total+P.image(e.id).n end
  for i,ch in ipairs(v.characterChannels)do local e=out[i]
   if e then publish(ch,e.id,e.x,e.y,e.face,e.scale,e.alpha,0,math.max(1,math.floor(320*P.image(e.id).n/math.max(1,total)))) else publish(ch) end
  end
 end
 function P.freeView(v)for _,ch in ipairs(v.characterChannels)do for _,b in ipairs(ch.slots)do b:free() end end end
end
end

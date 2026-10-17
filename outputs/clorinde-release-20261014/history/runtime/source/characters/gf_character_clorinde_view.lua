__loaders['gf_character_clorinde_view']=function()
local G=require('gf_gfx')
local Rules=require('gf_clorinde_rules_data')
return function(P,D)
 local publish=require('gf_character_effect_channel')(P)
 -- Compact tracer and muzzle flash are code-native rectangles, not a flying sword.
 -- Original raster effects stay in the immutable bank for historical reference.
 local image=P.image
 local function procedural(w,h,ax,ay,bytes,pal)
  return {w=w,h=h,ax=ax,ay=ay,n=#bytes/5,bytes=bytes,pal=pal,u=1,baked=true,seam=0}
 end
 local tracer=procedural(30,6,0,3,{0,2,20,2,0,14,2,10,2,1,24,1,6,4,2,25,2,4,2,3},
  {{136,78,245,130},{190,133,255,170},{255,200,45,255},{255,241,161,255}})
 local muzzle=procedural(24,24,12,12,{0,10,24,4,0,10,0,4,24,0,6,6,12,12,1,9,9,6,6,2},
  {{136,78,245,110},{210,184,255,190},{255,249,255,255}})
 function P.image(id)
  if id==D.effectIds.bullet then return tracer end
  if id==D.effectIds.gun then return muzzle end
  if id==D.effectIds.sword then return image(D.effectIds.bullet) end
  return image(id)
 end

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
  if f.airMove then id,t=f.airMoveId,(f.airT or 0)-1 elseif f.state=='skill' then id='skill' elseif f.state=='burst' then id='burst' elseif f.state~='attack' then id=nil end
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
    if shot then
     local cfg=Rules.shot[id] or Rules.shot.burst
     local spent=id=='skill' and ((f.skillHitMask or 0)&2~=0) or (id~='skill' and id~='burst' and f.connected)
     if age<3 then add(1,'gun',cfg.x,cfg.y,1-age/3) end
     if not spent then add(2,'bullet',cfg.x+age*Rules.shot.speed,cfg.y,math.min(1,(8-age)/2)) end
    else
     local blade=Rules.bladeAt(id,t)
     if blade then
      -- Match the body buffer actually being displayed; never float a sword over
      -- an older idle/startup pose while the next body buffer is still loading.
      if v.front and v.front.key~=blade.pose then blade=nil end
      if blade then
       local hx,hy,tx,ty=blade.hx/100,blade.hy/100,blade.tx/100,blade.ty/100
       local dx,dy=tx-hx,ty-hy;local angle=math.atan(dy,dx);local cs,sn=math.cos(angle),math.sin(angle)
       local scale=math.sqrt(dx*dx+dy*dy)/193.5
       out[1]={id=D.effectIds.sword,x=x+face*(tx-(202.5*cs+2.25*sn)*scale),
        y=y+ty-(202.5*sn-2.25*cs)*scale,face=face,scale=scale,alpha=.7,
        rotation=face*math.deg(angle),swordTipX=x+face*tx,swordTipY=y+ty}
      end
     end
    end
   end
  end
  return out
 end
 function P.drawExtras(v)
  local out=P.extras(v);local total=0;for _,e in pairs(out)do total=total+P.image(e.id).n end
  for i,ch in ipairs(v.characterChannels)do local e=out[i]
   if e then publish(ch,e.id,e.x,e.y,e.face,e.scale,e.alpha,e.rotation or 0,math.max(1,math.floor(320*P.image(e.id).n/math.max(1,total)))) else publish(ch) end
  end
 end
 function P.freeView(v)for _,ch in ipairs(v.characterChannels)do for _,b in ipairs(ch.slots)do b:free() end end end
end
end

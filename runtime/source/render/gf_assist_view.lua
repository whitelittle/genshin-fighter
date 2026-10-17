__loaders['gf_assist_view']=function()
local G=require('gf_gfx')
local Art=require('gf_art')
local UI=require('gf_ui')
local Rules=require('gf_assist_rules')
local M={}
local function poses(char)
 return Art.pose(char.key,'lo','idle'),Art.pose(char.key,'lo','slash')
end
function M.prepare(scene,budget)
 if not scene.sim.opts.assistChars then return true end
 if not scene.assistViews then
  scene.assistViews={}
  for side=1,2 do
   local v={root=G.group(scene.lay.body),slots={}}
   v.slots={G.bitmap(v.root),G.bitmap(v.root)}
   v.root:on(false)
   for _,bmp in ipairs(v.slots)do bmp.pinned=true;bmp.budgeted=true;bmp.node:on(false) end
   scene.assistViews[side]=v
  end
  scene.assistLayer=G.layer(scene.lay.fx)
 end
 local done=true
 for side,v in ipairs(scene.assistViews) do
  if not v.capacity then
   local n=0
   local candidates={}
   local char=scene.sim:assistPartner(side);if char then candidates[1]=char end
   for _,char in ipairs(candidates)do local idle,attack=poses(char);n=math.max(n,idle.n,attack.n) end
   v.capacity=n
  end
  local char=scene.sim:assistPartner(side)
  for i,bmp in ipairs(v.slots)do
   if #bmp.kids<v.capacity then bmp:ensure(math.min(v.capacity,#bmp.kids+budget));done=false
   elseif char then
    local idle,attack=poses(char);local img=i==1 and idle or attack;local key=char.key..':'..i
    if bmp.key~=key then
     if not bmp.job then bmp:start(img,key) end
     if not bmp:step(budget) then done=false end
     bmp.node:on(false)
    end
   end
  end
 end
 return done
end
function M.draw(scene)
 local L=scene.assistLayer;if not L then return end
 L:begin()
 for side,v in ipairs(scene.assistViews)do
  local a=scene.sim.assists[side]
  if not a then v.root:on(false)
  else
   local profile=Rules.profiles[a.key];local char=Art.byKey[a.key]
   local idle,attack=poses(char)
   local striking=a.t>=profile.startup and a.t<profile.startup+profile.active+8
   local index=striking and 2 or 1;local bmp=v.slots[index];local img=striking and attack or idle
   local key=a.key..':'..index
   if bmp.key~=key then
    bmp.node:on(false)
    if not bmp.job or bmp.job.key~=key then bmp:start(img,key) end
    bmp:step(240)
   end
   -- Prepare the strike before its logical active phase, using the same bounded
   -- buffers. Existing complete bodies remain visible; never expose half a body.
   local next=v.slots[2]
   if not striking and a.t<profile.startup and next.key~=a.key..':2' then
    if not next.job or next.job.key~=a.key..':2' then next:start(attack,a.key..':2') end
    next:step(240)
   end
   local shift=a.t<8 and -160*(1-a.t/8) or a.t>profile.life-10 and -180*(a.t-profile.life+10)/10 or 0
   v.root:pos(a.x/100+a.face*shift,0):scale(a.face,1):on(true)
   for i,slot in ipairs(v.slots)do slot.node:on(i==index and not slot.job and slot.key==key) end
   bmp.node:scale(img.u,img.u)
   L:label('协同 · '..char.name,a.x/100,350,260,32,21,UI.GOLD,'c',{0,0,0,170})
   local box=profile.box;local live=a.t>=profile.startup and a.t<profile.startup+profile.active
   if live then
    local x=(profile.spot and a.targetX or a.x)/100+a.face*(box.x+box.w/2)
    local y=box.y+box.h/2;local color=require('gf_kits').elementColor[char.element]
    if profile.spot then
     L:rect(x,y,18,box.h,color,.8);L:rect(x,y,6,box.h,UI.WHITE,.9)
    else
     L:shape(char.weapon=='catalyst' and G.STAR4 or G.ELLIPSE,x,y,box.w,box.h,color,.55)
     L:rect(x,y,box.w,.06*box.h+3,UI.WHITE,.8)
    end
   elseif profile.spot and a.t<profile.startup then
    L:shape(G.RING,a.targetX/100,6,box.w,32,UI.GOLD,.6)
   end
  end
 end
 L:finish()
end
function M.free(scene)
 if scene.assistViews then for _,v in ipairs(scene.assistViews)do
  v.root:on(false);for _,b in ipairs(v.slots)do b:free() end;G.release(v.root)
 end end
 if scene.assistLayer then scene.assistLayer:free() end
end
return M
end

__loaders['gf_character_effect_channel']=function()
local G=require('gf_gfx')
return function(P)
local function publish(ch,id,x,y,face,scale,alpha,rotation,budget)
  for _,b in ipairs(ch.slots) do b.budgeted=true end
  if not id then for _,b in ipairs(ch.slots) do b.node:on(false) end;return end
  local img=P.image(id);local front=ch.front;local back=ch.slots[1]==front and ch.slots[2] or ch.slots[1]
  -- Mobile fades use four stable opacity levels instead of recolouring hundreds
  -- of effect rectangles on every simulation tick. Geometry/timing stays intact.
  if G.mobileLightEffects or G.bitmapBudget then alpha=math.ceil(math.max(0,math.min(1,alpha or 1))*4)/4 end
  if not front or front.key~=id then
   if not back.job then back:start(img,id) end
   back:step(budget)
   if not back.job then
    if front then front.node:on(false) end
    ch.front=back;front=back
   end
  end
  if front then
   front.node:pos(x,y):scale(face*(scale or 1),scale or 1):rot(rotation or 0):on(true)
   front:opacity(P.image(front.key),alpha or 1)
  end
 end
return publish
end
end

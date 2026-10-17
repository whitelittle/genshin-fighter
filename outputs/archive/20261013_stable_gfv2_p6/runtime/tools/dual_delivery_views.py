"""Author independent visual adapters and append imported modules to the build."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
for key in ['clorinde','arlecchino']:
 code=f"""__loaders['gf_character_{key}_view']=function()
local G=require('gf_gfx')
return function(P,D)
 local publish=require('gf_character_effect_channel')(P)
 local function peak(exclude)local n=0;for name,id in pairs(D.effectIds)do if name~=exclude then n=math.max(n,D.frames[id].n) end end;return n end
 function P.newView(v,layers)
  v.characterChannels={{}}
  for i,capacity in ipairs({{D.auxPeak,peak('wings'),D.frames[D.effectIds.impact].n}})do
   local ch={{slots={{G.bitmap(layers.fx),G.bitmap(layers.fx)}},capacity=capacity}}
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
  local g=id and D.groups[id];local out={{}}
  if not g or (id=='burst' and not f.cinematicConfirmed) then return out end
  local x,y,face=f.x/100,f.y/100,f.face
  local function add(channel,name,dx,dy,alpha,scale)
   local image=D.effectIds[name];if image then out[channel]={{id=image,x=x+face*dx,y=y+dy,face=face,alpha=math.max(0,math.min(1,alpha or 1)),scale=scale or 1}} end
  end
"""
 if key=='clorinde':
  code+="""  for _,e in ipairs(g.events)do local age=t-e.tick
   if age>=0 and age<8 then
    local shot=e.kind=='shot' or e.kind=='confirm-shot'
    add(1,shot and 'gun' or (id=='airHeavy' and 'down' or id=='heavy' and 'diagonal' or 'sword'),170,180,1-age/8)
    if shot then add(2,'bullet',170+age*45,180,1-age/8) end
    if age>=3 then local image=D.effectIds.impact;out[3]={id=image,x=f.foe.x/100,y=f.foe.y/100+190,face=face,alpha=(8-age)/5,scale=1} end
   end
  end
"""
 else:
  code+="""  if id=='burst' and t>=42 and t<142 then add(1,'wings',0,220,t<52 and (t-42)/10 or t>=132 and (142-t)/10 or .55) end
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
"""
 code+="""  return out
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
"""
 (R/f'source/characters/gf_character_{key}_view.lua').write_text(code,encoding='utf-8')
 # Latest delivery portraits are already imported for selection. Keep the standard
 # Art picture interface, avoiding the old unrelated character portrait.
 legacy=(R.parent/f'game/lua/gen/gf_art_{key}.lua').read_text(encoding='utf-8')
 pictures=re.findall(r'^(?:face|round|portrait)=\{[^\n]+\},$',legacy,re.M);assert len(pictures)==3
 (R/f'source/assets/gf_art_{key}.lua').write_text(f"__loaders['gf_art_{key}']=function() return {{\n"+'\n'.join(pictures)+'\n} end\n',encoding='utf-8')
 p=R/f'source/characters/gf_character_{key}.lua';s=p.read_text(encoding='utf-8')
 s=s.replace("if st=='burst' then return sample('burst',t) end", "if st=='burst' then if not f.cinematicConfirmed then return t<6 and D.groups.burst.frames[1] or t<12 and D.groups.burst.frames[2] or D.groups.idle.frames[1] end;return sample('burst',t) end")
 p.write_text(s,encoding='utf-8')
order=json.loads((R/'source/order.json').read_text(encoding='utf-8'))
for key in ['clorinde','arlecchino']:
 for path in [f'source/assets/gf_{key}_data.lua',f'source/assets/gf_art_{key}.lua',f'source/characters/gf_{key}_rules_data.lua',f'source/characters/gf_character_{key}.lua',f'source/characters/gf_character_{key}_rules.lua',f'source/characters/gf_character_{key}_view.lua',f'source/battle/gf_sim_{key}.lua']:
  if path not in order:order.insert(-1,path)
(R/'source/order.json').write_text(json.dumps(order,indent=2),encoding='utf-8')

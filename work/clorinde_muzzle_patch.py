from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-muzzle-20261014';O.mkdir(exist_ok=True)
def edit(rel,fn):
 p=R/rel;h=O/'history'/rel;h.parent.mkdir(parents=True,exist_ok=True)
 assert not h.exists(),'patch once; inspect saved history before retry'
 shutil.copy2(p,h);p.write_text(fn(p.read_text(encoding='utf8')),encoding='utf8')
old='["shot"]={duration=8,origin=170,speed=45,near=9,far=203}'
new='["shot"]={duration=8,speed=75,near=0,far=30,radius=30,light2={x=168,y=272},heavy={x=101,y=261},airLight={x=200,y=279},skill={x=155,y=297},burst={x=155,y=297}}'
edit('runtime/source/characters/gf_clorinde_rules_data.lua',lambda s:s.replace(old,new))
def sim(s):
 s=s.replace('box={x=D.shot.origin+age*D.shot.speed+D.shot.near,y=0,w=D.shot.far-D.shot.near,h=230}',"local cfg=D.shot.skill;local near=age>0 and D.shot.far-D.shot.speed or D.shot.near\n    box={x=cfg.x+age*D.shot.speed+near,y=cfg.y-D.shot.radius,w=D.shot.far-near,h=2*D.shot.radius}")
 s=s.replace("},'skill')\n    if result", "},'skill',window==1 and {x=p.face==1 and a or b,y=math.max(c,math.min(d,p.y+D.shot.skill.y*C))} or nil)\n    if result",1)
 s=s.replace("local box={x=D.shot.origin+age*D.shot.speed+D.shot.near,\n    y=m.box.y,w=D.shot.far-D.shot.near,h=m.box.h}","local cfg=D.shot[p.airMoveId or p.moveId]\n  local near=age>0 and D.shot.far-D.shot.speed or D.shot.near\n  local box={x=cfg.x+age*D.shot.speed+near,\n    y=cfg.y-D.shot.radius,w=D.shot.far-near,h=2*D.shot.radius}")
 s=s.replace("self:hit(p,p.foe,m,kind) end", "self:hit(p,p.foe,m,kind,{x=p.face==1 and a or b,y=math.max(c,math.min(d,p.y+cfg.y*C))}) end",1)
 return s
edit('runtime/source/battle/gf_sim_clorinde.lua',sim)
def view(s):
 marker=" local publish=require('gf_character_effect_channel')(P)"
 insert='''
 -- Compact tracer and muzzle flash are code-native rectangles, not a flying sword.
 -- Original raster effects stay in the immutable bank for historical reference.
 local image=P.image
 local function procedural(w,h,ax,ay,bytes,pal)
  return {w=w,h=h,ax=ax,ay=ay,n=#bytes/5,bytes=bytes,pal=pal,u=1,baked=true,seam=0}
 end
 local tracer=procedural(30,8,0,4,{0,3,20,2,0,14,2,12,4,1,24,0,6,8,1,25,2,5,4,2},
  {{136,78,245,130},{196,161,255,220},{247,239,255,255}})
 local muzzle=procedural(24,24,12,12,{0,10,24,4,0,10,0,4,24,0,6,6,12,12,1,9,9,6,6,2},
  {{136,78,245,110},{210,184,255,190},{255,249,255,255}})
 function P.image(id)
  if id==D.effectIds.bullet then return tracer end
  if id==D.effectIds.gun then return muzzle end
  return image(id)
 end
'''
 s=s.replace(marker,marker+insert)
 a=s.index('    add(1,shot and');b=s.index('\n   end',a)
 s=s[:a]+'''    if shot then
     local cfg=Rules.shot[id] or Rules.shot.burst
     local spent=id=='skill' and ((f.skillHitMask or 0)&2~=0) or (id~='skill' and id~='burst' and f.connected)
     if age<3 then add(1,'gun',cfg.x,cfg.y,1-age/3) end
     if not spent then add(2,'bullet',cfg.x+age*Rules.shot.speed,cfg.y,math.min(1,(8-age)/2)) end
    else
     add(1,id=='airHeavy' and 'down' or id=='heavy' and 'diagonal' or 'sword',170,180,1-age/8)
    end'''+s[b:]
 return s
edit('runtime/source/characters/gf_character_clorinde_view.lua',view)
edit('runtime/source/characters/gf_character_clorinde.lua',lambda s:s.replace("moveTime(id,f.airT or 0,f.airMove)","moveTime(id,(f.airT or 0)-(id=='airLight' and 1 or 0),f.airMove)"))
edit('runtime/source/battle/gf_sim_combat.lua',lambda s:s.replace("x = d.x, y = d.y + floor(170 * C * d.size), heavy = (m.damage", "x = opts.x or d.x, y = opts.y or (d.y + floor(170 * C * d.size)), heavy = (m.damage"))
print('shot origins measured per pose; short tracer + swept ray; protocol 8')

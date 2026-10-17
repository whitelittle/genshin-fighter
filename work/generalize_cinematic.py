from pathlib import Path
import json
s=Path('runtime/source')
p=s/'characters/gf_furina_cinematic_view.lua';t=p.read_text(encoding='utf-8').replace('gf_furina_cinematic_view','gf_character_cinematic_view')
t=t.replace('local M={}',"local M={}\nlocal profiles={furina={finish=158,hits={56,78,100},name='芙宁娜',burst='万众狂欢',confirmed=true,stage=true},kamisatoayaka={finish=152,hits={70,94,118},name='神里绫华',burst='神里流·霜灭'}}")
t=t.replace("f.key=='furina' and f.state=='burst'","profiles[f.key] and f.state=='burst'")
a=t.index('function M.reserve(');b=t.index('function M.backdrop(',a)
t=t[:a]+'''function M.reserve(scene,budget)
 scene.characterCuts=scene.characterCuts or {}
 for _,f in ipairs(scene.sim.f) do if profiles[f.key] then
  local b=scene.characterCuts[f.key]
  if not b then b=G.bitmap(scene.app.layers.top);b.pinned=true;b.node:on(false);scene.characterCuts[f.key]=b end
  local P=Registry.provider(f.key);local img=P.image(P.data.portrait)
  if #b.kids<img.n then b:ensure(math.min(img.n,#b.kids+budget));return false end
  if b.key~=f.key..'Portrait' then
   if not b.job then b:start(img,f.key..'Portrait') end
   if not b:step(budget) then return false end
   b.node:on(false);return false
  end
 end end
 return true
end
function M.hide(scene)
 for _,b in pairs(scene.characterCuts or {}) do b.node:on(false) end
 scene.characterCutActive=nil
end
function M.free(scene)
 for _,b in pairs(scene.characterCuts or {}) do b:free() end
 scene.characterCuts=nil
end
'''+t[b:]
t=t.replace('local t=f.t;local W,H','local profile=profiles[f.key];local t=f.t;local W,H',1).replace('(158-t)/20','(profile.finish-t)/20').replace('if t>=42 then','if profile.stage and t>=42 then').replace('ipairs({56,78,100})','ipairs(profile.hits)')
a=t.index('function M.cut(scene)');b=t.index(' scene.furinaCutActive=true',a)
t=t[:a]+'''function M.cut(scene)
 local f=actor(scene);local L=scene.cut.L
 if not f or (profiles[f.key].confirmed and not f.cinematicConfirmed) or f.t<12 or f.t>=42 then
  if scene.characterCutActive then M.hide(scene);L:clear() end
  return false
 end
 local b=scene.characterCuts[f.key]
 if scene.characterCutActive~=f.key then M.hide(scene) end
'''+t[b:]
t=t.replace('scene.furinaCutActive=true','scene.characterCutActive=f.key').replace("Registry.provider('furina')","Registry.provider(f.key)").replace("if b.key~='furinaPortrait' then b:draw(img,'furinaPortrait') end", "assert(b.key==f.key..'Portrait','portrait must be warmed before battle')")
t=t.replace("L:label('万众狂欢'","L:label(profiles[f.key].burst").replace("L:label('芙宁娜'","L:label(profiles[f.key].name")
new=s/'characters/gf_character_cinematic_view.lua';new.write_text(t,encoding='utf-8');p.unlink()
for p in (s/'battle').glob('*.lua'):
 t=p.read_text(encoding='utf-8').replace('gf_furina_cinematic_view','gf_character_cinematic_view').replace("ty == 'furinaCinematic'", "(ty == 'furinaCinematic' or ty == 'ayakaCinematic')")
 if p.name=='gf_scene_fight.lua':
  t=t.replace('function S:exit()','function S:exit()\n    require(\'gf_character_cinematic_view\').hide(self)')
  t=t.replace('if self.cut then self.cut.L:free(); self.cut.bmp:free() end',"require('gf_character_cinematic_view').free(self)\n    if self.cut then self.cut.L:free(); self.cut.bmp:free() end")
 p.write_text(t,encoding='utf-8')
p=s/'order.json';p.write_text(p.read_text(encoding='utf-8').replace('gf_furina_cinematic_view','gf_character_cinematic_view'),encoding='utf-8')

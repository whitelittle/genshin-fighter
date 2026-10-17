__loaders['gf_character_cinematic_view']=function()
local G=require('gf_gfx')
local Registry=require('gf_character_registry')
local M={}
local profiles={furina={finish=158,hits={56,78,100},name='芙宁娜',burst='万众狂欢',confirmed=true,stage=true},kamisatoayaka={finish=152,hits={70,94,118},name='神里绫华',burst='神里流·霜灭'}}
local portraits={}
profiles.clorinde={finish=162,hits={70,94,118},name='克洛琳德',burst='残光将终',confirmed=true}
profiles.arlecchino={finish=162,hits={70,94,118},name='阿蕾奇诺',burst='厄月将升',confirmed=true}
local function portrait(key)
 if portraits[key] then return portraits[key] end
 local P=Registry.provider(key);local source=P.image(P.data.portrait)
 -- Clip rectangle geometry at the banner's lower edge. Keep the approved head
 -- size and source pixels; no native mask, resampling or source-data mutation.
 local bytes={};local height=math.min(source.h,228)
 for i=1,source.n do
  local o=(i-1)*5;local x,y,w,h,ci=table.unpack(source.bytes,o+1,o+5)
  local bottom=math.min(y+h,height)
  if bottom>y then
   bytes[#bytes+1]=x;bytes[#bytes+1]=y;bytes[#bytes+1]=w;bytes[#bytes+1]=bottom-y;bytes[#bytes+1]=ci
  end
 end
 local img={n=#bytes/5,bytes=bytes,pal=source.pal,ax=source.ax,ay=source.ay,w=source.w,h=height,u=1,seam=source.seam}
 portraits[key]=img;return img
end
local function actor(scene)
 for _,f in ipairs(scene.sim.f) do if profiles[f.key] and f.state=='burst' then return f end end
end
function M.reserve(scene,budget)
 scene.characterCuts=scene.characterCuts or {}
 if scene.sim.teams then
  for key,b in pairs(scene.characterCuts)do
   if scene.sim.f[1].key~=key and scene.sim.f[2].key~=key then
    b.node:on(false);local previous=G.deferRelease;G.deferRelease=true;b:free();G.deferRelease=previous;scene.characterCuts[key]=nil
   end
  end
 end
 for _,f in ipairs(scene.sim.f) do if profiles[f.key] then
  local b=scene.characterCuts[f.key]
  if not b then b=G.bitmap(scene.app.layers.top);b.pinned=true;b.node:on(false);scene.characterCuts[f.key]=b end
  local img=portrait(f.key)
  if #b.kids<img.n then b:ensure(math.min(img.n,#b.kids+budget));return false end
  if b.key~=f.key..'Portrait' then
   if not b.job then b:start(portrait(f.key),f.key..'Portrait') end
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
 for _,b in pairs(scene.legacyCuts or {})do b:free() end;scene.legacyCuts=nil
end
function M.reserveLegacy(scene,budget)
 local Art=require('gf_art');scene.legacyCuts=scene.legacyCuts or {}
 local active={};for _,f in ipairs(scene.sim.f)do active[f.key]=true end
 if scene.sim.teams then for key,b in pairs(scene.legacyCuts)do if not active[key] then
  if scene.cut.bmp==b then scene.cut.bmp=scene.cut.placeholder end
  b.node:on(false);local previous=G.deferRelease;G.deferRelease=true;b:free();G.deferRelease=previous;scene.legacyCuts[key]=nil
 end end end
 for _,f in ipairs(scene.sim.f)do if f.key=='raidenshogun' or f.key=='nahida' then
  local b=scene.legacyCuts[f.key]
  if not b then b=G.bitmap(scene.app.layers.top);b.pinned=true;b.node:on(false);scene.legacyCuts[f.key]=b end
  if b.key~=f.key..':legacyPortrait' then
   local src=Art.portrait(f.key)
   if not b.job then b:start(src,f.key..':legacyPortrait') end
   if not b:step(budget) then return false end
   b.node:scale(5.2,5.2):on(false);return false
  end
 end end;return true
end
function M.backdrop(scene,L)
 local f=actor(scene);if not f then return false end
 local profile=profiles[f.key];local t=f.t;local W,H=scene.app.W,scene.app.H;local s=math.min(W/1200,H/650)
 if profile.confirmed and not f.cinematicConfirmed then return false end
 local fade=math.min(1,t/10,math.max(0,(profile.finish-t)/20))
 -- Native UI has no radial-gradient primitive. Bounded nested ellipses implement the same palette and centre.
 scene.app:cover(L,{11,24,44},fade)
 for i=12,1,-1 do local u=i/12
  L:shape(G.ELLIPSE,150*s,5*s,1360*u*s,1360*u*s,{66,107,140},.10*fade,0,.25)
 end
 if profile.stage and t>=42 then
  L:shape(G.RING,50*s,-225*s,880*s,52*s,{158,220,234},fade)
  for j=0,2 do L:shape(G.TRI,(-220+j*260)*s,35*s,240*s,520*s,{195,244,255},.12*fade) end
 end
 for i=0,23 do L:rect(((i*173+t*2)%1200-600)*s,(325-(i*89+t*.4)%550)*s,3*s,3*s,i%2==1 and {201,234,255} or {138,203,233},.4*fade) end
 for _,hit in ipairs(profile.hits) do if t>=hit and t<hit+4 then scene.app:cover(L,{234,250,255},.35*fade) end end
 return true
end
function M.cut(scene)
 local f=actor(scene);local L=scene.cut.L
 if not f or (profiles[f.key].confirmed and not f.cinematicConfirmed) or f.t<12 or f.t>=42 then
  if scene.characterCutActive then M.hide(scene);L:clear() end
  return false
 end
 local b=scene.characterCuts[f.key]
 if scene.sim.teams and (not b or b.key~=f.key..'Portrait') then return false end
 if scene.characterCutActive~=f.key then M.hide(scene) end
 scene.characterCutActive=f.key;L:begin()
 local t=f.t;local W,H=scene.app.W,scene.app.H;local s=math.min(W/1200,H/650)
 local fade=math.min(1,(t-12)/5,(42-t)/7)
 L:rect(0,85*s,scene.app.coverW,240*s,{11,35,64},.92*fade)
 L:rect(0,204*s,scene.app.coverW,2*s,{154,223,246},fade);L:rect(0,-34*s,scene.app.coverW,2*s,{154,223,246},fade)
 local img=portrait(f.key)
 assert(b.key==f.key..'Portrait','portrait must be warmed before battle')
 b.node:pos((-500+math.min(40,(t-12)*3))*s,200*s):scale(s,s):rot(0):on(fade>0)
 b:opacity(img,scene.app:isMobile() and 1 or fade)
 L:label(profiles[f.key].burst,165*s,85*s,420*s,70*s,46*s,{225,246,255},'l',nil,fade)
 L:label(profiles[f.key].name,115*s,40*s,220*s,40*s,22*s,{225,246,255},'l',nil,fade)
 L:finish();return true
end
return M
end

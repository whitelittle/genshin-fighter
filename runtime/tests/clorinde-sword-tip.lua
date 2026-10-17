local S,R=GF_REQUIRE('gf_sim'),GF_REQUIRE('gf_roster')
local Rules=GF_REQUIRE('gf_clorinde_rules_data')
local D=GF_REQUIRE('gf_clorinde_data')
local P=GF_REQUIRE('gf_character_registry').provider('clorinde')
local function fresh(id,face)
 local s=S.new({chars={R[5],R[5]},rounds=2,time=99,seed=123});s.phase='fight';s.freeze=0
 local p,d=s.f[1],s.f[2];p.x=0;p.y=0;p.face=face;d.invul=0;d.y=0;d.inNow=0;d.hp=1000
 s:setState(d,'idle');s:setState(p,id=='airHeavy' and 'air' or 'idle');p.skillCd=0
 if id=='skill' then s:startSkill(p) else s:startMove(p,id) end
 return s,p,d
end
local function tick(s,p,id,t)
 if id=='skill' then p.t=t;s:skillUpdate(p)
 elseif id=='airHeavy' then p.airT=t;s:airAttackUpdate(p)
 else p.t=t;s:attackUpdate(p) end
end
local cases=0
for id,list in pairs(Rules.blades) do
 for _,b in ipairs(list) do
  for _,face in ipairs({1,-1}) do
   for _,offset in ipairs({-1,1,10000}) do
    local s,p,d=fresh(id,face);local _,right=s:hurtbox(d);local half=right-d.x
    d.x=face*(b.tx+half+offset);s.events={};tick(s,p,id,b.start)
    assert((d.hp<1000)==(offset<0),'tip damage boundary '..id..' '..b.pose..' '..face..' '..offset)
    for _,e in ipairs(s.events) do if e.type=='hit' then assert(not e.projectileShot,'sword is not a bullet') end end
    cases=cases+1
   end
   local s,p,d=fresh(id,face);d.x=face*100000;tick(s,p,id,b.start)
   local out=P.extras({f=p,app={t=0}});local e=out[1]
   assert(e and not out[2],'blade effect instead of projectile '..id)
   local a=math.rad(e.rotation);local cs,sn=math.cos(a),math.sin(a)
   local tipX=e.x+(face*202.5*cs+2.25*sn)*e.scale
   local tipY=e.y+(face*202.5*sn-2.25*cs)*e.scale
   assert(math.abs(tipX-face*b.tx/100)<1e-6 and math.abs(tipY-b.ty/100)<1e-6,'rendered right endpoint matches sword tip '..id)
   assert(P.sample(id,id=='airHeavy' and p.airT-1 or p.t)==b.pose,'body and sword clocks match')
   local old=P.extras({f=p,app={t=0},front={key='idle_0'}});assert(not old[1],'do not float a sword over stale body')
   cases=cases+1
  end
 end
end
-- The live blade markers use unchanged source image anchors and time windows.
for id,list in pairs(Rules.blades) do for _,b in ipairs(list) do
 assert(D.frames[b.pose],'marker body exists')
 for t=b.start,b.finish-1 do assert(P.sample(id,t)==b.pose,'marker/source timeline mismatch '..b.pose..' '..t) end
end end
local bullet=P.image(D.effectIds.bullet);assert(bullet.h==6,'small bullet')
assert(bullet.pal[3][1]==255 and bullet.pal[3][2]==200 and bullet.pal[3][3]==45,'gold bullet')
assert(bullet.pal[1][3]>bullet.pal[1][1],'purple trail')
print('PASS '..cases..' sword tip/render/clock/boundary cases and gold bullet / purple trail')

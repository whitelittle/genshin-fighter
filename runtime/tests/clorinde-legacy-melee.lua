local S,R=GF_REQUIRE('gf_sim'),GF_REQUIRE('gf_roster')
local P=GF_REQUIRE('gf_character_registry').provider('clorinde')
local Rules=GF_REQUIRE('gf_clorinde_rules_data')
assert(not Rules.blades,'sword-tip candidate withdrawn')
for _,id in ipairs({'light1','light3','crouchLight','crouchHeavy','airHeavy'}) do
 for _,face in ipairs({1,-1}) do
  for _,hit in ipairs({true,false}) do
   local s=S.new({chars={R[5],R[5]},rounds=2,time=99,seed=123});s.phase='fight'
   local p,d=s.f[1],s.f[2];p.x=0;p.y=0;p.face=face;d.invul=0;d.hp=1000;d.inNow=0
   s:setState(d,'idle');s:setState(p,id=='airHeavy' and 'air' or 'idle');s:startMove(p,id)
   local m=p.airMove or p.move;local x0,x1,y0,y1=S.boxOf(p,m.box,p.kit.weapon.reach)
   d.x=hit and (x0+x1)//2 or face*100000;d.y=hit and y0 or 0
   if id=='airHeavy' then p.airT=m.startup;s:airAttackUpdate(p) else p.t=m.startup;s:attackUpdate(p) end
   assert((d.hp<1000)==hit,'original melee box '..id)
   local out=P.extras({f=p,app={t=0}});assert(not out[1] and not out[2],'no long melee/gun effect on swords '..id)
  end
 end
end
local D=GF_REQUIRE('gf_clorinde_data');local b=P.image(D.effectIds.bullet)
assert(b.h==6 and b.pal[3][1]==255 and b.pal[3][2]==200,'small gold bullet kept')
assert(b.pal[1][3]>b.pal[1][1],'purple trail kept')
print('PASS original melee boxes and no sword projectile effect; gold bullet retained')

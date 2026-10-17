local S,R=GF_REQUIRE('gf_sim'),GF_REQUIRE('gf_roster')
local D=GF_REQUIRE('gf_clorinde_data')
local P=GF_REQUIRE('gf_character_registry').provider('clorinde')
local original=GF_REQUIRE('gf_character_assets').new(D)
local s=S.new({chars={R[5],R[5]}});local p=s.f[1]
p.state='burst';p.moveId='burst';p.move=p.kit.burst;p.x=0;p.y=0
for _,face in ipairs({1,-1}) do
 p.face=face;p.cinematicConfirmed=true
 for t=6,13 do
  p.t=t;local e=P.extras({f=p,app={t=0}});assert(e[1] and e[2])
  assert(e[1].x==170*face and e[2].x==face*(170+(t-6)*45) and e[1].y==180)
  assert(P.image(e[1].id)==original.image(D.effectIds.gun),'Q gun uses old image')
  assert(P.image(e[2].id)==original.image(D.effectIds.bullet),'Q uses old electric projectile')
 end
 for _,t in ipairs({70,73,94,97,118,121}) do
  p.t=t;local e=P.extras({f=p,app={t=0}})
  assert(e[1] and e[1].id==D.effectIds.sword and not e[2],'old Q electric slash restored')
  assert(not e[3],'no foe impact from timeline alone')
 end
 p.cinematicConfirmed=false;p.t=70
 local e=P.extras({f=p,app={t=0}});assert(not e[1] and not e[2] and not e[3],'whiff does not show cinematic effects')
end
print('PASS legacy Q effect identity, positions, mirrored stages and no false impact')

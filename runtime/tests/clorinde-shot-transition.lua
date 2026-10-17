local S,R=GF_REQUIRE('gf_sim'),GF_REQUIRE('gf_roster')
local Rules=GF_REQUIRE('gf_clorinde_rules_data')
local cases=0
for _,slot in ipairs({1,2}) do
 for _,face in ipairs({1,-1}) do
  for _,airId in ipairs({'airHeavy','airLight'}) do
   for _,groundId in ipairs({'light2','heavy'}) do
    local s=S.new({chars={R[5],R[5]},rounds=2,time=99,seed=32})
    s.phase='fight';s.freeze=0
    local p,d=s.f[slot],s.f[3-slot]
    p.x=0;p.face=face;p.y=10000;p.vy=0
    d.x=face*85000;d.y=0
    s:setState(p,'air');s:setState(d,'idle')
    assert(s:startMove(p,airId))
    -- Advance real simulation through the air attack, floor contact and landing recovery.
    local landed=false
    for _=1,180 do
     s:step(0,0)
     if p.y==0 and p.state=='idle' then landed=true;break end
    end
    assert(landed and not p.airMove,'landing did not finish')
    assert(p.airMoveId==airId,'reproduction must retain historical air move id')
    -- At this distance the old air-Light muzzle misses; both ground muzzles hit.
    p.x=0;p.face=face;d.x=face*15000;s:setState(d,'idle')
    local hp=d.hp
    assert(s:startMove(p,groundId))
    local snapshot=S.copy(s)
    local total=Rules[groundId].startup+Rules[groundId].active+Rules[groundId].recovery
    for _=1,total+60 do
     s:step(0,0);snapshot:step(0,0)
     assert(s:hash()==snapshot:hash(),'transition snapshot replay diverged')
    end
    assert(hp-d.hp==Rules[groundId].damage,'wrong ground shot damage/configuration')
    assert(p.state=='idle','ground attack recovery did not finish')
    cases=cases+1
   end
  end
 end
end
print('PASS '..cases..' air attack -> landing -> ground shot cases and snapshot replay')

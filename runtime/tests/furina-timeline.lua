local S=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_roster');local D=GF_REQUIRE('gf_furina_rules_data')
local function new(face)
 local s=S.new({chars={R[3],R[1]},training=true,infinite=true,time=99,rounds=2,seed=21})
 s.phase='fight';s.phaseT=0
 for _,f in ipairs(s.f) do s:setState(f,'idle');f.invul=0 end
 s.f[1].face=face or 1;s.f[2].face=-(face or 1)
 s.f[1].x=0;s.f[2].x=(face or 1)*20000
 return s,s.f[1],s.f[2]
end
for _,face in ipairs({1,-1}) do
 local s,p,d=new(face)
 d.x=face*60000
 assert(s:startSkill(p));assert(p.move.style=='salon')
 for t=1,48 do s:step(0,0);assert(#s.proj==0,'salon must not spawn legacy bubbles') end
 assert(p.state=='idle','E timeline must complete in 48 delivered ticks')
 s,p,d=new(face);p.energy=100;assert(s:startBurst(p));assert(s.freeze==0)
 local damageTicks={}
 for t=1,158 do
  local hp=d.hp;s:step(0,0)
  if hp~=d.hp then damageTicks[#damageTicks+1]=t end
  if t>=12 and t<158 then assert(p.cinematicConfirmed,'Q confirmation lost') end
  if t==40 then
   local c=S.copy(s)
   for _=1,30 do s:step(0,0);c:step(0,0);assert(dump(s)==dump(c),'Q snapshot replay') end
   -- Restore the requested tick without losing the rest of the scenario.
   s,p,d=new(face);p.energy=100;s:startBurst(p);for _=1,40 do s:step(0,0) end
  end
 end
 assert(#damageTicks==3 and damageTicks[1]==56 and damageTicks[2]==78 and damageTicks[3]==100)
 assert(p.state=='idle' and d.state=='down' and d.y==0)
 s,p,d=new(face);d.x=face*14000;s:tryThrow(p);assert(p.state=='throw')
 local hp=d.hp
 for t=1,72 do
  s:step(0,0)
  if t<30 then assert(d.hp==hp) end
  if t==30 then assert(d.hp<hp and d.state=='thrown' and d.y==0) end
  if t==38 then assert(d.y==10000 and d.x==face*32500) end
  if t==50 then assert(d.state=='down' and d.y==0 and d.x==face*38500) end
 end
 assert(p.state=='idle')
 s,p,d=new(face);p.energy=100;d.x=face*60000;s:startBurst(p)
 for _=1,42 do s:step(0,0) end
 assert(not p.cinematicConfirmed and p.state=='idle' and d.hp==d.maxhp,'Q miss adaptation')
end

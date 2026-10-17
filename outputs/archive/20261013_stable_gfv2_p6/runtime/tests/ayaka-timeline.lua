local S=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_roster')
local D=GF_REQUIRE('gf_ayaka_rules_data')
local function new(face)
 local s=S.new({chars={R[4],R[3]},training=true,infinite=true,time=99,rounds=2,seed=21})
 s.phase='fight';s.phaseT=0
 for _,f in ipairs(s.f) do s:setState(f,'idle');f.invul=0 end
 local p,d=s.f[1],s.f[2];p.x=0;p.face=face;d.face=-face;d.x=face*20000
 return s,p,d
end
for _,face in ipairs({1,-1}) do
 local s,p,d=new(face);d.x=face*60000;assert(s:startSkill(p))
 for _=1,38 do s:step(0,0);assert(#s.proj==0) end
 assert(p.state=='idle','E exact duration')
 s,p,d=new(face);p.energy=100;assert(s:startBurst(p));assert(s.freeze==0)
 local hits={}
 for t=1,152 do
  local hp=d.hp;s:step(0,0)
  if hp~=d.hp then hits[#hits+1]=t end
  if t>=52 and t<152 then assert(p.cinematicConfirmed) end
  if t==60 then
   local c=S.copy(s)
   for _=1,30 do s:step(0,0);c:step(0,0);assert(dump(s)==dump(c),'Ayaka Q snapshot') end
   s,p,d=new(face);p.energy=100;s:startBurst(p);for _=1,60 do s:step(0,0) end
  end
 end
 assert(#hits==3 and hits[1]==70 and hits[2]==94 and hits[3]==118,'Q hit ticks')
 assert(p.state=='idle' and d.state=='down' and d.y==0)
 s,p,d=new(face);d.x=face*14000;s:tryThrow(p);assert(p.state=='throw')
 local hp=d.hp
 for t=1,72 do
  s:step(0,0)
  if t<34 then assert(d.hp==hp) end
  if t==34 then assert(d.hp<hp) end
  if t==24 then assert(d.y==22000) end
  if t==44 then assert(d.state=='down' and d.y==0 and d.x==p.x+face*18000) end
 end
 assert(p.state=='idle')
 s,p,d=new(face);d.x=face*65000;p.energy=100;s:startBurst(p)
 for _=1,72 do s:step(0,0) end
 assert(p.state=='idle' and not p.cinematicConfirmed,'Q miss short recovery')
 s,p,d=new(face);p.energy=100;s:startBurst(p)
 for _=1,52 do s:step(0,face==1 and 8 or 4) end
 assert(not p.cinematicConfirmed and d.hp==d.maxhp,'Q block must not capture')
end

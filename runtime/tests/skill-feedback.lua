local S=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_roster')
local ticks={nahida=2,raidenshogun=2,furina=12,kamisatoayaka=52,clorinde=6,arlecchino=6}
local reach={nahida=2400,raidenshogun=950,furina=410,kamisatoayaka=420,clorinde=410,arlecchino=410}
local function fresh(i,face)
 local s=S.new({chars={R[i],R[i]},rounds=2,time=99,seed=42});s.phase='fight';s.freeze=0
 local p,d=s.f[1],s.f[2];p.x=0;p.face=face or 1;d.x=20000*p.face;p.energy=100
 s:setState(p,'idle');s:setState(d,'idle');return s,p,d
end
local function code(s,c)
 for _,e in ipairs(s.events) do if e.type=='skillFeedback' and e.code==c then return true end end
 return false
end
local cases=0
for i=1,6 do
 for _,face in ipairs({1,-1}) do
  for _,kind in ipairs({'edge','outside','back','invul','down','block','high','crouch'}) do
   local s,p,d=fresh(i,face);local r=reach[p.key];local margin=math.floor(50*100*d.size)
   d.x=face*(r*100+margin-1);d.inNow=0
   if kind=='outside' then d.x=face*(r*100+margin+1) end
   if kind=='back' then d.x=-face*((p.key=='nahida' or p.key=='raidenshogun') and (p.kit.burst.range+1)*100 or 4100) end
   if kind=='invul' then d.invul=30 end
   if kind=='down' then s:setState(d,'down') end
   if kind=='block' then d.inNow=face==1 and 8 or 4 end
   if kind=='high' then d.y=42000 end
   if kind=='crouch' then s:setState(d,'crouch') end
   assert(s:startBurst(p));s.freeze=0;p.t=ticks[p.key];s.events={};s:burstUpdate(p)
   local yes=kind=='edge' or kind=='crouch' or (kind=='high' and p.key=='nahida')
   assert(p.cinematicConfirmed==yes,p.key..' '..kind..' '..face)
   if kind=='block' then assert(code(s,'block'),p.key..' block feedback')
   elseif not yes then assert(code(s,'miss'),p.key..' miss feedback') end
   assert(p.energy==0,'accepted burst cost retained')
   cases=cases+1
  end
 end
 local s,p,d=fresh(i);p.energy=30;s:step(128,0);assert(code(s,'energy') and p.energy==30)
 s:step(128,0);assert(not code(s,'energy'),'held key is not another press')
 s,p,d=fresh(i);s:setState(p,'down');s:step(128,0);assert(code(s,'state') and p.energy==100)
 s,p,d=fresh(i);p.skillCd=50;s:step(64,0);assert(code(s,'cooldown') and p.skillCd==49)
 s,p,d=fresh(i);p.energy=100;s:step(128,0);assert(not code(s,'energy') and not code(s,'state'))
end
-- Every role must replay complete mutable state and feedback across a delayed input correction.
local function same(a,b,seen)
 if type(a)~=type(b) then return false end
 if type(a)~='table' then return a==b end
 seen=seen or {};if seen[a] then return seen[a]==b end;seen[a]=b
 for k,v in pairs(a) do if not same(v,b[k],seen) then return false end end
 for k in pairs(b) do if a[k]==nil then return false end end
 return true
end
for i=1,6 do
 local s,p,d=fresh(i);d.x=30000
 local replay=S.copy(s)
 for t=1,200 do
  local m=t==1 and 128 or t==40 and 64 or t==80 and 128 or t==100 and 16 or 0
  s:step(m,0);replay:step(m,0)
  assert(same(s,replay),'complete snapshot + events replay '..i..' '..t)
  assert(s:hash()==replay:hash(),'Q replay hash '..i..' '..t)
  for k,v in pairs(s.f[1]) do if type(v)~='table' and type(v)~='function' then assert(v==replay.f[1][k],'snapshot field '..k) end end
  assert(#s.events==#replay.events)
  for n,e in ipairs(s.events) do for k,v in pairs(e) do if type(v)~='table' then assert(v==replay.events[n][k]) end end end
 end
end
assert(GF_REQUIRE('gf_online').VERSION==8,'changed rules reject old peer versions')
print('PASS '..cases..' six-role mirrored burst boundaries + refusal, held edge, cost and 1200 replay ticks')

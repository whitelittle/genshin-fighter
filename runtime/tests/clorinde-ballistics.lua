local S,R=GF_REQUIRE('gf_sim'),GF_REQUIRE('gf_roster')
local Rules=GF_REQUIRE('gf_clorinde_rules_data')
local P=GF_REQUIRE('gf_character_registry').provider('clorinde')
local D=GF_REQUIRE('gf_clorinde_data')
local function fresh(face,id,distance)
 local s=S.new({chars={R[5],R[5]},rounds=2,time=99,seed=32});s.phase='fight';s.freeze=0
 local p,d=s.f[1],s.f[2];p.x=0;p.face=face;d.x=face*distance*100;d.y=0;p.y=0
 s:setState(d,'idle');s:setState(p,id=='airLight' and 'air' or 'idle');p.skillCd=0
 if id=='skill' then assert(s:startSkill(p)) else assert(s:startMove(p,id)) end
 return s,p,d
end
local function update(s,p,id,t)
 s.events={}
 if id=='skill' then p.t=t;s:skillUpdate(p)
 elseif id=='airLight' then p.airT=t;s:airAttackUpdate(p)
 else p.t=t;s:attackUpdate(p) end
end
local n=0
for _,id in ipairs({'light2','heavy','airLight','skill'}) do
 for _,face in ipairs({1,-1}) do
  for _,distance in ipairs({150,350,450,550,650,850,-300}) do
   local s,p,d=fresh(face,id,distance);local hp=d.hp
   local startup=id=='skill' and 8 or Rules[id].startup
   local damage=id=='skill' and 35 or Rules[id].damage
   for age=0,7 do update(s,p,id,startup+age) end
   assert((d.hp<hp)==(distance>0 and distance<=650 and not (id=='airLight' and distance==150)),id..' range '..distance..' '..face)
   if d.hp<hp then assert(hp-d.hp==damage,'one shot, one damage '..id) end
   n=n+1
  end
  for _,kind in ipairs({'block','invul','down','tooHigh'}) do
   local s,p,d=fresh(face,id,450);local hp=d.hp
   if kind=='block' then d.inNow=face==1 and 8 or 4 end
   if kind=='invul' then d.invul=40 end
   if kind=='down' then s:setState(d,'down') end
   if kind=='tooHigh' then d.y=100000 end
   local startup=id=='skill' and 8 or Rules[id].startup;local blocked=false
   for age=0,7 do
    update(s,p,id,startup+age)
    for _,e in ipairs(s.events) do if e.type=='block' then blocked=true end;assert(e.type~='hit','invalid full hit '..kind) end
   end
   if kind=='block' then assert(blocked and d.hp>=hp-3,'guard feedback / existing chip')
   else assert(d.hp==hp,'invalid damage '..kind) end
   n=n+1
  end
  -- Visual bullet envelope must agree with the current attack box at every age,
  -- and never persist after a confirmed contact.
  for age=0,7 do
   local s,p,d=fresh(face,id,850);local start=id=='skill' and 8 or Rules[id].startup
   update(s,p,id,start+age)
   local out=P.extras({f=p,app={t=0}});assert(out[2],id..' visible shot '..age)
   local cfg=Rules.shot[id]
   assert(out[2].x==face*(cfg.x+age*Rules.shot.speed) and out[2].y==cfg.y,'shot clock/location mismatch')
   if age==0 then assert(out[1].x==face*cfg.x and out[1].y==cfg.y,'flash must be at muzzle') end
   if age>=3 then assert(not out[1],'muzzle flash must not fly with projectile') end
   local im=P.image(out[2].id);local lo,hi=1e9,-1e9
   for i=0,im.n-1 do lo=math.min(lo,im.bytes[i*5+1]-im.ax);hi=math.max(hi,im.bytes[i*5+1]+im.bytes[i*5+3]-im.ax) end
   assert(lo==Rules.shot.near and hi<=Rules.shot.far and Rules.shot.far-hi<=1,'rules measured from actual fitted image')
   if id=='skill' then p.skillHitMask=2 else p.connected=true end
   assert(not P.extras({f=p,app={t=0}})[2],'bullet should end on hit or block')
   n=n+1
   for _,offset in ipairs({-1,1}) do
    local edge,ep,ed=fresh(face,id,850)
    local _,right=edge:hurtbox(ed);local half=right-ed.x
    ed.x=face*((cfg.x+age*Rules.shot.speed+Rules.shot.far)*100+half+offset)
    local hp=ed.hp;update(edge,ep,id,start+age)
    assert((ed.hp<hp)==(offset<0),'bullet tip boundary '..id..' '..age..' '..face)
    n=n+1
   end
  end
 end
 -- Preserve total action time and damage definition. A near bullet at the end of
 -- its life cannot damage someone entering after the visible bullet disappeared.
 local s,p,d=fresh(1,id,850);local hp=d.hp;local start=id=='skill' and 8 or Rules[id].startup
 update(s,p,id,start+8);assert(d.hp==hp,'shot expired')
 if id~='skill' then
  local total=Rules[id].startup+Rules[id].active+Rules[id].recovery
  update(s,p,id,total);assert(id=='airLight' and not p.airMove or id~='airLight' and p.state=='idle','total action length')
 end
end
-- E's separate thrust keeps its original near-range damage and hit mask.
local s,p,d=fresh(1,'skill',150);update(s,p,'skill',18);assert(p.skillHitMask==4 and d.hp==d.maxhp-50)
local hp=d.hp;update(s,p,'skill',19);assert(d.hp==hp,'no duplicate thrust')
print('PASS '..n..' mirrored projectile range/status/visual clock cases for J2, K, air-J, E')
-- A swept ray must hit a target crossed between two 75-unit positions, not tunnel.
local sweep,sp,sd=fresh(1,'light2',320);update(sweep,sp,'light2',13);assert(sd.hp<sd.maxhp,'swept contact between render positions')
-- Ray height follows the weapon: low crouching bodies can duck horizontal shots,
-- while the existing near-range E thrust still handles crouching opponents.
local duck,dp,dd=fresh(1,'light2',450);duck:setState(dd,'crouch');local hp=dd.hp
for age=0,7 do update(duck,dp,'light2',11+age) end
assert(dd.hp==hp,'horizontal gun ray must not hit under its trajectory')

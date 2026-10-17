local Sim=GF_REQUIRE('gf_sim_lumine_training')
local X=GF_REQUIRE('gf_training_extended')
local Registry=GF_REQUIRE('gf_character_registry')
local report={courses={},reactions={}}
local function create(course,index)
 local s=Sim.new({chars={Registry.byKey.lumine,Registry.byKey.lawachurl},training=true,seed=21})
 s.phase='fight';s.freeze=0
 local l={scene={sim=s},course=course,index=index or 1,pending=0,lessons=X.steps(course)}
 local x=X.new(l);l.extended=x;x:prepare(l.lessons[l.index].kind)
 return s,x,l
end
local function tick(s,x,mask,n)
 for i=1,n or 1 do s:step(mask or 0,x:input());if x:tick()then x.done=true end end
end
local function untilDone(s,x,mask,n)
 for i=1,n or 400 do tick(s,x,mask);if x.done then return end end
 error('objective did not complete: '..x.lesson.course..' '..x.kind..' '..x.label)
end
local cases={'low','air','skill','burst','assist','throw','side','anemo','geo','electro','dendro','hydro','pyro','cryo'}
for _,course in ipairs(cases)do
 local count=#X.steps(course)
 for index=1,count do
  local s,x,l=create(course,index);local kind=x.kind;local goal=l.lessons[index]
  tick(s,x,0,5);assert(not x.done,'idle falsely completed '..kind)
  -- Ordinary light cannot stand in for any required special action or reaction.
  if kind~='throwTech' and kind~='shield' then tick(s,x,16);tick(s,x,0,45);assert(not x.done,'light falsely completed '..kind);x:prepare(kind)end
  if kind=='crouchLight' or kind=='crouchHeavy' then tick(s,x,2|(kind=='crouchLight' and 16 or 32));untilDone(s,x,0)
  elseif kind=='airLight' or kind=='airHeavy' then tick(s,x,1,6);tick(s,x,0,3);tick(s,x,kind=='airLight' and 16 or 32);untilDone(s,x,0)
  elseif kind=='skill' or kind=='skillUp' or kind=='skillDown' then tick(s,x,64|(kind=='skillUp' and 1 or kind=='skillDown' and 2 or 0));untilDone(s,x,0)
  elseif kind=='skillCooldown' then tick(s,x,64);assert(x.rejected and not x.done);tick(s,x,0,95);tick(s,x,64);untilDone(s,x,0)
  elseif kind=='burstEmpty' then tick(s,x,128);assert(s.f[1].energy==0);untilDone(s,x,0)
  elseif kind:find('burst') then tick(s,x,128);assert(s.f[1].energy==0,'burst failed to consume energy');untilDone(s,x,0)
  elseif kind=='supportHit' or kind=='supportMiss' then tick(s,x,1024);untilDone(s,x,0)
  elseif kind=='supportCooldown' then tick(s,x,1024);assert(x.rejected and not s.assist);tick(s,x,0,360);tick(s,x,1024);untilDone(s,x,0)
  elseif kind=='throwHit' or kind=='throwMiss' then tick(s,x,512);untilDone(s,x,0)
  elseif kind=='throwTech' then
   for i=1,160 do if s.f[1].state=='thrown' then break end;tick(s,x,0)end
   assert(s.f[1].state=='thrown');local hp=s.f[1].hp;tick(s,x,512);untilDone(s,x,0);assert(s.f[1].hp==hp)
  elseif kind=='crossRight' or kind=='crossLeft' then tick(s,x,1|(kind=='crossRight' and 8 or 4),6);untilDone(s,x,0,160)
  elseif kind=='sideGuard' then untilDone(s,x,8)
  elseif kind=='reaction' then
   local mask=64|(goal.branch=='skillUp' and 1 or goal.branch=='skillDown' and 2 or 0)
   tick(s,x,mask)
   if goal.chain then tick(s,x,0,80);assert(#s.cores==1,'Bloom did not create a real core');assert(not x.done);tick(s,x,64)end
   untilDone(s,x,0);report.reactions[#report.reactions+1]={course=course,reaction=goal.reaction,branch=goal.branch}
  elseif kind=='pickup' then tick(s,x,64);tick(s,x,0,80);assert(s.f[1].shield==0,'crystal granted automatic shield');untilDone(s,x,8)
  elseif kind=='shield' then untilDone(s,x,0)
  elseif kind=='shatter' then tick(s,x,64);tick(s,x,0,65);assert(s.f[2].frozen>0);tick(s,x,32);untilDone(s,x,0)
  else error(kind)end
  assert(x.done,kind)
 end
 report.courses[#report.courses+1]={course=course,objectives=count}
end
-- Replay the new mutable state, including cores, aura, support and cooldowns.
do
 local s,x=create('electro',6);tick(s,x,64);tick(s,x,0,24)
 local copy=Sim.copy(s);assert(s:hash()==copy:hash());assert(copy.cores~=s.cores and copy.f[2].dots~=s.f[2].dots)
 for i=1,400 do local mask=i==70 and 64 or i==130 and 1024 or i%100==0 and 16 or 0;s:step(mask,0);copy:step(mask,0);assert(s:hash()==copy:hash(),'new state replay mismatch')end
 local a=Sim.copy(s);a.f[1].face=-a.f[1].face;assert(a:hash()~=s:hash(),'facing missing from teaching hash')
end
report.snapshotReplay=true
-- Wrong direction E can cause a real reaction but must not satisfy the requested branch.
do
 local s,x=create('anemo',2);tick(s,x,64);tick(s,x,0,170);assert(not x.done)
 assert(s.f[2].aura=='hydro','wrong branch consumed the setup permanently')
 tick(s,x,65);untilDone(s,x,0)
end
-- A held early throw and a late throw cannot count as an escape.
for _,late in ipairs({false,true})do
 local s,x=create('throw',2)
 if not late then tick(s,x,512,160);assert(not x.done,'held early input escaped throw')
 else
  for i=1,160 do if s.f[1].state=='thrown' then break end;tick(s,x,0)end
  tick(s,x,0,15);tick(s,x,512);assert(not x.done,'late input escaped throw')
 end
end
report.wrongBranchRecovery=true;report.earlyHeldAndLateTechRejected=true
return report

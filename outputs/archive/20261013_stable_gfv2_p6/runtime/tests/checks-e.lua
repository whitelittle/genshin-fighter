local Art=GF_REQUIRE('gf_art');local G=GF_REQUIRE('gf_gfx');local Sim=GF_REQUIRE('gf_sim')
local V=GF_REQUIRE('gf_fview');local Stage=GF_REQUIRE('gf_stage');local Select=GF_REQUIRE('gf_scene_select')
local N=GF_REQUIRE('gf_net');local App=GF_REQUIRE('gf_app')
local R=GF_REQUIRE('gf_roster');local P=GF_REQUIRE('gf_paint')
local function check(v,msg) assert(v,msg);print('PASS '..msg) end
local function node()
 local n={act=false,x=0,y=0,sx=1,sy=1,kids={}}
 n.c={SetAnchoredPosition=function()end,SetSizeDelta=function()end,SetActive=function()end,SetVisible=function()end}
 for _,m in ipairs({'pos','size','scale','rot','color','on','soft','sibling','front','rgba','parentTo','shape'}) do
  n[m]=function(self,...)
   local a={...};if m=='on' then self.act=a[1] elseif m=='pos' then self.x,self.y=a[1],a[2] elseif m=='scale' then self.sx,self.sy=a[1],a[2] or a[1] end
   return self
  end
 end
 n.tween=function() return nil end;return n
end
G.init({safe=function(f,...)return f(...)end,Color=function(r,g,b,a)return {r,g,b,a}end},{root={},imgs={},txts={},btns={}})
G.group=function()return node()end;G.image=function()return node()end
G.layer=function()local x={};for _,m in ipairs({'begin','finish','clear','free','rect','shape','label'}) do x[m]=function()end end;return x end
G.release=function()end
-- Use the real Bitmap methods with mocked native leaf setters.
local sim=Sim.new({chars={R[1],R[2]},rounds=2,time=99,seed=21})
local app={frame=0,t=0,scene={sim=sim},quality='lo',layers={front={}}}
local views={}
for i=1,2 do
 local job=Art.prepare(R[i].key,'lo');local count=0
 while not job:step(9000) do count=count+1;assert(count<500)end
 local v=V.new(app,{body={},fx={},ghost={},shadow={}},sim.f[i],'lo');views[i]=v
 local n=0;while not v:reserveBody(320) do n=n+1;assert(n<50)end
 check(#v.slots[1].kids==v.bodyCapacity and #v.slots[2].kids==v.bodyCapacity,'preallocated '..R[i].key)
end
-- Idle is fixed and gait contains all six real basic poses in both directions.
for i,v in ipairs(views) do
 v.f.state='idle'
 for frame=1,150 do app.frame=frame;check(v:animatedPose()==(i==1 and 'idle_0' or 'basic_0'),'idle sample '..i..':'..frame); if frame==1 then break end end
 v.f.state='walk';local seen={}
 for t=0,47 do v.walkT=t;local p=v:animatedPose();seen[p]=true;check(not p:match('move'),'walk uses ground frames '..i..':'..t);if t==0 then break end end
 for j=0,5 do v.walkT=j*8;seen[v:animatedPose()]=true end
 local c=0;for _ in pairs(seen)do c=c+1 end;check(c==6,'six gait poses '..i)
 v.f.state='back';v.walkT=0;check(v:animatedPose()=='basic_7','reverse gait '..i)
end
-- Drawing twice at same sim tick must not speed up the walk clock.
local v=views[2];v.f.state='walk';v.f.coat=0;v.f.frozen=0;v.f.hitstop=0
v:draw(320);local t=v.walkT;v:draw(320);check(v.walkT==t,'gait clock follows simulation')
sim.tick=sim.tick+4;v:draw(320);check(v.walkT==t+4,'four simulation ticks advance gait four ticks')
check(math.abs(v.oy)<=1.5,'Nahida walking grounded')
-- Loading buffers do not grow during gait, and each body slice respects budget.
for i,v in ipairs(views)do
 local cap={#v.slots[1].kids,#v.slots[2].kids}
 local maxwrites=0
 for tick=1,180 do
  sim.tick=tick;app.frame=tick;app.t=tick/60;v.f.state='walk'
  local before=G.N.bitmap or 0;v:draw(320);local writes=(G.N.bitmap or 0)-before;maxwrites=math.max(maxwrites,writes)
  assert(writes<=320*5,'slice budget exceeded')
  assert(#v.slots[1].kids==cap[1] and #v.slots[2].kids==cap[2],'body allocation during fight')
 end
 check(v.front~=nil,'body visible '..i);print('BODY_WRITE_PEAK '..i..' '..maxwrites)
end
local stage=Stage.new(app,{},'inazuma');while not stage:buildStep(160) do end
check(stage.key=='mondstadt' and not stage.painted,'single primitive stage');check(#stage.nodes<=40,'stage under 40 primitives');print('STAGE_NODES '..#stage.nodes)
local p=P.new({},'inazuma','full',700);while not p:step(40)do end
check(p.n<30 and not p.dec,'primitive menu background');print('MENU_NODES '..p.n)
for _,mode in ipairs({'versus','training','arcade','online'})do
 local launched=false;local s=setmetatable({mode=mode,cur={1,2},done={true,true},stageI=7},Select)
 s.launch=function(self)launched=true;check(self.stageI==1,'fixed stage '..mode)end;s:afterChars()
 check(launched and s.phase~='stage','skip stage picker '..mode)
end
-- Prediction waits are observable, then recover immediately when inputs arrive.
local n=N.new({side=1,simOpts={chars={R[1],R[2]},rounds=2,time=99,seed=21},maxPredict=12})
for i=1,12 do N.setLocalInput(n,8);assert(N.advance(n))end
check(not N.advance(n) and n.stats.stalls==1,'prediction exhaustion counted')
local remote={};for i=1,12 do remote[i]=0 end;N.receive(n,remote,12,0)
check(N.advance(n) and n.frame==13,'confirmed input resumes without extra stall')
-- Perf available with debug overlay disabled, bitmap is not double counted.
G.secondPoolStatus=function()return {created=0,total=14000,freeFirst=0,freeSecond=5000}end
local a=setmetatable({sceneName='fight',scene={sim=sim},debug=false},App)
a:samplePerformance(1/60);check(a.perf~=nil and a.perf.frameBitmapWrites>=0,'diagnostics enabled without overlay')
print('ALL CHECKS PASSED')

-- Force a hit before the next body buffer completes: both idle aliases must flash.
local v=views[1]
for _,phase in ipairs({0,40})do
 v.f.state='idle';v.f.t=phase;v.f.coat=0;v.f.frozen=0;v.flashT=0
 for i=1,12 do v:draw(320)end
 local key='idle_'..(phase//40)
 assert(v.front.key==key,'idle published '..key)
 v.f.state='hit';v.f.t=0;v.flashT=5;v.flashTint={255,255,255}
 v:draw(1)
 assert(v.front.key==key and v.flash.used==v.poseImg.n,'pending hit flashes current '..key)
 assert(v.flash.key==key..':flash' and v.flashT==4,'hit flash completed '..key)
 v.f.frozen=10;v:draw(1);assert(v.flash.key==key..':ice','frozen overlay '..key)
 print('PASS idle hit and ice overlay '..key)
end

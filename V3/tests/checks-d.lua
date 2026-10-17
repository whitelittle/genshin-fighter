local Sim=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_roster')
local sim=Sim.new({chars={R[1],R[2]},rounds=2,time=99,seed=21})
local x1,x2=sim.f[1].x,sim.f[2].x
for i=1,60 do
 sim:step(8|16|64|128,4|32)
 assert(sim.f[1].x==x1 and sim.f[2].x==x2,'intro movement at '..i)
 assert(sim.f[1].hp==sim.f[1].maxhp and sim.f[2].hp==sim.f[2].maxhp,'intro damage')
 assert(sim.f[1].energy==0 and #sim.proj==0,'intro action')
 if i==40 then assert(sim.phase=='intro' and sim.events[1].what=='fight','fight banner before unlock')end
end
assert(sim.phase=='fight' and sim.f[1].state=='idle','60 tick intro')
sim:step(8|16|64|128,0)
assert(sim.f[1].state=='walk' and sim.f[1].x>x1,'movement opens after intro')
sim:step(0,0);sim:step(16,0)
assert(sim.f[1].state=='attack','fresh attack after release')
sim.f[1].bufferedMove='heavy';sim:startRound(false)
assert(sim.f[1].bufferedMove==nil and sim.f[1].histN==0,'new round clears history')
print('PASS 60-tick frozen intro, 20-tick FIGHT, no held attack leakage, next-round reset')
local G=GF_REQUIRE('gf_gfx')
local function native()
 local c={}
 for _,k in ipairs({'SetAsLastSibling','SetActive','SetVisible','SetParent','SetImage','SetLocalRotation','SetLocalScale','SetSoftness','SetFillUnused','SetSizeDelta','SetAnchoredPosition'})do c[k]=function()end end
 return c
end
G.init({Enum={ImageSource={StaticReference=1}},safe=function(f,...)return f(...)end,Color=function(...)return {...}end},{root=native(),imgs={},txts={},btns={}})
local function nd()
 return setmetatable({c=native(),kind='image',act=true},G.Node)
end
local a,b=nd(),nd()
G.deferRelease=true;G.release(a);G.release(b);G.release(a);G.deferRelease=false
assert(G.retiredPending()==2 and #G.freeImg==0,'retired nodes cannot be reused')
G.flushRetired(1);assert(a.freed and not b.freed and G.retiredPending()==1,'leaf-first retirement budget')
G.flushRetired(1);assert(b.freed and G.retiredPending()==0 and #G.freeImg==2,'queue completion')
local pinned=G.bitmap(nil);pinned.pinned=true;pinned.node.act=false;pinned.kids={nd()};pinned.used=1
local dormant=G.bitmap(nil);dormant.node.act=false;dormant.kids={nd()};dormant.used=1
G.reclaimDormant();assert(#pinned.kids==1 and #dormant.kids==0,'pinned body survives reclaim')
print('PASS retirement budget, no double enqueue, no early reuse, pinned buffers')
local A=GF_REQUIRE('gf_art');local V=GF_REQUIRE('gf_fview')
local app={scene={sim={tick=0}}};local v=setmetatable({key='raidenshogun',tier='lo',app=app,f={key='raidenshogun',state='idle',t=0}},V)
local seen={};for t=0,159 do app.scene.sim.tick=t;v.f.t=t;seen[v:animatedPose()]=true end
assert(seen.idle_0 and seen.idle_1 and not seen.basic_between_0,'real idle poses only')
local a,b=v:image('idle_0'),v:image('idle_1')
assert(math.abs(b.ox-16.153846153846)<0.01,'boot-anchor correction')
assert(A.pose('raidenshogun','lo','basic_1').ox~=b.ox,'alignment copy leaves original asset intact')
print('PASS animated Raiden idle, no walking inbetween, aligned boot anchors')

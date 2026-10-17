"""Callback FPS diagnostics and fixed-step catch-up; offline, not native FPS."""
from pathlib import Path
import json
from performance import BenchClient
from mock_flow import ROOT,wait

c=BenchClient(ROOT/'dist/genshin_fighter.lua')
c.env.GF_FIRST_SCENE='fight'
c.env.GF_FIRST_ARGS=c.rt.eval("{chars={'furina','kamisatoayaka'},mode='training',cpu={false,false},infinite=true,time=99}")
wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
c.run(1)
# Test the exact accumulator with identical logical input streams and real Sim.
c.lua('''(function()
local App,Sim=GF_REQUIRE('gf_app'),GF_REQUIRE('gf_sim')
local base=Sim.copy(GF_APP().scene.sim)
base.phase='fight';base.freeze=0
for i,p in ipairs(base.f)do base:setState(p,'idle');p.x=i==1 and -10000 or 10000;p.y=0;p.invul=0;p.hitstop=0;p.energy=100 end
local results={}
for _,hz in ipairs({60,30,15})do
 local a=GF_APP();local real=a.scene;local oldAcc=a.acc;local oldDrop=a.droppedTime
 local s=Sim.copy(base);local tick=0
 a.scene={sim=s,tick=function()tick=tick+1;s:step(tick==1 and 128 or 0,0)end,draw=function()end}
 a.acc=0;a.droppedTime=0
 for i=1,hz*3 do a:update(1/hz)end
 results[#results+1]={tick=tick,hash=s:hash(),hp=s.f[2].hp,damage=s.f[1].stats.damage}
 assert(a.droppedTime==0)
 a.scene=real;a.acc=oldAcc;a.droppedTime=oldDrop
end
assert(results[1].tick==180)
assert(results[1].damage>0)
for i=2,3 do assert(results[i].tick==results[1].tick and results[i].hash==results[1].hash and results[i].hp==results[1].hp and results[i].damage==results[1].damage)end
local a=GF_APP();a.frameRate=nil
for i=1,30 do a:sampleFrameRate(1/30)end
a:sampleFrameRate(1/30)
assert(math.abs(a.frameRate.fps-30)<.001)
a.frameRate=nil;a:sampleFrameRate(.5);a:sampleFrameRate(.5)
assert(a.frameRate.fps==2 and a.frameRate.maxMs==500)
local before=a.droppedTime or 0;a:update(.5)
assert(a.droppedTime-before>.25)
return true end)()
''')
c.run(1.1)
c.render(ROOT/'verification/fps-fight.png')
c.lua('(function()GF_APP().scene:openPause();GF_APP().scene.showMoves=true;return true end)()')
c.run(.3)
c.render(ROOT/'verification/fps-pause.png')
report={'mockOnly':True,'fixedStepRates':[60,30,15],'equalLogicTicks':180,'equalDamageAndHash':True,'rawCallbackIntervalMeasured':True,'halfSecondClampCounted':True,'productionTextPool':96,'pauseCommandList':True}
(ROOT/'verification/fps-monitor.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))

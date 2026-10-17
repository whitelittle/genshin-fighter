"""Real simulation + native-UI approximation for the isolated teaching sample."""
from pathlib import Path
import sys,json,random
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'outputs/lumine-training-20261015'
sys.path.insert(0,str(ROOT/'tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'candidate.lua'
results=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600))]:
 c=RuntimeClient(device=device,canvas=canvas)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':False,'seed':21})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans",limit=2800)
 c.run(.4);c.render(OUT/f'training-idle-{device}-{canvas[0]}.png')
 wait(c,'not GF_APP().scene.lesson or not GF_APP().scene.lesson:isBriefing()')
 x=c.lua('GF_APP().scene.sim.f[1].x');c.key('D',True);c.run(.5);c.key('D',False);c.step()
 assert c.lua('GF_APP().scene.sim.f[1].x')>x
 c.lua("(function()local s=GF_APP().scene.sim;s.f[1].x=-9000;s.f[2].x=9000;s.f[1].vx=0;s.f[2].vx=0;s:setState(s.f[1],'idle');s:setState(s.f[2],'idle');return true end)()")
 hp=c.lua('GF_APP().scene.sim.f[2].hp');c.key('J',True)
 hit=False
 for _ in range(40):
  c.step()
  if c.lua("GF_APP().scene.sim.f[2].state=='hit'"):
   hit=True
   assert c.lua("GF_APP().scene.views[2]:poseFor()=='hurt'")
   for _ in range(12):
    c.step()
    if c.lua("GF_APP().scene.views[2].front and GF_APP().scene.views[2].front.key=='hurt'"):break
   assert c.lua("GF_APP().scene.views[2].front.key=='hurt'")
   c.render(OUT/f'training-hit-{device}-{canvas[0]}.png')
   break
 c.key('J',False);assert hit
 assert c.lua('GF_APP().scene.sim.f[2].hp')<hp
 c.run(1.4);assert c.lua("GF_APP().scene.sim.f[2].state=='idle'")
 c.lua("(function()local s=GF_APP().scene.sim;s.f[1].x=-50000;s.f[2].x=50000;s.f[2].hp=s.f[2].maxhp;s:setState(s.f[1],'idle');return true end)()")
 hp=c.lua('GF_APP().scene.sim.f[2].hp');c.key('J',True);c.run(.6);c.key('J',False)
 assert c.lua('GF_APP().scene.sim.f[2].hp')==hp
 c.key('W',True);c.run(.15);c.key('W',False);assert c.lua('GF_APP().scene.sim.f[1].y')>0;c.run(1)
 c.lua("(function()GF_APP().scene:openPause();return true end)()");c.step();assert c.lua('GF_APP().scene.paused')
 c.lua("(function()GF_APP().scene:closePause();return true end)()");c.step()
 c.lua("(function()GF_APP().scene:pausePick('restart');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 assert c.lua("GF_APP().scene.sim.f[1].key=='lumine' and GF_APP().scene.sim.f[2].key=='lawachurl'")
 # Raw sim replay tests complete snapshots/hash, unaffected by rendered-frame delay.
 replay=c.lua('''(function()local S=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_character_registry');local opts={chars={R.byKey.lumine,R.byKey.lawachurl},training=true,seed=21};local a=S.new(opts);local b=S.new(opts);for t=1,1200 do local m=(t%80<20 and 8 or t%80<40 and 4 or t%80==50 and 16 or 0);a:step(m,0);b:step(m,0);assert(a:hash()==b:hash());if t==600 then b=a:copy() end end;return a:hash() end)()''')
 results.append({'device':device,'canvas':canvas,'movement':True,'realHitHurtAndRecovery':True,'whiffNoDamage':True,'jump':True,'pause':True,'replay1200':replay,'stats':c.stats()})
 print(json.dumps(results[-1]),flush=True)
(OUT/'checks.json').write_text(json.dumps({'mockOnly':True,'results':results},indent=2),encoding='utf-8')

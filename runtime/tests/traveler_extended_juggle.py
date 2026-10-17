"""Actual timed ground catches, E relaunch and manual dash pursuit until protection."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-wind-fx-v27-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'genshin_fighter.lua'
def run():
 c=RuntimeClient();c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()local s=GF_APP().scene;s.sim.f[1].x=-9000;s.sim.f[2].x=9000;return true end)()');trace=[]
 def step():
  c.step();trace.append(dict(c.lua("(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];return {tick=s.sim.tick,move=a.moveId,state=a.state,air=a.airMoveId,hits=a.stats.hits,combo=b.combo,juggle=b.juggle,y=a.y,foeY=b.y,foeVy=b.vy,dist=b.x-a.x,invul=b.invul,cooldown=a.skillCd}end)()").items()))
 def until(expr,n=160):
  for _ in range(n):
   if c.lua('(function()local a,b=GF_APP().scene.sim.f[1],GF_APP().scene.sim.f[2];return '+expr+' end)()'):return
   step()
  (OUT/'verification/extended-failure.json').write_text(json.dumps(trace,indent=2),encoding='utf-8')
  raise AssertionError((expr,trace[-3:]))
 def press(k):c.key(k,True);step();c.key(k,False)
 def hits(n):until(f'a.stats.hits>={n}')
 def launcher(n):c.key('S',True);press('K');c.key('S',False);hits(n)
 press('J');hits(1);press('J');hits(2);launcher(3)
 press('E');hits(4)
 until("a.state=='idle'");press('U');until("b.y<=28000 and b.vy<0 and (a.state=='idle' or a.state=='dash' and a.t>=5)")
 press('J');hits(5);press('J');hits(6);launcher(7)
 press('U');until("b.y<=28000 and b.vy<0 and (a.state=='idle' or a.state=='dash' and a.t>=5)")
 press('J');hits(8);press('J');hits(9)
 press('SPACE');until("a.state=='air'");press('J');hits(10);press('G');hits(11)
 assert c.lua('GF_APP().scene.sim.f[2].juggle')==9
 assert c.lua('GF_APP().scene.sim.f[2].combo')==11
 assert c.lua('GF_APP().scene.sim.f[2].invul')>0
 before=c.lua('GF_APP().scene.sim.f[1].stats.hits');press('K')
 for _ in range(30):step()
 assert c.lua('GF_APP().scene.sim.f[1].stats.hits')==before
 assert c.max_instr<1000000,c.max_instr
 (OUT/'verification/extended-juggle.json').write_text(json.dumps({'realInput':True,'continuousCombo':11,'airborneHits':9,'usesAetherSupport':True,'protectionStopsNextAirHeavy':True,'maxInstructions':c.max_instr,'trace':trace},indent=2),encoding='utf-8')
 print('11-hit actual route reached protection; next air heavy denied')
if __name__=='__main__':run()

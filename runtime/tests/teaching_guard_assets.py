"""Real standing blocks must publish the revised body and recover cleanly."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/tutorial-guard-v23-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
RuntimeClient.source=OUT/'genshin_fighter.lua'
def run(device,hz,face):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()'+CHECK+'return true end)()')
 c.lua(f"(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x={-9000*face};b.x={9000*face};a.face={face};b.face={-face};a.hitstop=0;b.hitstop=0;a.inPrev=0;a.releaseMask=0;return true end)()")
 c.run(.2);hp=c.lua('GF_APP().scene.sim.f[1].hp')
 c.key('A' if face==1 else 'D',True)
 c.lua("(function()local s=GF_APP().scene;assert(s.sim:startMove(s.sim.f[2],'light1'));return true end)()")
 seen=False;blocked=False
 for tick in range(110 if hz==60 else 55):
  c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])')
  blocked=blocked or c.lua("GF_APP().scene.sim.f[1].state=='block'")
  if c.lua('GF_APP().scene.views[1].front.key')=='block_1':
   seen=True
   if device=='KeyboardAndMouse' and hz==60 and face==1:c.render(OUT/'verification/standing-block-runtime.png')
 c.key('A' if face==1 else 'D',False);c.run(.4)
 assert blocked and seen,(device,hz,face,blocked,seen)
 assert c.lua('GF_APP().scene.sim.f[1].hp')==hp
 assert c.lua('GF_APP().scene.views[1].front.key')=='teaching_master'
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'face':face,'realBlock':True,'publishedGeometryExact':True,'returnedToMaster':True,'maxInstructions':c.max_instr}
if __name__=='__main__':
 rows=[run(d,h,f)for d,h,f in [('KeyboardAndMouse',60,1),('KeyboardAndMouse',30,1),('Mobile',60,1),('Mobile',30,1),('KeyboardAndMouse',60,-1)]]
 (OUT/'verification/guard-assets.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 print(json.dumps(rows))

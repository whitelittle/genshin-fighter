"""Actual low/air move constructors and physical bindings publish the intended assets."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-low-air-v21-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
RuntimeClient.source=OUT/'genshin_fighter.lua'
GROUPS=['crouchLight','crouchHeavy','airLight','airHeavy']
def run(device,hz,face):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()'+CHECK+'return true end)()');results={}
 def reset():
  c.lua(f"(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x={-35000*face};b.x={35000*face};a.face={face};b.face={-face};a.y=0;a.vy=0;a.vx=0;a.airMove=nil;a.airMoveId=nil;a.hitstop=0;b.hitstop=0;a.inPrev=0;a.releaseMask=0;return true end)()")
  c.run(.2)
 for g in GROUPS:
  reset()
  # Use the real constructor with sufficient airtime to expose all four attack phases.
  c.lua("(function()local s=GF_APP().scene;local a=s.sim.f[1];"+("s.sim:setState(a,'air');a.y=80000;a.vy=0;" if g.startswith('air')else '')+f"assert(s.sim:startMove(a,'{g}'));return true end)()")
  seen=[]
  for tick in range(100 if hz==60 else 50):
   c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])');key=c.lua('GF_APP().scene.views[1].front.key')
   if key.startswith(g+'_') and key not in seen:
    seen.append(key)
    if device=='KeyboardAndMouse' and hz==60 and face==1:c.render(OUT/'verification'/f'{key}-runtime.png')
  assert set(seen)=={f'{g}_{i}'for i in range(4)},(g,device,hz,seen)
  results[g]=seen
 # Physical S+J/K and jump+J/K must select the same move IDs.
 for g in GROUPS:
  reset()
  if g.startswith('crouch'):c.key('S',True);c.run(.15)
  else:c.press('SPACE');c.run(.1)
  c.key('J'if g.endswith('Light')else 'K',True);c.step(1/hz)
  assert c.lua('GF_APP().scene.sim.f[1].'+('airMoveId'if g.startswith('air')else 'moveId'))==g,g
  c.key('J'if g.endswith('Light')else 'K',False);c.key('S',False)
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'face':face,'displayed':results,'geometryExact':True,'physicalBindings':True,'maxInstructions':c.max_instr}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--target');args=ap.parse_args()
 if args.target:OUT=ROOT/args.target;RuntimeClient.source=OUT/'genshin_fighter.lua'
 rows=[run(d,h,f)for d,h,f in [('KeyboardAndMouse',60,1),('KeyboardAndMouse',30,1),('Mobile',60,1),('Mobile',30,1),('KeyboardAndMouse',60,-1)]]
 result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'results':rows,'offlineOnly':True}
 (OUT/'verification/low-air-assets.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

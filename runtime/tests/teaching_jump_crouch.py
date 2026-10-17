"""Jump/crouch input must display the new approved-palette frames and clean ground roots."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-jump-v19-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
RuntimeClient.source=OUT/'genshin_fighter.lua'

def run(device,hz,face):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()'+CHECK+'return true end)()')
 c.lua(f"(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];a.x={-20000*face};b.x={20000*face};a.face={face};b.face={-face};return true end)()")
 c.run(.3);seen=[]
 c.key('SPACE',True)
 for tick in range(70 if hz==60 else 35):
  c.step(1/hz)
  if tick==1:c.key('SPACE',False)
  c.lua('checkBody(GF_APP().scene.views[1])')
  key=c.lua('GF_APP().scene.views[1].front.key')
  if key not in seen:
   seen.append(key)
   if device=='KeyboardAndMouse' and hz==60 and face==1:c.render(OUT/'verification'/f'{key}-jump.png')
 assert {f'jump_{i}'for i in [0,2,3,4,5]}<=set(seen),(device,hz,face,seen)
 assert c.lua('GF_APP().scene.sim.f[1].y==0 and GF_APP().scene.views[1].front.key=="teaching_master"')
 c.key('S',True);c.run(.25)
 assert c.lua('GF_APP().scene.sim.f[1].state=="crouch" and GF_APP().scene.views[1].front.key=="cblock_0"')
 c.lua('checkBody(GF_APP().scene.views[1])')
 c.render(OUT/'verification'/f'crouch-{device}-{hz}-{face}.png')
 c.key('S',False);c.run(.2)
 assert c.lua('GF_APP().scene.views[1].front.key=="teaching_master"')
 # Crouch guard must use the new crouch body as well, rather than the old skin.
 c.lua("(function()local s=GF_APP().scene;s.sim:setState(s.sim.f[1],'cblock');s.sim.f[1].stun=40;return true end)()")
 c.run(.15);assert c.lua('GF_APP().scene.views[1].front.key=="cblock_1"')
 c.lua('checkBody(GF_APP().scene.views[1])')
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'face':face,'actualJumpPoses':seen,'crouchAndGuardUseNewBody':True,'geometryExact':True,'maxInstructions':c.max_instr}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--target');args=ap.parse_args()
 if args.target:OUT=ROOT/args.target;RuntimeClient.source=OUT/'genshin_fighter.lua'
 rows=[run(d,h,f)for d,h,f in [('KeyboardAndMouse',60,1),('KeyboardAndMouse',30,1),('Mobile',60,1),('Mobile',30,1),('KeyboardAndMouse',60,-1)]]
 result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'results':rows,'offlineOnly':True}
 (OUT/'verification/jump-crouch.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

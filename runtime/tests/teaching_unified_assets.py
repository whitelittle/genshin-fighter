"""Check named asset provenance and actual displayed geometry, not only data loading."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-unified-v17-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
RuntimeClient.source=OUT/'genshin_fighter.lua'

def run(device,hz,face):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()'+CHECK+'return true end)()')
 def reset():
  c.lua(f"""(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x={-18000*face};b.x={18000*face};a.face={face};b.face={-face};a.vx=0;b.vx=0;a.hitstop=0;b.hitstop=0;a.inPrev=0;a.releaseMask=0;b.hp=1500;return true end)()""")
  c.run(.3)
 def capture(group,steps):
  seen=[]
  for i in range(steps):
   c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])')
   key=c.lua('GF_APP().scene.views[1].front.key')
   if key not in seen:seen.append(key)
   if key.startswith(group+'_') and device=='KeyboardAndMouse' and hz==60 and face==1 and key not in saved:
    c.render(OUT/'verification'/f'{key}-runtime.png');saved.add(key)
  return seen
 results={};saved=set()
 for group,key in [('walk','D' if face==1 else 'A'),('back','A' if face==1 else 'D')]:
  reset();c.key(key,True);seen=capture(group,80 if hz==60 else 40);c.key(key,False);c.run(.3)
  assert set(k for k in seen if k.startswith('walk_'))=={'walk_00','walk_02','walk_04','walk_06'},seen
  assert not any(k.startswith('back_')for k in seen),seen
  results[group]=seen
 reset();c.press('U');results['dash']=capture('dash',40 if hz==60 else 20)
 assert set(k for k in results['dash']if k.startswith('dash_'))=={f'dash_{i}'for i in range(4)},results['dash']
 for group in ['light1','light2','light3','heavy']:
  reset()
  # Start via the real move constructor. Full lesson/cancel logic has its own suite.
  c.lua(f"(function()local s=GF_APP().scene;s.sim:startMove(s.sim.f[1],'{group}');return true end)()")
  results[group]=capture(group,70 if hz==60 else 35)
  assert set(k for k in results[group]if k.startswith(group+'_'))=={f'{group}_{i}'for i in range(4)},(group,results[group])
  assert c.lua('GF_APP().scene.views[1].front.key')=='teaching_master'
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'face':face,'displayed':results,'allPublishedGeometryExact':True,'maxInstructions':c.max_instr}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--target');args=ap.parse_args()
 if args.target:OUT=ROOT/args.target;RuntimeClient.source=OUT/'genshin_fighter.lua'
 rows=[run(d,h,f)for d,h,f in [('KeyboardAndMouse',60,1),('KeyboardAndMouse',30,1),('Mobile',60,1),('Mobile',30,1),('KeyboardAndMouse',60,-1)]]
 result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'results':rows,'offlineOnly':True}
 (OUT/'verification/unified-assets.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result))

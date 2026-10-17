"""Verify actual walk buffer publication, teaching input and candidate preservation."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/tutorial-walk-v14-20261016'
ART=ROOT/'outputs/lumine-teaching-walk-20261016'
E=OUT/'verification'
sys.path.insert(0,str(ROOT/'runtime/tests'))
sys.path.insert(0,str(ROOT/'runtime/tools'))
from mock_flow import RuntimeClient,wait
from compact_assets import python_table

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def publication():
 rows=[]
 for device,hz,face in [('KeyboardAndMouse',60,1),('Mobile',60,1),('KeyboardAndMouse',30,1),('Mobile',30,1),('Mobile',60,-1)]:
  c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
  c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
  wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
  c.lua(f"(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x={-45000*face};b.x={65000*face};a.face={face};a.inPrev=0;a.releaseMask=0;return true end)()")
  c.run(.3);c.key('D' if face==1 else 'A',True)
  seen=[]
  for tick in range(80 if hz==60 else 40):
   c.step(1/hz)
   key=c.lua('GF_APP().scene.views[1].front and GF_APP().scene.views[1].front.key')
   if key and key.startswith('walk_0') and key not in seen:
    seen.append(key)
    if hz==60:c.render(E/f'walk-{device}-{face}-{key}.png')
  c.key('D' if face==1 else 'A',False);c.run(.3)
  actual=c.lua('GF_APP().scene.views[1].front.key')
  assert set(seen)=={'walk_00','walk_02','walk_04','walk_06'},(device,hz,face,seen)
  assert actual=='teaching_master',actual
  assert c.max_instr<1000000,c.max_instr
  rows.append({'device':device,'hz':hz,'face':face,'published':seen,'returnedToMaster':True,'maxInstructions':c.max_instr})
  print(json.dumps(rows[-1]),flush=True)
 return rows

def confirmation():
 # Run the established physical-input and lesson-confirmation checks on THIS build.
 source=ROOT/'runtime/tests/teaching_confirm.py';code=source.read_text(encoding='utf-8')
 code=code.replace("OUT=ROOT/'outputs/tutorial-polish-v12-20261016'", "OUT=ROOT/'outputs/tutorial-walk-v14-20261016'")
 exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'teaching_walk_confirm'})

def main():
 ap=argparse.ArgumentParser();ap.add_argument('suite',choices=['walk','rules','confirm','regression','flow']);args=ap.parse_args()
 E.mkdir(exist_ok=True);RuntimeClient.source=OUT/'genshin_fighter.lua'
 before=sha(RuntimeClient.source)
 if args.suite=='walk':result=publication()
 elif args.suite=='confirm':confirmation();result=True
 elif args.suite=='rules':
  c=RuntimeClient();result=python_table(c.lua('(function()'+(ROOT/'runtime/tests/teaching_complete_rules.lua').read_text(encoding='utf-8')+' end)()'))
 elif args.suite=='regression':
  import run
  run.CLIENT_OVERRIDE=RuntimeClient.source
  result={'logic':run.logic(),'pixels':run.pixels_and_views()}
 else:
  import mock_flow as flow
  flow.ROOT=OUT
  def wait_notice(c,expr,limit=2800):
   for _ in range(limit):
    c.step()
    if c.lua("GF_APP() and GF_APP().scene and GF_APP().sceneName=='notice' and GF_APP().scene.t>.4 and not GF_APP().trans"):c.press('J')
    if c.lua(expr):return
   raise AssertionError(expr)
  flow.wait=wait_notice
  result={'local':[flow.local_flow(d,s,(4,3)) for d,s in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600))]],'network':flow.network_flow((4,3))}
 assert before==sha(RuntimeClient.source)
 (E/(args.suite+'-passed.json')).write_text(json.dumps({'clientSha256':before,'passed':True,'offlineOnly':True,'result':result},ensure_ascii=False,indent=2),encoding='utf-8')
 print(args.suite+' passed',flush=True)

if __name__=='__main__':main()

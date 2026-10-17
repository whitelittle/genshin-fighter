"""Exercise the entire movement course through physical inputs, including dash reuse."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait
OUT=ROOT/'outputs/tutorial-input-v15-20261016'
RuntimeClient.source=OUT/'genshin_fighter.lua'

def run(hz=60):
 c=RuntimeClient()
 c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'movement','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 def probe(e):return c.lua('GF_APP().scene.'+e)
 def state():return {e:probe(e) for e in ['lesson.index','lesson.pending','lesson.briefTicks','sim.tick','sim.f[1].state','sim.f[1].x','sim.f[1].vx','sim.f[1].inPrev','sim.f[1].releaseMask']}
 def confirm():c.press('J');c.step()
 for index,key in [(1,'D'),(2,'A'),(3,'SPACE'),(4,'U')]:
  confirm();assert not probe('lesson:isSpeaking()'),state()
  c.run(.15)
  c.key(key,True)
  if key=='U':
   # Repeated Down notifications used to accumulate a permanently held dash.
   for _ in range(5):c.key(key,True)
  for _ in range(150):
   c.step(1/hz)
   if probe('lesson.pending')>0:break
   if index in (3,4) and _==2:c.key(key,False)
  if index in (1,2):c.key(key,False)
  c.step()
  assert probe('lesson.pending')>0,state()
  confirm()
 confirm();c.run(.2)
 assert c.lua('GF_APP().input:pad(1).held & 256')==0,'U remains held after one physical release'
 c.key('A',True);c.step();c.press('U');c.key('A',False)
 c.run(1)
 assert probe('lesson.pending')>0,state()
 c.render(OUT/'verification'/f'movement-complete-{hz}.png')
 confirm();confirm()
 # Pick free practice through the real completion menu, then reuse dash repeatedly.
 c.press('S');c.press('S');c.press('J');c.run(.2)
 assert probe('lesson.completeMenu==nil'),state()
 for key in ['U','U','A','U']:
  if key=='A':c.key('A',True);continue
  c.press(key)
  assert probe('sim.f[1].state') in ('dash','backdash'),state()
  c.run(.6)
 c.key('A',False);c.run(.2)
 # Aliases must remain held until BOTH physical keys have been released.
 c.key('E',True);c.key('I',True);c.key('E',False)
 assert c.lua('GF_APP().input:pad(1).held & 64')==64
 c.key('I',False);assert c.lua('GF_APP().input:pad(1).held & 64')==0
 assert c.max_instr<1000000,c.max_instr
 return {'hz':hz,'fullMovementCourse':True,'repeatedDownReleased':True,'repeatedForwardAndBackdash':True,'aliasesPreserved':True,'maxInstructions':c.max_instr}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',action='store_true');ap.add_argument('--target');args=ap.parse_args()
 if args.target:
  OUT=ROOT/args.target;RuntimeClient.source=OUT/'genshin_fighter.lua'
 if args.baseline:RuntimeClient.source=ROOT/'outputs/tutorial-walk-v14-20261016/genshin_fighter.lua'
 rows=[run(hz) for hz in (60,30)]
 result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'offlineOnly':True,'results':rows}
 (OUT/'verification/movement-input.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result))

"""Complete the four lessons with actual keys/touch, including a whiff denial."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-wind-combo-v26-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
RuntimeClient.source=OUT/'genshin_fighter.lua'
def run(device,hz):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'launcher','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()'+CHECK+'return true end)()')
 def step():c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])')
 def until(expr,n=240):
  for _ in range(n):
   if c.lua(expr):return
   step()
  raise AssertionError((device,hz,expr,c.lua('GF_APP().scene.lesson.extended.stage'),c.lua('GF_APP().scene.sim.f[1].state')))
 def direction(kind):
  if device=='Mobile':
   if kind:
    v=c.lua('(function()local a=GF_APP();return {a.cw/2+(-a.W/2+230)*a.s,a.ch/2+(-a.H/2+200)*a.s,a.s}end)()')
    c.touch('down',v[1],v[2],2);c.touch('drag',v[1]+(80*v[3]if kind=='D'else 0),v[2]-(70*v[3]if kind=='S'else 0),2)
   else:c.touch('up',0,0,2)
  else:
   for k in ['S','D']:c.key(k,k==kind)
 def press(key):
  if device=='Mobile':
   id={'J':'LP','K':'HP','SPACE':'UP'}[key]
   v=c.lua("(function()local a=GF_APP();for _,b in ipairs(a.scene.touch.buttons)do if b.id=='"+id+"'then return {a.cw/2+b.x*a.s,a.ch/2+b.y*a.s}end end end)()")
   c.touch('down',v[1],v[2],1);step();c.touch('up',v[1],v[2],1)
  else:c.key(key,True);step();c.key(key,False)
 def enter(index):
  c.lua(f'(function()GF_APP().scene.lesson:enter({index});return true end)()');step();c.press('J');step()
  assert not c.lua('GF_APP().scene.lesson:isSpeaking()')
 def hits(n):until(f'GF_APP().scene.sim.f[1].stats.hits>={n}')
 for index in [1,2,3,4]:
  enter(index);base=c.lua('GF_APP().scene.sim.f[1].stats.hits')
  if index==4:
   press('J');hits(base+1);press('J');hits(base+2);base+=2
  direction('S');press('K');direction(None);hits(base+1)
  if index>=2:
   direction('D');press('SPACE');until("GF_APP().scene.sim.f[1].state=='air'");direction(None)
  if index>=3:press('J');hits(base+2)
  if index==4:press('K');hits(base+3)
  until('GF_APP().scene.lesson.pending>0')
  if index==4:assert c.lua('GF_APP().scene.lesson.extended.stage')==5
  c.render(OUT/'verification'/f'juggle-{device}-{hz}-{index}.png')
 # Real whiff cannot cancel into chase; ordinary jumping only happens after recovery.
 enter(2)
 c.lua('(function()local s=GF_APP().scene;s.sim.f[1].x=-45000;s.sim.f[2].x=45000;return true end)()')
 direction('S');press('K');direction(None)
 for _ in range(25 if hz==60 else 13):step()
 press('SPACE');step()
 assert c.lua("GF_APP().scene.sim.f[1].state=='attack' and not GF_APP().scene.lesson.extended.jump and GF_APP().scene.lesson.pending==0")
 enter(2)
 c.lua("(function()GF_APP().scene.lesson.extended.input=function()return 2|8 end;return true end)()")
 direction('S');press('K');direction(None)
 until("GF_APP().scene.sim.f[2].state=='cblock'")
 press('SPACE');step()
 assert c.lua("GF_APP().scene.sim.f[1].state=='attack' and not GF_APP().scene.sim.f[1].trainingLaunchHit and GF_APP().scene.lesson.pending==0")
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'fourActualObjectives':True,'fiveHitsWithoutDrop':True,'whiffCannotJumpCancel':True,'blockCannotJumpCancel':True,'maxInstructions':c.max_instr}
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--target');args=ap.parse_args()
 if args.target:OUT=ROOT/args.target;RuntimeClient.source=OUT/'genshin_fighter.lua'
 rows=[run(d,h)for d,h in [('KeyboardAndMouse',60),('KeyboardAndMouse',30),('Mobile',60),('Mobile',30)]]
 (OUT/'verification/juggle-lessons.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))

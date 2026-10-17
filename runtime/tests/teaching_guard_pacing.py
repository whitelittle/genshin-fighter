"""Reaction delay, actual retreat whiff, dash punish and dash approach."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-guard-pacing-v25-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'genshin_fighter.lua'
def run(device,hz):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'guard','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 def probe(expr):return c.lua('(function()local sim=GF_APP().scene.sim;local lesson=GF_APP().scene.lesson;return '+expr+' end)()')
 def until(expr,n=500):
  for _ in range(n):
   if probe(expr):return
   c.step(1/hz)
  raise AssertionError((device,hz,expr,probe('lesson.coach.age')))
 def button(key,down):
  if device=='Mobile':
   id={'U':'DA','J':'LP'}[key]
   v=c.lua("(function()local a=GF_APP();for _,b in ipairs(a.scene.touch.buttons)do if b.id=='"+id+"'then return {a.cw/2+b.x*a.s,a.ch/2+b.y*a.s}end end end)()")
   c.touch('down'if down else 'up',v[1],v[2],1)
  else:c.key(key,down)
 def direction(back,on=True,low=False):
  if device=='Mobile':
   if on:
    v=c.lua('(function()local a=GF_APP();return {a.cw/2+(-a.W/2+230)*a.s,a.ch/2+(-a.H/2+200)*a.s,a.s}end)()')
    c.touch('down',v[1],v[2],2);c.touch('drag',v[1]+(-80 if back else 80)*v[3],v[2]-(70 if low else 0)*v[3],2)
   else:c.touch('up',0,0,2)
  else:
   c.key('A'if back else 'D',on)
   if low:c.key('S',on)
 def enter(i):
  c.lua(f'(function()GF_APP().scene.lesson:enter({i});return true end)()');c.step();c.press('J');c.run(.1)
  assert not probe('lesson:isSpeaking()')
 for i in [1,2]:
  enter(i)
  until('lesson.coach.age>=59')
  assert probe("sim.f[2].state=='idle'")
  until("sim.f[2].state=='attack'")
  assert probe('sim.f[2].move.startup')==(90 if i==1 else 96)
  until('sim.f[2].t>=sim.f[2].move.startup-3')
  direction(True,low=i==2);until('lesson.pending>0');direction(True,False,low=i==2)
  assert probe('lesson.coach.success')
 for i in [3,4]:
  enter(i);until("sim.f[2].state=='attack' and sim.f[2].t>=24")
  direction(True);until('sim.f[2].x-sim.f[1].x>=46000');direction(True,False)
  until('lesson.coach.missed')
  assert probe('sim.f[1].hp==sim.f[1].maxhp')
  if i==3:assert probe('lesson.pending>0')
  else:
   button('U',True);c.step(1/hz);button('U',False)
   assert probe("sim.f[1].state=='dash'")
   until("sim.f[1].state~='dash'")
   assert probe('sim.f[2].x-sim.f[1].x<=23000'),probe('sim.f[2].x-sim.f[1].x')
   button('J',True);c.step(1/hz);button('J',False);until('lesson.pending>0')
   assert probe('lesson.coach.success');c.render(OUT/'verification'/f'guard-punish-{device}-{hz}.png')
 # Enter the real approach lesson and verify it never freezes a live dash.
 c.lua("(function()GF_APP():travel('fight',{chars={'lumine','lawachurl'},mode='training',tutorial=true,lessonCourse='attack',seed=21});return true end)()")
 wait(c,"GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.press('J');c.run(.1)
 c.lua('(function()local s=GF_APP().scene;s.sim.f[1].x=-20000;s.sim.f[2].x=20000;return true end)()')
 button('U',True);c.step(1/hz);button('U',False);saw=False
 for _ in range(40):
  c.step(1/hz)
  if probe("sim.f[1].state=='dash'"):saw=True;assert probe('lesson.pending')==0
  if probe('lesson.pending>0'):break
 assert saw and probe('lesson.pending>0') and probe("sim.f[1].state~='dash'"),(saw,probe('lesson.pending'),probe('sim.f[2].x-sim.f[1].x'),probe('sim.f[1].state'))
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'readyDelay':True,'bothGuards':True,'retreatAfter24TickReaction':True,'dashPunish':True,'dashApproachFinishesBeforeFeedback':True,'maxInstructions':c.max_instr}
if __name__=='__main__':
 rows=[run(d,h)for d in ['KeyboardAndMouse','Mobile']for h in [60,30]]
 (OUT/'verification/guard-pacing.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))

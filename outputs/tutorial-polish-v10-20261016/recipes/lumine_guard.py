"""Native-input checks for the real defender, attack windows and punish lesson."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v10-20261016'
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'genshin_fighter.lua'
E=OUT/'verification';E.mkdir(exist_ok=True)
results=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'guard','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 def probe(expr):return c.lua('GF_APP().scene.'+expr)
 def point(x,y):
  p=c.lua(f'(function()local a=GF_APP();return {{a.cw/2+({x})*a.s,a.ch/2+({y})*a.s}}end)()')
  return p[1],p[2]
 def attack():
  if device=='Mobile':
   x,y=point('GF_APP().scene.touch.buttons[1].x','GF_APP().scene.touch.buttons[1].y')
   c.touch('down',x,y);c.step();c.touch('up',x,y);c.step()
  else:c.press('PAD_X' if device=='Controller' else 'J')
 def hold(keys,condition,limit=400):
  if device=='Mobile':
   x,y=point('-GF_APP().W/2+230','-GF_APP().H/2+200')
   x2,y2=point('-GF_APP().W/2+230'+(' - 80' if 'A' in keys else ' + 80'),'-GF_APP().H/2+200'+(' - 70' if 'S' in keys else ''))
   c.touch('down',x,y);c.touch('drag',x2,y2)
  elif device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(-1 if 'A' in keys else 1,-1 if 'S' in keys else 0)
  else:
   for key in keys:c.key(key,True)
  try:wait(c,'GF_APP().scene.'+condition,limit)
  finally:
   if device=='Mobile':c.touch('up',x2,y2)
   elif device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(0,0)
   else:
    for key in keys:c.key(key,False)
   c.step()
 def next_step(n):wait(c,f'GF_APP().scene.lesson.index=={n} and not GF_APP().scene.lesson:isBriefing()')
 # Wrong height really takes a hit, stays on the objective, then recovers to retry.
 hold(['A','S'],'lesson.coach.retry>0')
 assert probe('lesson.index')==1 and probe('lesson.pending')==0
 wait(c,'GF_APP().scene.lesson.coach.retry==0')
 hold(['A'],'lesson.pending>0')
 assert probe('sim.f[1].stats.blocks')>=1
 c.render(E/f'guard-standing-{device}-{canvas[0]}.png')
 # Pause must freeze the simulation-controlled next-line countdown and coach clock.
 c.lua('(function()GF_APP().scene:openPause();return true end)()')
 pending=probe('lesson.pending');age=probe('lesson.coach.age');c.run(.6)
 assert probe('lesson.pending')==pending and probe('lesson.coach.age')==age
 c.lua('(function()GF_APP().scene:closePause();return true end)()')
 next_step(2);hold(['A','S'],'lesson.pending>0')
 c.render(E/f'guard-crouching-{device}-{canvas[0]}.png')
 next_step(3);hold(['A'],'lesson.pending>0')
 assert probe('lesson.coach.missed')
 next_step(4)
 # Early hits do not complete a recovery punish; the full next attempt must work.
 attack();c.run(.35);assert probe('lesson.pending')==0
 # Restart this objective through its public lesson entry; no fake hit or completion.
 c.lua('(function()GF_APP().scene.lesson:enter(4);return true end)()')
 hold(['A'],'lesson.coach.missed')
 c.render(E/f'guard-whiff-{device}-{canvas[0]}.png')
 hold(['D'],'sim.f[2].x-GF_APP().scene.sim.f[1].x<=23000')
 attack()
 wait(c,'GF_APP().scene.lesson.pending>0')
 assert probe('lesson.coach.success')
 c.render(E/f'guard-punish-{device}-{canvas[0]}.png')
 next_step(5);assert c.lua('GF_APP().trainingCompleted.guard and GF_APP().scene.lesson.completeMenu~=nil')
 c.lua("(function()GF_APP().scene.lesson.completeMenu.o.onPick('retry');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.lesson.index==1 and not GF_APP().trans")
 assert probe('lesson.pending')==0 and not probe('lesson.coach.missed')
 row={'device':device,'canvas':canvas,'inputMethod':'touch stick drag and light button' if device=='Mobile' else 'controller axis and attack event' if device=='Controller' else 'keyboard events','wrongHeightHitDoesNotComplete':True,'standBlock':True,'crouchBlock':True,'realAttackWhiff':True,'earlyHitDoesNotCompletePunish':True,'realRecoveryPunish':True,'pauseStopsClock':True,'restartResets':True,'maxInstructions':c.max_instr}
 results.append(row);print(json.dumps(row),flush=True)
(E/'guard-checks.json').write_text(json.dumps({'sha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'mockOnly':True,'results':results},indent=2),encoding='utf-8')

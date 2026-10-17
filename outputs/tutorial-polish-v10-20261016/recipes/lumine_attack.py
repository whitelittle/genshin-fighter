"""Complete the five attack objectives through real device input routes."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v10-20261016'
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'genshin_fighter.lua';E=OUT/'verification';E.mkdir(exist_ok=True)
rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'attack','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 def probe(e):return c.lua('GF_APP().scene.'+e)
 def point(x,y):
  v=c.lua(f'(function()local a=GF_APP();return {{a.cw/2+({x})*a.s,a.ch/2+({y})*a.s}}end)()');return v[1],v[2]
 def press(heavy=False,hold=2):
  if device=='Mobile':
   button='HP' if heavy else 'LP'
   v=c.lua("(function()for _,b in ipairs(GF_APP().scene.touch.buttons)do if b.id=='"+button+"'then return {b.x,b.y}end end end)()")
   assert v is not None,button+' missing';x,y=point(v[1],v[2]);c.touch('down',x,y)
   for _ in range(hold):c.step()
   c.touch('up',x,y)
  else:
   key=('PAD_Y' if heavy else 'PAD_X') if device=='Controller' else ('K' if heavy else 'J')
   c.key(key,True)
   for _ in range(hold):c.step()
   c.key(key,False)
  c.step()
 def forward_until(expr):
  if device=='Mobile':
   x,y=point('-GF_APP().W/2+230','-GF_APP().H/2+200');xx,yy=point('-GF_APP().W/2+310','-GF_APP().H/2+200')
   c.touch('down',x,y);c.touch('drag',xx,yy)
  elif device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(1,0)
  else:c.key('D',True)
  wait(c,'GF_APP().scene.'+expr)
  if device=='Mobile':c.touch('up',xx,yy)
  elif device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(0,0)
  else:c.key('D',False)
  c.step()
 def next_step(n):wait(c,f'GF_APP().scene.lesson.index=={n} and not GF_APP().scene.lesson:isBriefing()')
 def idle():wait(c,"GF_APP().scene.sim.f[1].state=='idle' and GF_APP().scene.sim.f[2].state=='idle'")
 forward_until('lesson.pending>0');next_step(2)
 press(True);c.run(1.5);assert probe('lesson.pending')==0,'heavy completed light target'
 press();wait(c,'GF_APP().scene.lesson.pending>0');next_step(3)
 press(hold=55);assert probe('lesson.pending')==0,'held light auto completed combo'
 idle()
 for _ in range(3):press();c.run(1)
 assert probe('lesson.pending')==0,'three separate light1 hits completed combo'
 c.lua('(function()GF_APP().scene.lesson:enter(3);return true end)()')
 wait(c,'not GF_APP().scene.lesson:isBriefing()')
 for progress in [1,2,3]:
  press();wait(c,f'GF_APP().scene.lesson.attack.progress=={progress}')
  if progress==2:c.render(E/f'attack-combo-{device}-{canvas[0]}.png')
 assert probe('lesson.pending')>0;next_step(4)
 press();c.run(1);assert probe('lesson.pending')==0,'light completed heavy target'
 press(True);wait(c,'GF_APP().scene.lesson.pending>0');c.render(E/f'attack-heavy-{device}-{canvas[0]}.png');next_step(5)
 c.run(.3);assert probe('lesson.pending')==0,'idle completed whiff target'
 press();c.run(.7);assert probe('lesson.pending')==0,'light whiff completed heavy whiff target'
 press(True)
 wait(c,"GF_APP().scene.sim.f[1].state=='attack' and GF_APP().scene.sim.f[1].t>=32")
 assert probe('lesson.pending')==0,'whiff completed before recovery'
 c.render(E/f'attack-whiff-recovery-{device}-{canvas[0]}.png')
 c.lua('(function()GF_APP().scene:openPause();return true end)()');t=probe('sim.f[1].t');c.run(.5);assert probe('sim.f[1].t')==t
 c.lua('(function()GF_APP().scene:closePause();return true end)()')
 wait(c,'GF_APP().scene.lesson.pending>0');assert probe('sim.f[1].state')=='idle'
 next_step(6);assert c.lua('GF_APP().trainingCompleted.attack and GF_APP().scene.lesson.completeMenu~=nil')
 c.lua("(function()GF_APP().scene.lesson.completeMenu.o.onPick('retry');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.lesson.index==1 and not GF_APP().trans")
 assert probe('lesson.attack.progress')==0 and not probe('lesson.attack.whiffSaw')
 row={'device':device,'canvas':canvas,'actualFiveObjectives':True,'heavyCannotReplaceLight':True,'heldButtonCannotAutoCombo':True,'separateLightHitsCannotFakeCombo':True,'nativeLight1Light2Light3Combo':True,'lightCannotReplaceHeavy':True,'whiffRequiresFullRecovery':True,'pauseStopsRecovery':True,'restartClearsAttempt':True,'maxInstructions':c.max_instr,'stats':c.stats()}
 rows.append(row);print(json.dumps(row),flush=True)
(E/'attack-checks.json').write_text(json.dumps({'sha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'mockOnly':True,'results':rows},indent=2),encoding='utf-8')

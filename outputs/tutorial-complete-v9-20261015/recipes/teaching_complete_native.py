"""Finish every newly opened lesson through keyboard, touch and controller events."""
from teaching_complete import *
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--device',default='KeyboardAndMouse');ap.add_argument('--portrait',action='store_true');args=ap.parse_args()
device=args.device;canvas=(900,1600) if args.portrait else (1600,900)
c=RuntimeClient(device=device,canvas=canvas)
c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'low','seed':21})
def probe(e):return c.lua('(function()local s=GF_APP().scene;local sim,lesson=s.sim,s.lesson;return '+e+' end)()')
def until(e,limit=1200):wait(c,"(function()local a=GF_APP();if not a or not a.scene then return false end;local s=a.scene;local sim,lesson,state,args=s.sim,s.lesson,s.state,s.args;return "+e+" end)()",limit)
def point(x,y):
 v=c.lua(f'(function()local a=GF_APP();return {{a.cw/2+({x})*a.s,a.ch/2+({y})*a.s}}end)()');return v[1],v[2]
stick=None
def dirs(dx=0,dy=0):
 global stick
 if device=='Mobile':
  if stick:c.touch('up',*stick);stick=None
  if dx or dy:
   x,y=point('-GF_APP().W/2+230','-GF_APP().H/2+200');xx,yy=point(f'-GF_APP().W/2+230+({dx})*80',f'-GF_APP().H/2+200+({dy})*75')
   c.touch('down',x,y);c.touch('drag',xx,yy);stick=(xx,yy)
 elif device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(dx,dy)
 else:
  for key in ['W','A','S','D']:c.key(key,False)
  if dx:c.key('D' if dx>0 else 'A',True)
  if dy:c.key('W' if dy>0 else 'S',True)
def pulse(action,dx=0,dy=0):
 dirs(dx,dy)
 if device=='Mobile':
  button={'light':'LP','heavy':'HP','skill':'SK','burst':'BU','throw':'TH','support':'AS','jump':'UP'}[action]
  v=c.lua("(function()for _,b in ipairs(GF_APP().scene.touch.buttons)do if b.id=='"+button+"'then return {b.x,b.y}end end end)()")
  assert v is not None,button+' missing';x,y=point(v[1],v[2]);c.touch('down',x,y,tid=1);c.step();c.touch('up',x,y,tid=1)
 elif device=='Controller':
  if action=='throw':
   c.H.fireKey(c.root,'ControllerCharacterSkill4KeyDown');c.step();c.H.fireKey(c.root,'ControllerCharacterSkill4KeyUp')
  elif action=='support':c.key('PAD_B',True);c.key('PAD_Y',True);c.step();c.key('PAD_Y',False);c.key('PAD_B',False)
  else:
   key={'light':'PAD_X','heavy':'PAD_Y','skill':'PAD_E','burst':'PAD_Q','jump':'PAD_A'}[action];c.key(key,True);c.step();c.key(key,False)
 else:
  key={'light':'J','heavy':'K','skill':'E','burst':'Q','throw':'L','support':'G','jump':'SPACE'}[action];c.key(key,True);c.step();c.key(key,False)
 dirs();c.step()
until("state=='run' and sim.phase=='fight' and not GF_APP().trans")
rows=[]
courses=['low','air','skill','burst','assist','throw','side','anemo','geo','electro','dendro','hydro','pyro','cryo']
for course in courses:
 if course!='low':
  c.lua("(function()GF_APP():travel('fight',{chars={'lumine','lawachurl'},mode='training',tutorial=true,lessonCourse='"+course+"',seed=21});return true end)()")
  until("args.lessonCourse=='"+course+"' and state=='run' and sim.phase=='fight' and not GF_APP().trans")
 count=probe('#lesson.lessons') if False else c.lua('#GF_APP().scene.lesson.lessons')
 for index in range(1,count+1):
  until(f'lesson.index=={index}')
  kind=probe('lesson.lessons[lesson.index].kind')
  if kind=='crouchLight' or kind=='crouchHeavy':pulse('light' if kind=='crouchLight' else 'heavy',dy=-1)
  elif kind=='airLight' or kind=='airHeavy':pulse('jump');until("sim.f[1].state=='air'");pulse('light' if kind=='airLight' else 'heavy')
  elif kind in ['skill','skillUp','skillDown']:pulse('skill',dy=1 if kind=='skillUp' else -1 if kind=='skillDown' else 0)
  elif kind=='skillCooldown':pulse('skill');assert probe('lesson.extended.rejected');until('sim.f[1].skillCd==0');pulse('skill')
  elif kind.startswith('burst'):pulse('burst')
  elif kind=='supportCooldown':pulse('support');assert probe('lesson.extended.rejected');until('sim.assistCd==0');pulse('support')
  elif kind.startswith('support'):
   pulse('support')
   if kind=='supportHit':until('sim.assist and sim.assist.t>=25');c.render(E/f'support-{device}-{canvas[0]}.png')
  elif kind=='throwTech':until("sim.f[1].state=='thrown'");pulse('throw')
  elif kind.startswith('throw'):pulse('throw')
  elif kind.startswith('cross'):
   dirs(1 if kind=='crossRight' else -1,1);c.step();until("sim.f[1].state=='air'");dirs();c.step()
  elif kind=='sideGuard':dirs(1,0)
  elif kind=='reaction':
   branch=probe('lesson.lessons[lesson.index].branch');pulse('skill',dy=1 if branch=='skillUp' else -1 if branch=='skillDown' else 0)
   if probe('lesson.lessons[lesson.index].chain'):
    until('lesson.extended.chainReady');until("sim.f[1].state=='idle'");pulse('skill')
  elif kind=='pickup':pulse('skill');until('#sim.crystals>0');until("sim.f[1].state=='idle'");dirs(1,0)
  elif kind=='shield':pass
  elif kind=='shatter':pulse('skill');until("sim.f[1].state=='idle'");pulse('heavy')
  else:raise AssertionError(kind)
  try:until('lesson.pending>0',1000)
  except Exception:
   c.render(E/f'FAILED-{device}-{canvas[0]}.png')
   print('FAILED OBJECTIVE',course,index,kind,probe('sim.f[1].state'),probe('sim.f[1].moveId'),probe('lesson.extended.label'),flush=True)
   raise
  dirs();c.step()
  if index==1 or kind in ['throwTech','sideGuard','pickup','shatter']:
   c.render(E/f'{course}-{kind}-{device}-{canvas[0]}.png')
  # Pausing cannot move the objective, support timer or reaction objects.
  if index==1:
   c.lua('(function()GF_APP().scene:openPause();return true end)()');tick=probe('sim.tick');c.run(.15);assert probe('sim.tick')==tick;c.lua('(function()GF_APP().scene:closePause();return true end)()')
 until('lesson.completeMenu~=nil')
 assert c.lua("GF_APP().trainingCompleted['"+course+"']")
 rows.append({'course':course,'objectives':count,'completed':True})
 print(json.dumps({'device':device,'canvas':canvas,'course':course,'passed':True}),flush=True)
c.lua("(function()GF_APP():travel('fight',{chars={'lumine','lawachurl'},mode='training',seed=21});return true end)()")
until("state=='run' and sim.phase=='fight' and not GF_APP().trans")
assert c.lua('GF_APP().scene.lesson==nil and GF_APP().scene.trainingView~=nil')
pulse('support');until('sim.assist and sim.assist.t>=25')
assert c.lua('(function()for _,b in ipairs(GF_APP().scene.trainingView.support)do if b.node.act and b.used>0 then return true end end;return false end)()'),'free room support invisible'
c.render(E/f'free-support-{device}-{canvas[0]}.png')
assert c.max_instr<1000000,c.max_instr
result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'device':device,'canvas':canvas,'allObjectivesThroughInput':rows,'freeRoomSupportVisible':True,'maxMockInstructions':c.max_instr,'stats':c.stats(),'scope':'native-control mock, not physical device acceptance'}
(E/f'complete-native-{device}-{canvas[0]}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True),flush=True)

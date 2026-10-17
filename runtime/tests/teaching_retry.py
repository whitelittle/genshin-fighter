"""Real failed attempts keep feedback visible without reopening the dialogue."""
from teaching_complete import *
rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas)
 def enter(course,index):
  c.lua("(function()GF_APP():travel('fight',{chars={'lumine','lawachurl'},mode='training',tutorial=true,lessonCourse='"+course+"',seed=21});return true end)()")
  wait(c,"GF_APP().scene and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
  c.lua(f'(function()GF_APP().scene.lesson:enter({index});return true end)()')
  wait(c,'not GF_APP().scene.lesson:isBriefing()')
 def pulse(key):
  if device=='Mobile':
   button={'J':'LP','E':'SK'}[key]
   v=c.lua("(function()local a=GF_APP();for _,b in ipairs(a.scene.touch.buttons)do if b.id=='"+button+"'then return {a.cw/2+b.x*a.s,a.ch/2+b.y*a.s}end end end)()")
   c.touch('down',v[1],v[2]);c.step();c.touch('up',v[1],v[2]);c.step()
  else:
   k=({'J':'PAD_X','E':'PAD_E'}[key] if device=='Controller' else key)
   c.press(k)
 def feedback(needle,name):
  wait(c,"GF_APP().scene.lesson.retryText and GF_APP().scene.lesson.retryTicks>0")
  c.step()
  assert c.lua("GF_APP().scene.lesson.retryText").find(needle)>=0
  assert c.lua('GF_APP().scene.hud.root.act and not GF_APP().scene.lesson.avatar.node.act and not GF_APP().scene.lesson.dialogue.node.act')
  assert c.lua('GF_APP().scene.lesson.pending')==0
  # The message is rendered, rather than merely stored on the lesson object.
  assert any(needle in str(it[16]).replace('\n','') for _,it in c.snapshot().items())
  c.render(E/f'retry-{name}-{device}-{canvas[0]}.png')
 wait(c,"GF_APP() and GF_APP().sceneName=='intro' and not GF_APP().poolNext")
 enter('guard',1);feedback('看清上段','guard')
 left=c.lua('GF_APP().scene.lesson.retryTicks');c.lua('(function()GF_APP().scene:openPause();return true end)()');c.run(.3);assert c.lua('GF_APP().scene.lesson.retryTicks')==left;c.lua('(function()GF_APP().scene:closePause();return true end)()')
 enter('attack',3);pulse('J');wait(c,'GF_APP().scene.lesson.attack.progress==1');feedback('间隔有点久','combo')
 enter('anemo',2);pulse('E');feedback('指定方向','reaction')
 wait(c,"GF_APP().scene.sim.f[1].skillCd==0 and GF_APP().scene.sim.f[1].state=='idle'");assert c.lua('GF_APP().scene.sim.f[2].aura')=='hydro'
 c.lua('(function()GF_APP().scene.lesson:enter(1);return true end)()');assert c.lua('GF_APP().scene.lesson.retryText==nil and GF_APP().scene.lesson.retryTicks==0')
 # Free-room support uses a separate drawing helper. Exercise the real exit path.
 for attempt in range(3):
  c.lua("(function()GF_APP():travel('fight',{chars={'lumine','lawachurl'},mode='training',seed=21});return true end)()")
  wait(c,"GF_APP().scene and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
  c.lua("(function()local s=GF_APP().scene;local x=s.trainingView;local old=x.free;GF_CLEANUP=false;x.free=function(self)old(self);GF_CLEANUP=true end;s.sim.phase='fight';s.sim.freeze=0;s.sim:setState(s.sim.f[1],'idle');s.sim.assistCd=0;s.sim:callSupport();s.trainingView:drawWorld();return true end)()")
  assert c.lua('GF_APP().scene.trainingView.support~=nil')
  c.lua("(function()GF_APP():travel('trainingcourses');return true end)()")
  wait(c,"GF_APP().sceneName=='trainingcourses' and not GF_APP().trans")
  assert c.lua('GF_CLEANUP')
 row={'device':device,'canvas':canvas,'guardComboWrongBranchFeedback':True,'retryKeepsHudAndControls':True,'pauseFreezesHint':True,'nextTargetClearsHint':True,'supportExitCleanupThreeTimes':True,'maxInstructions':c.max_instr};rows.append(row);print(json.dumps(row),flush=True)
(E/'retry-checks.json').write_text(json.dumps({'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'mockOnly':True,'results':rows},indent=2),encoding='utf-8')

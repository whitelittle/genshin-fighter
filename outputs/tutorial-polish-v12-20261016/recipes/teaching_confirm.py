"""Speech stays until explicit physical input; confirmation cannot attack."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v12-20261016';E=OUT/'verification';E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'genshin_fighter.lua'
rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'movement','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 def probe(e):return c.lua('GF_APP().scene.'+e)
 def confirm():
  if device=='Mobile':
   v=c.lua("(function()local a=GF_APP();local b=a.scene.lesson.dialogue.taps['speech-confirm'];return {a.cw/2+b.x*a.s,a.ch/2+b.y*a.s}end)()")
   c.touch('down',v[1],v[2]);c.step();c.touch('up',v[1],v[2]);c.step()
  else:c.press('PAD_A' if device=='Controller' else 'J')
 c.run(8);assert probe('lesson:isSpeaking()') and probe('lesson.index')==1
 c.render(E/f'confirm-wait-{device}-{canvas[0]}.png')
 tick=probe('sim.tick');c.run(.4);assert probe('sim.tick')==tick
 confirm();c.run(.2)
 assert not probe('lesson:isSpeaking()') and probe('hud.root.act')
 assert probe('sim.f[1].state')=='idle','confirm became an attack or jump'
 assert not probe('lesson.avatar.node.act')
 if device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(1,0)
 elif device=='Mobile':
  v=c.lua('(function()local a=GF_APP();return {a.cw/2+(-a.W/2+230)*a.s,a.ch/2+(-a.H/2+200)*a.s,a.s}end)()');x,y,s=v[1],v[2],v[3];c.touch('down',x,y);c.touch('drag',x+80*s,y)
 else:c.key('D',True)
 wait(c,'GF_APP().scene.lesson.pending>0')
 if device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(0,0)
 elif device=='Mobile':c.touch('up',x+80*s,y)
 else:c.key('D',False)
 c.run(8);assert probe('lesson.index')==1 and probe('lesson:isSpeaking()')
 c.render(E/f'confirm-feedback-{device}-{canvas[0]}.png')
 confirm();c.step();assert probe('lesson.index')==2 and probe('lesson:isBriefing()')
 c.run(7);assert probe('lesson:isSpeaking()')
 confirm();c.step();assert not probe('lesson:isSpeaking()')
 # First-course dash is a full visible movement before success feedback freezes play.
 c.lua('(function()GF_APP().scene.lesson:enter(4);return true end)()');c.step();confirm();c.step()
 x0=probe('sim.f[1].x')
 if device=='Mobile':
  v=c.lua("(function()local a=GF_APP();for _,b in ipairs(a.scene.touch.buttons)do if b.id=='DA'then return {a.cw/2+b.x*a.s,a.ch/2+b.y*a.s}end end end)()")
  c.touch('down',v[1],v[2]);c.step();c.touch('up',v[1],v[2]);c.step()
 else:c.press('PAD_B' if device=='Controller' else 'U')
 wait(c,'GF_APP().scene.lesson.pending>0')
 distance=(probe('sim.f[1].x')-x0)/100
 assert distance>=180 and probe('sim.f[1].state')!='dash'
 c.render(E/f'dash-complete-{device}-{canvas[0]}.png')
 # Completed course also waits for confirmation before menu navigation.
 c.lua('(function()GF_APP().scene.lesson:enter(6);return true end)()');c.step();c.run(7);assert probe('lesson:isSpeaking()');confirm();c.step();assert not probe('lesson:isSpeaking()') and probe('lesson.completeMenu~=nil')
 row={'device':device,'canvas':canvas,'introAndFeedbackWaitForConfirm':True,'clickOrPhysicalConfirm':True,'speechFreezesCombat':True,'confirmDoesNotAttackOrJump':True,'nextIntroRequiresOwnConfirm':True,'completionMenu':True,'fullForwardDashDistance':distance,'maxInstructions':c.max_instr};rows.append(row);print(json.dumps(row),flush=True)
(E/'confirm-checks.json').write_text(json.dumps({'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'mockOnly':True,'results':rows},indent=2),encoding='utf-8')

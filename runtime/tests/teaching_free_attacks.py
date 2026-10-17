"""Physical attacks after the actual course completion/free-practice menu."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
def run(out,course,hz=60):
 RuntimeClient.source=out/'genshin_fighter.lua'
 c=RuntimeClient(device='KeyboardAndMouse',canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':course,'seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()local l=GF_APP().scene.lesson;l:enter(#l.lessons+1);return true end)()');c.step();c.press('J');c.step()
 pos=c.lua('(function()local a=GF_APP();local m=a.scene.lesson.completeMenu;return {a.cw/2+m.o.x*a.s,a.ch/2+m:rowY(3)*a.s}end)()')
 c.touch('down',pos[1],pos[2]);c.step();c.touch('up',pos[1],pos[2]);c.run(.2)
 assert c.lua('GF_APP().scene.lesson.completeMenu==nil and not GF_APP().scene.lesson:isSpeaking()')
 c.lua('(function()'+CHECK+'return true end)()');rows=[]
 for name,pre,attack,delay in [('crouchLight','S','J',5),('crouchHeavy','S','K',5),('airLight','SPACE','J',5),('airHeavy','SPACE','K',5),('airLight','SPACE','J',0),('airHeavy','SPACE','K',0)]:
  # Only reposition between independent cases; preserve all input and move state.
  c.run(1.3)
  c.lua("(function()local s=GF_APP().scene;s.sim.f[1].x=-35000;s.sim.f[2].x=35000;return true end)()")
  c.key(pre,True)
  for _ in range(delay):c.step(1/hz)
  c.key(attack,True);seen=[];states=[]
  for _ in range(55 if hz==60 else 28):
   c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])')
   key=c.lua('GF_APP().scene.views[1].front.key')
   if key not in seen:seen.append(key)
   state=c.lua("(function()local p=GF_APP().scene.sim.f[1];return p.state..':'..tostring(p.moveId)..':'..tostring(p.airMoveId)end)()")
   if state not in states:states.append(state)
  c.key(pre,False);c.key(attack,False);c.run(.3)
  rows.append({'expected':name,'delay':delay,'seen':seen,'states':states,'passed':any(k.startswith(name+'_')for k in seen)})
 return {'course':course,'hz':hz,'cases':rows}
def quick_touch(out,device='Mobile',hz=60,free=False):
 RuntimeClient.source=out/'genshin_fighter.lua'
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'low','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.press('J');c.run(.2)
 if free:
  c.lua('(function()local l=GF_APP().scene.lesson;l:enter(#l.lessons+1);return true end)()');c.step();c.press('J');c.step()
  v=c.lua('(function()local a=GF_APP();local m=a.scene.lesson.completeMenu;return {a.cw/2+m.o.x*a.s,a.ch/2+m:rowY(3)*a.s}end)()')
  c.touch('down',v[1],v[2]);c.step();c.touch('up',v[1],v[2]);c.run(.2)
 def tap(id):
  if device=='Mobile':
   v=c.lua("(function()local a=GF_APP();for _,b in ipairs(a.scene.touch.buttons)do if b.id=='"+id+"'then return {a.cw/2+b.x*a.s,a.ch/2+b.y*a.s}end end end)()")
   c.touch('down',v[1],v[2]);c.touch('up',v[1],v[2])
  else:
   key={'UP':'SPACE','LP':'J','HP':'K'}[id];c.key(key,True);c.key(key,False)
 rows=[]
 c.lua('(function()'+CHECK+'return true end)()')
 for attack in ['LP','HP']:
  for simultaneous in [False,True]:
   c.run(1.4)
   c.lua('(function()local s=GF_APP().scene;s.sim.f[1].x=-35000;s.sim.f[2].x=35000;return true end)()')
   tap('UP')
   if simultaneous:tap(attack)
   c.step(1/hz);jump=c.lua("GF_APP().scene.sim.f[1].state=='jumpsq'")
   if not simultaneous:c.run(.12);tap(attack);c.step(1/hz)
   group='airLight' if attack=='LP' else 'airHeavy';seen=False;swings=0
   for _ in range(60 if hz==60 else 30):
    c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])')
    key=c.lua('GF_APP().scene.views[1].front.key')
    if key.startswith(group+'_'):
     seen=True
     if device=='Mobile' and hz==60 and not simultaneous:c.render(out/'verification'/f'quick-{free}-{group}.png')
    swings+=c.lua("(function()local n=0;for _,e in ipairs(GF_APP().scene.sim.events)do if e.type=='swing' and e.p==1 then n=n+1 end end;return n end)()")
   rows.append({'move':group,'simultaneous':simultaneous,'jump':jump,'visible':seen})
 return {'device':device,'hz':hz,'free':free,'cases':rows,'maxInstructions':c.max_instr}
def snapshot_cases(out):
 RuntimeClient.source=out/'genshin_fighter.lua';c=RuntimeClient()
 count=c.lua("""(function()
 local S=GF_REQUIRE('gf_sim_lumine_training');local R=GF_REQUIRE('gf_character_registry');local n=0
 for _,m in ipairs({17,33,49})do
  local s=S.new({chars={R.byKey.lumine,R.byKey.lawachurl},training=true,seed=21});s.phase='fight';s.freeze=0
  for _,p in ipairs(s.f)do s:setState(p,'idle')end
  s:step(m,0);assert(s.f[1].state=='jumpsq' and s.f[1].trainingJumpAttack)
  local snap=S.snapshot(s)
  for i=1,65 do s:step(0,0);snap:step(0,0);assert(s:hash()==snap:hash())end
  assert(s.f[1].airMoveId==(m&32~=0 and 'airHeavy' or 'airLight'));n=n+1
 end
 return n end)()""")
 (out/'verification/same-tick-snapshots.json').write_text(json.dumps({'passed':True,'cases':count}),encoding='utf-8')
 return count
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--target',default='outputs/tutorial-guard-v23-20261017');a=ap.parse_args();out=ROOT/a.target
 rows=[run(out,g)for g in ['movement','low','air','guard']]
 quick=[quick_touch(out,d,h,f)for d in ['Mobile','KeyboardAndMouse']for h in [30,60]for f in [False,True]]
 rows.extend(quick)
 (out/'verification/free-attacks.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))
 assert all(c['passed'] for r in rows if 'course'in r for c in r['cases'])
 assert all(c['jump'] and c['visible'] for r in quick for c in r['cases'])
 assert all(r['maxInstructions']<1000000 for r in quick)
 assert snapshot_cases(out)==3

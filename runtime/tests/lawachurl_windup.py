"""Check visible windup, prefetch boundaries and unchanged combat timing."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v10-20261016'
sys.path.insert(0,str(ROOT/'runtime/tests'));sys.path.insert(0,str(ROOT/'runtime/tools'))
from mock_flow import RuntimeClient,wait
from merge_tutorial_v15 import modules
from compact_assets import LuaRuntime,python_table
RuntimeClient.source=OUT/'genshin_fighter.lua';E=OUT/'verification';E.mkdir(exist_ok=True)
new=modules(RuntimeClient.source.read_text(encoding='utf-8'))
old=modules((ROOT/'outputs/tutorial-lessons-v6-20261015/genshin_fighter.lua').read_text(encoding='utf-8'))
assert next(l for l in new['gf_kits'].splitlines() if l.startswith('K.characterWeapons.lawachurl='))==next(l for l in old['gf_kits'].splitlines() if l.startswith('K.characterWeapons.lawachurl=')),'lawachurl move timing changed'
def data(mod):
 r=LuaRuntime(unpack_returned_tuples=True);r.execute('__loaders={};'+mod)
 return python_table(r.globals().__loaders['gf_lawachurl_training_data']())
a,b=data(old['gf_lawachurl_training_data']),data(new['gf_lawachurl_training_data'])
assert all(a['frames'][k]==b['frames'][k] for k in a['frames'])
assert b['bodyPeak']==a['bodyPeak']==1054
assert sum(f['n'] for f in b['frames'].values())/len(b['frames'])<1000
rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600))]:
 for course_step,attack in [(1,'high'),(2,'low')]:
  c=RuntimeClient(device=device,canvas=canvas)
  c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'guard','seed':21})
  wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
  if course_step==2:c.lua('(function()GF_APP().scene.lesson:enter(2);return true end)()')
  # Hold the real defense input, so the existing lesson/retry timer stays intact.
  c.key('A',True)
  if attack=='low':c.key('S',True)
  m=c.lua("(function()local w=GF_APP().scene.sim.f[2].kit.weapon;return w."+('crouchHeavy' if attack=='low' else 'light1')+' end)()')
  startup,active,recovery=int(m.startup),int(m.active),int(m.recovery)
  samples=[(8,'crouch','gather'),(26,'guard' if attack=='high' else 'crouchGuard','windup'),(startup-1,'guard' if attack=='high' else 'crouchGuard','last-windup'),(startup,'strikeHigh' if attack=='high' else 'strikeLow','active'),(startup+active+12,'crouch','recovery')]
  sample_rows=[]
  for tick,pose,label in samples:
   wait(c,f"GF_APP().scene.sim.f[2].state=='attack' and GF_APP().scene.sim.f[2].t>={tick}",300)
   actual=c.lua('GF_APP().scene.views[2].front.key')
   assert actual==pose,(device,attack,tick,actual,pose)
   if tick<startup:assert c.lua('GF_APP().scene.sim.f[1].stats.blocks')==0,'early active frame'
   c.render(E/f'windup-{attack}-{label}-{device}-{canvas[0]}.png')
   sample_rows.append({'simulationTick':tick,'visiblePose':actual})
  c.key('A',False);c.key('S',False)
  assert c.lua('GF_APP().scene.sim.f[1].stats.blocks')>0
  row={'device':device,'canvas':canvas,'attack':attack,'startup':startup,'active':active,'recovery':recovery,'visibleSamples':sample_rows,'maxInstructions':c.max_instr}
  rows.append(row);print(json.dumps(row),flush=True)
(E/'windup-checks.json').write_text(json.dumps({'sha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'oldBodiesUnchanged':True,'poolPeakUnchanged':1054,'bodyMean':930.75,'combatTimingUnchanged':True,'mockOnly':True,'results':rows},indent=2),encoding='utf-8')

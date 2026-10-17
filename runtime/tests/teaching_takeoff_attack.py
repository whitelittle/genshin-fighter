"""Reproduce quick jump+attack presses using normal physical jump height."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-air-input-v22-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
def run(device,hz,face):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()'+CHECK+'return true end)()');rows=[]
 for attack in ['J','K']:
  group='airLight' if attack=='J' else 'airHeavy'
  for delay in [1,2,3,4,5,6,10,20]:
   c.lua(f"(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x={-35000*face};b.x={35000*face};a.face={face};b.face={-face};a.y=0;a.vy=0;a.vx=0;a.airMove=nil;a.airMoveId=nil;a.trainingJumpAttack=nil;a.inPrev=0;a.releaseMask=0;a.hitstop=0;b.hitstop=0;return true end)()")
   c.run(.15);c.key('SPACE',True)
   for _ in range(delay):c.step(1/hz)
   before=c.lua('GF_APP().scene.sim.f[1].state')
   c.key(attack,True);c.step(1/hz);c.key(attack,False);c.key('SPACE',False)
   seen=[];triggered=False
   for tick in range(65 if hz==60 else 33):
    c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])')
    if c.lua('GF_APP().scene.sim.f[1].airMoveId')==group:triggered=True
    key=c.lua('GF_APP().scene.views[1].front.key')
    if key.startswith(group+'_') and key not in seen:
     seen.append(key)
     if delay==1 and device=='KeyboardAndMouse' and hz==60 and face==1:c.render(OUT/'verification'/f'takeoff-{key}.png')
   # Decide from actual simulated state, rather than guessing airtime from display Hz.
   if before not in ('air','jumpsq'):assert not triggered
   else:assert triggered and seen,(device,hz,attack,delay,seen)
   rows.append({'key':attack,'delayDisplayFrames':delay,'airTriggered':triggered,'seen':seen})
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'face':face,'normalJumpHeight':True,'geometryExact':True,'cases':rows,'maxInstructions':c.max_instr}
LUA='''
local S=GF_REQUIRE('gf_sim_lumine_training');local R=GF_REQUIRE('gf_character_registry')
local function make()local s=S.new({chars={R.byKey.lumine,R.byKey.lawachurl},training=true,seed=21});s.phase='fight';s.freeze=0;for _,p in ipairs(s.f)do s:setState(p,'idle')end;return s end
local count=0
for _,attack in ipairs({16,32,48})do
 for delay=1,4 do
  local s=make();s:step(1,0);for i=2,delay do s:step(1,0)end
  s:step(1|attack,0)
  local snap=S.snapshot(s);assert(s:hash()==snap:hash())
  local saved=s.f[1].trainingJumpAttack
  if saved then s.f[1].trainingJumpAttack=saved==16 and 32 or 16;assert(s:hash()~=snap:hash());s.f[1].trainingJumpAttack=saved end
  for i=1,45 do s:step(0,0);snap:step(0,0);assert(s:hash()==snap:hash(),'rollback mismatch')end
  assert(s.f[1].airMoveId==(attack&32~=0 and 'airHeavy' or 'airLight'))
  assert(not s.f[1].trainingJumpAttack);count=count+1
 end
end
-- Interruption must discard a pending press rather than firing it on a later jump.
local s=make();s:step(1,0);s:step(17,0);assert(s.f[1].trainingJumpAttack==16);s:setState(s.f[1],'hit');s.f[1].stun=10;s:step(0,0);assert(not s.f[1].trainingJumpAttack)
return count
'''
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--target');a=ap.parse_args()
 if a.target:OUT=ROOT/a.target
 RuntimeClient.source=OUT/'genshin_fighter.lua'
 rows=[run(d,h,f)for d,h,f in [('KeyboardAndMouse',60,1),('KeyboardAndMouse',30,1),('Mobile',60,1),('Mobile',30,1),('KeyboardAndMouse',60,-1)]]
 c=RuntimeClient();rollback=c.lua('(function()'+LUA+'end)()')
 result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'results':rows,'bufferSnapshotReplayCases':rollback,'interruptionClearsBuffer':True,'offlineOnly':True}
 (OUT/'verification/takeoff-attack.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'passed':True,'bufferSnapshotReplayCases':rollback,'cases':sum(len(r['cases'])for r in rows)}))

"""Actual input route and three independent wind projectiles in the native mock."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-wind-combo-v26-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
RuntimeClient.source=OUT/'genshin_fighter.lua'
def client(hz=60,face=1):
 c=RuntimeClient(canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua(f"(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];a.x={-9000*face};b.x={9000*face};a.face={face};b.face={-face};return true end)()")
 c.lua('(function()'+CHECK+'return true end)()');return c
def combo(hz,face):
 c=client(hz,face);timeline=[];seen=set()
 def step():
  c.step(1/hz);c.lua('checkBody(GF_APP().scene.views[1])')
  row=dict(c.lua("(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];return {tick=s.sim.tick,state=a.state,move=a.moveId,air=a.airMoveId,airActive=a.airMove~=nil,hits=a.stats.hits,combo=b.combo,y=a.y,foeY=b.y,shown=s.views[1].front.key}end)()").items());timeline.append(row);seen.add(row['shown'])
 def until(expr,n=140):
  for _ in range(n):
   if c.lua(expr):return
   step()
  raise AssertionError((expr,timeline[-5:]))
 def press(key):c.key(key,True);step();c.key(key,False)
 press('J');until('GF_APP().scene.sim.f[1].stats.hits>=1');press('J')
 until('GF_APP().scene.sim.f[1].stats.hits>=2');c.key('S',True);press('K');c.key('S',False)
 until('GF_APP().scene.sim.f[1].stats.hits>=3');c.key('D'if face==1 else 'A',True);press('SPACE')
 until("GF_APP().scene.sim.f[1].state=='air'");c.key('D'if face==1 else 'A',False);press('J')
 until('GF_APP().scene.sim.f[1].stats.hits>=4');press('K')
 until('GF_APP().scene.sim.f[1].stats.hits>=5')
 assert c.lua('GF_APP().scene.sim.f[2].combo')==5
 for _ in range(70 if hz==60 else 35):step()
 assert any(k.startswith('airLight_')for k in seen) and any(k.startswith('airHeavy_')for k in seen)
 c.render(OUT/'verification'/f'combo-{hz}-{face}.png')
 assert c.max_instr<1000000,c.max_instr
 return {'hz':hz,'face':face,'maxInstructions':c.max_instr,'fiveHitCombo':True,'timeline':timeline}
def wind():
 c=client();rows=[]
 for branch,keys in [('skill',['E']),('skillUp',['W','E']),('skillDown',['S','E'])]:
  c.lua("(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x=-22000;b.x=22000;a.y=0;a.vy=0;a.vx=0;a.hitstop=0;b.hitstop=0;a.skillCd=0;b.hp=b.maxhp;s.sim.proj={};return true end)()")
  c.run(.2)
  for k in keys:c.key(k,True)
  c.step()
  for k in keys:c.key(k,False)
  poses=[];styles=set();height=0;hit=False
  for i in range(100):
   c.step();c.lua('checkBody(GF_APP().scene.views[1])');key=c.lua('GF_APP().scene.views[1].front.key')
   if key.startswith(branch+'_') and key not in poses:poses.append(key);c.render(OUT/'verification'/f'{key}.png')
   height=max(height,c.lua('GF_APP().scene.sim.f[1].y'))
   styles.update(v['style']for _,v in c.lua('GF_APP().scene.sim.proj').items())
   hit=hit or c.lua('GF_APP().scene.sim.f[2].hp<GF_APP().scene.sim.f[2].maxhp')
  assert len(poses)==4,(branch,poses)
  assert styles and hit,(branch,styles,hit)
  if branch=='skillUp':assert height>0
  rows.append({'branch':branch,'poses':poses,'projectiles':list(styles),'realHit':hit,'maxHeight':height})
 assert c.max_instr<1000000,c.max_instr
 return rows
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--target');args=ap.parse_args()
 if args.target:OUT=ROOT/args.target;RuntimeClient.source=OUT/'genshin_fighter.lua'
 combos=[combo(h,f)for h,f in [(60,1),(30,1),(60,-1)]]
 result={'combos':combos,'wind':wind(),'offlineOnly':True}
 (OUT/'verification/wind-combo.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('wind E and 5-hit combo passed')

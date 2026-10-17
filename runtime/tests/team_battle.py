"""Three-fighter completion, HP carry, double KO and rollback across stock changes."""
from pathlib import Path
import sys,json,random
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import runtime,ROOT,DUMP
rt=runtime(ROOT);rt.execute(DUMP)
rt.execute('''
S=GF_REQUIRE('gf_sim');R=GF_REQUIRE('gf_roster')
local teams={{R[1],R[3],R[5]},{R[2],R[4],R[6]}}
sim=S.new({teams=teams,rounds=1,time=99,seed=21})
for i=1,60 do sim:step(0,0)end
assert(sim.phase=='fight' and sim.f[1].key=='raidenshogun' and sim.f[2].key=='nahida')
sim.f[1].hp=611;sim.f[1].energy=73
for stock=1,3 do
 sim.f[2].hp=0;sim.f[2].ko=true
 sim:step(0,0)
 for i=1,92 do sim:step(0,0)end
 if stock<3 then
  assert(sim.teamIndex[2]==stock+1 and sim.teamIndex[1]==1)
  assert(sim.f[1].hp==611 and sim.f[1].energy==73,'winner must carry HP/energy')
  assert(sim.f[2].hp==sim.f[2].maxhp and sim.f[2].energy==0,'new stock must be fresh')
  for i=1,60 do sim:step(0,0)end
 else assert(sim.phase=='over' and sim.matchWinner==1,'third stock must conclude match') end
end
sim=S.new({teams=teams,time=99,seed=21})
for stock=1,3 do
 for i=1,60 do sim:step(0,0)end
 sim.f[1].hp=0;sim.f[2].hp=0;sim:step(0,0)
 for i=1,92 do sim:step(0,0)end
 if stock<3 then assert(sim.teamIndex[1]==stock+1 and sim.teamIndex[2]==stock+1)
 else assert(sim.phase=='over' and sim.matchWinner==nil,'double third KO must draw')end
end
sim=S.new({teams=teams,time=1,seed=42});for i=1,60 do sim:step(0,0)end
sim.f[1].hp=500;sim.f[2].hp=100;for i=1,155 do sim:step(0,0)end
assert(sim.teamIndex[2]==2 and sim.f[1].hp==500,'timeout must consume only losing stock')
sim=S.new({teams=teams,time=99,seed=73});for i=1,60 do sim:step(0,0)end
sim.f[2].hp=0;sim:step(0,0);for i=1,75 do sim:step(0,0)end
copy=S.copy(sim);for i=1,170 do sim:step(0,0);copy:step(0,0);assert(dump(sim)==dump(copy),'stock swap snapshot mutated shared indices')end
assert(sim.teamIndex[2]==2 and sim:hash()==copy:hash())
''')
data={'completion':True,'winnerHpEnergyCarry':True,'thirdStockEnds':True,'doubleKOAndDraw':True,'timeout':True,'snapshotAcrossSwap':True,'mockOnly':True}
(ROOT/'verification/team-battle.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(data)

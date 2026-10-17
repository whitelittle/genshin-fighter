"""Seeded six-role/four-level command curves and full matches; mock simulation only."""
from pathlib import Path
import sys,json,argparse,statistics
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
PROBE='''return function(char,level,seed)
 local S=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_roster');local A=GF_REQUIRE('gf_ai')
 local sim=S.new({chars={R[1],R[char]},time=999,seed=seed});sim.phase='fight'
 local p,d=sim.f[2],sim.f[1];sim:setState(p,'idle');sim:setState(d,'idle');p.x=0;d.x=10000;p.face=1;d.face=-1;p.energy=0;p.skillCd=9999
 local ai=A.new(sim,2,level,seed);local attacks,heavy,throws,defend=0,0,0,0
 for t=1,3600 do sim.tick=t;local m=ai:tick()
  if m&48~=0 then attacks=attacks+1 end;if m&32~=0 then heavy=heavy+1 end;if m&512~=0 then throws=throws+1 end
 end
 -- Isolate defence: one decision per telegraphed attack, not a repeated roll each frame.
 ai=A.new(sim,2,level,seed);local defended=0;local count=0
 for t=1,8000 do
  sim.tick=t;d.hitId=t//80;local phase=t%80;d.state=phase<30 and 'attack' or 'idle';d.t=phase;d.move=d.kit.weapon.light1;d.moveId='light1'
  local m=ai:tick();if phase==0 then if count>0 then defended=defended+1 end;count=0 end
  if d.state=='attack' and m&4~=0 then count=count+1 end
 end
 return attacks,heavy,throws,defended
end'''
rows=[]
for label in ['before','after']:
    run.CLIENT_OVERRIDE=a.before if label=='before' else None
    rt=run.runtime(run.ROOT);fn=rt.execute(PROBE)
    for char in range(1,7):
        last=0
        for level in range(1,5):
            values=[fn(char,level,seed) for seed in range(1,17)]
            avg=[round(statistics.mean(v[k] for v in values),2) for k in range(4)]
            if label=='after':assert avg[0]>last,(char,level,avg,last)
            last=avg[0]
            rows.append({'version':label,'character':char,'difficulty':level,'attacksPer60Seconds':avg[0],'heavyRequests':avg[1],'throwRequests':avg[2],'defendedAttackWindowsPer100':avg[3]})
run.CLIENT_OVERRIDE=None
rt=run.runtime(run.ROOT);rt.execute('''
local S=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_roster');local A=GF_REQUIRE('gf_ai')
for level=1,4 do local sim=S.new({chars={R[4],R[6]},time=15,rounds=1,seed=73})
 local cpu=A.new(sim,2,level,71);for i=1,1800 do sim:step(i%45<5 and 16 or 0,cpu:tick());if sim.phase=='over' then break end end
 assert(sim.phase=='over')
end
local sim=S.new({teams={{R[4],R[5],R[3]},{R[6],R[2],R[1]}},time=1,seed=73})
local ai=A.new(sim,2,2,71);for i=1,1000 do sim:step(0,ai:tick())end
assert(ai.profileKey==sim.f[2].key,'stock swap must reset role policy')
''')
a.out.write_text(json.dumps({'scope':'seeded isolated decision probes; 16 seeds, 6 roles, 4 difficulties; not human win-rate','curves':rows,'fourFullMatchesAndTeamProfileChange':True},indent=2),encoding='utf-8')
print([r for r in rows if r['character']==6]);print('six-character difficulty curves and four full matches PASS')

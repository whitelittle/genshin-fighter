"""Rollback and confirmed-input replay spanning three real timed team bouts."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import runtime,ROOT
sys.path.insert(0,str(ROOT.parent/'game/tests'))
from test_net import RUN

code=RUN.replace("require(","GF_REQUIRE(")
code=code.replace('c.me.ready = true','c.me.ready = true;c.me.selecting=true')
code=code.replace("clients[1].me.char, clients[2].me.char = 3, 9","clients[1].me.char, clients[2].me.char = 5, 6")
old="return {chars = {R[chars[1]], R[chars[2]]}, rounds = setup.rounds, time = setup.time, seed = sd}"
code=code.replace(old,"return {teams={{R[5],R[3],R[1]},{R[6],R[4],R[2]}}, time=1, seed=sd}")
assert old not in code
code=code.replace("refOk, upto, na.stats.rollbacks", "refOk and ref.phase=='over' and ref.teamIndex[1]+ref.teamIndex[2]>=5, upto, na.stats.rollbacks")
rows=[]
for latency,jitter,loss,seed in [(0.02,.01,0,3),(.06,.04,.05,7),(.10,.08,.10,11)]:
    rt=runtime(ROOT);fn=rt.execute('return function(...) '+code+' end')
    r=fn(latency,jitter,loss,1800,seed)
    assert r[0]=='ok' and r[1] and r[2]>=3 and r[3:6]==(0,0,0) and r[6],r
    rows.append({'latency':latency,'jitter':jitter,'loss':loss,'confirmedFrames':r[7],'rollbacks':[r[8],r[11]],'confirmedReplayAndThreeBouts':True})
(ROOT/'verification/team-net.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(rows)

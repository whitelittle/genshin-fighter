from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime/tests'))
from run import runtime,ROOT
rt=runtime(ROOT)
result=rt.execute('''
local S,R,P=GF_REQUIRE('gf_sim'),GF_REQUIRE('gf_roster'),GF_REQUIRE('gf_character_clorinde')
local s=S.new({chars={R[5],R[1]},time=99,rounds=2,seed=21});local p,d=s.f[1],s.f[2]
p.x=-30000;d.x=30000;p.face=1;d.invul=0;d.y=0;d.state='idle'
local hp=d.hp;assert(s:startSkill(p));local samples={}
for t=0,30 do p.t=t;s:skillUpdate(p);local out=P.extras({f=p})
 if out[3] then samples[#samples+1]={tick=t,impactX=out[3].x,defenderX=d.x/100,defenderHp=d.hp} end
end
assert(d.hp==hp and #samples>0,'far whiff should reproduce an impact without damage')
return {distance=600,hpBefore=hp,hpAfter=d.hp,impactSamples=samples,scope='isolated E adapter timeline and effect data; not real-device reproduction'}
''')
def plain(x):
 if hasattr(x,'items'):
  d={k:plain(v) for k,v in x.items()}
  return [d[i] for i in range(1,len(d)+1)] if d and set(d)==set(range(1,len(d)+1)) else d
 return x
data=plain(result);O=R/'outputs/clorinde-feedback-audit-20261014';O.mkdir(exist_ok=True);(O/'far-whiff-impact.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(data,ensure_ascii=False))

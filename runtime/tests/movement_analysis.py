"""Inspect locomotion rectangle continuity, without changing renderer or assets."""
from pathlib import Path
import sys,json,collections,bisect
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient,wait
ROOT=Path(__file__).resolve().parents[1]
source=ROOT.parent/'outputs/all-codec-comparison-20261012_053101/保留的普通可读版.lua'
results=[]
for key in ['raidenshogun','nahida','furina','kamisatoayaka']:
 c=BenchClient(source);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,'nahida' if key!='nahida' else 'raidenshogun'],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run'")
 c.run(2);c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=0;for i,f in ipairs(s.sim.f) do f.x=i==1 and -30000 or 30000;f.hitstop=0;s.sim:setState(f,'idle') end return true end)()")
 c.key('D',True);banks={};seq=[]
 for t in range(240):
  c.step();pose=c.lua('GF_APP().scene.views[1].front.key')
  if not seq or seq[-1]!=pose:seq.append(pose)
  if pose not in banks:
   img=c.lua('GF_APP().scene.views[1].poseImg');b=list(img.bytes.values());pal=img.pal
   banks[pose]=[(b[o]+(img.ox or 0)-(img.ax or 0),b[o+1]+(img.ay or 0),b[o+2],b[o+3],tuple(pal[int(b[o+4])+1].values())) for o in range(0,len(b),5)]
 runCounts={pose:1+sum(x[4]!=y[4] for x,y in zip(rects,rects[1:])) for pose,rects in banks.items()}
 rows=[]
 for a,b in zip(seq,seq[1:]):
  x,y=banks[a],banks[b];counts=collections.Counter(x);match=sum(min(n,counts[r]) for r,n in collections.Counter(y).items())
  rows.append({'from':a,'to':b,'sourceRects':len(x),'targetRects':len(y),'exactGeometryColorMatches':match,'sameIndex':sum(i==j for i,j in zip(x,y))})
 results.append({'key':key,'poses':seq,'colorRuns':runCounts,'transitions':rows})
print(json.dumps(results,ensure_ascii=False,indent=2))
(ROOT/'verification/movement-continuity.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')

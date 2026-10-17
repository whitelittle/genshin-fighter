"""Locomotion writes, publication lag and exact settled mock pixels on four fighters."""
from pathlib import Path
import sys,json,statistics,hashlib
import argparse
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient,wait
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path);ap.add_argument('--after',type=Path,default=ROOT/'dist/genshin_fighter.lua');ap.add_argument('--out',type=Path,default=ROOT/'verification/movement-fix');args=ap.parse_args()
OUT=args.out;OUT.mkdir(exist_ok=True)
before=args.before or OUT/'before.lua'
if not args.before:
 raw=(ROOT.parent/'outputs/smooth-comparison-20261013/working-source.lua').read_text(encoding='utf-8')
 old="if #self.teams[1]==3 then label=self.ready[1] and '取消准备' or '准备'"
 assert raw.count(old)==1
 before.write_text(raw.replace(old,old+' end'),encoding='utf-8')
sources=[before,args.after]

def client(source,key,other=None):
 c=BenchClient(source);c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,other or ('nahida' if key!='nahida' else 'raidenshogun')],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 c.run(2);c.env.math.randomseed(73)
 c.lua("(function()local s=GF_APP().scene;s.banners={};s.sim.phase='fight';s.sim.freeze=0;for i,f in ipairs(s.sim.f) do f.x=i==1 and -30000 or 30000;f.y=0;f.vx=0;f.hitstop=0;s.sim:setState(f,'idle') end return true end)()")
 return c

results=[]
for key in ['raidenshogun','nahida','furina','kamisatoayaka']:
 for direction,button in [('walk','D'),('back','A')]:
  pair=[]
  for source in sources:
   c=client(source,key);c.key(button,True);instr=[];calls=[];mismatch=0;size=[];last=dict(c.lua("GF_REQUIRE('gf_gfx').N").items());poses=[];stale=0
   for t in range(480):
    # Keep distance off either wall, without changing the animation clock.
    if t%90==0:c.lua("(function()local s=GF_APP().scene;s.sim.f[1].x=-30000;s.sim.f[2].x=30000;return true end)()")
    c.max_instr=0;c.step();instr.append(c.max_instr);calls.append(c.calls[-1])
    now=dict(c.lua("GF_REQUIRE('gf_gfx').N").items());size.append(now.get('size',0)-last.get('size',0));last=now
    want=c.lua('(GF_APP().scene.views[1]:poseFor())');front=c.lua('GF_APP().scene.views[1].front.key')
    if front!=want:mismatch+=1
    if not poses or poses[-1]!=front:poses.append(front)
   pair.append({'callsMean':round(statistics.mean(calls),2),'callsPeak':max(calls),'instructionsMean':round(statistics.mean(instr)),
    'instructionsPeak':max(instr),'latePoseCallbacks':mismatch,'sizeCounterWrites':sum(size),'publishedPoses':poses,
    'resident':c.lua('GF_SECOND_POOL_STATUS().total'),'createdAfterLoad':c.lua('GF_SECOND_POOL_STATUS().created'),'errors':list(c.H.err.values())})
  results.append({'key':key,'direction':direction,'before':pair[0],'after':pair[1]})
  print(key,direction,'calls',pair[0]['callsMean'],pair[1]['callsMean'],'peak',pair[0]['callsPeak'],pair[1]['callsPeak'],'late',pair[0]['latePoseCallbacks'],pair[1]['latePoseCallbacks'],flush=True)

# Verify every movement pose at the same simulation, position, clock and root transform.
pixels=[]
for key in ['raidenshogun','nahida','furina','kamisatoayaka']:
 clients=[client(s,key) for s in sources]
 for direction in ['walk','back']:
  for phase in range(6):
   images=[]
   for variant,c in enumerate(clients):
    provider=c.lua(f"GF_REQUIRE('gf_character_registry').provider('{key}')")
    tick=phase*8
    if provider:
     durations=provider.data.groups[direction].durations
     tick=sum(durations[i] for i in range(1,phase+1))
    c.lua(f"""(function()local s=GF_APP().scene;local sim=s.sim;s.app.t=10;sim.tick=600;sim.phase='fight';sim.freeze=10000;s.banners={{}};s.cine=nil;s.shakeT=0;s.camX=0;s.zoom=1;s.zoomPunch=0;sim.proj={{}};sim.events={{}};local p=sim.f[1];p.state='{direction}';p.hitstop=10000;p.t=0;p.face=1;p.x=-10000;p.y=0;p.coat=0;p.frozen=0;local v=s.views[1];v.flashT=0;v.walkT={tick};local d=sim.f[2];d.state='idle';d.t=0;d.hitstop=10000;d.x=30000;d.y=0;return true end)()""")
    c.run(.3)
    # Derive the exact multiset of rectangles in each palette run: order may only
    # change inside an identical RGBA run, which also preserves opacity lookup.
    valid=c.lua("""(function()local v=GF_APP().scene.views[1];local img=v.poseImg;local bmp=v.front;local b=img.bytes;local first=1;local seam=img.seam or .08
while first<=img.n do local last=first;while last<img.n and b[(last+1)*5]==b[first*5] do last=last+1 end
local wanted={};for i=first,last do local o=(i-1)*5;local x=(img.ox or 0)-(img.ax or 0)+b[o+1]+b[o+3]/2;local y=(img.oy or 0)+(img.ay or 0)-b[o+2]-b[o+4]/2
local sig=x..':'..y..':'..(b[o+3]+seam)..':'..(b[o+4]+seam);wanted[sig]=(wanted[sig] or 0)+1 end
for i=first,last do local n=bmp.kids[i];local sig=n.x..':'..n.y..':'..n.w..':'..n.h;assert((wanted[sig] or 0)>0,'geometry crossed run');wanted[sig]=wanted[sig]-1 end;first=last+1 end
return true end)()""")
    assert valid
    path=OUT/f'{key}-{direction}-{phase}-{variant}.png';c.render(path);images.append(np.array(Image.open(path)))
   diff=int(np.count_nonzero(np.any(images[0]!=images[1],axis=2)))
   assert diff==0,(key,direction,phase,diff)
   pixels.append({'key':key,'direction':direction,'phase':phase,'changedPixels':diff})
report={'scope':'offline Lua53/mock only, 480 movement callbacks per case; no native FPS acceptance','beforeSha256':hashlib.sha256(before.read_bytes()).hexdigest(),
 'afterSha256':hashlib.sha256(sources[1].read_bytes()).hexdigest(),'cases':results,'settledPixelChecks':pixels}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

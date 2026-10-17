"""Read-only production audit; display ablations live only in isolated mocks."""
from pathlib import Path
import sys,json,statistics,hashlib,argparse
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime/tests'))
from mock_flow import RuntimeClient,wait
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=R/'runtime/dist/genshin_fighter.lua');ap.add_argument('--variant',default='development');args=ap.parse_args()
O=R/'outputs/pc-continuous-attack-audit-20261014'/args.variant;O.mkdir(parents=True,exist_ok=True)
source=args.source;RuntimeClient.source=source
def sample(pair,mode):
 c=RuntimeClient(device='KeyboardAndMouse',canvas=(1600,900));c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':pair,'mode':'training','cpu':[False,False],'infinite':True,'time':999})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans");c.run(1)
 c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=0;for i,f in ipairs(s.sim.f)do f.x=i==1 and -20000 or 20000;f.hitstop=0;f.frozen=0;s.sim:setState(f,'idle')end;return true end)()")
 if 'no-body' in mode:c.lua("(function()for _,v in ipairs(GF_APP().scene.views)do v.updatePose=function()end end;return true end)()")
 if 'no-flash' in mode:c.lua("(function()for _,v in ipairs(GF_APP().scene.views)do v.onHit=function()end end;return true end)()")
 if 'no-extras' in mode:c.lua("(function()local r=GF_REQUIRE('gf_character_registry');for _,v in ipairs(GF_APP().scene.views)do v.drawAnimatedFx=function()end;v.drawCapture=function()end;v.drawAssistants=function()end;local p=r.provider(v.key);if p then p.drawExtras=function()end end end;return true end)()")
 calls=[];instr=[];deltas={k:[] for k in ['bitmap','col','par','size','vis']};last=dict(c.lua("GF_REQUIRE('gf_gfx').N").items());states={}
 for t in range(180):
  if mode!='idle' and t%30==0:
   move=['light1','light2','light3','heavy'][t//30%4]
   c.lua("(function()local s=GF_APP().scene;for _,f in ipairs(s.sim.f)do s.sim:setState(f,'idle');f.hitstop=0;if not s.sim:startMove(f,'"+move+"') then assert(s.sim:startMove(f,'light1')) end end;return true end)()")
  if mode not in ['idle','attack-natural'] and not mode.startswith('natural-') and t%12==0:c.lua("(function()for _,v in ipairs(GF_APP().scene.views)do v:onHit({heavy=false})end;return true end)()")
  c.max_instr=0;c.step();calls.append(c.calls[-1]);instr.append(c.max_instr)
  now=dict(c.lua("GF_REQUIRE('gf_gfx').N").items())
  for k in deltas:deltas[k].append(now.get(k,0)-last.get(k,0))
  last=now
  for i in [1,2]:
   st=c.lua(f'GF_APP().scene.sim.f[{i}].state');states[st]=states.get(st,0)+1
 row={'pair':pair,'scenario':mode,'callbacks':180,'callbackHz':60,'callsMean':round(statistics.mean(calls)),'callsP95':sorted(calls)[170],'callsPeak':max(calls),'instructionsMean':round(statistics.mean(instr)),'instructionsPeak':max(instr),'writesMean':{k:round(statistics.mean(v)) for k,v in deltas.items()},'writesPeak':{k:max(v) for k,v in deltas.items()},'residentImages':c.lua('GF_SECOND_POOL_STATUS().total'),'simulationHash':c.lua('GF_APP().scene.sim:hash()'),'sampledStates':states,'errors':list(c.H.err.values())}
 print(json.dumps(row),flush=True);return row
progress=O/'progress.json'
rows=json.loads(progress.read_text(encoding='utf8')) if progress.exists() else []
for pair in [['clorinde','clorinde'],['furina','arlecchino'],['raidenshogun','nahida']]:
 for mode in ['idle','attack-natural','attack-feedback','no-flash','no-body','no-extras','natural-no-flash','natural-no-body','natural-no-extras']:
  if any(r['pair']==pair and r['scenario']==mode for r in rows):continue
  rows.append(sample(pair,mode));progress.write_text(json.dumps(rows,indent=2),encoding='utf8')
for pair in {tuple(r['pair']) for r in rows}:
 hashes=[r['simulationHash'] for r in rows if tuple(r['pair'])==pair and r['scenario']!='idle'];assert len(set(hashes))==1,(pair,hashes)
(O/'mock-cost.json').write_text(json.dumps({'scope':'isolated PC mock; forced simultaneous attacks at 30-tick cadence with natural combat hits; attack-feedback adds synthetic visual hit feedback every 12 ticks; not native FPS or user input chain','sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'renderAblationsKeepSimulationHash':True,'rows':rows},ensure_ascii=False,indent=2),encoding='utf8')

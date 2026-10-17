"""Assist selection, high-bit packet, independent hit, reset and full snapshot replay."""
from pathlib import Path
import sys,json,random
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run import runtime,DUMP
from performance import BenchClient,wait
OUT=ROOT.parent/'outputs/nahida-raiden-rework-20261015'
SOURCE=OUT/'assist.lua'
def engine():
 r=runtime(ROOT);r.execute(SOURCE.read_text(encoding='utf-8'));r.execute(DUMP)
 r.execute("S=GF_REQUIRE('gf_sim');R=GF_REQUIRE('gf_roster');N=GF_REQUIRE('gf_net');O=GF_REQUIRE('gf_online')")
 return r
def rules():
 r=engine()
 r.execute("assert(N.BITS==11 and N.PER_INT==2 and N.LEN==24);local p=N.packInputs(function(f)return f%2==0 and (1024|32) or 2047 end,100);local packet={};for i=1,N.LEN do packet[i]=0 end;for i,v in ipairs(p)do packet[N.F.inputs+i-1]=v end;local u=N.unpackInputs(packet,100);for f=79,100 do assert(u[f]==(f%2==0 and 1056 or 2047)) end;local w=O.rosterWord(1,2,2,1,5,6);local q=O.parseRoster(w);assert(q.assists[1]==5 and q.assists[2]==6)")
 rows=[]
 for partner in range(1,7):
  for face in [1,-1]:
   for outcome in ['hit','block','invulnerable','miss']:
    r.execute(f"sim=S.new({{chars={{R[2],R[1]}},assistChars={{R[{partner}],R[2]}},training=true,infinite=true}});sim.phase='fight';p=sim.f[1];d=sim.f[2];sim:setState(p,'idle');sim:setState(d,'idle');p.x=0;p.face={face};d.x={face*15000};d.face={-face};d.y=0;d.vy=0;d.inNow={8 if outcome=='block' and face==1 else 4 if outcome=='block' else 0};d.invul={200 if outcome=='invulnerable' else 0};p.connected=false;hp=d.hp;assert(sim:callAssist(1));assert(not sim:callAssist(1));assert(p.state=='idle')")
    if outcome=='miss':r.execute('d.x=100000')
    # Tick only the independent assist so fixed test targets and their guard remain stable.
    r.execute('for t=1,60 do sim:updateAssists() end;assert(sim.assists[1]==nil);assert(p.connected==false and p.hitstop==0)')
    if outcome=='hit':assert r.eval('d.hp<hp'),(partner,face,outcome)
    elif outcome=='block':assert r.eval('d.stats.blocks>0'),(partner,face,outcome)
    else:assert r.eval('d.hp==hp'),(partner,face,outcome)
    rows.append({'partner':partner,'face':face,'outcome':outcome})
 r.execute("sim=S.new({chars={R[2],R[1]},assistChars={R[1],R[2]}});sim.phase='fight';p=sim.f[1];sim:setState(p,'idle');sim:step(1|16,0);assert(p.state=='jumpsq' and p.jumpAttack=='airLight');for i=1,4 do sim:step(0,0) end;assert(p.state=='air' and p.airMoveId=='airLight')")
 r.execute("sim:startRound(false);assert(sim.assistCd[1]==0 and sim.assists[1]==nil);for i=1,60 do sim:step(1024,0) end;sim:step(1024,0);assert(sim.assists[1]==nil);sim:step(0,0);sim:step(1024,0);assert(sim.assists[1]);local clone=S.copy(sim);assert(clone.assists[1]~=sim.assists[1]);clone.assists[1].t=99;assert(sim.assists[1].t~=99)")
 r.execute("p.state='hit';sim.assists[1]=nil;sim.assistCd[1]=0;assert(not sim:callAssist(1));p.state='idle';assert(sim:callAssist(1));p.state='hit';sim:updateAssists();assert(sim.assists[1]==nil)")
 r.execute("sim=S.new({teams={{R[1],R[2],R[3]},{R[4],R[5],R[6]}},assistChars={R[5],R[2]}});assert(#sim.teams[1]==3 and sim:assistPartner(1).key=='clorinde');sim.phase='ko';sim.phaseT=90;sim.roundWinner=2;sim.f[1].hp=0;sim:flow();assert(sim.teamIndex[1]==2 and sim:assistPartner(1).key=='clorinde')")
 r.execute("sim=S.new({chars={R[2],R[1]},assistChars={R[1],R[2]},training=true,infinite=true,seed=73});sim.phase='fight';for _,p in ipairs(sim.f)do sim:setState(p,'idle')end;sim:step(1024,1024);clone=S.copy(sim)")
 rng=random.Random(43)
 for _ in range(1200):
  a,b=rng.randrange(2048),rng.randrange(2048)
  r.globals().sim.step(r.globals().sim,a,b);r.globals().clone.step(r.globals().clone,a,b)
  assert r.eval('dump(sim)==dump(clone)'), 'assist snapshot divergence'
 return {'partners':rows,'introReleaseAndReset':True,'mainFighterUnaffected':True,'earlyInterrupt':True,'aerialInput':True,'dedicatedFourthSlot':True,'packet11BitRoundtrip':True,'fullStateReplayTicks':1200}
def visuals():
 result=[]
 for device,canvas in [('Mobile',(1600,900)),('KeyboardAndMouse',(1600,900))]:
  c=BenchClient(SOURCE)
  # BenchClient is fixed to Mobile; construct the real UI harness for desktop below.
  if device!='Mobile':
   from mock_flow import RuntimeClient
   RuntimeClient.source=SOURCE;c=RuntimeClient(device=device,canvas=canvas)
  c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':['nahida','raidenshogun'],'assistChars':['raidenshogun','nahida'],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
  wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans",limit=4000)
  c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=0;s.banners={};for i,p in ipairs(s.sim.f)do p.x=i==1 and -12000 or 12000;p.y=0;p.hitstop=0;s.sim:setState(p,'idle')end;s.sim:callAssist(1);s.sim:callAssist(2);return true end)()")
  c.run(.3);c.lua('(function()GF_APP().scene.sim.freeze=10000;return true end)()');c.run(.1)
  path=OUT/f'assist-active-{device}.png';c.render(path)
  assert c.lua('GF_APP().scene.assistViews[1].root.act and GF_APP().scene.assistViews[2].root.act')
  assert not list(c.H.err.values()),list(c.H.err.values())
  result.append({'device':device,'stats':c.stats(),'errors':False})
 return result
if __name__=='__main__':
 report={'rules':rules(),'visuals':visuals(),'scope':'offline simulation; not native device acceptance'}
 (OUT/'assist-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Assist outcomes, full state replay, input packet and visible partner checks passed.')

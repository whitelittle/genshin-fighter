"""Ordinary GFV2 matchmaking, private three-person preparation, same connection fight."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,Relay
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();RuntimeClient.source=a.source
a.out.mkdir(parents=True,exist_ok=True)
relay=Relay(.06,.04,.03,seed=47);clients=[]
def make(slot,team):
 c=RuntimeClient(device='Mobile' if slot==2 else 'KeyboardAndMouse',canvas=(1600,900))
 c.env.GF_FIRST_SCENE='online';c.env.GF_FIRST_ARGS=c._to_lua({'teamOnline':team})
 c.env.GF_NETIO=relay.io(c,slot,1000+slot)
 def unexpected_signal(name):raise AssertionError('Match-first flow must not send native GF3 preparation/battle signals: '+name)
 c.H.game.ServerSignal=unexpected_signal
 clients.append(c);relay.clients.append(c);return c
def step(n=1,active=None):
 for _ in range(n):
  relay.tick(1/60)
  for c in active or clients:c.step()
def until(expr,limit=4200):
 for _ in range(limit):
  step()
  if all(c.lua(expr) for c in clients):return
 raise AssertionError('timeout: '+expr+' '+str([c.lua('GF_APP().sceneName') for c in clients]))
c1=make(1,True);step(480);assert c1.lua("GF_APP().sceneName=='online'")
c2=make(2,False);step(480)
assert all(c.lua("GF_APP().sceneName=='online'") for c in clients),'Different modes matched'
c2.lua("(function()GF_APP():go('online',{teamOnline=true});return true end)()")
until("GF_APP().sceneName=='select' and GF_APP().scene.initialized and GF_APP().scene.built==6 and not GF_APP().poolNext and not GF_APP().trans")
for c in clients:
 assert c.lua("GF_APP().scene.args.teamMatched and GF_APP().netFamily=='GFV2'")
 c.env.EXPECTED_NET=c.lua('GF_APP().net')
def draft():
 for c,team in zip(clients,[(5,3,1),(6,4,2)]):
  for id in team:c.lua(f"(function()local s=GF_APP().scene;s.cur[1]={id};s.focused=true;s:confirm();return true end)()")
 step(120)
 assert all(c.lua("GF_APP().scene.teamIO.remoteCount==3 and not GF_APP().scene.teamIO.reveal") for c in clients)
 assert all(c.lua("GF_APP().net.peers[3-GF_APP().net.slot].pkt[10]==0") for c in clients),'Private roster leaked before ready'
draft();c1.lua("(function()GF_APP().scene:confirm();return true end)()");step(90)
assert all(c.lua("GF_APP().sceneName=='select'") for c in clients)
c1.lua("(function()GF_APP().scene:confirm();return true end)()");step(120)
assert all(c.lua("#GF_APP().scene.teams[1]==0 and not GF_APP().scene.ready[1]") for c in clients),'Cancel failed to isolate previous preparation'
draft()
for c in clients:c.lua("(function()GF_APP().scene:confirm();return true end)()")
until("GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
for c in clients:
 assert c.lua("GF_APP().net==EXPECTED_NET and GF_APP().netFamily=='GFV2' and GF_APP().scene.args.teamMatched")
 assert c.lua("GF_APP().scene.sim.teams[1][3].key=='raidenshogun' and GF_APP().scene.sim.teams[2][3].key=='nahida'")
for i in range(720):
 if i%60==0:
  for c in clients:c.key('J',True)
 if i%60==20:
  for c in clients:c.key('J',False)
 step()
hashes=[dict(c.lua('GF_APP().net.match.session.myHash').items()) for c in clients]
common=set(hashes[0])&set(hashes[1]);assert len(common)>=3 and all(hashes[0][f]==hashes[1][f] for f in common)
rollbacks=[c.lua('GF_APP().net.match.session.stats.rollbacks') for c in clients]
for c in clients:assert not c.lua('GF_APP().net.match.session.desync') and not list(c.H.err.values())
c1.render(a.out/'team-fight-pc.png');c2.render(a.out/'team-fight-mobile.png')
# Result -> matching -> selection preserves the existing connection and sequence.
for c in clients:c.lua("(function()GF_APP().scene:finish();return true end)()")
until("GF_APP().sceneName=='result' and not GF_APP().trans")
for c in clients:c.lua("(function()GF_APP().scene:pick('lobby');return true end)()")
until("GF_APP().sceneName=='select' and GF_APP().scene.initialized and not GF_APP().trans")
for c in clients:assert c.lua("GF_APP().net==EXPECTED_NET and #GF_APP().scene.teams[1]==0")
relay.muted.add(2)
step(420,active=[c1]);assert c1.lua("GF_APP().sceneName=='online'")
r={'mockOnly':True,'singleClientWaitsBeforeSelection':True,'differentModesDoNotMatch':True,'sameGFV2ConnectionForSelectionAndFight':True,'privateDraftAndMutualReadyAcknowledgment':True,'cancelResetsBothAndPreventsStaleRoster':True,'resultReturnsToMatchFirst':True,'disconnectDuringDraftReturnsToMatching':True,'commonConfirmedHashes':len(common),'rollbacks':rollbacks}
(a.out/'match-first-flow.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r)

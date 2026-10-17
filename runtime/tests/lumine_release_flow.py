"""Existing full flow, with an explicit acknowledgement of the new startup notice."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'outputs/lumine-training-20261015'
sys.path.insert(0,str(ROOT/'tests'))
import mock_flow as flow
flow.RuntimeClient.source=OUT/'candidate.lua'
def wait_notice(c,expr,limit=2400):
 for _ in range(limit):
  c.step()
  if c.lua("GF_APP() and GF_APP().scene and GF_APP().sceneName=='notice' and GF_APP().scene.t>.4 and not GF_APP().trans"):
   c.key('J',True);c.step();c.key('J',False)
  if c.lua(expr):return
 raise AssertionError(expr)
flow.wait=wait_notice
local=[]
for dev,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600))]:
 r=flow.local_flow(dev,canvas,(4,3));local.append(r);print(json.dumps(r),flush=True)
net=flow.network_flow((4,3));print(json.dumps(net),flush=True)
(OUT/'mock-flow-notice.json').write_text(json.dumps({'mockOnly':True,'local':local,'network':net},indent=2),encoding='utf-8')

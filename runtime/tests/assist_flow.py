"""Run existing full flow/rollback coverage with explicit second assist picks."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'outputs/nahida-raiden-rework-20261015'
raw=(ROOT/'tests/mock_flow.py').read_text(encoding='utf-8')
old="c.lua(\"(function()local s=GF_APP().scene;s:confirm(1);s:confirm(2);return true end)()\")"
new="c.lua(\"(function()local s=GF_APP().scene;for side=1,2 do s:confirm(side);s.cur[side]=s.mainChoice[side]==1 and 2 or 1;s:confirm(side) end;return true end)()\")"
assert raw.count(old)==1;raw=raw.replace(old,new)
old="for c in clients:c.lua(\"(function()GF_APP().scene:confirm(1);return true end)()\")"
new="for c in clients:c.lua(\"(function()local s=GF_APP().scene;s:confirm(1);s.cur[1]=s.mainChoice[1]==1 and 2 or 1;s:confirm(1);return true end)()\")"
assert raw.count(old)==1;raw=raw.replace(old,new)
namespace={'__name__':'assist_flow_checks','__file__':str(ROOT/'tests/mock_flow.py')}
exec(compile(raw,str(ROOT/'tests/mock_flow.py'),'exec'),namespace)
namespace['RuntimeClient'].source=OUT/'assist.lua'
local=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(900,1600)),('Mobile',(1600,900))]:
 result=namespace['local_flow'](device,canvas,(2,1));local.append(result);print(json.dumps(result),flush=True)
net=namespace['network_flow']((2,1));print(json.dumps(net),flush=True)
(OUT/'assist-flow.json').write_text(json.dumps({'mockOnly':True,'explicitSecondPick':True,'clientSha256':hashlib.sha256((OUT/'assist.lua').read_bytes()).hexdigest(),'local':local,'network':net},indent=2),encoding='utf-8')

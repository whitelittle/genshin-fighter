"""Extend the existing real-UI team and match-first fixtures to the fourth assist pick."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'outputs/nahida-raiden-rework-20261015'
sys.path.insert(0,str(ROOT/'tests'))
raw=(ROOT/'tests/team_flow.py').read_text(encoding='utf-8')
raw=raw.replace('for index in (5,6,4):','for index in (5,6,4,2):')
raw=raw.replace('teams={{5,3,1},{6,4,2}}','teams={{5,3,1,2},{6,4,2,1}}')
space={'__name__':'assist_team_checks','__file__':str(ROOT/'tests/team_flow.py')}
exec(compile(raw,str(ROOT/'tests/team_flow.py'),'exec'),space)
space['RuntimeClient'].source=OUT/'assist.lua'
dest=OUT/'assist-team';dest.mkdir(exist_ok=True)
result=[space['check']('KeyboardAndMouse',(1600,900),dest),space['check']('Mobile',(1950,900),dest)]
(dest/'team-flow.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result,flush=True)
raw=(ROOT/'tests/team_match_first.py').read_text(encoding='utf-8')
raw=raw.replace('[(5,3,1),(6,4,2)]','[(5,3,1,2),(6,4,2,1)]').replace('remoteCount==3','remoteCount==4')
raw=raw.replace("assert c.lua(\"GF_APP().scene.sim.teams[1][3].key=='raidenshogun' and GF_APP().scene.sim.teams[2][3].key=='nahida'\")", "assert c.lua(\"GF_APP().scene.sim.teams[1][3].key=='raidenshogun' and GF_APP().scene.sim.teams[2][3].key=='nahida' and GF_APP().scene.sim:assistPartner(1).key=='nahida' and GF_APP().scene.sim:assistPartner(2).key=='raidenshogun'\")")
sys.argv=['assist_team_flow','--source',str(OUT/'assist.lua'),'--out',str(dest)]
space={'__name__':'assist_matched_checks','__file__':str(ROOT/'tests/team_match_first.py')}
exec(compile(raw,str(ROOT/'tests/team_match_first.py'),'exec'),space)

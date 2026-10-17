from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
raw=(ROOT/'tests/team_match_first.py').read_text(encoding='utf-8')
raw=raw.replace('[(5,3,1),(6,4,2)]','[(5,3,1,2),(6,4,2,1)]').replace('remoteCount==3','remoteCount==4')
raw=raw[:raw.index('for i in range(720):')]
raw='\n'.join(" print('team state',c.lua(\"GF_APP().scene.sim.teams~=nil\"),c.lua(\"GF_APP().scene.args.teamRoster~=nil\"),c.lua(\"GF_APP().scene.sim.opts.teams~=nil\"))" if 'assert c.lua("GF_APP().scene.sim.teams[1][3]' in line else line for line in raw.splitlines())
sys.argv=['probe','--source',str(ROOT.parent/'outputs/nahida-raiden-rework-20261015/assist.lua'),'--out',str(ROOT.parent/'outputs/nahida-raiden-rework-20261015/assist-team')]
ns={'__name__':'assist_probe','__file__':str(ROOT/'tests/team_match_first.py')}
exec(compile(raw,ns['__file__'],'exec'),ns)
for c in ns['clients']:
 print('opts',dict(c.lua('GF_APP().scene.sim.opts').items()))
 print('session options',dict(c.lua('GF_APP().net.match.session.state.opts').items()))

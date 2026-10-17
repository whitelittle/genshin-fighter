from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
sys.path.insert(0,'runtime/tests')
from performance import BenchClient,wait
sources=[Path('outputs/four-character-gia-20261011_233317/gpt_20261011_233317_原神格斗_四角色整理版.lua'),Path('runtime/dist/genshin_fighter.lua')]
checks=[]
for key,state,t in [(key,state,t) for key in ['furina','kamisatoayaka'] for state,t in [('skill',18),('burst',24),('burst',94),('frozen',0)]]:
 shots=[]
 for variant,source in enumerate(sources):
  c=BenchClient(source);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from([key,'kamisatoayaka' if key=='furina' else 'furina']),'mode':'training','cpu':c.rt.table_from([False,False]),'infinite':True,'seed':21})
  wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
  c.lua(f"""(function()local s=GF_APP().scene;s.banners={{}};s.sim.phase='fight';s.sim.freeze=10000;s.sim.events={{}};s.sim.proj={{}};s.camX=0;s.zoom=1;s.shakeT=0;for i,f in ipairs(s.sim.f) do f.x=i==1 and -20000 or 18000;f.y=0;f.t=0;f.face=i==1 and 1 or -1;f.coat=0;f.hitstop=0;f.state='idle';f.frozen=0 end
local p=s.sim.f[1];p.state='{'idle' if state=='frozen' else state}';p.t={t};p.move=p.kit.{'skill' if state=='skill' else 'burst'};p.moveId='{state}';p.cinematicConfirmed=true;{'p.frozen=1000' if state=='frozen' else ''}
return true end)()""")
  c.run(.2)
  path=Path(f'runtime/verification/perf-visual-{key}-{state}-{t}-{variant}.png');c.render(path);shots.append(np.array(Image.open(path)))
 diff=int(np.count_nonzero(np.any(shots[0]!=shots[1],axis=2)));assert diff==0,(state,t,diff);checks.append({'key':key,'state':state,'tick':t,'changedPixels':diff})
Path('runtime/verification/performance-visual-equivalence.json').write_text(json.dumps({'mockOnly':True,'checks':checks},indent=2));print(checks)

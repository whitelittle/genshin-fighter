"""Speculative locomotion cannot block a turn, hit or attack."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient,wait
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
checks=[]
for key in ['raidenshogun','nahida','furina','kamisatoayaka']:
 c=BenchClient(args.source);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,'nahida' if key!='nahida' else 'raidenshogun'],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run'")
 for target in ['back','attack','hit']:
  result=c.lua("""(function()
local s=GF_APP().scene;local sim=s.sim;local f=sim.f[1];local v=s.views[1]
sim.phase='fight';sim.freeze=0;f.hitstop=0;f.stun=0;sim:setState(f,'walk');v.walkT=0
local walking=v:poseFor()
for i=1,8 do if v.front and v.front.key==walking then break end;v:updatePose(320) end
v:updatePose(320)
local back=v.slots[1]==v.front and v.slots[2] or v.slots[1]
assert(back.job and back.job.prefetch,'prefetch not exercised')
local oldKey=back.job.key
"""+ ("sim:setState(f,'back');v.walkT=17" if target=='back' else "sim:setState(f,'idle');assert(sim:startMove(f,'heavy'))" if target=='attack' else "sim:setState(f,'hit');f.stun=20")+"""
local want=v:poseFor();assert(want~=oldKey,'interrupt must change target')
v:updatePose(520)
assert(not back.job or back.job.key==want,'speculative job blocked new state')
local updates=1
while v.front.key~=want and updates<10 do v:updatePose(520);updates=updates+1 end
assert(v.front.key==want,'new pose starved')
return updates
end)()""")
  checks.append({'key':key,'interrupt':target,'updatesToPublish':result})
args.out.write_text(json.dumps({'mockOnly':True,'checks':checks},indent=2),encoding='utf-8');print(checks)

from profile import new, current, old
from compare import *

results=[]
for label,source,baseline in [('baseline',old,True),('current',current,False)]:
    for repeat in range(2):
        c=new(source,baseline)
        c.lua("(function()local sim=GF_APP().scene.sim;sim.phase='fight';sim.freeze=0;for i,f in ipairs(sim.f)do f.x=i==1 and -10000 or 10000;f.y=0;f.face=i==1 and 1 or -1;f.energy=100;f.hitstop=0;f.invul=0;sim:setState(f,'idle')end;assert(sim:startBurst(sim.f[1]));return true end)()")
        frames=[]
        for n in range(210):
            c.max_instr=0;c.step();frames.append({'callback':n,'instructions':c.max_instr,'calls':c.calls[-1],'actionTick':c.lua('GF_APP().scene.sim.f[1].t')})
        counts=c.lua("(function()local A=GF_REQUIRE('gf_art');local p=A.portrait('raidenshogun');local s=GF_APP().scene;local out={portraitRects=p.n,portraitW=p.w,portraitH=p.h,body1=s.views[1].poseImg.n,body2=s.views[2].poseImg.n};return out end)()")
        results.append({'version':label,'repeat':repeat+1,'maxInstructions':max(f['instructions'] for f in frames),'maxCalls':max(f['calls'] for f in frames),
            'heavyCallbacks':sum(f['instructions']>1000000 for f in frames),'images':dict(counts.items()),'largest':sorted(frames,key=lambda f:f['instructions'],reverse=True)[:4]})
write('fresh-Q-repeat.json',{'scope':'uninstrumented mock; Q is first attack after loading and idle; 2 independent clients per version','results':results})
print(json.dumps(results,ensure_ascii=False),flush=True)

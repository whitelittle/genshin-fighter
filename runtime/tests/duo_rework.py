"""Independent rules, replay, geometry, calls and pixel checks for the two-role prototype."""
from pathlib import Path
import sys, json, statistics, random
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run import runtime,DUMP
from performance import BenchClient,wait
OUT=ROOT.parent/'outputs/nahida-raiden-rework-20261015'

def engine(source):
    r=runtime(ROOT);r.execute(source.read_text(encoding='utf-8'));r.execute(DUMP)
    r.execute("S=GF_REQUIRE('gf_sim');R=GF_REQUIRE('gf_roster');sim=S.new({chars={R[2],R[1]},training=true,infinite=true,seed=31});sim.phase='fight';for _,p in ipairs(sim.f) do sim:setState(p,'idle');p.x=p.id==1 and -50000 or 50000 end")
    return r

def rules():
    rows=[]
    for roster,key in [(2,'nahida'),(1,'raidenshogun')]:
        distance=[]
        for variant in ['before','candidate']:
            r=engine(OUT/(variant+'.lua'))
            r.execute(f"sim=S.new({{chars={{R[{roster}],R[3]}},training=true,infinite=true}});sim.phase='fight';p=sim.f[1];p.x=-50000;sim.f[2].x=50000;sim:setState(p,'idle');sim:setState(sim.f[2],'idle');x=p.x;sim:step(256,0)")
            for _ in range(16):r.execute('sim:step(0,0)')
            distance.append(r.eval('(p.x-x)/100'))
        assert distance[1]>distance[0]*1.4,(key,distance)
        r=engine(OUT/'candidate.lua')
        for face in [1,-1]:
            forward=8 if face==1 else 4
            for mask,wanted in [(forward|16,'forwardLight'),(1|16,'upLight'),(1|32,'upHeavy'),(2|16,'crouchLight'),(2|32,'crouchHeavy'),(1|2|16,'crouchLight')]:
                r.execute(f"p=sim.f[{1 if key=='nahida' else 2}];p.face={face};p.inNow={mask};p.inPressed={mask};sim:setState(p,'idle');sim:neutral(p);assert(p.moveId=='{wanted}',p.moveId)")
            r.execute("sim:startMove(p,'upLight');p.connected=true;p.inNow=1|32;p.inPressed=32;assert(sim:tryCancel(p,p.move));assert(p.moveId=='upHeavy');sim:startMove(p,'crouchLight');p.connected=true;p.inNow=2|32;p.inPressed=32;assert(sim:tryCancel(p,p.move));assert(p.moveId=='crouchHeavy')")
            for mask,variant in ([(2,'seed'),(1,'leaf')] if key=='nahida' else [(2,'thunder'),(forward,'lunge')]):
                r.execute(f"p.skillCd=0;p.y=0;p.inNow={mask};sim:setState(p,'idle');assert(sim:startSkill(p));assert(p.move.reworkVariant=='{variant}');p.t=p.move.startup;sim:skillUpdate(p)")
                if variant in ['seed','thunder']:
                    r.execute("assert(sim.proj[#sim.proj].x==p.x+p.face*p.move.fixedOffset*100)")
                elif variant=='leaf':r.execute("assert(sim.proj[#sim.proj].vx==p.face*1000)")
                assert not r.eval('sim:startSkill(p)'), 'shared cooldown bypass'
        # Cancel at candidate tick 4, with no new immunity on the forward dash.
        r.execute("p.y=0;p.vy=0;p.invul=0;p.face=1;p.inNow=256;p.inPressed=256;sim:setState(p,'idle');sim:neutral(p);assert(p.state=='dash' and p.invul==0);p.t=3;p.inNow=16;p.inPressed=16;sim:fighterTick(p);assert(p.state=='attack')")
        rows.append({'key':key,'oldDistance':distance[0],'newDistance':distance[1],'mirrorsAndVariants':True})
    r=engine(OUT/'candidate.lua');rng=random.Random(73)
    for _ in range(250):r.globals().sim.step(r.globals().sim,rng.randrange(1024),rng.randrange(1024))
    r.execute('clone=S.copy(sim)')
    for _ in range(1200):
        a,b=rng.randrange(1024),rng.randrange(1024)
        r.globals().sim.step(r.globals().sim,a,b);r.globals().clone.step(r.globals().clone,a,b)
        assert r.eval('dump(sim)==dump(clone)'), 'full state rollback divergence'
    boundaries=[]
    for key,mask,variant in [('nahida',2,'seed'),('nahida',1,'leaf'),('raidenshogun',2,'thunder'),('raidenshogun',8,'lunge')]:
        for face in [1,-1]:
            for outcome in ['hit','block','invulnerable','miss']:
                r=engine(OUT/'candidate.lua');owner=1 if key=='nahida' else 2
                chosen_mask=mask if variant!='lunge' or face==1 else 4
                r.execute(f"p=sim.f[{owner}];d=p.foe;p.x=0;p.face={face};p.y=0;p.vy=0;p.skillCd=0;p.inNow={chosen_mask};sim:setState(p,'idle');sim:setState(d,'idle');d.face={-face};d.x={face*(240 if variant=='seed' else 180 if variant=='thunder' else 150)*100};d.y=0;d.vy=0;d.invul={1000 if outcome=='invulnerable' else 0};d.inNow={8 if outcome=='block' and face==1 else 4 if outcome=='block' else 0};hp=d.hp;assert(sim:startSkill(p))")
                if outcome=='miss':r.execute('d.x=90000')
                r.execute("for t=1,90 do sim:fighterTick(p);sim:physics(p);sim:updateProj() end")
                if outcome=='hit':assert r.eval('d.hp<hp'),(key,variant,face,'did not hit')
                elif outcome=='block':assert r.eval('d.stats.blocks>0'),(key,variant,face,'not blocked')
                else:assert r.eval('d.hp==hp'),(key,variant,face,outcome)
                boundaries.append({'variant':variant,'face':face,'outcome':outcome})
    direction_checks=[]
    for key,owner in [('nahida',1),('raidenshogun',2)]:
        r=engine(OUT/'candidate.lua')
        for face in [1,-1]:
            for move in ['upLight','upHeavy','crouchLight','crouchHeavy']:
                low=move.startswith('crouch')
                for airborne in [False,True]:
                    r.execute(f"p=sim.f[{owner}];d=p.foe;p.x=0;p.y=0;p.face={face};d.hp=d.maxhp;d.ko=false;d.hitstop=0;d.x={face*10000};d.y={20000 if airborne else 0};d.invul=0;d.inNow=0;sim:setState(d,'{'air' if airborne else 'idle'}');hp=d.hp;sim:startMove(p,'{move}');p.t=p.move.startup;sim:attackUpdate(p)")
                    assert r.eval('d.hp<hp')==(not low or not airborne),(key,move,face,airborne)
                # Upper directions are anti-air intents, not overhead guard types;
                # lower directions must be crouch guarded.
                guard=(8 if face==1 else 4)|(2 if low else 0)
                r.execute(f"d.hp=d.maxhp;d.ko=false;d.hitstop=0;d.x={face*10000};d.y=0;d.vy=0;d.invul=0;d.inNow={guard};d.face={-face};sim:setState(d,'{'crouch' if low else 'idle'}');blocks=d.stats.blocks;sim:startMove(p,'{move}');p.t=p.move.startup;sim:attackUpdate(p)")
                assert r.eval('d.stats.blocks>blocks'),(key,move,face,'guard',r.eval('d.hp'),r.eval('p.move.level'))
                direction_checks.append({'key':key,'move':move,'face':face,'groundAirAndGuard':True})
    return {'cases':rows,'fullStateReplayTicks':1200,'skillOutcomes':boundaries,'directionalOutcomes':direction_checks}

def client(source,key):
    c=BenchClient(source);c.env.GF_FIRST_SCENE='fight'
    c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,'furina'],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
    wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    c.run(2)
    c.env.math.randomseed(73)
    c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=0;s.sim.f[1].x=-40000;s.sim.f[2].x=40000;s.sim.f[2].hitstop=100000;s.banners={};s.cine=nil;s.shakeT=0;s.camX=0;s.zoom=1;s.zoomPunch=0;return true end)()")
    return c

def geometry():
    rows=[]
    for key in ['nahida','raidenshogun']:
        for label in ['walk','attack']:
            pair=[]
            for variant in ['before','geometry']:
                c=client(OUT/(variant+'.lua'),key);instr=[];calls=[];pixels=[]
                for tick in range(360):
                    phase=tick%36
                    if label=='walk':
                        c.lua(f"(function()local s=GF_APP().scene;local p=s.sim.f[1];s.sim:setState(p,'walk');p.x=-30000;p.inNow=0;s.views[1].walkT={tick};p.hitstop=10000;return true end)()")
                    else:
                        c.lua(f"(function()local s=GF_APP().scene;local p=s.sim.f[1];s.sim:startMove(p,'heavy');p.t={phase};p.x=-30000;p.hitstop=10000;return true end)()")
                    c.max_instr=0;c.step();instr.append(c.max_instr);calls.append(c.calls[-1])
                    if tick in [119,239,359]:
                        path=OUT/f'{key}-{label}-{tick}-{variant}.png';c.render(path);pixels.append(np.array(Image.open(path)))
                view=c.lua('GF_APP().scene.views[1]')
                entries=0
                for slot in [view.slots[1],view.slots[2]]:
                    if slot.geometryPlans:
                        assert slot.geometryPlanCount<=6
                        entries+=sum(len(plan) for _,plan in slot.geometryPlans.items())
                pair.append({'instructionsMean':round(statistics.mean(instr[120:])),'instructionsPeak':max(instr),
                    'callsMean':round(statistics.mean(calls[120:]),2),'callsTotal':sum(calls),
                    'residentControls':c.stats()['controls'],'geometryNumbers':entries,'errors':list(c.H.err.values()),'pixels':pixels})
            assert not pair[1]['errors']
            assert pair[0]['residentControls']==pair[1]['residentControls']
            assert pair[0]['callsTotal']==pair[1]['callsTotal'],(key,label,'native calls changed')
            assert all(np.array_equal(a,b) for a,b in zip(pair[0]['pixels'],pair[1]['pixels']))
            for p in pair:p.pop('pixels')
            rows.append({'key':key,'action':label,'before':pair[0],'after':pair[1],'exactPixelChecks':3,
                'instructionChangePercent':round((pair[1]['instructionsMean']/pair[0]['instructionsMean']-1)*100,2)})
            print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
    return rows

def candidate_visuals():
    from PIL import ImageDraw
    tiles=[];results=[]
    for key,variants in [('nahida',[('seed',2),('leaf',1)]),('raidenshogun',[('thunder',2),('lunge',8)])]:
        c=client(OUT/'candidate.lua',key)
        for variant,mask in variants:
            c.lua(f"""(function()local s=GF_APP().scene;local p=s.sim.f[1];s.sim.proj={{}};p.x=-12000;p.y=0;p.hitstop=0;p.energy=0;p.skillCd=0;p.inNow={mask};s.sim:setState(p,'idle');s.sim:startSkill(p);p.t=p.move.startup-1;s.sim.f[2].x=40000;return true end)()""")
            c.step();c.lua('(function()local s=GF_APP().scene;local p=s.sim.f[1];p.hitstop=10000;s.sim.freeze=10000;for _,pr in ipairs(s.sim.proj) do pr.t=pr.delay+2 end;return true end)()')
            c.run(.35)
            path=OUT/f'{key}-{variant}.png';c.render(path)
            assert not list(c.H.err.values())
            if key=='nahida':assert not c.lua('GF_APP().scene.views[1].captureBmp.node.act'), 'old capture overlay leaked'
            img=Image.open(path).convert('RGB');img.thumbnail((800,450))
            tile=Image.new('RGB',(800,480),(18,23,33));tile.paste(img,(0,30))
            ImageDraw.Draw(tile).text((12,8),key+' / '+variant+' / OLD BODY PLACEHOLDER',fill='white')
            tiles.append(tile);results.append({'key':key,'variant':variant,'errors':False})
    sheet=Image.new('RGB',(1600,960));
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%2)*800,(i//2)*480))
    sheet.save(OUT/'prototype-review.png')
    return results

def mixed_workload():
    result=[]
    for key in ['nahida','raidenshogun']:
        pair=[]
        for name in ['before','candidate']:
            c=client(OUT/(name+'.lua'),key);instr=[];calls=[]
            for tick in range(360):
                if tick%60==0:
                    phase=(tick//60)%6
                    # Same input intent, distinct old/new rules. Reset cooldown only
                    # in this training probe, not in the production simulation.
                    c.lua("(function()local s=GF_APP().scene;local p=s.sim.f[1];p.hitstop=0;p.x=-40000;p.y=0;p.vy=0;p.invul=0;p.skillCd=0;s.sim:setState(p,'idle');p.inPressed=0;p.inNow=0;return true end)()")
                    if phase==0:c.lua('(function()local s=GF_APP().scene;local p=s.sim.f[1];p.inPressed=256;p.inNow=256;s.sim:neutral(p);return true end)()')
                    elif phase==1:c.lua('(function()local s=GF_APP().scene;local p=s.sim.f[1];p.inPressed=16;p.inNow=8|16;s.sim:neutral(p);return true end)()')
                    elif phase==2:c.lua('(function()local s=GF_APP().scene;local p=s.sim.f[1];p.inPressed=32;p.inNow=1|32;s.sim:neutral(p);return true end)()')
                    elif phase==3:c.lua('(function()local s=GF_APP().scene;local p=s.sim.f[1];p.inNow=2;s.sim:startSkill(p);return true end)()')
                    elif phase==4:c.lua(f"(function()local s=GF_APP().scene;local p=s.sim.f[1];p.inNow={1 if key=='nahida' else 8};s.sim:startSkill(p);return true end)()")
                    else:c.lua("(function()local s=GF_APP().scene;s.sim:startMove(s.sim.f[1],'light1');return true end)()")
                c.max_instr=0;c.step();instr.append(c.max_instr);calls.append(c.calls[-1])
            pair.append({'instructionsMean':round(statistics.mean(instr)),'instructionsPeak':max(instr),'callsMean':round(statistics.mean(calls),2),'callsPeak':max(calls),'controls':c.stats()['controls'],'errors':list(c.H.err.values())})
        assert not pair[1]['errors']
        result.append({'key':key,'before':pair[0],'after':pair[1],'scope':'same six input intents; changed rules and pictures, not pixel-equivalent'})
    return result

if __name__=='__main__':
    report={'rules':rules(),'geometry':geometry(),'candidateVisuals':candidate_visuals(),'mixedWorkload':mixed_workload(),'scope':'offline Lua53/mock only; no native FPS acceptance'}
    (OUT/'duo-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Duo rules, full-state replay and exact pixel comparison passed.')

"""Read-only comparison of supplied snapshot and current source; local mock evidence."""
from pathlib import Path
import sys, json, hashlib, difflib, statistics, importlib.util

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OLD=HERE/'snapshot'
OUT=ROOT/'outputs/smooth-comparison-20261013'
OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
sys.path.insert(0,str(ROOT/'game/tests'))
from harness import Client

def digest(b):return hashlib.sha256(b).hexdigest()
def write(name,v): (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def inventory():
    rows=[]
    for p in sorted(OLD.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(OLD);q=ROOT/rel;b=p.read_bytes()
        rows.append({'path':rel.as_posix(),'baselineBytes':len(b),'baselineSha256':digest(b),
            'currentBytes':q.stat().st_size if q.is_file() else None,
            'status':'same' if q.is_file() and digest(q.read_bytes())==digest(b) else 'changed' if q.is_file() else 'missingAtOriginalPath'})
    current={p.stem:p for p in (ROOT/'runtime/source').rglob('gf_*.lua')}
    mappings=[];diffs=[]
    for p in sorted((OLD/'game/lua').rglob('gf_*.lua')):
        q=current.get(p.stem);a=p.read_text(encoding='utf-8')
        b=q.read_text(encoding='utf-8') if q else ''
        if b.startswith("__loaders["):
            b=b[b.index('\n')+1:];b=b.rsplit('\nend',1)[0]
        normalized=lambda s:'\n'.join(x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('--'))
        mappings.append({'module':p.stem,'baseline':p.relative_to(OLD).as_posix(),
                         'current':q.relative_to(ROOT).as_posix() if q else None,
                         'status':'sameCodeIgnoringWrapperCommentsWhitespace' if normalized(a)==normalized(b) else 'changedOrSplit' if q else 'removedOrRenamed',
                         'baselineBytes':p.stat().st_size,'currentBytes':q.stat().st_size if q else 0})
        if q:diffs.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='baseline/'+p.name,tofile=q.relative_to(ROOT).as_posix()))
    write('all-snapshot-files.json',rows);write('runtime-module-map.json',mappings)
    (OUT/'runtime-source.diff').write_text(''.join(diffs),encoding='utf-8')
    write('inventory-summary.json',{'snapshotFiles':len(rows),'same':sum(r['status']=='same' for r in rows),
          'changed':sum(r['status']=='changed' for r in rows),'missingAtOriginalPath':sum(r['status']=='missingAtOriginalPath' for r in rows),
          'baselineModules':len(mappings),'runtimeSourceFiles':len(list((ROOT/'runtime/source').rglob('*.lua'))),
          'newRuntimeModules':sorted(set(current)-{p.stem for p in (OLD/'game/lua').rglob('gf_*.lua')})})

class Mock(Client):
    def _build_tree(self):
        super()._build_tree()
        self.rt.execute("local H=...;H.game.InstantiateClientUIControl=function(index,parent)return H.newControl('image','dynamic',parent,nil) end",self.H)

def wait(c,expr,limit=2500):
    for _ in range(limit):
        c.step()
        if c.lua(expr):return
    raise AssertionError('timeout '+expr)

def benchmark(version,script,pair,variant='normal',stage='training'):
    baseline=version=='baseline'
    c=Mock(script=script,build=False,pools={'img':10000 if baseline else 256,'txt':160 if baseline else 96,'btn':24},device='Mobile',canvas=(1600,900))
    c.env.GF_SETTINGS=c.rt.table_from({'quality':'lo'})
    if variant=='pool14000':c.env.GF_BATTLE_IMAGE_POOL=14000
    c.env.GF_FIRST_SCENE='fight'
    c.env.GF_FIRST_ARGS=c._to_lua({'chars':pair,'mode':'training' if stage=='training' else 'versus','stage':stage,'cpu':[False,False],'time':99,'rounds':2,'infinite':True,'seed':21})
    wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    startup={'callbacks':c.frame,'peakInstructions':c.max_instr,'peakCalls':max(c.calls),'stats':c.stats()}
    c.run(2)
    c.env.math.randomseed(73)
    if variant=='noDiagnostics':c.env.GF_PERF_ENABLED=False;c.env.GF_FPS_VISIBLE=False
    if variant=='staticBody':
        c.lua("(function() for _,v in ipairs(GF_APP().scene.views) do v.updatePose=function()end end return true end)()")
    if variant=='noAnimatedFx':
        c.lua("(function() for _,v in ipairs(GF_APP().scene.views) do v.drawAnimatedFx=function(self)if self.animFx then self.animFx.node:on(false) end end end return true end)()")
    if variant=='noBurstBackdrop':
        c.lua("(function() GF_APP().scene.drawBurstBackdrop=function(self) self.burstBg:clear();if self.burstEye then self.burstEye.node:on(false) end end return true end)()")
    rows=[]
    reset="""local s=GF_APP().scene;local sim=s.sim;sim.phase='fight';sim.freeze=0;sim.proj={};sim.events={};s.cine=nil
for i,f in ipairs(sim.f) do f.x=i==1 and -10000 or 10000;f.y=0;f.vx=0;f.vy=0;f.face=i==1 and 1 or -1;f.hp=f.maxhp;f.ko=false;f.energy=100;f.skillCd=0;f.stun=0;f.hitstop=0;f.frozen=0;f.invul=0;f.airMove=nil;f.coat=0;sim:setState(f,'idle') end
local p=sim.f[1]
"""
    for label,command,n in [('idle','',180),('walk','',180),('heavy',"assert(sim:startMove(p,'heavy'))",120),('E','assert(sim:startSkill(p))',120),('Q','assert(sim:startBurst(p))',210),('frozen','p.frozen=120',120),('bothQ','assert(sim:startBurst(p));assert(sim:startBurst(sim.f[2]))',210)]:
        c.lua('(function()'+reset+command+';return true end)()')
        if label=='walk':c.key('D',True)
        ins=[];calls=[];vis=[];created=[];rects=[];colors=[];sizes=[];parents=[];poses=[set(),set()]
        before=c.lua('GF_REQUIRE("gf_gfx").N');last=dict(before.items());peakFrame=None;lastCreated=0
        if not baseline:lastCreated=c.lua('GF_SECOND_POOL_STATUS().created')
        for t in range(n):
            c.max_instr=0;c.step();ins.append(c.max_instr);calls.append(c.calls[-1])
            now=dict(c.lua('GF_REQUIRE("gf_gfx").N').items())
            rects.append(now.get('bitmap',0)-last.get('bitmap',0));colors.append(now.get('col',0)-last.get('col',0));sizes.append(now.get('size',0)-last.get('size',0));parents.append(now.get('par',0)-last.get('par',0));last=now
            for i in [1,2]:
                key=c.lua(f'GF_APP().scene.views[{i}].front and GF_APP().scene.views[{i}].front.key')
                if key:poses[i-1].add(key)
            if t%15==0:vis.append(c.stats()['visibleImages'])
            if peakFrame is None or calls[-1]>peakFrame[0]:peakFrame=(calls[-1],t)
        if label=='walk':c.key('D',False)
        if not baseline:created=c.lua('GF_SECOND_POOL_STATUS().created')-lastCreated
        row={'label':label,'callbacks':n,'instructionsMean':round(statistics.mean(ins)),'instructionsPeak':max(ins),
             'callsMean':round(statistics.mean(calls)),'callsPeak':max(calls),'callsP95':sorted(calls)[int(.95*(n-1))],
             'colorWrites':sum(colors),'sizeWrites':sum(sizes),'parentWrites':sum(parents),'bitmapWrites':sum(rects),
             'visibleImagesSamplePeak':max(vis),'statsEnd':c.stats(),'createdDuring':created if not baseline else 0,
             'displayedPoseCounts':[len(p) for p in poses],'heavyCallbacks':sum(x>1000000 for x in ins)}
        rows.append(row);print(version,pair,variant,stage,label,row['callsMean'],row['callsPeak'],row['instructionsPeak'],flush=True)
        if label in ('idle','Q') and variant=='normal':c.render(OUT/f'{version}-{pair[0]}-{stage}-{label}.png')
    return {'version':version,'pair':pair,'variant':variant,'stage':stage,'startup':startup,'cases':rows}

if __name__=='__main__':
    inventory()
    # Assemble current bytes in memory order without touching runtime/dist.
    order=json.loads((ROOT/'runtime/source/order.json').read_text(encoding='utf-8'))
    working=OUT/'working-source.lua';working.write_bytes(b''.join((ROOT/'runtime'/p).read_bytes() for p in order))
    # Native comparison uses a frozen, delivered readable release; newer team-selection
    # workspace code has its own identity and must not be mistaken for the native build.
    current=ROOT/'outputs/all-codec-comparison-20261012_053101/保留的普通可读版.lua'
    old=OLD/'game/dist/genshin_fighter.lua'
    write('source-identities.json',{'baselineCommit':'c7d2c3517e37411b0b0b3675cd152e263656a223',
      'baselineLuaBytes':old.stat().st_size,'baselineLuaSha256':digest(old.read_bytes()),'currentLuaBytes':current.stat().st_size,'currentLuaSha256':digest(current.read_bytes()),
      'workingSourceSha256':digest(working.read_bytes()),'workingSourceBytes':working.stat().st_size,
      'currentRelease':'ordinary readable frozen 20261012_053101; exact native codec variant unknown',
      'scope':'user confirms same device/level, both local and online lag; mock measurements are not native FPS'})
    prev=OUT/'mock-comparison.json'
    result=json.loads(prev.read_text(encoding='utf-8'))['results'] if prev.exists() else []
    jobs=[('baseline',old,['raidenshogun','nahida'],'normal','training'),
          ('current',current,['raidenshogun','nahida'],'normal','training'),
          ('baseline',old,['furina','kamisatoayaka'],'normal','training'),
          ('current',current,['furina','kamisatoayaka'],'normal','training'),
          ('current',current,['raidenshogun','nahida'],'staticBody','training'),
          ('current',current,['raidenshogun','nahida'],'noDiagnostics','training'),
          ('current',current,['raidenshogun','nahida'],'pool14000','training'),
          ('current',current,['raidenshogun','nahida'],'noAnimatedFx','training'),
          ('current',current,['raidenshogun','nahida'],'noBurstBackdrop','training'),
          ('baseline',old,['raidenshogun','nahida'],'normal','mondstadt'),
          ('current',current,['raidenshogun','nahida'],'normal','mondstadt')]
    for job in jobs:
        if any((r['version'],r['pair'],r['variant'],r['stage'])==(job[0],job[2],job[3],job[4]) for r in result):continue
        result.append(benchmark(*job));write('mock-comparison.json',{'scope':'Lua53 mock at 60 callbacks/s; visible sampled every 15 callbacks; no native FPS/GPU/template-children evidence','results':result})


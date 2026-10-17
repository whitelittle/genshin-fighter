"""All four fighters, real move clocks, both Qs and repeated Qs on one client.

Counts refer to image instances in the mock, not physical native template children.
"""
from pathlib import Path
import json,sys,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient
from mock_flow import wait,ROOT

MOVES=['light1','light2','light3','heavy','crouchLight','crouchHeavy','airLight','airHeavy']
def status(c):
    s=dict(c.lua('GF_SECOND_POOL_STATUS()').items())
    s['free']=s['freeFirst']+s['freeSecond'];s['inUse']=s['total']-s['free']
    return s
def measure(source,chars):
    c=BenchClient(source);c.env.GF_FIRST_SCENE='fight'
    c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(chars),'mode':'training','cpu':c.rt.table_from([False,False]),'rounds':2,'time':99,'infinite':True,'seed':21})
    wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    rows=[]
    def run(label,duration,command=None):
        if command:
            c.lua("""(function()local s=GF_APP().scene;local sim=s.sim
sim.phase='fight';sim.freeze=0;sim.proj={};sim.events={}
for i,f in ipairs(sim.f)do f.x=(i==1 and -10000 or 10000);f.y=0;f.vx=0;f.vy=0;f.face=i==1 and 1 or -1;f.hp=f.maxhp;f.ko=false;f.energy=100;f.skillCd=0;f.stun=0;f.hitstop=0;f.frozen=0;f.invul=0;f.airMove=nil;sim:setState(f,'idle')end
"""+command+"\nreturn true end)()")
        before=status(c);max_total=before['total'];max_used=before['inUse'];min_free=before['free'];peak_calls=0;peak_instr=0;confirmed=False
        for _ in range(duration):
            c.max_instr=0;c.step();s=status(c)
            max_total=max(max_total,s['total']);max_used=max(max_used,s['inUse']);min_free=min(min_free,s['free'])
            peak_calls=max(peak_calls,c.calls[-1]);peak_instr=max(peak_instr,c.max_instr)
            if 'Q' in label:confirmed=confirmed or bool(c.lua('GF_APP().scene.sim.f[1].cinematicConfirmed or GF_APP().scene.sim.f[2].cinematicConfirmed'))
        after=status(c)
        rows.append({'label':label,'steps':duration,'before':before,'after':after,'maxResidentImages':max_total,'maxInUseImages':max_used,'minFreeImages':min_free,
          'createdDuring':after['created']-before['created'],'emergenciesDuring':after['emergencies']-before['emergencies'],'warningsDuring':after['warnings']-before['warnings'],
          'peakMockCalls':peak_calls,'peakMockInstructions':peak_instr,'QConfirmed':confirmed if 'Q' in label else None})
    run('warm-idle',60)
    for seat in [1,2]:
        for move in MOVES:
            if not c.lua(f"GF_APP().scene.sim.f[{seat}].kit.weapon['{move}']~=nil"):
                continue  # Exercise the actual weapon kit; catalyst has no light3.
            air="sim:setState(p,'air');p.y=12000;p.vy=600;" if move.startswith('air') else ''
            run(f'p{seat}-{move}',85,f"local p=sim.f[{seat}];{air}assert(sim:startMove(p,'{move}'),'p{seat}-{move}')")
        run(f'p{seat}-E',120,f'assert(sim:startSkill(sim.f[{seat}]))')
    # No scene recreation between these casts: keep every body/effect/cut-in buffer.
    for cycle in range(1,4):
        for seat in [1,2]:run(f'cycle{cycle}-p{seat}-Q',230,f'assert(sim:startBurst(sim.f[{seat}]))')
        run(f'cycle{cycle}-after-both-Q',30)
    # Their burst states overlap; production events may suppress the second cut-in,
    # but both providers still receive their real state timelines.
    run('both-Q-overlap',250,'assert(sim:startBurst(sim.f[1]));assert(sim:startBurst(sim.f[2]))')
    for seat in [1,2]:
        run(f'p{seat}-throw',100,f"local p,d=sim.f[{seat}],sim.f[{3-seat}];p.x=0;d.x=7000;sim:tryThrow(p)")
    run('final-idle',120)
    report={'pair':chars,'cases':rows,'lastPool':status(c),'errors':list(c.H.err.values())}
    assert not report['errors'],report['errors']
    assert all(r['QConfirmed'] for r in rows if '-p' in r['label'] and r['label'].endswith('-Q')),[(r['label'],r['QConfirmed']) for r in rows if r['label'].endswith('-Q')]
    print(json.dumps({'pair':chars,'total':report['lastPool']['total'],'maxInUse':max(r['maxInUseImages'] for r in rows),'minFree':min(r['minFreeImages'] for r in rows),
      'bothQ':[{'label':r['label'],'resident':r['after']['total'],'used':r['after']['inUse'],'created':r['createdDuring']} for r in rows if 'after-both' in r['label']]}),flush=True)
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--new-only',action='store_true');ap.add_argument('--delivery-pair',action='store_true');ap.add_argument('--legacy-pair',action='store_true');args=ap.parse_args()
    pairs=[['clorinde','arlecchino'],['arlecchino','arlecchino']] if args.delivery_pair else [['furina','kamisatoayaka'],['furina','furina'],['kamisatoayaka','kamisatoayaka']]
    if args.legacy_pair:pairs=[['raidenshogun','nahida'],['raidenshogun','raidenshogun'],['nahida','nahida']]
    data={'scope':'offline mock only, all eight attacks/E/Q/throw; 3 cycles of both Qs, overlap and idle; native FPS unknown','source':args.source.name,'pairs':[measure(args.source,p) for p in pairs]}
    args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


"""Wide canvas, fail-once allocation, fixed camera and surplus retirement checks."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait,ROOT

def main():
    c=RuntimeClient(device='Mobile',canvas=(2832,1280));c.env.GF_FIRST_SCENE='fight'
    c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['furina','kamisatoayaka']),'mode':'training','cpu':c.rt.table_from([False,False]),'infinite':True})
    wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    assert c.lua('GF_APP().env.root.anchorMinX==0 and GF_APP().env.root.anchorMaxX==1 and GF_APP().env.root.sizeDeltaX==0')
    c.lua("""(function()local s=GF_APP().scene;local p=s.sim.f[1];s.banners={};s.sim.phase='fight';p.x=-20000;s.sim.f[2].x=18000;s.sim.freeze=1000;p.state='burst';p.t=24;p.cinematicConfirmed=true;p.move=p.kit.burst;return true end)()""")
    c.run(.2)
    assert c.lua('GF_APP().scene.cut.L.items[1].w>=GF_APP().W')
    assert c.lua("(function()local b=GF_APP().scene.characterCuts.furina;for i=1,b.used do local n=b.kids[i];assert(n.y-n.h/2>=-228.5 and n.y+n.h/2<=.5)end;return true end)()")
    c.render(ROOT/'verification/wide-furina-Q.png')
    c.lua("""(function()local s=GF_APP().scene;local p=s.sim.f[1];p.state='walk';p.t=0;p.cinematicConfirmed=false;return true end)()""")
    c.run(.2)
    assert c.lua('math.abs(GF_APP().scene.views[1].root.sx-80/70)<.0001')
    c.render(ROOT/'verification/wide-furina-walk.png')
    c.rt.execute("""local H=...;H.game.DestroyClientUIControl=function(c)
assert(#c._kids==0,'must destroy a leaf');c.parent=nil;c._f.alive=false;return true end""",c.H)
    # Simulate a capacity fallback peak, then leave through the real scene exit.
    c.lua("(function()local G=GF_REQUIRE('gf_gfx');G.requestImages(16512);while not G.growImages(512) do end;GF_APP():go('menu');return true end)()")
    wait(c,"GF_APP().sceneName=='menu' and not GF_APP().poolNext")
    c.run(3)
    s=dict(c.lua('GF_SECOND_POOL_STATUS()').items())
    assert s['total']==16000 and s['destroyed']==512,s
    assert s['retired']==0 and s['trash']==0,s
    rematches=[]
    for _ in range(6):
        c.lua("(function()GF_APP():go('fight',{chars={'furina','kamisatoayaka'},mode='training',cpu={false,false},infinite=true});return true end)()")
        wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run'")
        c.run(.5)
        c.lua("(function()GF_APP():go('menu');return true end)()")
        wait(c,"GF_APP().sceneName=='menu' and not GF_APP().poolNext")
        c.run(3)
        r=dict(c.lua('GF_SECOND_POOL_STATUS()').items());assert r['total']==16000 and r['inUse']<=s['inUse']+100,r
        rematches.append({'total':r['total'],'inUse':r['inUse'],'created':r['created']})
    # Menu portraits cycle, so occupation differs by portrait. Resident capacity
    # and cumulative creation must stay flat across every teardown/reload.
    assert len({(r['total'],r['created']) for r in rematches})==1,rematches
    assert max(r['inUse'] for r in rematches[3:])<=max(r['inUse'] for r in rematches[:3]),rematches
    # Failure injection during initial scene loading; one attempt, then no retries.
    f=RuntimeClient(device='Mobile',canvas=(2832,1280))
    f.rt.execute('local H=...;H.failAttempts=0;H.game.InstantiateClientUIControl=function()H.failAttempts=H.failAttempts+1;return nil end',f.H)
    try:f.run(1)
    except RuntimeError as e:assert '第二池创建失败' in str(e),str(e)
    else:raise AssertionError('expected allocation failure')
    f.run(1)
    assert f.H.failAttempts==1,f.H.failAttempts
    assert f.lua('script.object.anchorMinX==0 and script.object.anchorMaxX==1 and script.object.sizeDeltaX>0')
    f.render(ROOT/'verification/wide-template-failure.png')
    g=RuntimeClient(device='Mobile',canvas=(1600,900));g.env.GF_FIRST_SCENE='select'
    wait(g,"GF_APP() and GF_APP().sceneName=='select' and GF_APP().scene.built==4 and not GF_APP().poolNext")
    stageCounts=[g.lua('GF_SECOND_POOL_STATUS().total')]
    g.lua("(function()GF_APP():go('vs',{chars={'furina','kamisatoayaka'},mode='training',cpu={false,false},infinite=true});return true end)()")
    wait(g,"GF_APP().sceneName=='vs' and not GF_APP().poolNext")
    stageCounts.append(g.lua('GF_SECOND_POOL_STATUS().total'))
    wait(g,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().poolNext")
    stageCounts.append(g.lua('GF_SECOND_POOL_STATUS().total'))
    assert stageCounts==[14672,15344,16000],stageCounts
    data={'mockOnly':True,'canvas':[2832,1280],'QBannerCoversWidth':True,'furinaWalkScale':80/70,
      'surplusAfterSceneExit':s,'sixSceneCycles':rematches,'failedAllocationAttempts':f.H.failAttempts,'failureCoversCanvas':True,
      'portraitWithinBanner':True,'threeLoadingStages':stageCounts,'extraPerStage':[672,672,656]}
    (ROOT/'verification/pool-lifecycle.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps(data))
if __name__=='__main__':main()

"""Actual UI team match, stock renderer handover, result and rematch (mock only)."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait
from team_select import card,button
from test_online import Relay

def check(device,canvas,out):
    c=RuntimeClient(device=device,canvas=canvas)
    c.env.GF_FIRST_SCENE='select';c.env.GF_FIRST_ARGS=c.rt.eval('{teamPreview=true}')
    wait(c,"GF_APP() and GF_APP().sceneName=='select' and GF_APP().scene.initialized and GF_APP().scene.built==6 and not GF_APP().poolNext")
    for index in (5,6,4):card(c,index,canvas);card(c,index,canvas)
    button(c,'teamConfirm',canvas)
    wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    assert c.lua("#GF_APP().scene.sim.teams[1]==3 and GF_APP().scene.sim.f[1].key=='clorinde'")
    # Exercise a real attack before the controlled KO boundary checks.
    c.key('J',True);c.run(.15);c.key('J',False);c.run(.7)
    rows=[]
    for side in (1,2,1,2,2):
        c.lua(f"(function()local s=GF_APP().scene;s.args.cpu={{false,false}};s.sim.phase='fight';s.sim.freeze=0;local f=s.sim.f[{side}];f.hp=0;f.ko=true;return true end)()")
        if side==2 and len(rows)==4:break
        wait(c,"GF_APP().scene.sim.phase=='fight' and GF_APP().scene.sim.phaseT>5")
        c.run(.8)
        assert c.lua("GF_APP().scene.views[1].key==GF_APP().scene.sim.f[1].key and GF_APP().scene.views[2].key==GF_APP().scene.sim.f[2].key")
        assert c.lua("GF_APP().scene.hud.faceKeys[1]==GF_APP().scene.sim.f[1].key and GF_APP().scene.hud.faceKeys[2]==GF_APP().scene.sim.f[2].key")
        rows.append(list(c.lua('GF_APP().scene.sim.teamIndex').values()))
        c.render(out/f'team-{device}-bout{len(rows)+1}.png')
    wait(c,"GF_APP().sceneName=='result' and not GF_APP().trans and not GF_APP().poolNext")
    c.render(out/f'team-{device}-result.png')
    c.lua("(function()GF_APP().scene:pick('again');return true end)()")
    wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    assert c.lua("GF_APP().scene.sim.teamIndex[1]==1 and GF_APP().scene.sim.teamIndex[2]==1 and GF_APP().scene.sim.f[1].key=='clorinde'")
    assert not list(c.H.err.values()),list(c.H.err.values())
    assert not c.heavy,c.heavy
    return {'device':device,'stockIndices':rows,'selectionToFightResultRematch':True,'maxMockInstructions':c.max_instr,'stats':c.stats()}

def online():
    relay=Relay(.06,.04,.03);clients=[]
    for slot in (1,2):
        c=RuntimeClient();c.env.GF_FIRST_SCENE='gf_scene_team_vs'
        c.env.GF_FIRST_ARGS=c.rt.eval("{teams={{5,3,1},{6,4,2}},teamOnline=true,teamIO={epoch=1,slot="+str(slot)+",pump=function()end,stop=function()end,reset=function()end}}")
        c.env.GF_TEAM_NETIO=relay.io(c,slot,1000+slot)
        # Existing relay fixture reads this field to mark delivery dirty; App still uses GF3Battle.
        c.env.GF_NETIO=c.env.GF_TEAM_NETIO;relay.clients.append(c);clients.append(c)
    def step():
        relay.tick(1/60)
        for c in clients:c.step()
    for _ in range(2400):
        step()
        if all(c.lua("GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans") for c in clients):break
    else:raise AssertionError('GF3 revealed roster failed to enter synchronized fight')
    for c in clients:
        assert c.lua("GF_APP().netFamily=='GF3Battle' and GF_APP().scene.sim.teams[1][3].key=='raidenshogun' and GF_APP().scene.sim.teams[2][3].key=='nahida'")
    for tick in range(600):
        if tick%30==0:
            for c in clients:c.key('J',True)
        if tick%30==10:
            for c in clients:c.key('J',False)
        step()
    hashes=[dict(c.lua('GF_APP().net.match.session.myHash').items()) for c in clients]
    common=set(hashes[0])&set(hashes[1]);assert len(common)>=3 and all(hashes[0][f]==hashes[1][f] for f in common)
    assert all(not c.lua('GF_APP().net.match.session.desync') and not list(c.H.err.values()) and not c.heavy for c in clients)
    return {'revealedRosterToGF3BattleFight':True,'commonConfirmedHashes':len(common),'rollbacks':[c.lua('GF_APP().net.match.session.stats.rollbacks') for c in clients],'mockOnly':True}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    RuntimeClient.source=args.source;args.out.mkdir(exist_ok=True,parents=True)
    results=[check('KeyboardAndMouse',(1600,900),args.out),check('Mobile',(1950,900),args.out)]
    results.append(online())
    (args.out/'team-flow.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(results)

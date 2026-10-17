"""Blind local CPU selection, explicit confirmation, ready/cancel and VS reveal."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait,ROOT

def act(c,code):
    c.lua('(function()local s=GF_APP().scene;'+code+';return true end)()')
    c.run(.15)

def card(c,index,canvas):
    pos=c.lua('(function()return {GF_APP().scene:cardPos('+str(index)+')} end)()')
    scale=float(c.lua('GF_APP().s'))
    x,y=canvas[0]/2+pos[1]*scale,canvas[1]/2+pos[2]*scale
    c.touch('down',x,y);c.step();c.touch('up',x,y);c.run(.3)

def button(c,name,canvas):
    t=c.lua('GF_APP().scene.L.taps["'+name+'"]')
    assert t and t['on'],name
    scale=float(c.lua('GF_APP().s'))
    x,y=canvas[0]/2+float(t['x'])*scale,canvas[1]/2+float(t['y'])*scale
    c.touch('down',x,y);c.step();c.touch('up',x,y);c.run(.15)

def check(device,canvas):
    c=RuntimeClient(device=device,canvas=canvas)
    c.env.GF_FIRST_SCENE='select';c.env.GF_FIRST_ARGS=c.rt.eval('{teamPreview=true}')
    wait(c,"GF_APP() and GF_APP().sceneName=='select' and GF_APP().scene.initialized and GF_APP().scene.built==#GF_APP().scene.roster and not GF_APP().poolNext")
    c.run(.5)
    out=ROOT/'verification/team-select-blind';out.mkdir(exist_ok=True)
    c.render(out/f'{device}-{canvas[0]}-initial.png')
    for i in range(1,5):
        assert c.lua('(function()local s=GF_APP().scene;local x,y=s:cardPos('+str(i)+');local a,b=GF_REQUIRE("gf_scene_select").cardPos(s,'+str(i)+');return x==a and y==b end)()')
    for index in (1,3,4):
        count=int(c.lua('#GF_APP().scene.teams[1]'))
        card(c,index,canvas)
        assert c.lua('#GF_APP().scene.teams[1]')==count
        if count==0:c.render(out/f'{device}-{canvas[0]}-confirm.png')
        card(c,index,canvas)
        assert c.lua('#GF_APP().scene.teams[1]')==count+1
    assert c.lua('GF_APP().scene.teams[1][1]==1 and GF_APP().scene.teams[1][2]==3 and GF_APP().scene.teams[1][3]==4')
    assert c.lua('next(GF_APP().scene.thumbs[2])==nil')
    c.render(out/f'{device}-{canvas[0]}-ready.png')
    button(c,'teamConfirm',canvas)
    assert c.lua('GF_APP().scene.ready[1]')
    button(c,'teamConfirm',canvas)
    assert c.lua('not GF_APP().scene.ready[1]')
    act(c,"s:action('back')")
    assert c.lua('#GF_APP().scene.teams[1]==2')
    card(c,1,canvas)
    assert not c.lua('GF_APP().scene.L.taps.teamConfirm.on')
    card(c,4,canvas);card(c,4,canvas)
    button(c,'teamConfirm',canvas)
    wait(c,"GF_APP().sceneName=='gf_scene_team_vs' and GF_APP().scene.built==6 and not GF_APP().trans")
    c.run(.3);c.render(out/f'{device}-{canvas[0]}-reveal.png')
    assert c.lua('#GF_APP().scene.teams[1]==3 and #GF_APP().scene.teams[2]==3')
    c.key('K',True);c.step();c.key('K',False)
    wait(c,"GF_APP().sceneName=='select' and GF_APP().scene.initialized and not GF_APP().trans")
    assert c.lua('#GF_APP().scene.teams[1]==0')
    assert not c.heavy,c.heavy
    return {'device':device,'canvas':canvas,'browseDoesNotConfirm':True,'fixedOrderReadyCancelHiddenCpuRevealReturn':True,'maxMockInstructions':c.max_instr,'heavy':c.heavy}

if __name__=='__main__':
    result=[check('KeyboardAndMouse',(1600,900)),check('Mobile',(1950,900)),check('Mobile',(2832,1280))]
    (ROOT/'verification/team-select-blind/report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    c=RuntimeClient(device='Mobile',canvas=(1950,900));c.env.GF_FIRST_SCENE='menu'
    wait(c,"GF_APP() and GF_APP().sceneName=='menu' and not GF_APP().poolNext")
    c.run(.5)
    out=ROOT/'verification/team-select-blind'
    assert c.lua("GF_APP().scene.items[1].label=='单人模式' and GF_APP().scene.items[2].label=='联机模式' and GF_APP().scene.items[3].label=='教学模式' and GF_APP().scene.items[4].label=='训练模式' and GF_APP().scene.items[7].label=='退出游戏'")
    c.render(out/'main-menu.png')
    act(c,"s:pick('modes')")
    assert c.lua("GF_APP().scene.items[1].label=='单人模式' and GF_APP().scene.items[2].label=='联机模式'")
    c.render(out/'mode-choice.png')
    act(c,"s.menu.o.onPick('solo')")
    assert c.lua("GF_APP().scene.items[2].label=='多角色对战'")
    c.render(out/'solo-rules.png')
    act(c,"s:modeMenu('net')")
    c.render(out/'online-rules.png')
    act(c,"s.menu.o.onPick('team')")
    wait(c,"GF_APP().sceneName=='select' and GF_APP().scene.initialized and not GF_APP().trans and not GF_APP().poolNext")
    c.run(.5)
    assert c.lua('GF_APP().scene.teamIO~=nil and #GF_APP().scene.teams[2]==0')
    c.render(out/'online-waiting.png')
    c.lua("(function()GF_APP():travel('menu');return true end)()")
    wait(c,"GF_APP().sceneName=='menu' and not GF_APP().trans and not GF_APP().poolNext")
    act(c,"s:pick('tutorial')")
    c.render(out/'tutorial-menu.png')
    act(c,"s.menu.o.onPick('back')")
    act(c,"s:pick('quit')")
    assert c.lua('GF_APP().quitPending~=nil and not GF_APP().closed')  # This fixture has no native close reply; stay pending, never fake settlement by returning to title.
    c=RuntimeClient(device='Mobile',canvas=(2832,1280));c.env.GF_FIRST_SCENE='select';c.env.GF_FIRST_ARGS=c.rt.eval('{teamPreview=true}')
    wait(c,"GF_APP() and GF_APP().sceneName=='select' and GF_APP().scene.initialized and GF_APP().scene.built==6 and not GF_APP().poolNext")
    for idx,key in [(5,'clorinde'),(6,'arlecchino')]:
        card(c,idx,(2832,1280));c.run(.7)
        assert c.lua('GF_APP().scene.previewKey')==key
        c.render(out/f'candidate-{key}.png')
        card(c,idx,(2832,1280))
    assert c.lua('GF_APP().scene.teams[1][1]==5 and GF_APP().scene.teams[1][2]==6')
    assert c.lua('#GF_REQUIRE("gf_roster")==6')  # Six now have complete battle providers.
    card(c,1,(2832,1280));card(c,1,(2832,1280));button(c,'teamConfirm',(2832,1280))
    wait(c,"GF_APP().sceneName=='gf_scene_team_vs' and GF_APP().scene.built==6 and not GF_APP().trans")
    c.run(.3);c.render(out/'candidate-reveal.png')
    assert not c.heavy,c.heavy

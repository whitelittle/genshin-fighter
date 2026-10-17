"""Full bootstrap/scene checks with the repository's native UI approximation."""
from pathlib import Path
import json,sys,random
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
sys.path.insert(0,str(REPO/'work/optimization-test-deps'))
sys.path.insert(0,str(REPO/'game/tests'))
from harness import Client
from test_online import Relay

class RuntimeClient(Client):
    source=ROOT/'dist/genshin_fighter.lua'
    def __init__(self,**kwargs):
        super().__init__(script=self.source,build=False,
                         pools={'img':256,'txt':160,'btn':24},**kwargs)
    def _build_tree(self):
        super()._build_tree()
        self.rt.execute('''local H=...
H.game.InstantiateClientUIControl=function(index,parent)
 return H.newControl('image','dynamic',parent,nil)
end''',self.H)

def wait(c,expr,limit=2200):
    for _ in range(limit):
        c.step()
        if c.lua(expr):return
    raise AssertionError('scene timeout: '+expr)

def local_flow(device,canvas,chars=(3,1)):
    a,b=chars
    c=RuntimeClient(device=device,canvas=canvas)
    wait(c,"GF_APP() and GF_APP().sceneName=='intro' and not GF_APP().poolNext")
    wait(c,"GF_APP().sceneName=='title' and GF_APP().scene.t>.8 and not GF_APP().trans")
    c.render(ROOT/f'verification/title-{device}.png')
    c.touch('down',canvas[0]/2,canvas[1]/2);c.step();c.touch('up',canvas[0]/2,canvas[1]/2)
    wait(c,"GF_APP().sceneName=='menu' and not GF_APP().trans")
    c.lua("(function()GF_APP().scene:pick('versus');return true end)()")
    c.lua("(function()GF_APP().scene.menu.o.onPick('vcpu');return true end)()")
    wait(c,"GF_APP().sceneName=='select' and GF_APP().scene.built==#(GF_APP().scene.roster or GF_REQUIRE('gf_roster')) and not GF_APP().poolNext and not GF_APP().trans")
    c.lua(f"(function()local s=GF_APP().scene;s.cur={{{a},{b}}};return true end)()")
    c.run(.2)
    c.render(ROOT/f'verification/select-{device}.png')
    c.lua("(function()local s=GF_APP().scene;s:confirm(1);s:confirm(2);return true end)()")
    wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    assert c.lua(f"GF_APP().scene.sim.f[1].key==GF_REQUIRE('gf_roster')[{a}].key")
    c.run(1.2)
    c.render(ROOT/f'verification/fight-{device}.png')
    c.lua("(function()GF_APP().scene:openPause();return true end)()")
    c.run(.2);assert c.lua('GF_APP().scene.paused')
    c.lua("(function()GF_APP().scene:closePause();return true end)()")
    c.run(.2)
    c.lua("(function()local s=GF_APP().scene;local p=s.sim.f[2];p.hp=0;p.ko=true;s.sim.winsNeeded=1;return true end)()")
    wait(c,"GF_APP().sceneName=='result' and not GF_APP().trans and not GF_APP().poolNext")
    c.lua("(function()GF_APP().scene:pick('again');return true end)()")
    wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    assert c.lua(f"GF_APP().scene.sim.f[1].key==GF_REQUIRE('gf_roster')[{a}].key")
    c.lua("(function()local s=GF_APP().scene; s.sim.f[2].hp=0;s.sim.f[2].ko=true;s.sim.winsNeeded=1;return true end)()")
    wait(c,"GF_APP().sceneName=='result' and not GF_APP().trans and not GF_APP().poolNext")
    c.lua("(function()GF_APP().scene:pick('select');return true end)()")
    wait(c,"GF_APP().sceneName=='select' and GF_APP().scene.built==#(GF_APP().scene.roster or GF_REQUIRE('gf_roster')) and not GF_APP().trans")
    return {'device':device,'canvas':canvas,'titleMenuSelectFightPauseResultRematchReselect':True,'characters':chars,
            'updates':c.frame,'maxMockInstructions':c.max_instr,'stats':c.stats()}

def network_flow(chars=(3,1)):
    a,b=chars
    relay=Relay(.06,.04,.03);clients=[]
    for i in [1,2]:
        c=RuntimeClient();c.env.GF_FIRST_SCENE='online';c.env.GF_NETIO=relay.io(c,i,1000+i)
        relay.clients.append(c);clients.append(c)
    def step():
        relay.tick(1/60)
        for c in clients:c.step()
    def until(expr,limit=2200):
        for _ in range(limit):
            step()
            if all(c.lua(expr) for c in clients):return
        raise AssertionError('network timeout '+expr)
    until("GF_APP() and GF_APP().sceneName=='select' and not GF_APP().trans and not GF_APP().poolNext")
    for i,c in enumerate(clients):
        c.lua(f"(function()local s=GF_APP().scene;s.cur[1]={a if i==0 else b};s.net.me.char=s.cur[1];return true end)()")
    for _ in range(30):step()
    for c in clients:c.lua("(function()GF_APP().scene:confirm(1);return true end)()")
    until("GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    for c in clients:assert c.lua(f"GF_APP().scene.args.chars[1]==GF_REQUIRE('gf_roster')[{a}].key and GF_APP().scene.args.chars[2]==GF_REQUIRE('gf_roster')[{b}].key")
    rng=random.Random(9);held=[None,None]
    for tick in range(720):
        if tick%9==0:
            for i,c in enumerate(clients):
                if held[i]:c.key(held[i],False)
                held[i]=rng.choice(['A','D','W','S','J','K','L','U','I']);c.key(held[i],True)
        step()
    for i,c in enumerate(clients):c.key(held[i],False)
    hashes=[dict(c.lua('GF_APP().net.match.session.myHash').items()) for c in clients]
    common=set(hashes[0])&set(hashes[1]);assert common and all(hashes[0][f]==hashes[1][f] for f in common)
    assert all(not c.lua('GF_APP().net.match.session.desync') for c in clients)
    rollbacks=[c.lua('GF_APP().net.match.session.stats.rollbacks') for c in clients]
    relay.muted.add(2)
    for _ in range(840):
        relay.tick(1/60);clients[0].step()
        if clients[0].lua("GF_APP().sceneName=='result'"):break
    assert clients[0].lua("GF_APP().sceneName=='result'")
    return {'characters':chars,'commonConfirmedHashes':len(common),'rollbacks':rollbacks,
            'latency':.06,'jitter':.04,'packetLoss':.03,'disconnectToResult':True}

if __name__=='__main__':
    import argparse,hashlib
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=RuntimeClient.source);ap.add_argument('--out',type=Path,default=ROOT/'verification/mock-flow.json');ap.add_argument('--chars',default='4,3');args=ap.parse_args()
    chars=tuple(int(x) for x in args.chars.split(','));assert len(chars)==2
    RuntimeClient.source=args.source
    (ROOT/'verification').mkdir(exist_ok=True)
    local=[]
    for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(900,1600)),('Mobile',(1600,900))]:
        result=local_flow(device,canvas,chars);local.append(result);print(json.dumps(result),flush=True)
    net=network_flow(chars);print(json.dumps(net),flush=True)
    args.out.write_text(json.dumps({'mockOnly':True,'clientSha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'local':local,'network':net},indent=2),encoding='utf-8')

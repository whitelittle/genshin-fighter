"""Inject a fatal update, exercise native cursor controls, restart and server close."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait
OUT=Path('outputs/error-recovery-20261015')
RuntimeClient.source=OUT/'release/genshin_fighter.lua'
class RecoveryClient(RuntimeClient):
    def _build_tree(self):
        super()._build_tree()
        self.signal_handlers={};self.handler_counts={}
        def register(_script,name,fn):
            self.signal_handlers[name]=fn
            self.handler_counts[name]=self.handler_counts.get(name,0)+1
        self.script.RegisterServerSignalHandler=register
def fail(c):
    c.lua("(function()GF_APP().update=function()error(\"attempt to index a nil value (local 'cfg')\")end;return true end)()")
    try:c.step()
    except RuntimeError as e:assert 'GF fatal' in str(e),str(e)
    assert c.lua('GF_APP().recovery.root.act and not GF_APP().view.act')
    c.H.err=c.rt.table()
def tap(c,i):
    pos=c.lua(f"(function()local a=GF_APP();local m=a.recovery.menu;return {{a.cw/2+m.o.x*a.s,a.ch/2+m:rowY({i})*a.s}} end)()")
    c.touch('down',pos[1],pos[2]);c.touch('up',pos[1],pos[2]);c.step()
def main():
    OUT.mkdir(exist_ok=True);results=[]
    for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1950,900)),('Mobile',(900,1600))]:
        c=RecoveryClient(device=device,canvas=canvas)
        wait(c,"GF_APP() and GF_APP().sceneName=='title' and GF_APP().scene.t>.8 and not GF_APP().poolNext")
        start=c.lua("GF_REQUIRE('gf_gfx').secondPoolStatus().total")
        for n in range(3):
            if n==0:
                c.lua("(function()GF_APP():go('menu');return true end)()")
                wait(c,"GF_APP().sceneName=='menu' and not GF_APP().poolNext")
                c.lua("(function()local s=GF_APP().scene;s:pick('versus');s.menu.o.onPick('vcpu');return true end)()")
                wait(c,"GF_APP().sceneName=='select' and GF_APP().scene.built==#GF_REQUIRE('gf_roster') and not GF_APP().poolNext and not GF_APP().trans")
                c.lua("(function()local s=GF_APP().scene;s.cur={5,5};s:confirm(1);s:confirm(2);return true end)()")
                wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
                c.lua("(function()GF_APP().scene.exit=function()error('broken teardown')end;return true end)()")
            if n==1:
                c.lua("(function()local g=GF_REQUIRE('gf_gfx');g.testImage=g.image;g.testText=g.textNode;g.image=function()error('pool exhausted')end;g.textNode=g.image;return true end)()")
            fail(c)
            if n==1:
                c.step();c.step()
                c.lua("(function()local g=GF_REQUIRE('gf_gfx');g.image=g.testImage;g.textNode=g.testText;return true end)()")
            if n==0:c.render(OUT/f'error-{device}-{canvas[0]}.png')
            if n==2:c.press('J')
            else:tap(c,1)
            wait(c,"not GF_APP().recovery.root.act and GF_APP().sceneName=='title' and GF_APP().scene.t>.8 and not GF_APP().poolNext")
            assert c.lua('GF_APP().input.usedBtn>0'),'title touch area lost after restart'
        c.render(OUT/f'restarted-{device}-{canvas[0]}.png')
        # A click without coordinates must work and up+click must not double pick.
        fail(c)
        c.lua("(function()local h=GF_APP().recovery.menu.areas[2].node.handlers;h.down();h.up();h.click();return true end)()")
        c.step();c.step()
        assert c.lua('GF_APP().quitPending and GF_APP().quitPending.nextSend>0')
        c.run(6)
        assert c.lua('GF_APP().quitPending.elapsed>5 and GF_APP().recovery.root.act')
        c.render(OUT/f'exit-wait-{device}-{canvas[0]}.png')
        close=c.lua("GF_REQUIRE('gf_signal_names').resolve('GF3Close')")
        assert c.handler_counts[close]==1,'restart duplicated server close handler'
        quitName=c.lua("GF_REQUIRE('gf_signal_names').resolve('GF3Quit')")
        assert any(row[1]==quitName for row in c.H.signals.values()),'quit signal not sent'
        c.signal_handlers[close](None,None)
        assert c.lua('GF_APP().closed') and not c.update_enabled
        assert not c.root._f.active and not c.root._f.visible
        assert not c.heavy,c.heavy
        results.append({'device':device,'canvas':canvas,'restartCycles':3,'battleFatalAndBrokenTeardownRestart':True,'exhaustedPoolsStillShowReservedButtons':True,'nativeTouchAndKeyboardRestart':True,'coordinateFreeExit':True,'quitSignalAndServerClose':True,'exitTimeoutKeepsErrorPage':True,'imagePoolBefore':start,'imagePoolAfter':c.lua("GF_REQUIRE('gf_gfx').secondPoolStatus().total"),'maxInstructions':c.max_instr})
        print(json.dumps(results[-1]),flush=True)
    (OUT/'recovery-tests.json').write_text(json.dumps({'mockOnly':True,'cases':results},indent=2),encoding='utf-8')
if __name__=='__main__':main()


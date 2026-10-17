"""Real legacy cfg access failure via jump/air-K/landing/ground-K, then pointer restart."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from error_recovery import RecoveryClient,tap
from mock_flow import wait
OUT=Path('outputs/clorinde-real-crash-recovery-20261015')
RecoveryClient.source=OUT/'release/genshin_fighter.lua'
def main():
    results=[]
    for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1950,900))]:
        c=RecoveryClient(device=device,canvas=canvas)
        wait(c,"GF_APP() and GF_APP().sceneName=='title' and GF_APP().scene.t>.8 and not GF_APP().poolNext")
        c.lua("(function()GF_APP():go('fight',{chars={'clorinde','clorinde'},cpu={false,false},mode='versus',stage='mondstadt'});return true end)()")
        wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight'")
        c.key('W',True)
        wait(c,"GF_APP().scene.sim.f[1].state=='air' and GF_APP().scene.sim.f[1].y>0",120)
        c.key('W',False);c.press('K')
        assert c.lua("GF_APP().scene.sim.f[1].airMoveId=='airHeavy'")
        wait(c,"GF_APP().scene.sim.f[1].y==0 and GF_APP().scene.sim.f[1].state=='idle'",180)
        assert c.lua("GF_APP().scene.sim.f[1].airMoveId=='airHeavy' and not GF_APP().scene.sim.f[1].airMove")
        c.render(OUT/f'01-landed-{device}.png')
        # Ground K runs through the original firearm implementation in the real App update.
        c.key('K',True);caught=None
        for _ in range(100):
            try:c.step()
            except RuntimeError as exc:
                caught=str(exc);c.H.err=c.rt.table();break
        c.key('K',False)
        assert caught and "attempt to index a nil value (local 'cfg')" in caught,caught
        assert c.lua("GF_APP().scene.sim.f[1].moveId=='heavy' and GF_APP().scene.sim.f[1].airMoveId=='airHeavy'")
        assert c.lua('GF_APP().recovery.root.act and not GF_APP().view.act')
        message=c.lua('GF_APP().recovery.message')
        c.run(.4);c.render(OUT/f'02-real-cfg-error-{device}.png')
        oldApp=c.lua('GF_APP()')
        tap(c,1)
        wait(c,"GF_APP().sceneName=='title' and GF_APP().scene.t>1 and not GF_APP().poolNext and not GF_APP().recovery.root.act")
        c.run(1.5);c.render(OUT/f'03-restarted-title-{device}.png')
        # Check the title's native start area still responds after real-fault recovery.
        c.touch('down',canvas[0]/2,canvas[1]/2);c.touch('up',canvas[0]/2,canvas[1]/2)
        wait(c,"GF_APP().sceneName=='menu' and not GF_APP().trans")
        c.render(OUT/f'04-returned-menu-{device}.png')
        assert not c.heavy,c.heavy
        row={'device':device,'canvas':canvas,'trigger':'native W jump -> native air K -> real landing -> native ground K','restoredOriginalClorindeModule':True,'noArtificialErrorCall':True,'error':message,'nativePointerRestartPassed':True,'titleStartToMenuPassed':True,'maxInstructions':c.max_instr,'scope':'offline native UI approximation; no device acceptance'}
        results.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
    (OUT/'real-crash-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()

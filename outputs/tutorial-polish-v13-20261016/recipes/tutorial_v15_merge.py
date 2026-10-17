"""Exercise one frozen merged script, keeping fault-injected builds test-only."""
from pathlib import Path
import argparse,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/tutorial-polish-v11-20261016'
SOURCE=OUT/'genshin_fighter.lua'
EVIDENCE=OUT/'verification'
sys.path.insert(0,str(ROOT/'runtime/tests'))
sys.path.insert(0,str(ROOT/'runtime/tools'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('suite',choices=['tutorial','flow','recovery','real-fault','controller']);args=ap.parse_args()
    EVIDENCE.mkdir(exist_ok=True)
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert before==json.loads((OUT/'merge-audit.json').read_text(encoding='utf-8'))['sha256']
    import mock_flow as flow
    flow.RuntimeClient.source=SOURCE
    original_wait=flow.wait
    def wait_notice(c,expr,limit=2800):
        for _ in range(limit):
            c.step()
            if c.lua("GF_APP() and GF_APP().scene and GF_APP().sceneName=='notice' and GF_APP().scene.t>.4 and not GF_APP().trans"):
                c.press('J')
            if c.lua(expr):return
        raise AssertionError(expr)
    if args.suite=='tutorial':
        for name in ['lumine_training','lumine_lesson','lumine_courses','lumine_notice']:
            path=ROOT/'runtime/tests'/f'{name}.py'
            code=path.read_text(encoding='utf-8')
            code=code.replace("OUT=ROOT.parent/'outputs/lumine-training-20261015'",f'OUT=Path({str(EVIDENCE)!r})')
            code=code.replace("RuntimeClient.source=OUT/'candidate.lua'",f'RuntimeClient.source=Path({str(SOURCE)!r})')
            exec(compile(code,str(path),'exec'),{'__file__':str(path),'__name__':name})
    elif args.suite=='flow':
        flow.wait=wait_notice;flow.ROOT=OUT
        local=[]
        for dev,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600))]:
            result=flow.local_flow(dev,canvas,(4,3));local.append(result);print(json.dumps(result),flush=True)
        net=flow.network_flow((4,3));print(json.dumps(net),flush=True)
        (EVIDENCE/'mock-flow.json').write_text(json.dumps({'sha256':before,'mockOnly':True,'local':local,'network':net},indent=2),encoding='utf-8')
    elif args.suite in ['recovery','real-fault']:
        import error_recovery as recovery
        recovery.OUT=EVIDENCE
        recovery.RecoveryClient.source=SOURCE
        recovery.wait=wait_notice
        if args.suite=='recovery':recovery.main()
        else:
            from merge_tutorial_v15 import modules,BOOT
            broken=ROOT/'outputs/clorinde-real-crash-recovery-20261015/release/genshin_fighter.lua'
            fixed_code=SOURCE.read_text(encoding='utf-8');broken_module=modules(broken.read_text(encoding='utf-8'))['gf_sim_clorinde']
            fixed_module=modules(fixed_code)['gf_sim_clorinde'];assert broken_module!=fixed_module
            test_code=fixed_code.replace(fixed_module,broken_module,1)
            test_path=EVIDENCE/'TEST_ONLY_original_cfg_failure.lua';test_path.write_text(test_code,encoding='utf-8')
            assert {k for k,v in modules(test_code).items() if v!=modules(fixed_code)[k]}=={'gf_sim_clorinde'}
            import clorinde_real_crash_recovery as real
            real.OUT=EVIDENCE;real.RecoveryClient.source=test_path;real.wait=wait_notice
            real.main()
    else:
        c=flow.RuntimeClient(device='Controller',canvas=(1600,900))
        wait_notice(c,"GF_APP() and GF_APP().sceneName=='title' and GF_APP().scene.t>.8 and not GF_APP().poolNext")
        # Explicit project layout events, not proof of physical platform keycaps.
        expected=[('PAD_X',16),('PAD_Y',32),('PAD_A',1),('PAD_B',256),('PAD_E',64),('PAD_Q',128)]
        c.lua('(function()GF_APP().input:clearUI();return true end)()')
        for key,bit in expected:
            c.key(key,True)
            assert c.lua(f'GF_APP().input.pads[1].held & {bit}')==bit,key
            c.key(key,False)
            assert c.lua(f'GF_APP().input.pads[1].held & {bit}')==0,key+' stuck'
        c.H.fireKey(c.root,'ControllerCharacterSkill4KeyDown')
        assert c.lua('GF_APP().input.pads[1].held & 512')==512
        c.H.fireKey(c.root,'ControllerCharacterSkill4KeyUp')
        assert c.lua('GF_APP().input.pads[1].held & 512')==0
        c.lua("(function()GF_APP():go('trainingcourses');return true end)()")
        c.run(.5);c.press('PAD_A')
        original_wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
        c.run(.3);c.render(EVIDENCE/'controller-teaching.png')
        c.lua("(function()GF_APP():go('trainingcourses');return true end)()")
        original_wait(c,"GF_APP().scene and GF_APP().sceneName=='trainingcourses' and not GF_APP().poolNext and not GF_APP().trans")
        c.run(.5);c.press('PAD_B')
        original_wait(c,"GF_APP().sceneName=='menu' and not GF_APP().trans")
        c.lua("(function()GF_APP():go('howto');return true end)()")
        c.run(1);c.render(EVIDENCE/'controller-layout.png')
        assert c.lua("GF_APP().scene.pages[1].lines[3][2]:find('X',1,true)~=nil")
        (EVIDENCE/'controller-checks.json').write_text(json.dumps({'sha256':before,'eventPressRelease':expected,'skill4ThrowPressRelease':True,'jumpConfirmSprintBackMenus':True,'scope':'project layout on simulator; platform physical bindings still require configuration and device verification'},indent=2),encoding='utf-8')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before,'tested artifact changed'
    (EVIDENCE/f'{args.suite}-passed.json').write_text(json.dumps({'sha256':before,'suite':args.suite,'passed':True,'offlineOnly':True},indent=2),encoding='utf-8')

if __name__=='__main__':main()

"""Reproduce the delivered crash and check the surgical fix in offline Lua 5.3."""
from pathlib import Path
import hashlib,json,sys
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'work/optimization-test-deps'))
from lupa.lua53 import LuaRuntime
OUT=REPO/'outputs/clorinde-shot-crash-fix-20261015'
base=(REPO/'outputs/clorinde-q-fx-20261014/release/genshin_fighter.lua').read_text(encoding='utf-8')
fixed=(OUT/'release/genshin_fighter.lua').read_text(encoding='utf-8')
boot=(REPO/'runtime/source/bootstrap.lua').read_text(encoding='utf-8')
trial=(REPO/'runtime/tests/clorinde-shot-transition.lua').read_text(encoding='utf-8')
def check(code,test):
    assert code.endswith(boot)
    rt=LuaRuntime(unpack_returned_tuples=True)
    rt.execute(code[:-len(boot)])
    rt.execute(test)
errors={}
for name,test,expected in [('airHeavy',trial,"nil value (local 'cfg')"),('airLight',trial.replace("{'airHeavy','airLight'}","{'airLight'}"),'wrong ground shot damage/configuration')]:
    try:check(base,test)
    except Exception as exc:
        errors[name]=str(exc);assert expected in str(exc);print(name+': '+str(exc).splitlines()[0])
    else:raise AssertionError('old delivered script did not reproduce '+name)
check(fixed,trial)
start=base.index("__loaders['gf_sim_clorinde']=function()")
end=base.index('__loaders[',start+1)
newend=fixed.index('__loaders[',start+1)
assert base[:start]==fixed[:start] and base[end:]==fixed[newend:]
report={'scope':'offline Lua 5.3 simulation; native device pending','oldDeliveredScriptReproduced':True,'beforeErrors':errors,'afterTransitionCases':16,'nearRangeChecksWrongAirLightMuzzle':True,'snapshotReplay':True,'onlyChangedModule':'gf_sim_clorinde','protocolVersion':8,'sourceSha256':hashlib.sha256((OUT/'release/genshin_fighter.lua').read_bytes()).hexdigest()}
(OUT/'reproduction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

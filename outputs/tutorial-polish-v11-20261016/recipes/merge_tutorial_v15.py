"""Freeze the tutorial plus V15 fixes; reject unexpected changes in V15 modules."""
from pathlib import Path
import hashlib,json,re,shutil,sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/tutorial-polish-v11-20261016'
TRAIN=ROOT/'outputs/lumine-training-20261015'
RECOVERY=ROOT/'outputs/error-recovery-20261015/release/genshin_fighter.lua'
CRASH=ROOT/'outputs/clorinde-shot-crash-fix-20261015/release/genshin_fighter.lua'
BOOT='local POOLS = {img = 256'

def sha(data):return hashlib.sha256(data).hexdigest()
def modules(code):
    matches=list(re.finditer(r"__loaders\['([^']+)'\]\s*=\s*function\(\)",code))
    assert len({m[1] for m in matches})==len(matches),'duplicate loaders'
    return {m[1]:code[m.start():matches[i+1].start() if i+1<len(matches) else code.index(BOOT,m.start())].strip() for i,m in enumerate(matches)}

def main():
    sys.path.insert(0,str(ROOT/'runtime/tools'))
    import build_lumine_training as builder
    builder.build()
    candidate=(TRAIN/'candidate.lua').read_text(encoding='utf-8')
    recovery=RECOVERY.read_text(encoding='utf-8');crash=CRASH.read_text(encoding='utf-8')
    a,b,c=modules(recovery),modules(candidate),modules(crash)
    changed=[k for k in a if a[k]!=b[k]]
    expected={'gf_app','gf_character_registry','gf_art','gf_kits','gf_scene_menu','gf_battle_pause','gf_scene_fight','gf_touch','gf_input','gf_scene_howto','gf_fview'}
    from raw_assets import module,TARGETS
    serialized={k for k in changed if k in TARGETS}
    order=json.loads((ROOT/'runtime/source/order.json').read_text(encoding='utf-8'))
    for name in serialized:
        path=next(ROOT/'runtime'/p for p in order if Path(p).stem==name)
        encoded,_=module(path,name)
        assert encoded.decode('utf-8').strip()==a[name],name+' V15 data changed'
    assert set(changed)==expected|serialized,(set(changed)-expected-serialized,expected-set(changed))
    sim=[k for k in a if k.startswith('gf_sim')]
    assert all(a[k]==b[k] for k in sim)
    assert c['gf_sim_clorinde']==a['gf_sim_clorinde']==b['gf_sim_clorinde']
    protected=['gf_app_recovery','gf_app_exit','gf_gfx','gf_ui']
    assert all(a[k]==b[k] for k in protected)
    assert candidate[candidate.index(BOOT):]==recovery[recovery.index(BOOT):]
    # Retain V15's lazy scalar-field export profile. Readable daily sources stay
    # intact; eagerly decoding their base64 fields caused >1M title callbacks.
    raw_prefix="GF_RAW_ASSET_TABLES=true\nGF_ASSET_PRELOAD_AT_START=false\nGF_ASSET_PROFILE='raw-literal-tables'\n"
    for name in serialized:candidate=candidate.replace(b[name],a[name],1)
    candidate=raw_prefix+candidate
    exported=modules(candidate)
    assert all(a[k]==exported[k] for k in serialized)
    first_loader=re.search(r"__loaders\['",candidate).start()
    old_first=re.search(r"__loaders\['",recovery).start()
    assert candidate[:first_loader].rstrip()==recovery[:old_first].replace('GF_FPS_VISIBLE=true','GF_FPS_VISIBLE=false').rstrip()
    OUT.mkdir(exist_ok=True)
    (OUT/'genshin_fighter.lua').write_text(candidate,encoding='utf-8')
    order=json.loads((ROOT/'runtime/source/order.json').read_text(encoding='utf-8'))
    source_order=[]
    for p in order:
        if p=='source/bootstrap.lua':
            for name in ['gf_lumine_training_data','gf_lawachurl_training_data','gf_character_lumine_training','gf_character_lawachurl_training','gf_aether_support_data','gf_paimon_training_avatar','gf_training_lesson','gf_lumine_training_rules','gf_training_attack','gf_sim_lumine_training','gf_training_extended','gf_aether_support','gf_training_courses','gf_training_coach','gf_scene_training_courses','gf_update_notice_data','gf_scene_update_notice']:
                dest=OUT/'source/teaching'/f'{name}.lua';dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(TRAIN/'source'/f'{name}.lua',dest);source_order.append(dest.relative_to(OUT).as_posix())
        dest=OUT/p;dest.parent.mkdir(parents=True,exist_ok=True)
        code=(TRAIN/'candidate'/p).read_text(encoding='utf-8')
        if Path(p).stem in serialized:code=a[Path(p).stem]+'\n'
        if p=='source/prefix.lua':code=raw_prefix+code
        dest.write_text(code,encoding='utf-8');source_order.append(p)
    assert '\n'.join((OUT/p).read_text(encoding='utf-8') for p in source_order)==candidate
    (OUT/'source/order.json').write_text(json.dumps(source_order,indent=2),encoding='utf-8')
    manifest={'scope':'project-local merge; offline verification only; no native acceptance or external publishing',
        'sha256':sha((OUT/'genshin_fighter.lua').read_bytes()),
        'v15RecoverySha256':sha(RECOVERY.read_bytes()),'v15CrashFixSha256':sha(CRASH.read_bytes()),
        'changedV15Modules':[k for k in changed if k not in serialized],'addedModules':sorted(b.keys()-a.keys()),
        'exportProfile':'V15 lazy scalar fields, no base64/LZ4; daily readable sources retained',
        'assetModulesMatchV15AfterExactRawSerialization':sorted(serialized),
        'allSimulationModulesIdenticalToV15':sim,'protectedRecoveryModulesIdentical':protected,
        'bootstrapIdenticalToV15':True,'sourceFiles':{p:sha((OUT/p).read_bytes()) for p in source_order}}
    (OUT/'merge-audit.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k!='sourceFiles'},ensure_ascii=True,indent=2))

if __name__=='__main__':main()

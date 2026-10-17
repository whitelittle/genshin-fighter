"""One-variable export from the published performance baseline, without rebuilding it."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/four-character-perf-gia-20261012_005019/gpt_20261012_005019_原神格斗_四角色帧率优化版.lua'
OUT=ROOT/'runtime/verification/pool-comparison'
def main():
    original=BASE.read_bytes()
    assert hashlib.sha256(original).hexdigest()=='76686f269aea5b287fd1a48fa0b1d96fe370f5ed78e0d7ce113a658ba851683d'
    changes=[(b'GF_PERF_ENABLED=true',b'GF_PERF_ENABLED=true\nGF_POOL_BACKGROUND_GROWTH=false\nGF_DYNAMIC_IMAGE_TEMPLATE_INDEX=1073741845'),
             (b'if free<growth.warning then',b'if GF_POOL_BACKGROUND_GROWTH~=false and free<growth.warning then'),
             (b"if phase~='fight' then G.growImages() end",b"if GF_POOL_BACKGROUND_GROWTH~=false and phase~='fight' then G.growImages() end")]
    code=original
    for old,new in changes:
        assert code.count(old)==1;code=code.replace(old,new)
    restored=code
    for old,new in reversed(changes):restored=restored.replace(new,old)
    assert restored==original
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/'genshin_fighter.lua').write_bytes(code)
    manifest={'sha256':hashlib.sha256(code).hexdigest(),'bytes':len(code),'baselineSha256':hashlib.sha256(original).hexdigest(),
      'onlyPerformanceChange':'disable proactive low-free-pool target increases and background growth; keep scene loading and exhaustion fallback',
      'environmentChange':'user supplied template resource index 1073741845',
      'inversePatchByteIdentical':True,'nativeDeviceTested':False}
    (OUT/'build.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest))
if __name__=='__main__':main()

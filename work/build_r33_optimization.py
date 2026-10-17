"""Build isolated A/B candidates from the supplied r33 archive, preserving other modules."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'work/package-review-20261008/GF_FORMAL_r33'
OUT = ROOT / 'outputs/r33-opt-20261008'

def build():
    source = (BASE / 'genshin_fighter.lua').read_text(encoding='utf-8-sig')
    manifest = {}
    for label, names in {'A': ['gf_art', 'gf_scene_fight'], 'B': ['gf_art', 'gf_scene_fight', 'gf_gfx']}.items():
        result = source
        for name in names:
            original = (BASE / 'modules/genshin_fighter' / (name + '.lua')).read_text(encoding='utf-8')
            replacement = (OUT / 'modules' / (name + '.lua')).read_text(encoding='utf-8')
            assert result.count(original) == 1, name
            result = result.replace(original, replacement, 1)
        result = result.replace("GF_RELEASE_ID='archive-merged-sd-r33'", f"GF_RELEASE_ID='r33-opt-{label}-20261008'", 1)
        path = OUT / f'GF_r33_opt_{label}.lua'
        path.write_text(result, encoding='utf-8', newline='\n')
        manifest[label] = {'file': path.name, 'modules_changed': names, 'bytes': path.stat().st_size,
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (OUT / 'build.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    build()

import concurrent.futures, json, pathlib, subprocess

root = pathlib.Path(__file__).resolve().parent
tree = json.loads((root / 'bvn-tree.json').read_text(encoding='utf-8'))
paths = [x['path'] for x in tree['tree'] if x['path'].endswith('.as') and (
    '/fighter/' in x['path'] or '/ctrler/effect/' in x['path'] or
    '/ctrler/game_ctrls/' in x['path'] or '/views/effects/' in x['path'] or
    x['path'].endswith(('EffectCtrl.as', 'SoundCtrl.as', 'GameCamera.as', 'GameStage.as', 'HitsUI.as'))
)]
paths += ['AGENTS.md', 'README.md', '.gitmodules', 'HOW2BUILD.md']
paths += ['.agents/map.md']
paths += [x['path'] for x in tree['tree'] if x['path'].endswith(('GameConfig.as', 'GameLogic.as', 'BaseGameSprite.as', 'GameInputer.as', 'EffectModel.as', 'EffectVO.as', 'FighterMC.as', 'FighterHitRange.as', 'FighterSpecialFrame.as', 'FighterHurtType.as', 'HitType.as'))]

def fetch(path):
    target = root / 'bvn-source' / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 100:
        return {'path': path, 'ok': True, 'bytes': target.stat().st_size}
    url = f"https://raw.githubusercontent.com/5DPLAY-Game-Studio/BleachVsNaruto/{tree['sha']}/{path}"
    result = subprocess.run(['curl.exe', '-f', '-sS', '-L', '--connect-timeout', '10', '--max-time', '45', '--retry', '1', url, '-o', str(target)], capture_output=True)
    return {'path': path, 'ok': result.returncode == 0, 'bytes': target.stat().st_size if target.exists() else 0}

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(fetch, paths))
(root / 'bvn-fetch-manifest.json').write_text(json.dumps({'sha': tree['sha'], 'files': results}, indent=2), encoding='utf-8')
print(json.dumps({'files': len(results), 'success': sum(x['ok'] for x in results), 'failed': [x['path'] for x in results if not x['ok']]}, ensure_ascii=False))

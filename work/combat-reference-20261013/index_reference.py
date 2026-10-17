import hashlib, json, pathlib, re, zipfile

root = pathlib.Path(__file__).resolve().parent
repos = {
    '死火': ('bvn', root/'bvn-source', 'https://github.com/5DPLAY-Game-Studio/BleachVsNaruto'),
    '街霸III': ('sf3', root/'sf3-archive'/'3s-decomp-main', 'https://github.com/crowded-street/3s-decomp'),
}
selected = {
 '死火': {
  'GameConfig.as', 'FighterMC.as', 'FighterAction.as', 'FighterKeyCtrl.as', 'FighterActionLogic.as',
  'FighterMcCtrler.as', 'FighterMcFloorHandler.as', 'FighterMcAirHandler.as', 'FighterMcHurtCtrl.as',
  'FighterMcGhostHandler.as', 'FighterMcActionCtrl.as', 'GameMainLogicCtrl.as', 'HitVO.as',
  'FighterHitModel.as', 'FighterCtrler.as', 'FighterMain.as', 'Bullet.as', 'FighterAttacker.as',
  'BaseFighterEventCtrl.as', 'FighterEventCtrl.as', 'GameLogic.as', 'EffectCtrl.as', 'EffectVO.as',
  'EffectModel.as', 'EffectHitHandler.as', 'EffectManager.as', 'EffectSlowHandler.as',
  'EffectShadowHandler.as', 'EffectBlackBackHandler.as', 'FighterEffectCtrl.as',
  'GameCamera.as', 'GameCameraCtrler.as', 'FighterCameraCtrler.as', 'FighterVoiceCtrler.as',
  'SoundCtrl.as', 'HitsUI.as',
 },
 '街霸III': {
  'Game.c', 'PLMAIN.c', 'PLMAIN2.c', 'PLPAT.c', 'PLPAT00.c', 'PLPATUNI.c', 'PLPNM.c',
  'CHARSET.c', 'CMD_MAIN.c', 'cmd_data.c', 'PLS01.c', 'PLS02.c', 'PLS03.c', 'HITCHECK.c',
  'HITPLPL.c', 'HITEFPL.c', 'HITPLEF.c', 'HITEFEF.c', 'PLPDM.c', 'PLPCA.c', 'PLPCU.c',
  'PLCNT.c', 'PLCNT2.c', 'EFFECT.c', 'EFF02.c', 'EFF09.c', 'SLOWF.c', 'Sound3rd.c',
  'SE.c', 'Se_Data.c', 'bg.c', 'bg_sub.c', 'cmb_win.c', 'spgauge.c', 'stun.c', 'VITAL.c',
 }
}
audit = {}
lines = ['# 战斗源码定位索引', '', '2026-10-13。自动目录与符号索引，仅用于定位；列出文件不等于逐函数完成审阅。研究结论与覆盖边界见同目录的《死火与街霸战斗表现源码研究_20261013.md》。', '']
for label, (key, folder, url) in repos.items():
    tree = json.loads((root/f'{key}-tree.json').read_text(encoding='utf-8'))
    blobs = {x['path']: x['sha'] for x in tree['tree'] if x['type'] == 'blob'}
    checked, missing, mismatches = [], [], []
    for path, sha in blobs.items():
        file = folder/path
        if not file.exists():
            missing.append(path)
            continue
        data = file.read_bytes()
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        checked.append({'path':path,'sha256':hashlib.sha256(data).hexdigest(),'git_blob_matches':blob==sha})
        if blob != sha: mismatches.append(path)
    info = {'tree_commit':tree['sha'], 'checked_files':len(checked), 'mismatches':mismatches, 'not_downloaded':missing, 'files':checked}
    if key == 'sf3':
        with zipfile.ZipFile(root/'sf3.zip') as z:
            info['archive_commit'] = z.comment.decode('ascii')
    audit[key] = info
    lines += [f'## {label}', '', f"源码仓库：[{label}]({url})。目录查询提交：`{tree['sha']}`；已取文件与该树的 Git blob 校验差异：{len(mismatches)}。", '', '| 文件 | 入口定位 |', '|---|---|']
    for file in sorted(folder.rglob('*')):
        if file.name not in selected[label] or not file.is_file(): continue
        rel = file.relative_to(folder).as_posix()
        if key == 'sf3' and '/Source/Game/' not in rel: continue
        text = file.read_text(encoding='utf-8', errors='replace')
        symbols=[]
        for num, line in enumerate(text.splitlines(), 1):
            if key=='bvn':
                match=re.search(r'(?:public|private|protected)\s+(?:static\s+)?(?:override\s+)?function\s+(?:get\s+|set\s+)?(\w+)\s*\(',line)
            else:
                match=re.match(r'(?:static\s+)?(?:void|s32|s16|u8|u16|s8|u32)\s+(\w+)\s*\([^;]*\)\s*\{',line)
            if match: symbols.append(f"[{match.group(1)}:{num}]({url}/blob/{tree['sha']}/{rel}#L{num})")
        source=f"[{file.name}]({url}/blob/{tree['sha']}/{rel})"
        lines.append(f"| {source} | {'、'.join(symbols) if symbols else '数据表 / 定义'} |")
    lines.append('')
(root/'source-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
out=root.parents[1]/'docs'/'current'/'战斗源码定位索引_20261013.md'
out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:{x:v for x,v in a.items() if x not in ('files','not_downloaded')} for k,a in audit.items()},ensure_ascii=False))

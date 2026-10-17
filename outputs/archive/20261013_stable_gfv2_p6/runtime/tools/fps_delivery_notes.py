"""Record the callback FPS delivery; native testing remains pending."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2]
batch=json.loads((ROOT/'runtime/verification/fps-delivery-batch.json').read_text(encoding='utf-8-sig'))
folder=ROOT/batch['main']
manifest=json.loads((folder/'delivery.json').read_text(encoding='utf-8'))
manifest.update(templateResourceIndex=1073741845,retainedBattlePool=16000,loadingStages=[14672,15344,16000],backgroundGrowth=False,fpsMeasurement='OnUpdate callback count / raw dt, not GPU presents',fpsVisible=True)
(folder/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for name in ['logic.json','mock-flow.json','fps-monitor.json','widescreen-after.json']:
    shutil.copyfile(ROOT/'runtime/verification'/name,folder/name)
shutil.copyfile(ROOT/'runtime/verification/fps-fight.png',folder/'FPS显示预览.png')
script=next(f['filename'] for f in manifest['files'] if f['kind']=='luaOnly')
(folder/'安装说明.md').write_text(f'''# FPS检测版

已有工程导入 `{script}`，替换GF_HOST旧主脚本，仅保留一份。A用于整套UI导入，B图片模板默认索引1073741845。继承16000图片池、672／672／656三段加载、宽屏与角色修复。

左侧血条及能量条下方显示FPS、采样窗最大间隔和累计丢时，大招时仍显示。FPS为Lua更新回调频率，约一秒刷新，不是GPU呈现计数。丢时增长表示触及既有逻辑补算上限；单次命中伤害不按FPS比例变化。真机数据须导入后观察，本批仅离线验证。

详情见工作区 `docs/current/FPS检测与伤害判定_20261012.md`。源码SHA256 `{manifest['sourceSha256']}`。交付目录使用 `%LOCALAPPDATA%Low/miHoYo/原神/BeyondLocal/Beyond_Local_Export`，旧文件保留。
''',encoding='utf-8')
for rel,line in [('AI_START.md','> 2026-10-12 最新FPS检测：战斗左侧血条下显示回调FPS／最大间隔／累计丢时；保留原补算与伤害规则，补齐250ms截断丢时诊断。60／30／15回调对照180拍大招伤害与哈希一致，真机未测。见[检测记录](docs/current/FPS检测与伤害判定_20261012.md)。'),('runtime/README.md','最新FPS检测交付：`'+batch['main']+'`；详情 `../docs/current/FPS检测与伤害判定_20261012.md`。'),('docs/current/V4_执行与验收台账_20261009.md','2026-10-12：FPS监测接入；60／30／15回调伤害／状态对照、96文字池训练暂停、既有逻辑／流程检查通过；真机待测，详见[FPS记录](FPS检测与伤害判定_20261012.md)。')]:
    p=ROOT/rel;p.write_text(p.read_text(encoding='utf-8')+'\n'+line+'\n',encoding='utf-8')
(ROOT/'runtime/verification/latest-gia.json').write_text(json.dumps({'main':batch['main'],'sourceSha256':manifest['sourceSha256']},ensure_ascii=False,indent=2),encoding='utf-8')

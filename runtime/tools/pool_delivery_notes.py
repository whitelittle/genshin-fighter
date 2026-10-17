"""Record verified pool delivery with relative paths and anonymous device feedback."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2]
def main():
    batch=json.loads((ROOT/'runtime/verification/pool-delivery-batch.json').read_text(encoding='utf-8-sig'))
    for kind in ['main','comparison']:
        folder=ROOT/batch[kind];manifest=json.loads((folder/'delivery.json').read_text(encoding='utf-8'))
        is_main=kind=='main';manifest.update(templateResourceIndex=1073741845,backgroundGrowth=False,
            retainedBattlePool=16000 if is_main else 14000,loadingStages=[14672,15344,16000] if is_main else [14000,14000,14000],
            nativeDeviceTested=False,verification='offline mock only')
        (folder/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        files=['logic.json','mock-flow.json','skills-pool-16000.json','pool-lifecycle.json'] if is_main else ['pool-comparison-check.json','skills-pool-no-background.json']
        for name in files:
            source=ROOT/'runtime/verification'/name
            if source.exists():shutil.copyfile(source,folder/name)
        script=next(f['filename'] for f in manifest['files'] if f['kind']=='luaOnly')
        description=('性能版保留池16000，新增2000分在选人／VS／战斗（672／672／656）。关闭主动预扩池，保留耗尽补充及离场超额回收；宽屏遮罩、条幅内头像和芙宁娜前走尺寸已修订。'
          if is_main else '对照版保留原14000池，性能上只关闭低空闲主动预扩池。其余沿用005019性能版，另更新当前工程模板索引；不含16000预留与本次显示修订。')
        text=f'''# {manifest['name']}

{description}

已有工程导入 `{script}`，替换GF_HOST上的主脚本，解除旧挂载，只保留一份游戏主脚本。A已含挂载，重装时使用A+B；不要再同时挂仅脚本。沿用GFV2服务端，联机双方同版。

默认模板资源索引1073741845。如工程设置了GF_IMAGE_TEMPLATE_INDEX参数，该参数优先，需与实际B模板索引一致。B文件内控件GUID不是模板资源索引。

全技能、双方三轮大招、回收与流程结果见附带报告和工作区 `docs/current/双角色图元池与三段加载修复_20261012.md`。模拟器通过不等于真机FPS／兼容性通过，真机复测仍待完成。

GIA已按既有授权复制到 `%LOCALAPPDATA%Low/miHoYo/原神/BeyondLocal/Beyond_Local_Export`，复制后核对SHA256；旧文件不覆盖。仅脚本与A二选一使用。源码SHA256：`{manifest['sourceSha256']}`。
'''
        (folder/'安装说明.md').write_text(text,encoding='utf-8')
    (ROOT/'runtime/verification/latest-gia.json').write_text(json.dumps({'main':batch['main'],'comparison':batch['comparison'],'sourceSha256':json.loads((ROOT/batch['main']/'delivery.json').read_text(encoding='utf-8'))['sourceSha256']},indent=2),encoding='utf-8')
    for path,line in [
        ('AI_START.md','> 2026-10-12 最新性能修订：双芙宁娜14000池复现预扩池；默认16000，额外2000分选人／VS／战斗672／672／656，主动预扩池关闭、耗尽保底与离场超额回收保留。模板索引1073741845；宽屏、条幅头像及芙宁娜前走倍率修订。先读[双角色图元池记录](docs/current/双角色图元池与三段加载修复_20261012.md)。离线通过，真机待复测。'),
        ('runtime/README.md','最新性能交付：16000预留池分三段加载，模板索引1073741845；见 `../docs/current/双角色图元池与三段加载修复_20261012.md`。14000关闭后台扩池对照另包保留。'),
        ('docs/current/V4_执行与验收台账_20261009.md','2026-10-12：双角色全技能与三轮双方Q池计数、三段加载、六次场景循环及512超额回收通过；原生FPS未验收。模板索引按最新反馈改1073741845，头像条幅裁切及前走显示倍率修订。见[本批记录](双角色图元池与三段加载修复_20261012.md)。')]:
        p=ROOT/path;content=p.read_text(encoding='utf-8');p.write_text(content+'\n'+line+'\n',encoding='utf-8')
if __name__=='__main__':main()

"""Record the wide-screen delivery with anonymous feedback and relative paths."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2]
def main():
    batch=json.loads((ROOT/'runtime/verification/wide-delivery-batch.json').read_text(encoding='utf-8-sig'))
    folder=ROOT/batch['main'];manifest=json.loads((folder/'delivery.json').read_text(encoding='utf-8'))
    manifest.update(templateResourceIndex=1073741845,retainedBattlePool=16000,loadingStages=[14672,15344,16000],
      backgroundGrowth=False,wideCanvas=[2832,1280],pageStatesChecked=20,safeCanvasReproduction=[2648,1280],nativeDeviceTested=False)
    (folder/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ['logic.json','mock-flow.json','widescreen-before.json','widescreen-after.json','pool-lifecycle.json']:
        shutil.copyfile(ROOT/'runtime/verification'/name,folder/name)
    shutil.copyfile(ROOT/'runtime/verification/widescreen/after-safe-inset/all-pages.png',folder/'宽屏逐页预览.png')
    script=next(f['filename'] for f in manifest['files'] if f['kind']=='luaOnly')
    (folder/'安装说明.md').write_text(f'''# 宽屏逐页修复版

版本 {batch['stamp']}。已有工程导入 `{script}`，替换GF_HOST上的旧主脚本，只保留一份游戏脚本。A自带挂载，新建／重装使用A+B；不要同时挂仅脚本。B模板默认资源索引1073741845，显式GF_IMAGE_TEMPLATE_INDEX参数仍优先。

保留16000图片池、选人／VS／战斗三段新增672／672／656、关闭主动预扩池和耗尽保底。保留头像条幅裁切、芙宁娜前走倍率及GFV2联机。

背景／全屏遮罩与安全区域内交互分开：根容器跟随真实父画布，背景／加载／暂停／大招覆盖延伸到边缘，文字和按钮保留安全布局。修复标题与选人已建控件在尺寸变化后的定位；训练暂停空文字和未展开出招表不再提前占用文字池。

2832×1280两组模型、每组20页面／状态逐页截图与覆盖检查通过；349原始像素状态、旧双角色3600拍全状态差分、横竖屏流程及联机回滚通过。安全区模型是假设复现，不是手机API实测。原生屏幕是否完全覆盖仍需复测；不把模拟器登记成真机验收。

交付至 `%LOCALAPPDATA%Low/miHoYo/原神/BeyondLocal/Beyond_Local_Export`；旧文件不覆盖。源码SHA256 `{manifest['sourceSha256']}`。细节见工作区 `docs/current/宽屏逐页适配修复_20261012.md`。
''',encoding='utf-8')
    doc='''# 宽屏逐页适配修复

## 真机观察与待验证推断

匿名玩家提供2832×1280手机截图：加载、标题、选人仍有左右露边，要求模拟相同大小逐页修复。截图中的账号信息不留存。

旧版将根容器显式设置成GetUICanvasSize返回尺寸，同时把背景与操作区使用同一宽高。如果该尺寸是UI安全布局区域，而外层画布更宽，根容器会缩窄。此为待验证的原生原因，当前没有手机API日志；离线用真实屏2832×1280、UI区域2648×1280构造复现。旧版该模型底色边界为[92,0,2740,1280]，两侧未覆盖。

## 程序修改

- GF_ROOT继续锚定实际父画布全宽高，取消用安全区尺寸收窄根容器。操作区W/H及缩放规则保留。
- 单一App.cover入口绘制全屏覆盖，左右至少120、上下至少80设计单位的边缘余量。永久底色使用明确尺寸，避免依赖图片控件对零尺寸伸展的差异。此为有界余量，不声称已测得手机安全区。
- 开场、加载、菜单公共背景、VS、联机、组件展示、战斗加载、暂停、传统Q、新角色Q与闪屏、场景雾层、转场全部接入；大招条幅延伸到边缘，头像仍保留已修裁切。
- 标题角色和全屏开始点击区、选人预览／卡片／触摸区在画布变化后重新定位。角色卡片本身不拉伸。
- 真实96文字池发现训练暂停可能耗尽：Menu不再为缺省编号／空副标题／不存在的数值占用文字；未展开出招表不提前分配文字。展开出招表的实际功能和内容保留。
- 图片模板索引1073741845、16000池、672／672／656三次加载、应急补充及离场回收保留。模拟器新增2832×1280手机宽屏选项并作为默认。

## 模拟器验证

两组2832×1280物理画布，各检查20个页面／状态：池加载、开场、标题、菜单、设置、出招表三页、选人、选人后过渡加载、VS、战斗加载、战斗、暂停、展开出招表、芙宁娜Q、绫华Q、结算、联机、组件展示。普通画布与收窄UI区域模型均覆盖四边，加载遮罩左右边缘像素为纯黑；截图已逐页看过。原游戏没有独立场地选择页，确认角色后直接转入VS，不把加载截图标作场地选择。

标题点击区、选人卡片触摸区和预览在尺寸变化后更新；实际96文字池的训练暂停／展开出招表通过。继承的完整桌面／手机横竖屏流程、双端60ms延迟／40ms抖动／3%丢包回滚通过。旧双角色3600拍全状态一致、349原始像素状态重建及切片预算通过；六次菜单／战斗循环、512超额回收与三段真实加载池计数通过。

报告：`runtime/verification/widescreen-after.json`、`widescreen-before.json`、`mock-flow.json`、`logic.json`、`pool-lifecycle.json`。逐页图片：`runtime/verification/widescreen/after-full/`和`after-safe-inset/`。

## 真机待验收

本批模拟器没有原生安全区、裁切、层级、字体与热负载的完整行为。须用新版替换唯一GF_HOST脚本，在同一手机确认四边、点击位置、大招及长时间战斗。当前不登记真机FPS或适配验收。
'''
    (ROOT/'docs/current/宽屏逐页适配修复_20261012.md').write_text(doc,encoding='utf-8')
    for rel,line in [('AI_START.md','> 2026-10-12 最新宽屏修复：2832×1280逐页与安全区收窄模型，各20状态检查通过；GF_ROOT恢复父画布伸展，全屏覆盖统一、标题／选人尺寸变化重排，并修训练暂停文字池预占用。继承16000三段池与模板索引1073741845。先读[宽屏记录](docs/current/宽屏逐页适配修复_20261012.md)，真机待复测。'),
      ('runtime/README.md','最新宽屏交付：`'+batch['main']+'`；2832×1280模拟器默认，详见 `../docs/current/宽屏逐页适配修复_20261012.md`。'),
      ('docs/current/V4_执行与验收台账_20261009.md','2026-10-12：宽屏逐页40截图／状态、96文字池训练暂停与出招表、尺寸变化重排、流程及回滚检查通过。新版独立导出，原生复测未完成。见[宽屏记录](宽屏逐页适配修复_20261012.md)。')]:
        p=ROOT/rel;p.write_text(p.read_text(encoding='utf-8')+'\n'+line+'\n',encoding='utf-8')
    (ROOT/'runtime/verification/latest-gia.json').write_text(json.dumps({'main':batch['main'],'sourceSha256':manifest['sourceSha256']},indent=2),encoding='utf-8')
if __name__=='__main__':main()

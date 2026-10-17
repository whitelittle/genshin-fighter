from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'outputs/movement-fix-20261013'
report=json.loads((OUT/'verification/report.json').read_text(encoding='utf-8'))
manifest=json.loads((OUT/'build.json').read_text(encoding='utf-8'))
assert manifest['sha256']==report['afterSha256']
for name in ['logic.json','mock-flow.json']:
 assert json.loads((OUT/name).read_text(encoding='utf-8'))['clientSha256']==manifest['sha256']
rows=['|角色／方向|平均调用 前→后|调用峰值 前→后|姿势落后回调 前→后|','|---|---:|---:|---:|']
names={'raidenshogun':'雷电','nahida':'纳西妲','furina':'芙宁娜','kamisatoayaka':'绫华'}
for r in report['cases']:
 b,a=r['before'],r['after']
 rows.append(f"|{names[r['key']]}／{'前走' if r['direction']=='walk' else '后退'}|{b['callsMean']} → {a['callsMean']}|{b['callsPeak']} → {a['callsPeak']}|{b['latePoseCallbacks']} → {a['latePoseCallbacks']}|")
notes=f'''# 普通移动专项修复候选

2026-10-13。匿名玩家确认普通移动也比早期v2不流畅，因此本批优先处理移动显示时序和换帧写入。真机复测尚未进行。

## 安装与对照

已有上一批四角色工程，使用本目录`gpt_20261013_原神格斗_移动专项修复_仅脚本.gia`更新唯一的`GF_HOST`脚本；沿用GFV2节点和模板索引1073741845。双方联机使用同一份候选。完整重新安装可使用A+B；B与上一批字节一致。不要同时运行旧、新两份GF_HOST脚本。

本目录没有复制到外部应用导出目录，也未修改外部工程。只在项目本地生成可导入候选。原发布指针、历史Lua和GIA均保留。

本候选以`outputs/all-codec-comparison-20261012_053101/保留的普通可读版.lua`为底，仅替换五个渲染模块：`gf_gfx`、`gf_fview`、`gf_battle_loading`及芙宁娜／绫华的显示provider。其余模块逐字节保留，未带入后来的三人选人/GF3界面。因此与上一批真机版比较时，主要变量是本次移动修复。

候选Lua {manifest['bytes']:,}字节，SHA256 `{manifest['sha256']}`；开发源码仍未压缩、未精简。

## 程序修正

1. 补齐四角色前走／后退的下一姿势预取。后台槽在当前姿势停留时写下一姿势，完成后继续隐藏，直到原动作时钟要求该姿势才发布。双缓冲、所有姿势、帧持续时间、镜像和锚点保留。
2. 移动后台预取每人最多160矩形／显示回调；正常换姿势仍保留原320／520上限。启动和低回调率造成的积压不能因预取漏掉模拟事件。
3. 加载幕下分片准备首张前走姿势，仍用既有后台槽和容量，不新增位图槽／图片池。这样首次移动不用集中启用一整批从未使用的身体矩形。待机预取与加载预热协调，避免两者反复覆盖导致加载无法完成。
4. 芙宁娜／绫华的同一连续调色板索引组内按已有尺寸匹配矩形，减少SetSizeDelta。禁止跨颜色组移动任何矩形；同一RGBA、同一形状的矩形绘制次序可交换，包含半透明叠加。原始图片、像素、缩放、锚点和帧表不改。透明度查表仍按原组索引。
5. 每个缓冲最多缓存16个移动排列计划，循环复用；非移动写入、trim和free会清除。旧两人颜色交错的网格素材跳过此重排。第一次匹配成本留在首次循环，后续不反复分配整套匹配表。
6. 预取任务可以被转向、受击或出招立即取消；取消只影响后台派生显示，不改模拟、伤害、输入或回滚快照。

昨天的颜色／透明度缓存、统一色缓存、闪白预留、启用时排序和关闭主动扩池均保留。常驻图片池仍16000，不在本批同时改模板层级、容量或Q演出。

## 模拟器验证

Mobile 1600×900、固定种子、训练场、每项连续480回调，四角色前走／后退。两版都保留相同角色动作数据、模拟规则和显示倍率。表中的“姿势落后回调”是实际发布姿势与同一回调动作时钟要求的姿势不一致的次数，不是FPS；剩余0–2次主要在起步。

{chr(10).join(rows)}

芙宁娜平均调用下降约11%，绫华约9%–10%；雷电平均调用约增加1%，纳西妲接近原值，但移动循环显示延迟显著减少。不能把雷电描述为平均工作量已降低。缓存后平均Lua指令增量约0.5%–1.4%，与换帧提前准备及计划查找有关；不换算真机毫秒。

四角色×前后方向×六姿，48组修前／修后稳定姿势截图逐像素一致；另核验每一个连续颜色组内矩形几何的精确多重集，没有跨组、丢矩形或重复矩形。桌面和手机截图已人工查看。截图中固定60FPS来自桩客户端输入dt，不能当真机帧率。

12种转向／重攻／受击打断检查通过，目标新姿势在2–3次分片更新内完成，未被预取走路帧阻塞。349原素材显示状态重建、角色时间线、旧双角色3600拍全状态差分与快照复演通过。桌面、手机横屏／竖屏完整开始→选人→战斗→暂停→结算→重赛→重选流程通过；双端60ms延迟、40ms抖动、3%丢包回滚与断线结算通过。

GIA回读源码与候选哈希一致，A的原UI／挂载／未知字段保真；B字节一致；只有一个GF_HOST脚本挂载。仅脚本GIA回读一致。

## 真机与未完成项

本轮没有操作原神客户端，**真机流畅度待复测**。先用同设备同工程比较普通前走／后退和反向，再测出招打断；记录FPS、最大间隔、累计丢时和起步／连续移动的体感。

这是一批移动专项候选，不是全部卡顿完成。雷电Q集中绘制超预算、动态模板实际子控件／合批成本、常驻16000池的原生负担及长时间发热仍待处理。完整流程回执还保留约107万–111万的回调峰值，超过项目100万建议预算；因此只登记逻辑／流程可走通，不登记整个版本性能预算通过，也不提交或自动发布正式版本。

## 开发记录

源码同步到`runtime/source/`并重建`runtime/dist/`；当前开发目录包含后来的三人选人。本批顺带补齐三人选人`drawNameAction`遗漏的end，修复源码语法阻断；这个修复没有混入独立四角色性能候选。测试兼容旧版选人使用模块名单、当前版使用场景名单，仍读取真实名单长度，不放宽流程断言。

回执：`verification/report.json`、`logic.json`、`mock-flow.json`、`movement-interrupt.json`、`build.json`、`delivery.json`。复现工具在`runtime/tests/movement_performance.py`、`movement_interrupt.py`及`runtime/tools/movement_release.py`。
'''
(OUT/'安装与验证说明.md').write_text(notes,encoding='utf-8')
print('notes and hash consistency verified')

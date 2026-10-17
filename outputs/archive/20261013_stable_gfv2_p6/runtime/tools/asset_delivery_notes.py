"""Record both anonymous native-test candidates without replacing the stable pointer."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
batch=json.loads((ROOT/'runtime/verification/asset-delivery-batch.json').read_text(encoding='utf-8-sig'))
startup=json.loads((ROOT/'runtime/verification/asset-startup.json').read_text())
comparison=ROOT/('outputs/asset-codec-comparison-'+batch['stamp']);comparison.mkdir(exist_ok=True)
rows=[]
for profile in ['compact','compressed']:
    folder=ROOT/batch[profile];manifest=json.loads((folder/'delivery.json').read_text(encoding='utf-8'))
    build=json.loads((ROOT/'runtime'/('dist-'+profile)/'build.json').read_text())
    assert build['sha256']==manifest['sourceSha256']
    for kind in ['logic','flow','assets']:
        report=ROOT/'runtime/verification'/f'{profile}-{kind}.json'
        data=json.loads(report.read_text(encoding='utf-8'))
        assert data.get('clientSha256',data.get('sourceSha256'))==build['sha256']
        shutil.copyfile(report,folder/report.name)
    shutil.copyfile(ROOT/'runtime/verification/asset-startup.json',folder/'asset-startup.json')
    shutil.copyfile(ROOT/'runtime/verification'/f'{profile}-initial-loading.png',folder/'初始素材准备预览.png')
    shutil.copyfile(ROOT/'runtime/verification'/f'{profile}-startup-fight.png',folder/'FPS及准备时间预览.png')
    manifest.update(profile=build['profile'],templateResourceIndex=1073741845,retainedBattlePool=16000,loadingStages=[14672,15344,16000],backgroundGrowth=False,preparationAtInitialLoading=True,allFourCharactersPrepared=True,legacyNumericTablesRetained=True,codeMinified=False)
    (folder/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    script=next(f['filename'] for f in manifest['files'] if f['kind']=='luaOnly')
    lua=next(f['filename'] for f in manifest['files'] if f['kind']=='lua')
    label='无损紧凑编码' if profile=='compact' else 'LZ4无损压缩'
    (folder/'安装说明.md').write_text(f'''# {label}对照版

导入 `{script}` 替换GF_HOST旧主脚本；每次只运行一个版本。另有完整 `{lua}`。不做代码精简。现有界面和B模板继续使用，默认模板资源索引1073741845。

两版在初始加载、开场前准备全部四角色身体及芙宁娜／绫华辅助帧，后续选人／VS／战斗使用缓存。额外2000图元仍分672／672／656三段创建，16000池、关闭预扩池、宽屏与FPS保持一致。重赛保留缓存，所以比较初次加载需完整结束运行后重新启动，不能用热重赛时间代替首次准备时间。

加载页显示素材准备计时；完成后战斗FPS面板保留“素材准备”秒数。这个计时为回调dt累计，包括分片等待和数据构建，不是纯CPU解压秒数，也不包含后面的图元池加载、启动扫描和整个应用总启动时间。

只对芙宁娜／绫华素材做紧凑编码，旧两人的数值表保留。共享完全相同的调色板与载荷，不近似合并动作。LZ4版在紧凑数据上按字段分列再压缩，恢复完全相同的矩形、顺序、颜色和坐标。所有解压在初始阶段完成，已验证后续解压计数不增加。

Lua文件 {build['bytes']:,} 字节。离线逐像素、全部639条目／461672矩形和元数据一致、完整流程及双端回滚检查通过；真机解压与运行待测试。交付路径 `%LOCALAPPDATA%Low/miHoYo/原神/BeyondLocal/Beyond_Local_Export`，旧版保留。
''',encoding='utf-8')
    shutil.copyfile(folder/lua,comparison/lua)
    rows.append({'profile':profile,'folder':batch[profile],'bytes':build['bytes'],'sha256':build['sha256'],'lua':lua,'scriptGia':script})
normal=json.loads((ROOT/'runtime/dist/build.json').read_text())
(comparison/'comparison.json').write_text(json.dumps({'normalBytes':normal['bytes'],'variants':rows,'startupMock':startup,'nativeDeviceTested':False},ensure_ascii=False,indent=2),encoding='utf-8')
doc=f'''# 素材紧凑编码与LZ4对照

## 用户决定与程序设计

匿名玩家要求暂不精简代码，制作两个可真机对比的完整Lua：无损紧凑字段＋相同数据引用，以及进一步压缩版。最新要求所有角色解码／解压集中于初始加载，开场前完成，避免分散到选人／VS／战斗加载。

可编辑素材和普通构建保留。`runtime/tools/compact_assets.py`另导出两种配置；运行层只在素材访问边界兼容r8／r16及可选LZ4，战斗、帧序、图元拟合结果和网络协议不变。完全一致的调色板和编码载荷共享；每帧的可变解码缓存、倍率应用状态和锚点仍独立。没有相似图近似合并、降色、减帧或代码精简。

先试四角色全编码得到约4.27MB，但旧两人原本直接使用数值表，改字符串会增加逐帧准备指令；历史实验留在dist-compact-all及compact-all-assets.json。因此两份交付都保留旧两人数值表，只压芙宁娜和绫华。芙宁娜178条目177可用uint8，1保留uint16；绫华157均可用uint8。调色板分别178→5份、157→3份；矩形载荷分别178→159份、157→157份。共639条目461672矩形全部一致。

LZ4对照在紧凑字段上按坐标／宽高／颜色索引分列，压缩独立帧块，加载时恢复原顺序。329条目采用压缩，较小或无收益条目保持紧凑格式。Lua解码器限制输入／输出长度、验证偏移与零填充，按预算继续，不一次解整个人物。块格式依据[LZ4官方规范](https://github.com/lz4/lz4/blob/dev/doc/lz4_Block_format.md)，没有使用原生LZ4库，其C实现速度不能当成Lua真机性能。

两版开场前分片准备四角色，之后角色准备任务已完成；启动加载计时是raw OnUpdate dt累计，包含数据构建及分片等待。不是纯CPU解压耗时，不包括启动扫描、后续控件池或整个启动过程。战斗面板保留该计时。初始准备使四角色展开缓存提前常驻；这与按选择角色懒解码不同，是本轮明确要求的对照安排。

## 文件测量

普通Lua {normal['bytes']:,} 字节；紧凑版 {rows[0]['bytes']:,}；LZ4版 {rows[1]['bytes']:,}。相较普通版约减少20.8%／26.3%，LZ4比紧凑版再小约0.39MB。文件大小不是奇域统计容量，也不改变16000图元池。

交付目录 `{batch['compact']}` 与 `{batch['compressed']}`；两个Lua集中副本与比较回执在 `{comparison.relative_to(ROOT).as_posix()}`。

## 模拟器验证

全部矩形字段、顺序、调色板、尺寸、锚点、倍率及其余元数据一致；349原始像素状态重建、3600拍旧角色全状态差分、各角色时间线及回滚快照、桌面／手机横竖屏全流程与双端60ms延迟／40ms抖动／3%丢包通过。LZ4覆盖小预算、重复重叠复制、长度扩展、空块与坏偏移拒绝。初始LZ4计数329，进入战斗后仍329；紧凑版为0。

固定模拟器60回调／秒，初始准备约10.73秒／11.90秒，主要反映分片调度；不得当手机耗时。微观准备指令芙宁娜紧凑约10.85百万、LZ4约25.83百万；绫华约9.36百万／22.59百万，LZ4成本更高。分片峰值约0.20百万以内，整体流程峰值约1.37百万，图元常驻数一致。当前没有真机速度结论。

## 真机对比方法

同一手机、同一工程，每次只替换唯一GF_HOST脚本，完整停止再启动。记录素材准备秒数、从运行到标题的总时间、奇域统计大小，再走相同芙宁娜／绫华战斗。保持B模板、地图、16000池及三段创建不变。重赛是热缓存，不比较首次解压；版本名称会在初始加载显示。两版都是独立测试候选，普通发布指针保留，不因包体小自动替换正式版。
'''
(ROOT/'docs/current/素材紧凑编码与LZ4对照_20261012.md').write_text(doc,encoding='utf-8')
for rel,line in [('AI_START.md','> 2026-10-12 最新素材压缩对照：紧凑与LZ4两版，只压芙宁娜／绫华并保留旧两人数值表；全部四角色初始加载准备完成再进开场，后续不解压。639条目／461672矩形、逐像素／逻辑／流程通过，真机待测。先读[对照记录](docs/current/素材紧凑编码与LZ4对照_20261012.md)。'),('runtime/README.md','素材对照构建：`python runtime/tools/compact_assets.py`；压缩配置追加`--compressed --out runtime/dist-compressed`。两版初始加载全角色准备，不精简代码。交付详见`../docs/current/素材紧凑编码与LZ4对照_20261012.md`。普通发布指针保留。'),('docs/current/V4_执行与验收台账_20261009.md','2026-10-12：紧凑／LZ4对照完成，初始加载全角色准备、后续解压计数不增长；639条目／461672矩形及元数据、像素／模拟／流程／回滚通过。真机待测，见[压缩对照](素材紧凑编码与LZ4对照_20261012.md)。')]:
    p=ROOT/rel;p.write_text(p.read_text(encoding='utf-8')+'\n'+line+'\n',encoding='utf-8')

"""Full four-character encoding and token-preserving minification candidates."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
batch=json.loads((ROOT/'runtime/verification/all-delivery-batch.json').read_text(encoding='utf-8-sig'))
summary=ROOT/('outputs/all-codec-comparison-'+batch['stamp']);summary.mkdir(exist_ok=True)
normal=json.loads((ROOT/'runtime/dist/build.json').read_text())
shutil.copyfile(ROOT/'runtime/dist/genshin_fighter.lua',summary/'保留的普通可读版.lua')
shutil.copyfile(ROOT/'runtime/dist/build.json',summary/'普通版构建.json')
startup=json.loads((ROOT/'runtime/verification/all-asset-startup.json').read_text())
plans=[('compact','dist-all-compact','全四角色紧凑编码','all-compact'),('compressed','dist-all-compressed','全四角色LZ4压缩','all-compressed'),('minified','dist-minified','普通素材代码精简','minified'),('combined','dist-all-compressed-minified','全四角色压缩＋代码精简','all-compressed-minified')]
rows=[]
for key,dist,label,report_prefix in plans:
    folder=ROOT/batch[key];build=json.loads((ROOT/'runtime'/dist/'build.json').read_text())
    manifest=json.loads((folder/'delivery.json').read_text())
    assert manifest['sourceSha256']==build['sha256']
    counts=[]
    for kind in ['logic','flow']:
        report=ROOT/'runtime/verification'/f'{report_prefix}-{kind}.json'
        data=json.loads(report.read_text(encoding='utf-8'));assert data['clientSha256']==build['sha256']
        shutil.copyfile(report,folder/report.name)
        if kind=='flow':counts=[x['stats']['controls'] for x in data['local']];assert len(set(counts))==1
    if key in ['compact','compressed']:
        for suffix in ['assets','legacy-flow']:
            p=ROOT/'runtime/verification'/f'{report_prefix}-{suffix}.json';d=json.loads(p.read_text());assert d.get('clientSha256',d.get('sourceSha256'))==build['sha256'];shutil.copyfile(p,folder/p.name)
        shutil.copyfile(ROOT/'runtime/verification/all-asset-startup.json',folder/'all-asset-startup.json')
        shutil.copyfile(ROOT/'runtime/verification'/f'all-{key}-initial-loading.png',folder/'初始准备预览.png')
        shutil.copyfile(ROOT/'runtime/verification'/f'all-{key}-startup-fight.png',folder/'战斗及准备时间预览.png')
    lua=next(f['filename'] for f in manifest['files'] if f['kind']=='lua')
    gia=next(f['filename'] for f in manifest['files'] if f['kind']=='luaOnly')
    manifest.update(profile=build['profile'],codeMinified=build['minified'],fullFourCharacterAnimationBanks=key!='minified',templateResourceIndex=1073741845,retainedBattlePool=16000,loadingStages=[14672,15344,16000],mockControls=counts[0],initialPreparation=key!='minified',randomTitlePair=True,menuUsesTitlePair=True)
    (folder/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copyfile(folder/lua,summary/lua)
    note='初始阶段准备全部四角色主动作库；完成后进入开场，后续无新增LZ4解压。战斗面板保留素材准备计时。' if key!='minified' else '保持普通素材编码及原加载安排，仅删除注释／冗余空白，不进行素材LZ4解压。'
    (folder/'安装说明.md').write_text(f'''# {label}

本批版本 {batch['stamp']}。已有工程导入 `{gia}`，替换唯一GF_HOST主脚本，每次只挂一份。完整Lua为 `{lua}`。旧文件保留，新建／重装才使用A+B。

{note} 启动随机选两名不同角色，主菜单只在这两人之间切换。模板索引1073741845、16000图片池、选人／VS／战斗新增672／672／656、宽屏与FPS保留。

文件 {build['bytes']:,} 字节。固定GIA控件仍为256图片／96文字／24按钮，运行池仍16000；模拟器总控件16186。脚本变小不意味着图元减少。

四角色编码版处理gf_animation_data、gf_inbetween_data、gf_furina_data、gf_ayaka_data：全部主动作及新角色辅助帧纳入；头像、旧角色独立特效及背景等其余素材沿原编码，未删功能或美术。精简版保留所有标识符、字符串、数值和Lua语法标记，不做变量改名或混淆。报错行号会变化，定位使用对应可读源。

完整流程、像素／时序／确定性及双端回滚离线通过，真机待导入。对比初始加载需完整停止再启动，不能用热重赛。显示时间包括数据准备及分片等待，不是纯CPU解压耗时，也不等于应用总启动时间。详情见 `docs/current/全四角色压缩与代码精简对照_20261012.md`。
''',encoding='utf-8')
    rows.append({'key':key,'label':label,'folder':batch[key],'lua':lua,'gia':gia,'bytes':build['bytes'],'sha256':build['sha256'],'savedBytes':normal['bytes']-build['bytes'],'savedPercent':round((1-build['bytes']/normal['bytes'])*100,2),'mockControls':counts[0]})
(summary/'comparison.json').write_text(json.dumps({'ordinary':normal,'variants':rows,'startup':startup,'nativeDeviceTested':False},ensure_ascii=False,indent=2),encoding='utf-8')
table='\n'.join(f"|{r['label']}|{r['bytes']:,}|{r['savedPercent']}%|16000 / {r['mockControls']}|" for r in rows)
doc=f'''# 全四角色压缩与代码精简对照

## 用户决定与程序

2026-10-12，匿名玩家明确不是减少角色名单，而是把雷电／纳西妲也纳入两种编码方案，先导出观察真机解压与无损效果。后续明确保留现有版本，并做去多余格式的代码精简。退出按钮发信号至服务端结算、美术背景只记录，见[后续需求](退出结算与背景后续需求_20261012.md)，本批未实现。

本批另建四份候选：全四角色紧凑、全四角色LZ4、普通素材仅代码精简、全四角色LZ4＋代码精简。可读源码及旧发布文件保留，普通可读Lua副本存于`{summary.relative_to(ROOT).as_posix()}`。普通发布指针不自动替换。

编码目标为gf_animation_data／gf_inbetween_data／gf_furina_data／gf_ayaka_data，639帧条目、461672矩形。旧两人的304主动作／补间帧本次全部纳入，不再保留数值表。头像、旧角色独立特效、背景等其他素材仍原编码；“全四角色”表示四人主动作库覆盖，不能理解为文件中每一段数据都被LZ4压缩。

完全相同的调色板与载荷引用共享，颜色、透明度、矩形顺序及锚点／倍率保持。LZ4逐帧分块，调色板共享不要求全角色解压；本批全量初始准备是对照调度，不是编码格式限制。以后可以只准备展示帧与所选阵容，本批不同时改懒加载。

标题原来仅有雷电／纳西妲固定组合，本批改为从现有名单随机选两名不同角色，同次运行保持。主菜单原来轮换全名单，改为只在这两名角色之间切换。无战斗模拟或联机字段变更。

代码精简仅去注释、空白，完整Lua语法标记序列逐项相同；保留所有名称、字面量和功能。报错行号失去可读源直接对应关系，应使用构建SHA及可读源码排查。通过导出工具生成，不维护手写精简源码。

## 文件和控件测量

普通Lua {normal['bytes']:,} 字节，以下字节为UTF-8实际文件长度，MB采用十进制。奇域显示的统计大小仍需真机查看。

|方案|Lua字节|相对普通版减小|运行图片池／模拟器总控件|
|---|---:|---:|---:|
{table}

全四角色LZ4比紧凑版额外省1,076,235字节，约25.1%；代码去格式省115,530字节，普通版约1.6%、LZ4版约3.6%。控件减少为0。所有GIA固定UI仍256图片／96文字／24按钮，回读与逆向还原证明非脚本字段完全保留；动态图片池仍16000，额外2000仍三段672／672／656。

## 模拟器验证

编码两版639条目／461672矩形、调色板与全部元数据相同；旧两人304帧经过实际Art访问、倍率烘焙后的每个值和锚点一致。349新角色原图状态逐像素重建、3600拍旧两人全状态差分、各角色时间线与快照、桌面／手机横竖屏完整流程通过。旧两人和新两人均分别走完整流程与60ms延迟／40ms抖动／3%丢包双端回滚；四份候选均逻辑／流程通过。

LZ4初始解压计数633，选人、VS、正式战斗及两人Q后仍633；紧凑版为0。标题随机两人不同、80次抽样覆盖当前名单、菜单不越出该组合检查通过。固定60回调模拟器初始准备10.73秒／13.47秒，不是真机秒数；这包含分片等待和准备工作，不能据此承诺手机FPS或加载速度。

真机按同一工程、同一设备完整停止再启动，分别导入唯一GF_HOST脚本，记录奇域统计容量、素材准备秒数、总启动时间、FPS及动作外观。绫华缺边仍是原有待修项；压缩无损只证明没有改变既有图像，不代表修好了美术。

## 工具与交付

构建：`python runtime/tools/compact_assets.py --legacy --out runtime/dist-all-compact`；压缩追加`--compressed --out runtime/dist-all-compressed`。`--legacy`在此表示包含原雷电／纳西妲动画库。

精简：`python runtime/tools/minify_lua.py --source runtime/dist/genshin_fighter.lua --out runtime/dist-minified`，或以全压缩源码输入生成组合版。

集中Lua副本与比较回执：`{summary.relative_to(ROOT).as_posix()}`；各候选目录见comparison.json。GIA交付至`%LOCALAPPDATA%Low/miHoYo/原神/BeyondLocal/Beyond_Local_Export`，旧文件不覆盖；官方导入与真机未验收。
'''
(ROOT/'docs/current/全四角色压缩与代码精简对照_20261012.md').write_text(doc,encoding='utf-8')
for rel,line in [('AI_START.md','> 2026-10-12 最新全四角色对照：雷电／纳西妲304动作帧加入紧凑与LZ4，四人639条目全量一致。另导出普通素材代码精简及压缩＋精简，不改功能或控件数；标题随机两人，菜单沿这两人轮换。详见[本批记录](docs/current/全四角色压缩与代码精简对照_20261012.md)，真机待测。'),('runtime/README.md','全四角色压缩／精简：`--legacy`将旧两人加入编码，`minify_lua.py`仅去注释／空白。交付见`../docs/current/全四角色压缩与代码精简对照_20261012.md`；普通可读源保留。'),('docs/current/V4_执行与验收台账_20261009.md','2026-10-12：全四角色紧凑／LZ4及两份精简候选完成；639帧无损、旧角色304实际Art状态、逻辑／全流程／回滚与标题菜单随机组合检查通过。控件数量不变，真机待测。见[对照记录](全四角色压缩与代码精简对照_20261012.md)。')]:
    p=ROOT/rel;p.write_text(p.read_text(encoding='utf-8')+'\n'+line+'\n',encoding='utf-8')

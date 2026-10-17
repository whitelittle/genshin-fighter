from pathlib import Path
import hashlib, json, shutil

R = Path(__file__).resolve().parents[1]
A = R/'outputs/archive/20261013_stable_gfv2_p6'
D = R/'docs/current/稳定版资料_20261013'
assert not A.exists(), '冻结目录已存在，禁止覆盖'
D.mkdir(parents=True, exist_ok=True)
A.mkdir(parents=True)
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s.strip()+'\n',encoding='utf-8')
def js(p,o): write(p,json.dumps(o,ensure_ascii=False,indent=2))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

write(D/'README.md','''# 稳定版资料总览

2026-10-13：按用户决定，当前版本标记为 **稳定版本**，编号 `20261013_stable_gfv2_p6`。对应六角色、无压缩、GFV2先匹配车轮战版本。该标记作为后续开发和回退基线；保留已有验证证据，不将版本标记推定为新真机验收。

|资料|简要内容|
|---|---|
|[技术要点](技术要点.md)|模拟与回滚、渲染负载、性能经验、信号ID绑定|
|[策划与后续规划](策划与后续规划.md)|当前模式、选人规则、AI和仅记录的未来需求|
|[工作流与制作标准](工作流与制作标准.md)|设计、绘制、校准、接入、验证和交付门槛|
|[美术素材索引](美术素材索引.md)|六角色、候选角色、背景、源图与实际消费数据|
|[版本留档索引](版本留档索引.md)|全部现存outputs版本、阶段简述及保留位置|
|[稳定版冻结目录](../../../outputs/archive/20261013_stable_gfv2_p6/README.md)|源码副本、交付物、验证记录与SHA256|

阅读优先级：本入口与更晚的用户决定 → 对应版本交付说明 → 历史专题。旧19角色、GF10、GF3独立选人、LZ4整包等记录不代表当前实现。

当前已有工程只更新主脚本；GFV2服务器图负责匹配及转发，GF3服务器图保留退出结算关闭。两端使用协议6。冻结的两个节点包引用指定地图已有资源，只能用于相同资源上下文，不能当作任意新地图安装包。

证据状态：设计与实现已有记录；离线规则/像素、普通流程、新匹配、三场回滚通过；此前真实设备低帧、信号重名和连接失败是历史观察；最新真机匹配、退出、PC/手机帧率尚待复验，原因推断不得写成已测结果。
''')
write(D/'技术要点.md','''# 关键技术与已知边界

## 当前运行结构

维护入口是 `runtime/source/`，按app/menu/characters/battle/network/modes/render/input/assets分工，`order.json`控制组装。只改可读源再生成发布文件；`game/`是早期v2及模拟器依赖，不是当前主脚本入口。角色联机编号固定为雷电1、纳西妲2、芙宁娜3、绫华4、克洛琳德5、仆人6，新增只追加。

60Hz整数模拟与显示回调分离。输入、预测、确认与回滚负责确定性；快照覆盖会影响下一拍的状态，图元缓存为派生状态。显示跳帧不能漏掉命中或改变伤害。FPS诊断显示回调频率/最大间隔，并非模拟拍数。

## 连接与节点

当前车轮战先GFV2匹配，再选三人、双方准备与揭晓，同一连接开战；普通单角色三局两胜保留。协议6隔离旧协议及不同模式；24整数大厅包复用空闲字段同步人数、准备、代次和修订，双方准备后才传阵容。取消、断线、回结算时隔离过期准备，重赛保留连接序号。

节点信号绑定包含资源/操作ID、版本与端口；写对名称不能替代正确绑定。旧文件每次导入数字名递增，不能靠字符串替换判定修好。正确流程是读取当前地图命名资源，按名称和操作类型匹配真实ID，再校验端口/参数/常量。引用已有资源的交付包不附带新信号声明，但只适用于对应地图。GFV2恢复26节点，GF3重绑517节点，GF3自带17节点图变量；两者不能混为新增实体变量。详见[地图重绑记录](../../../outputs/map-signal-rebind-20261013/安装与验证说明.md)。

GIA需保留未知字段、头尾和执行/数据连接，泛型整数包装与索引不能沿用另一类变量节点。线格式、解释执行、编辑器导入、真实联机是四层不同证据。不得把校验专用带声明文件投放导入目录。

## 图元与性能

双身体缓冲、分片准备、计划缓存、下一移动姿势预取、同色组尺寸复用保留。统计必须区分图片/控件、常驻/可见/隐藏、换帧更新、颜色改写和覆盖面积；双缓冲不是简单开关，也不能把总控件数等同每帧成本。

当前六库无LZ4；PC在加载幕准备出场帧，最大追帧4拍；手机仍为按需读取、最大8拍、12000图片目标和轻量受击/取景框效果。手机8拍与延后准备没有真机收益证明，保留为待评估项，不能宣称已优化成功。PC性能回退后恢复4拍及加载准备；特效隐藏回收后shown为空已复现并加有效缓冲/图像检查。

历史观察：较早PC约30 FPS以上；后续出现21 FPS/134ms，手机录屏8–26 FPS且加载约33秒。不同素材和版本不可直接混算。最新离线通过不代表实际FPS恢复；后续用同设备、同角色、同场景逐项A/B，分别记录加载时间、普通移动、连续技能和回收峰值。

依据：[性能对照](../流畅快照与当前版性能对照_20261013.md)、[PC回归修复](../../../outputs/pc-regression-fix-20261013/修复与导入说明.md)、[先匹配说明](../../../outputs/team-match-first-20261013/安装与验证说明.md)。
''')
write(D/'策划与后续规划.md','''# 策划方案与后续规划

## 当前稳定版范围

六角色：雷电将军、纳西妲、芙宁娜、神里绫华、克洛琳德、阿蕾奇诺。保留单人AI、训练、既有街机流程、普通联机单角色三局两胜及三人车轮战。六角色可用不等于所有美术、平衡和设备性能逐项验收。

车轮战：联机先匹配同模式双方，各自在己方阵容连续选择三个不同角色，选择顺序就是出场顺序；准备前隐藏对手阵容，双方确认后揭晓。胜者继承血量/能量，败者依顺序换人；双KO、超时与第三人结束走对应规则。不能与历史“三角色分别打三局两胜”方案混用。结算可返回匹配重选，退出由服务器结算/关闭链完成。

角色统一的是同一角色的人体尺度，保留蹲下、跳跃、挥击的自然外框变化；不按武器或特效外框缩放。不同角色自然身高差保留。仆人普通AI已调慢反应、出手和追击；六角色四档难度需分别考察反应、进攻频率、追击和失误空间，后续以实际对局手感调曲线，不把更强角色的普通档等同困难档。

## 后续需求：仅记录，未排期开发

|需求|说明与待定点|
|---|---|
|4人淘汰赛|对阵晋级、单角色/车轮规则、掉线/平局/超时待定|
|观战|模式、人数、视角和同步边界待定|
|旅行者与派蒙|旅行者性别/元素待定；派蒙用于头像、小像素人与教学等，不默认可操作参战|
|教学关|按键、攻防、丘丘人木桩受击/被投、课程完成与进度待设计|
|剧情及剧情模式|分别规划故事/对白/演出和章节/战斗/保存/重试机制|
|常驻20–30角色，可更新轮换|指可用名单，不指全量动作控件常驻；名单、周期与兼容机制待定|

建议实施顺序（策划建议，非开发授权）：先复验当前连接、退出和性能 → 固定角色质量/制作门槛 → 教学与旅行者/派蒙 → 淘汰赛/观战 → 剧情模式与轮换系统。用户后续决定优先。

完整记录：[后续需求](../后续模式与轮换角色需求_20261013.md)、[教学记录](../教学关卡需求记录_20261012.md)。
''')
write(D/'工作流与制作标准.md','''# 工作流、工具与制作标准

1. 先读AI_START、目录AGENTS及最新交付，锁定基线/输入哈希；明确设计、实现、模拟器、真机和推断各自状态。旧来源不覆盖新决定。
2. 定动作设计卡与母版。参考原作特征并记录横版改编；先待机、真实步态、代表攻击，确认尺度后扩展，不由未来名单自动批量制作。
3. 生图/返修使用image_gen；保留源图、提示词、失败版本。Python/Pillow/NumPy逐对象提取RGBA，不按非均匀动作板等宽裁切，不混邻姿或误删细杆/发梢。原图保留，弃用项用标记隔离。
4. 以母版人体单位校准等比尺度，鞋底/虚拟支撑为锚点；不能用拉伸或武器外框“统一大小”。空攻继承root，镜像整体一致。降色与矩形拟合用项目artlib/canonical_fit；重建目标逐像素一致。
5. 动作具有支撑、重心、起手/命中/收势，步态含接触/承重/经过。重点检查每动作首尾到其他动作的衔接、待机循环、武器长度/握点、倒地起身方向。自然姿态变化不抹平。
6. 身体/武器与独立特效分层；光点绑定手掌或目标，投技双方接触与成人/低位变体分别校准。Q完整命中和短收招时间线分开；明确保持和复用帧，不能把显示状态数说成独立原画数。
7. HTML/JS播放器检查源图/拟合、逐帧/连播、镜像、首尾、跳跃→空攻→落地、投/被投；再接provider、帧时长、锚点、事件、判定、快照与回滚。美术播放通过不等于实际战斗通过。
8. 日常编辑runtime/source可读源，运行 `python runtime/tools/build.py`。当前发布无压缩用 `raw_assets.py` 另目录生成；不要重跑历史迁移脚本覆盖源码。export_gia.mjs使用已核验模板，回读Lua及哈希，B模板保真。
9. 改逻辑按目录规则跑run.py、mock_flow.py并查看PC/手机截图；改车轮跑team_match_first.py、team_net.py；改节点跑端口与原生线格式解释检查；改素材加像素/动作/预算检查。测试范围与真实设备结果分别登记。
10. 每次发布写用途、协议、需要导入的精确文件、节点/变量是否变化、哈希、通过项和待验项。已有工程最小更新仅脚本；原生导入还需验证资源绑定和试玩。历史保留，冻结目录不原地改写，新版本另建。

参考范例：[仆人实际制作方法及工具表](../仆人动作制作流程与标准_20261013.md)。仆人19色、25组/138主状态/120身体图/8特效是该角色记录，不作为全角色硬性张数。身体/特效矩形峰值也不是整场通用预算。

文档使用匿名代称和项目相对路径；必要环境写 `%USERPROFILE%`。不记录真实姓名、账号UID或联系方式；图元索引与实体/信号技术ID保留。
''')
write(D/'美术素材索引.md','''# 美术素材与候选索引

素材原地保留，文件清单与哈希见稳定版的 `art-inventory.json`。本次不重新绘图或拟合。运行实际使用的生成Lua在冻结 `runtime/source/assets/` 和角色模块中，原画/动作页是后续返修来源，二者不混作同一版本。

|对象|来源与用途|状态说明|
|---|---|---|
|雷电/纳西妲|`outputs/dual-character-reference-20261011/`；runtime对应资产和规则|旧双角色行为基线，当前编号1/2|
|芙宁娜|`outputs/furina-design-20261010/size-review.html` → size-review-app.js → actions-size-candidate.json|以页面实际消费的尺寸/锚点为准，25组138显示状态；伙伴/特效/Q独立接入|
|绫华|`outputs/v4-one-character-20261010/ayaka-armed-v2/index.html`及actions.json|最终动作页来源；六角色接入后补外轮廓，旧训练探针不是最终交付|
|克洛琳德|`outputs/clorinde-actions-20261011/`动作设计卡、actions/effects、源图和播放器|25组动作来源，已有制作反馈；正式设备表现单独验证|
|仆人|`outputs/arlecchino-actions-20261011/`源图/prompts/actions/effects/pairing及player.html|25组138主状态120身体图8特效，动作获正面反馈；完整流程见制作方法|
|统一尺度/补边|`outputs/six-character-size-20261013/`|300动作首尾端点倍率与绫华126唯一身体图补边记录；倍率检查不代替部位美术判断|
|那维莱特|`outputs/neuvillette-actions-20261012/`|候选10组49状态42身体图6特效，尚非当前六人可用角色|
|历史角色/参考|`assets/fighters/`、`assets/roster-v2/`、`assets/references-vNext/`、`outputs/roster-v2/`|历史/参考资产，不能由存在文件推定已接入|
|历史背景|`assets/stages-country-v1/`、`outputs/stage-pixel-nearest-9000/`|七地区最近邻拟合历史方案；不宣称当前战斗已完整恢复这些背景|
|UI/头像/探针|assets其余目录、outputs动作/场景/训练探针|按版本说明使用，探针不作完整游戏验收|

运行接入回执：runtime下furina/ayaka/clorinde/arlecchino-import.json；完整绘制帧与元数据需一起保留。历史V3/V4恢复参考位于work对应恢复目录，版本清单另登记；不删除原图和否决候选。
''')

# Clarify current pointers; retain history in place.
for rel, link in [('AI_START.md','docs/current/稳定版资料_20261013/README.md'),('docs/current/README.md','稳定版资料_20261013/README.md'),('runtime/README.md','../docs/current/稳定版资料_20261013/README.md')]:
    p=R/rel
    write(p,f'> 2026-10-13 稳定版本：用户指定当前六角色、无压缩、GFV2先匹配版为稳定基线（协议6）。[统一资料与版本留档]({link})优先于下方历史状态；真机待验项仍单独保留。\n\n'+p.read_text(encoding='utf-8-sig'))
for name in ['设计基线.md','工作流与工具.md','节点图知识与排错.md']:
    p=R/'docs/current'/name
    write(p,'> 历史专题：本文原有“当前”指当时版本。最新六角色稳定版请读[统一资料](稳定版资料_20261013/README.md)，不要按本文旧19角色/GF10/构建命令覆盖当前版本。\n\n'+p.read_text(encoding='utf-8-sig'))

latest=R/'outputs/team-match-first-20261013/gia/delivery.json'
delivery=json.loads(latest.read_text(encoding='utf-8-sig'))
delivery['serverNodes']='GFV2 matching, draft and battle; existing GF3 retained for exit settlement/close'
delivery['releaseStatus']='stable'
delivery['stableDesignation']='user-requested 2026-10-13; native verification remains separate'
delivery['archiveId']=A.name
js(latest,delivery)

# Immutable copies of the runnable source, tools/tests, release and node dependencies.
for name in ['source','tools','tests']:
    shutil.copytree(R/'runtime'/name,A/'runtime'/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for p in (R/'runtime').glob('*'):
    if p.is_file(): shutil.copy2(p,A/'runtime'/p.name)
shutil.copytree(R/'outputs/team-match-first-20261013',A/'release')
nodes=R/'outputs/map-signal-rebind-20261013'
for p in nodes.iterdir():
    if p.is_file() and (p.suffix in ['.json','.md'] or p.name.startswith('gpt_')):
        dest=A/'nodes'/p.name; dest.parent.mkdir(exist_ok=True); shutil.copy2(p,dest)

descriptions={
'team-match-first-20261013':'当前稳定来源：六角色无压缩，GFV2先匹配，协议6',
'map-signal-rebind-20261013':'当前节点依赖：真实地图ID重绑GF3及恢复GFV2，同地图使用',
'pc-regression-fix-20261013':'PC恢复4拍/加载准备，shown空值回收修复',
'mobile-performance-20261013':'去压缩、选人/退出与AI阶段修订；性能方案后续有回退',
'team-battle-20261013':'六角色车轮战首批，压缩和独立GF3路线已被替代',
'six-character-size-20261013':'六角色人体尺度与绫华补边',
'movement-fix-20261013':'普通移动预取与缓存专项',
'smooth-comparison-20261013':'早期流畅快照差分分析，不是新发布',
'existing-signal-update-20261013':'数字资源引用阶段方案，后被真实地图命名ID重绑替代',
'signal-name-fix-20261013':'名称修订历史，未解决导入资源重新命名',
'signal-reference-fix-20261013':'引用修订历史，后由地图重绑替代',
'native-port-fix-20261013':'节点泛型端口修正阶段',
'multi-role-selection-20261012':'独立GF3选人阶段，当前入口已改GFV2先匹配',
'four-character-gia-20261011_233317':'四角色完整动作接入阶段',
'full-reinstall':'历史210009全套方案，非当前安装入口',
}
rows=[]; inventory=[]
for folder in sorted((R/'outputs').iterdir()):
    if not folder.is_dir() or folder.name=='archive': continue
    files=sorted(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    records=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
    inventory.extend(records)
    desc=descriptions.get(folder.name)
    if desc is None:
        if 'actions-' in folder.name or 'design-' in folder.name: desc='角色动作/美术制作留档；接入状态见素材索引'
        elif any(x in folder.name for x in ['compressed','lz4','compact','minified','codec']): desc='编码/压缩体积对照；当前不采用LZ4'
        elif any(x in folder.name for x in ['probe','inspection','diagnostic','comparison','audit','check']): desc='专项探针/诊断/对照证据，不代表完整发布'
        else: desc='历史阶段产物；用途与验收以目录内说明为准'
    entries=[p for p in files if p.parent==folder and p.suffix=='.md']
    entry=entries[0] if entries else folder
    rows.append(f'|[{folder.name}](../../../{entry.relative_to(R).as_posix()})|{desc}|{len(files)}|')
js(A/'historical-output-inventory.json',inventory)
write(D/'版本留档索引.md','''# 各版本留档索引

当前稳定：20261013_stable_gfv2_p6。下表覆盖本次整理时outputs所有一级目录（archive另列）。历史原地留档、不删除、不复写旧包；所有文件大小和SHA256登记在冻结目录historical-output-inventory.json，提供核对依据。它们不是都通过验收的正式版本。

主要演进：早期v0.x/双人原型 → 210009历史冻结与加载探索 → V3 E行为基线/V4角色制作 → 四角色整合与性能/池/宽屏 → 编码压缩对照 → 六角色尺度与车轮战 → 无压缩/AI/退出 → PC回退与信号ID修正 → GFV2先匹配稳定版。

旧冻结目录outputs/archive/20261004_210009继续保留。work中的V3/V4恢复材料与用户流畅快照保留，不从文件名推定对应真机帧率；详见性能对照报告。素材候选按美术索引区分，未来名单不当作已交付名单。

|目录/说明入口|简要说明|文件数|
|---|---|---|
'''+ '\n'.join(rows))

artroots=['assets','outputs/dual-character-reference-20261011','outputs/furina-design-20261010','outputs/v4-one-character-20261010','outputs/clorinde-actions-20261011','outputs/arlecchino-actions-20261011','outputs/neuvillette-actions-20261012','outputs/six-character-size-20261013','outputs/stage-pixel-nearest-9000']
arts=[r for r in inventory if any(r['path'].startswith(x+'/') for x in artroots)]
arts += [{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((R/'assets').rglob('*')) if p.is_file()]
js(A/'art-inventory.json',arts)
write(A/'README.md','''# 稳定版本 20261013_stable_gfv2_p6

2026-10-13按用户要求冻结。六角色、无压缩、先GFV2匹配再选三人，协议6；既有单角色模式保留。

- runtime：当前可读源码、组装顺序、工具、测试与接入回执的独立副本。
- release：当前Lua/GIA、交付清单、截图及离线验证证据副本。
- nodes：恢复GFV2与按地图现有信号绑定GF3的节点包及证据；不包含校验专用声明包。
- docs：本次知识总结与版本/素材导航副本。
- manifest.json：冻结文件SHA256与大小；historical-output-inventory.json与art-inventory.json是历史/美术原地留档清单。

已有工程只更新release/gia内“车轮战先匹配_复用GFV2_仅脚本.gia”；两个节点已挂载则不用再导。节点引用特定地图现有信号，不能当独立新地图全套包。开发源码与发布Lua分开：发布采用raw_assets.py生成无压缩表示。恢复交付时复制冻结文件，勿覆盖冻结目录；新开发另建版本。

稳定标记是用户指定的版本基线。离线规则/像素、普通流程、新匹配与三场回滚已通过；最新原生导入、真机连接/退出及PC/手机帧率仍待复验。本次仅归档与说明修正，没有改运行代码、素材或重新导出游戏。

详细入口见docs/README.md。历史和原图未删除，本地留档不等于异地备份，也未执行Git提交或外部发布。
''')
ledger=R/'docs/current/V4_执行与验收台账_20261009.md'
write(ledger,'> 2026-10-13 归档：按用户要求将当前GFV2先匹配协议6六角色版标记稳定版本，冻结源码/交付/节点/证据，整理技术、策划、制作标准、工作流、美术与后续规划。历史原地保留并登记哈希；未改运行代码。最新真机待验状态保留。入口：[稳定版资料](稳定版资料_20261013/README.md)。\n\n'+ledger.read_text(encoding='utf-8-sig'))
shutil.copytree(D,A/'docs')
files=[{'path':p.relative_to(A).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(A.rglob('*')) if p.is_file()]
js(A/'manifest.json',{'archiveId':A.name,'status':'stable','designatedBy':'user','date':'2026-10-13','protocolVersion':6,'nativeDeviceTested':False,'files':files,'historicalOutputFiles':len(inventory),'artFiles':len(arts)})
js(R/'outputs/archive/CURRENT_STABLE.json',{'archiveId':A.name,'manifest':A.name+'/manifest.json','status':'stable','protocolVersion':6,'nativeDeviceTested':False})
print(json.dumps({'snapshotFiles':len(files),'historicalFiles':len(inventory),'artFiles':len(arts),'versions':len(rows)},ensure_ascii=False))

import {readFileSync,writeFileSync,mkdirSync,existsSync,readdirSync,statSync} from 'node:fs';
import {createHash} from 'node:crypto';
const read=p=>readFileSync(p,'utf8'), put=(p,s)=>writeFileSync(p,s,'utf8');
mkdirSync('docs/current',{recursive:true});mkdirSync('docs/archive',{recursive:true});
const snapshot='docs/archive/AI_START_历史_20261004.md';
if(!existsSync(snapshot))put(snapshot,read('AI_START.md'));
put('AI_START.md',`# 工作区入口：当前测试交付与下一阶段

更新：2026-10-04。当前交付以 outputs/midphase-final/delivery.json 为准，时间戳 20261004_143008。旧入口已保留在 [历史入口](docs/archive/AI_START_历史_20261004.md)，其中“最新”只表示当时状态，不覆盖本页。

先读 [当前资料入口](docs/current/README.md)，再按任务读取专题。安装看 [GIA安装说明](outputs/midphase-final/GIA安装说明.md)、[节点安装说明](outputs/midphase-final/节点安装说明.md)。技术分享看 [分享入口](docs/share/README.md)。

当前是19角色双人完整测试版：开始、三人选定、两端同步、每场按需加载、ROUND 1/2/3、三局两胜、结算返回选人。仅第一批十四位和五位样板；第二、第三批不在选人页。七张最近邻背景使用9000图元档，实际8660～8841。

绫华新比例56姿势已接入；基础板与攻击板逐帧裁切，攻击13收招裁头修复。其他角色真实交替步态仍未完成。模拟器回归通过不表示官方导入、节点或手机性能已验收。所有未完成项见 [问题台账](docs/current/问题台账.md)。

工作规则：用户后续明确要求优先；保留源素材和弃用记录；删除前核验依赖；文档匿名；技术和设计分开；不得把模拟器逻辑当成已导出的官方节点图。不要改生成Lua后仅交付临时修改，须修构建源再重建。外部目录未复制，不声称千星已安装。
`);
put('docs/current/README.md',`# 当前资料入口

本目录是2026-10-04归档基线，引用当前测试交付；历史文档留作追溯。新的人工验收和用户决定应更新此目录及问题台账，不能仅在旧入口追加“最新”。

- [安装](../../outputs/midphase-final/GIA安装说明.md)、[节点](../../outputs/midphase-final/节点安装说明.md)：当前19角色编号、模板索引、接线和排错。
- [设计基线](设计基线.md)：当前范围、视觉和战斗意图。
- [技术实现与验证](技术实现与验证.md)：实现、证据和验证边界。
- [工作流与工具](工作流与工具.md)：制作、构建、测试和导出入口。
- [问题台账](问题台账.md)：已修复、待验、未完成，含后续玩家建议。
- [交接与中期计划](交接与中期计划.md)：下一位执行者的顺序、交付和停止条件。
- [清理与保留](清理与保留.md)、[有效资源索引](有效资源索引.json)：依赖与保留依据。
- [可分享技术](../share/README.md)：不含项目设计、会话及个人信息。

标记：设计=意图；程序实现=已有代码；模拟器验证=本地抽样；真机观察=实际设备证据；待验证推断=尚无证据。没有真机证据的性能结论一律保留待验。
`);
put('docs/current/设计基线.md',`# 当前项目设计基线

游戏名称“原神格斗1.0”，无副标题。主菜单全黑、左右刻晴与迪卢克半身像，居中文字圆润按钮；PC无摇杆/触控攻击按钮。选择页只显示第一批十四位加五位样板，双方各选三名不同角色，三栏阵容给出名字，确认后同步。

双人优先。三名角色分别参加ROUND 1、ROUND 2、ROUND 3，先胜两场结束，不是局内接力。比赛开始从七张国家背景随机选三张不同场景，两端同序。单人AI、接力模式和后续角色批次不属于已交付功能。

场景地面与中远景相连，前方移动区用道具或地形提示，保留地区地标。9000图元档采用像素母版、最近邻、降色、矩形拟合；不能拿旧5000档替代。枫丹/至冬属于地域概念改编，不冒充逐点原作地图。

角色画风统一，拒绝擅自Q版化。可莉以已指定v3母版为准，绮良良参照烟绯修正版；丘丘王用已有正确版本。身体尺度不因伸剑/举手改变，成人站姿显示高度参考约226画布单位，小体型和大型单独规格。视觉身高不等于受击框高度。绫华动作板存在非均匀排版，逐帧ROI解决裁头。

动作和技能保持场上相同侧视角；立绘不能当场上动作帧。角色与特效独立，按位置锚点绑定，具有伤害的特效单独攻击框。E/Q按角色原作特征改编，不要求还原三维原作机制。领域可转为命中演出；状态型必杀的配套动作仍待定。入场和胜利动画要讨论确认，未全员制作。

HUD深色底板覆盖头像、血条、能量、圆点、回合、地点。三蓝点/红点在各自头像下面，当前高亮、败北灰色。快捷键H打开指令表。战斗页不用长篇操作说明，结算返回选人需双方同步。

匿名玩家的伤害、连招衰减、盾反馈、血条拖尾及下段博弈意见保留下一阶段，不在本版静默改变数值。全部角色精做优先于继续扩名单。
`);
put('docs/current/技术实现与验证.md',`# 技术实现与验证

## 交付身份

outputs/midphase-final/delivery.json记录A/B及Lua、时间戳和SHA-256。A是服务器控件界面与客户端Lua，B是通用图元客户端模板。B容器索引必须和Lua的PIXEL_TEMPLATE_INDEX一致，图片孩子名Pixel。脚本挂FighterDemo。没有隐藏LoadingPixelTemplate绑定步骤。服务器官方节点需按说明手工建立；serverLogic只是模拟器。

## 绘制与加载

980静态控件，28662是全部动态池声明容量合计，不是同时常驻。当前背景8660～8841图片；每个模板还有容器，图片数量不能当总控件数量。每场仅建立当前两位角色和当前背景；取消预加载撤队列，后续复用池容量，显示帧以差量更新。软时间预算4ms，创建初值PC96/手机48，不是帧率保证。

跨界面先显示全屏黑幕与派蒙/进度，再分批建图元；显示进度100%后联机仍可能等同Epoch双方Ready。绘制预算和网络等待分开。下一阶段应测解析、创建、写属性、UI布局、联网等待各段时间，不能用模拟器更新次数推真机秒数。

## 战斗和联网

推挤框、受击框、攻击框分开；武器不扩大身体碰撞。普通、儿童、大型有不同初始尺寸，蹲伏/浮空调整受击框。近战仅有效帧检测重叠；火鸟有随运动的独立攻击框，尾迹不通条伤害。每个攻击实例去重，逐招参数仍待人工调校。

连续防御采用guardStun区别受击硬直，加入回滚字段和布尔序列化。快照长度由字段数推导，禁止硬编码长度。动画走时钟使用各自运动累计，不能依赖世界时钟；这只能修时序，不能把平移源图变成真实步态。

脚底、影子、诊断框共用场景地面基线。现用画布高度81%及cover缩放推导，七场景未逐张真机校准。Ayaka攻击13及基础板非均匀ROI已经修正；不得重新用等分4×4覆盖。

FighterTeam按节点说明十一整数，Stage种子1～210编码七场景的有序三张不重复选择；角色ID0～19，0为未选择。Frames透传Slot/FirstFrame/AckFrame/Payload，依Started和席位转发给对方。轮次代Epoch用于准备与状态隔离。两端必须同版本和同编号。签名以节点安装说明为准，不混用旧45角色/旧六参数协议。

## 已有证据

|证据|范围|限制|
|---|---|---|
|verification.json|双方阵容[14,19,8]/[18,11,13]、锁定、三场、背景一致、结算返回|模拟器抽样，非19角色逐个测试|
|collision-verification.json及测试脚本|边缘命中、分离不命中、镜像、蹲/空中、墙推、体型、实际扣血、连续防御/序列化|非逐招美术校准|
|loading-verification.json|全屏黑幕、取消/复用、切页|非手机耗时|
|mobile-verification.json|19.5:9与4:3背景覆盖及触控布局|未全面确认所有窄屏HUD细节|
|round-1.png、绫华拟合检查图|头部完整、顶栏与圆点位置、地面基线|静态抽样，非所有姿势无伪影|
|delivery.json|导出身份和哈希|非官方编辑器实装验收|

真机官方导入、完整节点、加载时长/内存/FPS、网络差异和所有姿势质量尚待验证。旧录像属于历史版本真机观察，不能归给本次包。
`);
put('docs/current/工作流与工具.md',`# 工作流与工具

## 重建当前包

在项目根目录执行 powershell -File work/build-midphase.ps1 -Deliver。可用-NodePath指定Node。构建链依次组装19角色、主菜单、动画工具入口、修复/场景/战斗、加载、四组验证、导出和安装说明。任一步非零停止。导出不自动复制外部千星目录。

已有素材拟合产物是构建输入；重建游戏不等于重新生图。必须保留outputs/test-v1/base.save.json、outputs/group1-full-test/home-portraits.json、当前角色数据、七场景数据及work生成链。不要因目录旧而删除。改代码先改构建源，再构建；不要仅编辑会被覆盖的最终Lua。

## 素材制作

先定动作、尺度、近远腿/武器关系和参考，再生成母版/姿势板。用户撤回专武查询要求，不自行恢复。已否决素材加弃用标记并由导入守卫排除，不物理删除。

透明度查实际alpha通道，不依据预览背景判断。非均匀姿势板用逐帧ROI，保留完整头/脚/剑尖；身体尺寸由站姿参考，不由挥剑最大外框。脚底固定，特效另层。基本姿势、攻击、连接、步态各自播放，镜像验收；帧索引正确不代表肢体正确。

背景重新拟合使用work/build-pixel-country-scenes.mjs，环境STAGE_BUDGET=9000、STAGE_PIXEL_OUT=outputs/stage-pixel-nearest-9000。源图见work/pixel-stage-sources.json；只在本地使用其路径，不复制个人路径到分享文档。角色绫华拟合入口work/build-ayaka-final.mjs。已敲定美术不应因为拟合重生图。

## 可用工具

|入口|作用|注意|
|---|---|---|
|outputs/motion-production/index.html|角色动画工具，下拉角色/动作、可拖关面板|不是官方模拟器，不证明碰撞/联机|
|outputs/action-probe/index.html|动作/独立特效设计实验|历史研究候选，非交付游戏|
|outputs/stage-pixel-nearest-9000/index.html|七场景最近邻拟合查看|看report的实际档位|
|work/inspect-ui-layout.mjs|检查控件层级/位置/尺寸|布局数据不替代截图|
|work/audit-png-alpha.mjs|实际alpha检查|不要凭背景猜透明|
|work/view-ayaka-fit.mjs|绫华基础/攻击ROI抽样查看|不会自动证明所有帧|
|work/verify-repair-collision.mjs|战斗逻辑回归|人工逐招调框仍必要|
|work/verify-repair-loading.mjs、mobile.mjs、verify-test-repair.mjs|加载/比例/双人流程回归|保持REPAIR_OUT为当前目录|
|work/deliver-test-repair.mjs|A/B/Lua命名与哈希|依已有构建成功结果|
|work/write-midphase-install.mjs|从delivery生成当前安装说明|导出之后执行|

历史work/update-nearest-repair-docs.mjs、finalize-repair-docs.mjs不得用于当前文档，会回写旧5000档/旧状态。网页4197/4198旧服务器并不自动成为最新包；核对启动输入和版本，不凭URL断言最新版。

## 交付门槛

抽样选不同体型、不同武器、远程特效；两端选择、单方Ready、三场、返回选人；边缘碰撞、连防、快照恢复；切页进度、取消/复用；19.5:9与4:3。通过后导出，用delivery哈希确认A/B，说明写清模板索引、角色编号和节点变更。每次只交当前A/B，旧包保留在工作区。
`);
put('docs/current/问题台账.md',`# 问题台账

截至当前20261004_143008包。优先级P0阻塞/P1重要/P2后续；“已修复”指程序与抽样证据，不等于真机最终验收。

|项|状态|证据/下一步|
|---|---|---|
|第二/三批退出选人，保留19位|程序实现、模拟器通过|角色编号与双人抽样；源素材保留|
|9000档七背景、每赛三张随机同步|程序实现、模拟器通过|report实际8660～8841，三场一致|
|绫华新比例与56姿势接入|程序实现、模拟器抽样|攻击13和基础逐帧ROI头脚完整，仍须全动作人工复核|
|顶栏完整覆盖、无空蓝框、圆点头像下|程序实现、截图抽样|round-1；窄屏全部HUD还需检查|
|碰撞分离/有效攻击/特效攻击框|程序实现、模拟器通过|边缘/镜像/体型/墙；逐招校准P1|
|连续防御、防御回滚字段|程序实现、模拟器通过|guardStun、动态快照长度；真实连防待验|
|全屏切页黑幕、取消加载、池复用|程序实现、模拟器通过|加载报告；真机耗时/内存P0待测|
|选人同步、双方准备、结算返回|程序实现、模拟器通过|官方节点未安装，实机联机P0待验|
|其余角色左右脚真实步态|P1未完成|源图主要平移，运动时钟修复不能代替补帧|
|体型、脚底与场景尺度|P1待人工复核|站姿参考226；统一81%地面不是逐场景最终标定|
|全部角色效果、独立魔法/武器判定|P1未完成|当前仅部分原型，按招制作验收|
|全员碰撞与数值平衡|P1待逐招调校|体型初值，不依据武器外框放大受击框|
|当前手机FPS/启动/换场网络滞后|P0无当前真机数据|不能引用旧版视频当本版证据|
|完整单人AI|P2未实现|双人流程稳定后研究|
|入场/胜利/状态必杀配套|P2待设计确认|禁止立绘充动作帧|

匿名玩家建议 [原始整理](../玩家反馈需求_20261004_匿名玩家.md) 暂存下一阶段：迪卢克迈步/武器与受击框反直觉；先精做少量角色；防御反馈弱；普攻伤害/连招修正；血条伤害拖尾和连招显示；轻脚/重脚及下段博弈。连续防御修复不等于这些建议全落实。

当前没有“全部已知问题完成”的结论。下位执行者应从P0实装/负载和P1步态补全开始，而不是继续批量扩人物或反复生已确认美术。
`);
put('docs/current/交接与中期计划.md',`# 交接与中期计划

## 接手第一步

读AI_START→本目录→当前安装/节点说明→问题台账。核对delivery.json时间戳20261004_143008和SHA-256。当前A/B在工作区，外部千星复制未获批准，未自动安装。不要向其他任务发送消息，不调整其他AI环境或技能。旧资料是历史证据。

## 第一阶段：实装和负载基线

按节点文档在官方编辑器安装19角色当前协议，双端同版本，验证B容器索引、FighterDemo挂载、列表序号0/1、实体/GUID区别。采集PC/手机冷启动、主菜单→选人、预览、首场、换场、返回选人秒数、创建峰值/驻留控件、内存、帧率、网络确认差。记录设备类别与版本，不记用户姓名/账号/UID。

验收：一次完整双人三场、结算返回再选；单方Ready不开始，旧Epoch输入不跨轮；手机每次切换都有即时黑幕反馈。若慢，按解析/建控件/属性/布局/等待分段找瓶颈，先优化有证据的项。图元预算不是性能承诺。

## 第二阶段：动作与碰撞精做

先刻晴、迪卢克及一位小体型/一位大型做样板，再拓展当前19位。建立真实左右脚交替、接触/通过/离地姿势，固定脚底与头身。保留用户确认的画风，拒绝源标记不解除。动画工具播放与官方游戏都检查；每招对照动作有效段调攻击框，身体受击/推挤框独立，特效绑定独立框。必要时覆盖多种姿态，不能仅加攻击距离。

验收：步态不滑步、不重复同腿；起手/有效/收招可读；贴身与边缘、站蹲空中、墙边、同角色/不同体型有正确结果；同快照重复输入确定。每角色一页参数和截图记录，源板与拟合数据可追溯。

## 第三阶段：战斗反馈与数值

逐条落实匿名玩家建议：先防御/命中反馈、血条拖尾与连招统计，再连招衰减、伤害和下段博弈。轻重脚是否增加需设计决定，不直接扩按键。现行简化键位保留直到确认。以少量角色对战结果调数值，不把六下伤害变更当全平衡。

## 第四阶段：特效与补充模式

先独立效果时间轴、位置/朝向、生命周期和命中框，再补代表性火鸟/雷楔/水流等；复杂状态必杀先做方案确认。演出仍用同侧视角，命中判定与演出结算分离；不让对方无条件受击。单人AI读取可见战斗状态、有限反应/难度，禁止读未来输入。后续人物批次、接力包留后，不进入当前19角色修复范围。

## 每次结束必须交接

版本身份、改动源文件、实际测试证据、未完成/失败、当前A/B与安装说明、可复现命令、人工参数和已否决资源。真机观察/模拟器验证/设计/推断分别标注。未完成不改为完成，不删除历史依赖，不在分享文档存会话及个人信息。
`);
put('docs/current/清理与保留.md',`# 清理与保留

本轮没有物理删除文件。确认无效必须满足：不被构建/页面/素材索引/脚本引用、不承担已批准母版或复现实验、无用户保留要求、有可复核清单。不能仅根据“旧”“小”“重复文件名”删除。构建依赖跨历史目录，当前有效资源索引是保留线索，不是完整无引用证明。

历史文档保留为追溯；本轮根docs专题加历史提示指向current，旧AI_START完整快照移存archive。已否决绫人板、可莉Q版、绮良良旧比例保留弃用标记；后续专门清理再逐个核验。中间GIA保留，只有delivery.json所指为当前安装包，旧时间戳不要再次交付。

安装说明、Lua、数据、截图不放外部千星目录；那里只复制当前A/B，且外部写入需授权。已经拒绝的复制不重试。分享入口只提供通用技术，不含人物名单、美术设计、原始聊天或个人路径；技术复用不更改接收项目工作规则。

有效资源索引含当前构建源、关键数据、交付和验证的相对路径/哈希。它是抽取的有效材料目录，不是整个磁盘扫描。项目以外个人目录不参与整理。下一阶段可按依赖图收集真正冗余清单再交给人工核对。
`);
put('docs/share/图元裁切与回滚字段的排错.md',`# 图元裁切与回滚字段的排错

可分享通用技术，无项目设计或个人信息。以下是本地实现与模拟器实践，目标平台仍应重新验证。

1. 姿势板的行列不一定等宽等高。等分切帧会裁头、截脚或混入邻帧。存每帧ROI，并保留原图；抽样站姿、举武器、空中及收招。身体尺度按站姿参考，武器最大外框不当身高。
2. 预览的黑色/渐变不证明PNG不透明。读取alpha通道统计，再复核边缘；透明判断错误会误拒可用资源。
3. 加新回滚字段时同步序列化、反序列化和长度校验。长度应由结构计算，不硬编码。用往返和恢复后重复输入测确定性；渲染缓存不能进入权威战斗状态。
4. 防御硬直与受击硬直分开，持续按防御不能因上一击进入硬直就失去合法连防。确认代码、显示姿势、快照均一致。
5. 图元数、总控件数、当场容量、实际可见、属性写入量和布局成本分开。池化降低重复创建，差量写入降低换帧属性成本，取消队列防止预加载残留；总声明量不能当驻留量。
6. 黑幕先反馈再分批加载，绘制100%与网络准备等待分开。测实际阶段耗时，模拟器tick不能冒充手机秒数。
7. 空蓝按钮可能是原生按钮的文字缺失，不先当无用控件删除。检查节点类型、子文本范围/最小字号、事件绑定；保留返回/帮助功能再替换视觉。

技术资料不要求读者修改全局提示、任务权限或其他AI工作内容。
`);
const historical=readdirSync('docs').filter(n=>n.endsWith('.md'));
for(const n of historical){const p='docs/'+n;const s=read(p);if(!s.startsWith('> 历史专题'))put(p,'> 历史专题：本文保留当时的设计与实现状态；当前交付及未完成项以 [当前资料入口](current/README.md) 为准。\n\n'+s);}
const share='docs/share/README.md';if(!read(share).includes('图元裁切与回滚字段的排错'))put(share,read(share)+'\n- [图元裁切与回滚字段的排错](图元裁切与回滚字段的排错.md)：非均匀ROI、alpha核验、快照字段、连防和加载诊断。\n');
const walk='assets/repair-art-v1/ayaka-walk-candidates/状态.md';if(existsSync(walk)){const s=read(walk);put(walk,'# 绫华行走试稿状态修订\n\n2026-10-04：此前依据预览背景认定v2不透明，证据不足。实际alpha核验含透明及半透明像素，v2经切帧拟合已进入outputs/motion-group1/kamisatoayaka-final的8帧步态，并接入当前测试包与动画工具。模拟器接入不等于用户确认完整动作质量，仍需逐帧真机复核。\n\n## 原记录（历史判断，不能用于阻止当前已修订接入）\n\n'+s);}
const delivery=JSON.parse(read('outputs/midphase-final/delivery.json'));
const paths=['work/build-midphase.ps1','work/group1-sets.mjs','work/build-group1-full.mjs','work/restyle-group1-home.mjs','work/attach-group1-all.mjs','work/build-test-repair.mjs','work/build-country-scene-repair.mjs','work/final-game-mechanics.mjs','work/build-repair-loading.mjs','work/repair-loading.lua','work/build-roster-v2-loading-generated.mjs','work/finalize-test-repair.mjs','work/deliver-test-repair.mjs','work/write-midphase-install.mjs','work/build-ayaka-final.mjs','outputs/test-v1/base.save.json','outputs/group1-full-test/home-portraits.json','outputs/stage-pixel-nearest-9000/report.json','outputs/midphase-final/delivery.json','outputs/midphase-final/角色编号.json','outputs/midphase-final/verification.json','outputs/midphase-final/collision-verification.json','outputs/midphase-final/loading-verification.json','outputs/midphase-final/mobile-verification.json',...delivery.files.map(f=>'outputs/midphase-final/'+f.filename),'outputs/midphase-final/'+delivery.lua];
const roles=JSON.parse(read('outputs/midphase-final/角色编号.json'));
const routes={kaeya:'kaeya',yanfei:'yanfei',klee:'klee-approved-v3',kamisatoayaka:'kamisatoayaka-final'};
const roleSources=roles.map(r=>{const root='outputs/motion-group1/'+(routes[r.key]||r.key);const manifest=root+'/manifest.json';if(existsSync(manifest)){paths.push(manifest);const data=root+'/data/'+r.key+'.json';if(existsSync(data))paths.push(data);return{...r,source:root,type:'motion-set'};}const data=['assets/roster-v2/'+r.key+'-frames.json','assets/vnext/'+r.key+'-frames.json','assets/test-v1/'+r.key+'-frames.json'].find(existsSync);if(data)paths.push(data);return{...r,source:data||'legacy fallback: consult build-group1-full.mjs',type:'legacy-sample'};});
const resources=[...new Set(paths)].filter(existsSync).map(p=>({path:p,bytes:statSync(p).size,sha256:createHash('sha256').update(readFileSync(p)).digest('hex')}));
put('docs/current/有效资源索引.json',JSON.stringify({version:delivery.stamp,scope:'Selected current dependencies; not an exhaustive deletion allowlist',roles:roleSources,resources},null,2));
console.log(JSON.stringify({documents:7,historicalNotices:historical.length,indexedResources:resources.length,deletedFiles:0}));

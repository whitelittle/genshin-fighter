import fs from 'node:fs';
const write=(p,t)=>fs.writeFileSync(p,t);
write('AI_START.md',`# 工作区入口：210009归档基线

更新：2026-10-04。冻结版本20261004_210009，身份见outputs/full-reinstall/delivery.json。[归档入口](outputs/archive/20261004_210009/README.md)含交付副本、哈希与验收记录。后续版本另建输出，不覆盖冻结文件。

最新真机确认：本版本交互正常，双方进入准备角色。PC和手机资源加载慢未解决；加载结束后开战、完整三场及结算未确认。归档不等于全部已知问题完成。

先读[当前资料入口](docs/current/README.md)。节点看[节点专题](docs/current/节点图知识与排错.md)，下一阶段看[加载对照](docs/current/加载慢与嘟嘟可对照_20261004.md)及[交接计划](docs/current/交接与中期计划.md)。安装以[整套说明](outputs/full-reinstall/安装说明.md)为准，旧midphase-final、network-current-gia及191454/191546是历史，不混用旧信号和GF10套件。

本版19角色、七张9000档最近邻背景和绫华56姿势保留。第二/第三批不在选人页；其余真实步态、逐招碰撞精校等未完成项见台账。用户提供动作设计、Codex接入，先读docs/双人下一版实施与动作交接.md，后续明确指令优先。

工作规则：设计/程序/模拟器/真机/推断分别记录；文档匿名；保留原素材、样例、工具及历史，不因归档删除文件。修构建源再导出。三个GIA、完整Lua、说明已复制千星目录并验哈希，无压缩包；本次归档不操作外部应用。
`);
write('docs/current/README.md',`# 当前资料入口

2026-10-04归档基线：20261004_210009。用户确认交互正常，双方进入准备角色。加载慢未解决；完整对战真机未确认。

- [冻结归档](../../outputs/archive/20261004_210009/README.md)、[交付身份](../../outputs/full-reinstall/delivery.json)、[整套安装](../../outputs/full-reinstall/安装说明.md)。
- [节点图知识与排错](节点图知识与排错.md)：十信号、17变量、分支、GIA编码、绑定与工具。
- [加载对照](加载慢与嘟嘟可对照_20261004.md)：下一阶段优先，优化尚未实施。
- [设计基线](设计基线.md)、[技术实现与验证](技术实现与验证.md)、[工作流与工具](工作流与工具.md)。
- [问题台账](问题台账.md)、[交接与中期计划](交接与中期计划.md)。
- [清理与保留](清理与保留.md)、[有效资源索引](有效资源索引.json)、[可分享技术](../share/README.md)。

历史不覆盖后续决定。设计、程序、模拟器、真机、待验证推断分别标记。归档不表示全部完成。
`);
let p='docs/current/交接与中期计划.md',t=fs.readFileSync(p,'utf8');const a=t.indexOf('读AI_START'),b=t.indexOf('\n\n## 第一阶段');t=t.slice(0,a)+`读AI_START→当前资料→210009整套安装与节点专题→台账。核对full-reinstall及冻结副本哈希。已复制千星目录，用户已确认本版交互正常，双方进入准备角色。下一阶段先修PC/手机加载；真机加载结束后战斗未确认。

保留210009，后续另建版本输出，不重制已敲定美术，不删除历史依赖，不向其他任务发消息或改AI环境。`+t.slice(b);t=t.replace('按节点文档在官方编辑器安装19角色当前协议，双端同版本，验证B容器索引、FighterDemo挂载、列表序号0/1、实体/GUID区别。','先读加载对照，不重做已通过的席位通路。减少提示动画重绘与重复布局，显示解码/创建/回收/绘制阶段及速率；同素材同设备测量。单父容器规模影响待对照，再决定背景分组。保持GF10协议与当前B索引一致。');write(p,t);
p='docs/current/技术实现与验证.md';t=fs.readFileSync(p,'utf8').replace('outputs/midphase-final/delivery.json记录A/B及Lua、时间戳和SHA-256。','当前outputs/full-reinstall/delivery.json为210009，记录A/B、完整Lua、服务器节点及SHA-256；冻结副本在outputs/archive/20261004_210009。').replace('服务器官方节点需按说明手工建立；serverLogic只是模拟器。','服务器节点已有完整GIA，GF10十信号和40项原生定义；导入需核对名称。serverLogic仍只是模拟器。').replace('依Started和席位转发给对方','依同Epoch、双方Ready=2和席位转发给对方，不引用Started').replace('真机官方导入、完整节点、加载时长/内存/FPS、网络差异和所有姿势质量尚待验证。','最新真机确认交互正常、双方进入准备角色；完整对战、加载耗时/内存/FPS、网络差异及姿势质量仍待验。');write(p,t);
fs.appendFileSync('docs/current/工作流与工具.md',`\n## 210009重建与归档\n\nbuild-midphase是基础构建链，不单独保证产出GF10套件。最终组装work/build-full-reinstall.mjs依赖样例5、midphase-final存档和可见诊断Lua，必须保留。节点工具见[节点专题](节点图知识与排错.md)。不要直接交付默认Fighter名称生成器产物。归档脚本仅用于本次冻结，不重复覆盖冻结目录。\n`);
fs.appendFileSync('docs/current/问题台账.md',`\n## 210009归档最新验收（优先于旧记录）\n\n用户真机确认交互正常，双方进入准备角色；席位/选人阻塞不再是当前复现问题。PC和手机加载慢仍是P0；加载完成开战、三场、结算和重赛仍待真机验收。本地节点16项和指针流程3项通过，不扩大真机范围。冻结副本outputs/archive/20261004_210009；本次无删除。\n`);
fs.appendFileSync('docs/share/README.md',`\n- [服务器节点GIA保真生成与验证](服务器节点GIA保真生成与验证.md)：样例、编码、端口与分层验收。\n- [信号与整数导入注意](GIA信号与整数常量导入注意事项.md)：直接/泛型常量及状态陷阱。\n`);
fs.appendFileSync('docs/share/服务器节点GIA保真生成与验证.md',`\n## 整数和导入回读补充\n\n直接整数literal.102与泛型literal.110.2.102不能同时填。泛型已填写整数需字面量状态field2=1，漏状态可能导入变0；负数按有符号32位读取，避免浮点精度丢失。解释器必须检查格式和状态，不仅读取数值。\n\n官方导入后重新导出逐节点对照：信号实际名字和资源ID、参数端口、未连接常量及状态。信号可能自动改名，客户端API绑定必须同步；节点显示名不代表绑定成功。含完整定义用于重装，省略定义引用已有资源仅用于匹配的同关卡，不是独立包。\n\n已有本版交互及双方进入资源准备的真机反馈，但性能与完整战斗未验收。保留版本和样例关系，不扩大发生过的确认范围。\n`);
fs.appendFileSync('docs/current/加载慢与嘟嘟可对照_20261004.md',`\n## 旧格斗轻量Demo的补充核查\n\n本地保留demo-online-light-rollback-diagnostic/fighter.lua和fighter.save.json显示：固定刻晴/迪卢克场景，图元预置在GIA，Lua没有InstantiateClientUIControl创建队列，OnInit直接找控件并绘制。该Lua约339KB，当前完整Lua约4.87MB；字节差不能单独推断耗时。当前新增选人/预览、9000背景及多动作数据，并在试玩时解码、创建当前资源。旧包较快不等于现动态加载应同样快；静态导入成本与试玩动态准备是不同环节。用户尚未指明成功Demo精确文件名，轻量旧版对照需保留这个范围限制。\n`);
console.log('Archive entries and knowledge updated.');

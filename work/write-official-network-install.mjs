import{readFileSync,writeFileSync}from'node:fs';
const out='outputs/network-current-gia',d=JSON.parse(readFileSync(out+'/delivery.json')),v=JSON.parse(readFileSync(out+'/verification.json'));
const ui=JSON.parse(readFileSync('outputs/midphase-final/delivery.json'));
const text=`# 当前完整联机节点图：安装与首次验证

文件：${d.filename}。与界面包outputs/midphase-final/${ui.stamp}版配套。基于两份千星实际导出的节点样例生成，156节点、40信号节点附件（10个信号，每个有4种节点定义）。只有五条业务监听入口，不是40条监听。

## 安装顺序

1. 在服务器节点图资源管理器导入本GIA。本次席位与选人修订需要更新A界面包及节点图，B模板沿用；模板索引按现有B填写，不因更换A而改B。
2. 检查导入图名为${d.filename.slice(0,-4)}。如编辑器提示信号重名，保留当前同名同参数定义；检查导入节点实际仍绑定正确名称与端口。不要把信号改成带编号后缀，否则现有Lua不会收到。
3. 将新图挂到公共控制实体1077936129上。它的“获取自身实体”就是控制实体；不要挂到玩家实体。
4. 暂时取消旧联机图的挂载/启用，只运行新图。旧文件保留；不要把旧图和新图一起运行导致重复发送、旧Started逻辑干扰。
5. 确认控制实体已建好下表17变量。多出的P1Assigned/P2Assigned/Started/IsInit保留也无妨，新图不使用。
6. 确认服务器界面A显示给双方玩家，B客户端图元模板容器索引与当前Lua一致。节点图不替代界面显示或Lua挂载。
7. 开始双端试玩，按下方验证顺序观察。首次官方导入结果尚未验证；如有红色端口、丢信号或导入报错，记录节点号与整段错误，保留本候选及旧图。

## 17变量

|变量|类型|初始值|
|---|---|---|
|P1、P2|实体|无初始引用，Hello时赋值|
|Epoch、Stage、Round|整数|1|
|Wins1、Wins2|整数|0|
|P1Role1、P1Role2、P1Role3、P1Ready|整数|0|
|P2Role1、P2Role2、P2Role3、P2Ready|整数|0|
|P1Revision、P2Revision|整数|-1|

## 这张图做什么

- Hello：列表第0项=P1，第1项=P2。单人先收到Slot1；两人收到各自席位。重复Hello不清阵容/比分。
- Team：按Slot保存阵容Ready/Revision；校验0～19角色范围，锁定时三人非零且不同。Stage为1～210、Round为1～3。新Epoch清双方准备/Revision；旧Epoch与更低Revision丢弃，相同Revision允许补回包。P1发布地图/回合/比分，P2不覆盖公共数据。向双方发送完整11参数。
- Join：人数至少2、请求Epoch等于公共Epoch、两端Ready=2才给双方Joined。重复Join可重发，没有永久Started门槛。
- Frames：当前Epoch及两端Ready=2；Slot1发P2，Slot2发P1。五参数原样发送，包括字符串Payload。静止端输入也转发。
- Flow：Slot1/2、Action1/2/3；再战Action1要求同Epoch；重选/首页Action2/3转发给双方。退出通知的相邻Epoch范围与Flow Revision由现有客户端检查，避免新Team先到后丢退出包。服务器未另外实现加减一计算，不冒称已做精确相邻代次过滤。

图按用户要求不做来源玩家身份校验。信号Slot只是玩家席位，角色取三人阵容和Round；出招、碰撞、动画、进度条在Lua，不增加每技能服务器监听。

## 十个信号

|名称|按顺序的参数|
|---|---|
|FighterHello|无|
|FighterSeat|Slot整数|
|FighterTeam / FighterTeamOut|Slot、Role1、Role2、Role3、Ready、Stage、Epoch、Revision、Round、Wins1、Wins2，11整数|
|FighterJoin / FighterJoined|Epoch整数|
|FighterFrames / FighterFramesOut|Slot整数、FirstFrame整数、AckFrame整数、Payload字符串、Epoch整数|
|FighterFlow / FighterFlowOut|Slot、Action、Epoch、Revision，4整数|

## 真机首次抽样

1. 单端进入有Slot1；双端进入分别Slot1/2。
2. 双方各选三人，两端对方阵容同步；只一端确认或加载完成不得开战。
3. 双方完成加载才开始ROUND 1；两端能移动、跳跃、攻击和防御；静止端仍保持输入确认。
4. 下一回合Epoch增加，双方重新完成加载再开始，背景/比分一致。
5. 结算任一端“返回选人”，两端回选择页；再选再开。再战需双方同意。
6. 测试退出回首页，另一端同时返回；旧场输入不带入新场。

节点号/名称/执行和数据连线见generated-logic.json；逻辑可视说明见节点图逻辑.md。

## 本地证据与限制

verification.json对实际导出后的二进制节点进行独立解释，${v.tests.length}项逻辑检查通过，306引用无悬空、所有信号端口匹配、二进制无损往返与文件头长度通过。这是本地节点模型验证，不是官方引擎执行验证。官方导入、重新映射信号引用、控件显示挂载和双端真机尚待验证。

SHA-256：${d.sha256}。源GIA只读，未删除任何文件。更早同目录导出为生成过程历史候选，以delivery.json所指文件为准。
`;
writeFileSync(out+'/安装说明.md',text);

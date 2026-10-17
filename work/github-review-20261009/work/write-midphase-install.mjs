import{readFileSync as read,writeFileSync as write}from'node:fs';
const out='outputs/midphase-final',d=JSON.parse(read(out+'/delivery.json')),roster=JSON.parse(read(out+'/roster.json')),stage=JSON.parse(read(out+'/scene-report.json')),build=JSON.parse(read(out+'/build.json'));
const A=d.files.find(f=>f.kind==='server').filename,B=d.files.find(f=>f.kind==='client').filename;
write(out+'/GIA安装说明.md',`# 原神格斗1.0：当前19角色测试版安装

交付时间戳：${d.stamp}（Asia/Hong_Kong）。本页对应本目录 delivery.json，不使用历史包的角色编号。

## 导入两个文件

1. 服务器控件模板页导入 **${A}**。
2. 客户端控件模板页导入 **${B}**。已有兼容的通用模板可复用；保留其图片子控件名 **Pixel**。
3. 读取B的容器索引。本包客户端Lua使用 local PIXEL_TEMPLATE_INDEX=${d.pixelTemplateIndex||1073741845}；实际索引不同就修改这个数字。不是Pixel图片的索引、玩家实体、账号UID或控制实体GUID。不需要绑定隐藏LoadingPixelTemplate引用。
4. A中脚本挂在 **FighterDemo** 容器。内嵌映射为 ${d.scriptPath}。不能挂到黑色图片、LoadingScreen或B的Pixel上。
5. 显示A给双方玩家，停止旧界面同时运行。两端必须换成同版A；角色18/19已重新编号。
6. 按本目录《节点安装说明》接线。GIA包含界面和客户端Lua，**不包含已经安装好的官方服务器节点图**；simulator.save.json里的serverLogic是模拟器验证逻辑。

千星导出目录只放A/B的GIA。Lua、说明和验证报告留在工作区。外部目录使用 %USERPROFILE%/AppData/LocalLow/miHoYo/原神/BeyondLocal/Beyond_Local_Export；复制后应核对delivery.json中的SHA-256。

## 游戏流程与操作

开始界面→双方各选三名不同角色→双方锁定→当场加载→ROUND 1。阵容第二、第三位分别用于ROUND 2、ROUND 3，先赢两场结束；不是局内接力。每场背景从开赛时同步选定的三张不同国家背景中取一张。

结算“返回选人”由任一端点击即可让双方返回；再战须双方确认。退出返回游戏首页，不关闭原神。血条下方已替换为蓝/红三圆点：当前出战高亮，败北灰色。

PC：A/D移动、S蹲伏、空格跳跃、J轻攻、K重攻、L防御、E特殊技、Q必杀、H指令表。PC隐藏手机摇杆和攻击按钮；手机使用触控。

## 本次内容

- 仅第一批十四位加五位样板，共19位可选。第二、第三批不在选人页，源素材保留。
- 七张背景采用现有像素母版→最近邻采样→降色→矩形拟合，**9000图元档**；实际范围${Math.min(...stage.countries.map(s=>s.rectangles))}～${stage.maxCurrentStageImages}，只建立当前场景。
- 绫华新比例56姿势（基础16、攻击16、连接16、行走8）接入游戏和角色动画工具；图像边缘和动作仍须真机目视复核。
- 身体推挤框、受击框、有效帧攻击框分离；火鸟使用移动攻击框，尾迹不造成整条伤害。参数为可人工校准的初值。
- 跨界面全屏黑幕、任务进度与派蒙；当前两位角色池、当前背景按需创建，预解码限量，取消锁定撤销队列，后续场次复用池容量。
- 修复连续防御与防御姿态，防御状态纳入序列化；不在这版重新平衡玩家新增反馈中的伤害数值。
- 顶部底板包住双方头像、血条/能量、头像下三圆点、回合和地点；原蓝色空按钮改为可读的返回首页/指令表文字入口。
- 绫华基础与攻击板均改为逐帧裁切；成人站姿身体显示高度基准约226，举手和武器不作为身体身高。脚底、影子、诊断框采用统一场景地面基线。

${build.staticControls}个静态控件；${build.deferredImages}为所有动态池声明上限的合计，**不是同时常驻的图片数**。一个图元模板含容器和图片，不把图片数当成总控件数。

## 安装抽样

双方席位1/2→双方阵容同步→单方锁定不开战→双方Ready=2和同Epoch开战→移动/轻攻/站蹲防御→下一场新Epoch→背景两端一致→结算单方返回选人。若100%后等待，先查Ready、Epoch和Join；若进度/派蒙都不动，先查脚本挂载与B索引。

## 验证与未完成项

【模拟器验证】三场同步、手机19.5:9/4:3全屏、加载取消/复用、碰撞边缘/镜像/推挤、连续防御与序列化通过，报告见verification.json、mobile-verification.json、loading-verification.json、collision-verification.json。

【真机待验证】官方导入、节点接线、手机耗时/内存/帧率。模拟器更新次数不等于真机秒数。

【仍未完成】绫华之外的全员真实交替步态不能标记已修复；已有动作和正确丘丘王素材继续复用。逐招碰撞精调、全部技能特效、单人AI等留在后续清单。新玩家建议暂存，未自动改成当前数值规范。此包是当前测试交付，不宣称所有已知问题已关闭。

## 角色编号

|ID|角色|资源键|
|---|---|---|
${roster.map(([key,name],i)=>'|'+(i+1)+'|'+name+'|'+key+'|').join('\n')}
`);
let nodes=read('outputs/test-repair-v1/节点安装说明.md','utf8');
nodes=nodes.replace('# 第一批完整测试版：节点安装与迁移','# 当前19角色测试版：节点安装与迁移').replaceAll('0–45','0–19').replaceAll('《角色列表与改编》','《GIA安装说明》的角色编号表').replaceAll('R=11,41,32','Roles=14,19,8');
nodes='> 本文适用于 '+A+'。角色范围0–19；Stage为1–210。两端必须同版。官方节点仍需手动创建与真机验证。\n\n'+nodes;
write(out+'/节点安装说明.md',nodes);
write(out+'/角色编号.json',JSON.stringify(roster.map(([key,name],i)=>({id:i+1,key,name})),null,2));
console.log('INSTALL_DOCS_READY',A,B);

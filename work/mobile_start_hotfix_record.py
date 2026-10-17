from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/mobile-start-hotfix-20261014'
doc='''# 移动端开始页紧急补丁 · V9

2026-10-14。匿名玩家反馈已至少两例无法从开始页进入；用户自己的手机可正常进入。这是严重入口兼容问题，不能归因单个设备故障或登记已全面解决。未知机型和版本保留为待核对项。

## 推荐文件

普通六角色稳定/尺寸修复版使用：`gia/gpt_20261014_移动端开始紧急修复_稳定基线_仅脚本.gia`。

若已使用PC连续攻击B预算候选，使用：`gia/gpt_20261014_移动端开始紧急修复_保留PC预算候选_仅脚本.gia`，保留此前显示优化。

只替换GF_HOST主脚本，一次只挂载一份；已有UI模板、图片模板、服务器节点和变量不重导，协议仍6。双方联机可按现有协议运行，但建议保持同一候选便于核对。原文件保留，失败时可换回此前主脚本。没有复制到外部应用目录或实际安装关卡。

## 修复

仅修改`gf_input`和`gf_scene_title`。开始确认不依赖触摸坐标；只对开始页显式启用，战斗摇杆和普通菜单仍要求有效坐标。兼容松开事件CursorUp与点击CursorClick，去重为一次待处理的开始请求，在页面准备好且上一次过渡结束后执行，避免同次事件立即切页穿透。前0.6秒的触摸不再直接丢掉；页面输入代次变化会重建点击区。移动端文字改为“轻触屏幕开始”。没有增加全局自动点击、长按跳过或改变战斗输入。

旧入口只有click处理器，且GetUIPos失败时静默跳过；现已在隔离模拟器复现：点击事件缺坐标、GetUIPos报错、只有松开无click三类无法进入。补丁解决这些条件，不代表已确认两位受影响用户的真实根因。

## 验证

稳定基线：三类旧失败复现；新补丁PC、移动横/竖屏、重复触摸、早期触摸排队、真实近似器命中测试、普通坐标区域仍拒绝无坐标事件，17项检查通过。保留PC预算版执行同一专项检查。稳定版规则3600拍差分、240拍快照、188＋161像素状态通过；完整PC及手机横/竖屏开场到战斗/暂停/结算/重赛/重选通过，60ms延迟、抖动、3%丢包、71/71回滚与断线结算通过。PC预算版的战斗显示/回滚验证沿用上一批，本批专项只核对入口兼容。

两份交付只替换各自原构建中的两个完整模块，反向替换与各自基线逐字节一致；仅脚本GIA只替换一个源码字段，反向还原与原GIA逐字节一致。原生导入及受影响设备复验尚未完成。

## 紧急复验

先让不能进入的设备使用对应补丁，等开始提示出现后轻点并松开，确认能进入菜单、选人并开始战斗。再验证原本正常的手机依然可用。记录设备型号、系统/游戏版本、使用的文件名及是否提示仍闪动；不要记录账号、联系方式等个人信息。

若补丁后仍无响应，下一步区分没有触摸事件、被控件遮挡、脚本停止更新与切页加载停顿。若文字/背景动画完全停止，不能继续认定仅是点击事件问题，需获取对应错误或停住阶段。当前阻断问题继续开放，直到受影响设备确认恢复。

证据：`start-regression.json`、`pc-budget-start-regression.json`、`logic-and-pixels.json`、`mock-flow.json`；`menu-1600x900.png`与`menu-900x1600.png`是模拟器截图，不是真机验证。
'''
(O/'安装与验证说明.md').write_text(doc,encoding='utf8')
p=R/'docs/current/移动端开始页无法进入反馈_20261014.md';s=p.read_text(encoding='utf8');note='> 2026-10-14更新：至少两例匿名玩家无法进入，用户自己的手机可进入，升级为严重入口兼容阻断。仅入口紧急补丁已生成，隔离复现与横竖屏通过，受影响设备真机待复验，问题未关闭。见[补丁说明](../../outputs/mobile-start-hotfix-20261014/安装与验证说明.md)。下方单例状态为历史。\n\n'
if not s.startswith('> 2026-10-14更新：至少两例'):p.write_text(note+s,encoding='utf8')
p=R/'docs/current/V9_匿名玩家反馈汇总_20261014.md';s=p.read_text(encoding='utf8').replace('移动端开始页目前明确只有一位用户报告','移动端开始页现已至少两例反馈，用户自己的手机可正常进入').replace('|单例。标题只处理click，取坐标失败会静默跳过；尚未复现该设备故障|核对动画是否继续、触摸事件、切页、机型与版本；单独诊断，不直接归因机器|','|至少两例，严重阻断。旧click缺坐标/事件缺失三类离线复现，紧急补丁通过横竖屏，受影响设备待验|优先试对应仅入口补丁，核对动画、触摸、切页和版本，不直接归因机器|');p.write_text(s,encoding='utf8')
for p,target in [(R/'AI_START.md','outputs/mobile-start-hotfix-20261014/安装与验证说明.md'),(R/'docs/current/V9_执行与验收台账_20261013.md','../../outputs/mobile-start-hotfix-20261014/安装与验证说明.md')]:
 s=p.read_text(encoding='utf8');note=f'> 2026-10-14 移动端入口紧急修复：至少两例无法开始，用户手机可进入，按严重兼容阻断处理。仅gf_input/gf_scene_title两模块，开始确认无坐标兼容、松开兜底、早触摸排队与去重；稳定/保留PC预算两份仅脚本GIA生成。横竖屏专项及稳定完整流程/规则/回滚通过，受影响设备与原生导入待验，问题未关闭。见[安装与验证]({target})。\n\n'
 if not s.startswith('> 2026-10-14 移动端入口紧急修复：'):p.write_text(note+s,encoding='utf8')
files=[{'file':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in O.rglob('*') if p.is_file() and p.name!='delivery.json']
(O/'delivery.json').write_text(json.dumps({'version':'V9','affectedReports':'at least two; user own phone can enter','severity':'entry blocking','nativeAffectedDeviceVerified':False,'changedModules':['gf_input','gf_scene_title'],'externalDelivery':False,'files':files},ensure_ascii=False,indent=2),encoding='utf8')
print('Urgent entry hotfix recorded; affected-device acceptance remains open')

# 双人回滚 Debug

> 2026-10-03更新：当前候选Lua为`outputs/visual-cache/fighter_online_rollback_debug.lua`，增加席位持续探针与LuaHz/Pose/Writes统计。实机回包已观察成功，性能优化尚未真机验收。最新读数解释见[战斗回滚与诊断技术说明](docs/战斗回滚与诊断技术说明.md)，替换方式见`outputs/visual-cache/使用说明.md`。下文“真机未确认”指历史交付状态。

使用 outputs/demo-online-light-rollback-diagnostic 的最新 build.json 指定 GIA，模板 FighterOnlineRollbackDebug，内部 FighterDemo 绑定 lua/fighter_online_rollback_debug.lua。仍为原 light 人物素材，不是 minimum 精简版。替换当前双人界面，不同时激活两个联机界面；服务端 Hello/Seat/Join/Joined/Frames 信号及接线保持。

画面右侧显示 Lua 更新次数、握手阶段、席位、Hello/Join 调用次数、输入发送与接收次数、最近发送批次字节数、网络帧、连续收到的远端输入确认帧、对方确认收到的本地输入帧、回滚次数、重算帧数与最近事件。计数每秒刷新；错误仍由启动诊断显示。

日志前缀 [NET CLIENT]：Hello SEND、Join SEND、Seat RECEIVED、Joined RECEIVED、首次 FramesOut RECEIVED、STATE 状态变化。Hello/Join 前三次和每十次打印一次，其余不会逐包刷屏。客户端 Lua 日志不等于服务端节点日志；请查看编辑器提供的相应脚本日志位置。

Hello/Join 在未开战时每秒重试。Hello 调用计数证明发送 API 被调用，不能证明服务器收到。Seat RECEIVED/Joined RECEIVED 才证明对应回包回调被执行。

若 Lua 更新次数上升，Hello 调用增加但席位始终 0，检查服务端图实际创建/启用及 FighterHello 监听路标。若服务端 [01] 已出现，而单人测试席位仍 0，这是本图等待第二人后才发 Seat 的正常行为。两人均报到后仍无 Seat，再检查发送目标和 FighterSeat 整数参数。

席位 2、Join 次数上升但开战为否：检查服务端 Join 发送者判断、Started 默认值及 Joined 双方发送。已开战但输入接收为 0：检查 Frames 到达、身份/Slot 校验及 Out 的目标；网络帧停在预测上限通常表示缺少远端输入。

已通过模拟器回滚回归、无服务端时重试和诊断面板文本测试，真机未确认。未新增共享暂停或断线恢复。

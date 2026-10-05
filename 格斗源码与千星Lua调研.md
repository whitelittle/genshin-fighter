# 格斗源码与千星 Lua 调研

调研日期：2026-10-02（Asia/Hong_Kong）。范围：源码入口查找、公开仓库说明及部分源码阅读、本地 Lua API 查阅；未下载完整仓库、未运行外部引擎、未做千星真机验证。

## 源码候选

| 项目 | 语言 / 运行环境 | 本次确认 | 对本项目的参考价值（判断） |
|---|---|---|---|
| [IKEMEN GO](https://github.com/ikemen-engine/Ikemen-GO) | Go，支持 MUGEN 资源 | 官方仓库声明引擎 MIT；界面资源另有许可 | 优先参考传统对战格斗的输入指令、角色状态和碰撞判定 |
| [L2DF](https://github.com/atom-tm/l2df-engine) | Lua，LÖVE 后端 | README 声明 MIT、实体组件、逐帧架构和碰撞；第三方组件许可单列 | 优先参考 Lua 代码结构；其 LF2 风格也适合横版多人打斗 |
| [godot-mugen](https://github.com/jefersondaniel/godot-mugen) | Godot | 已定位项目入口，尚未深入源码和许可 | 备用参考；暂不作为主要移植候选 |

实际读取的 IKEMEN 源码入口：

- [src/input.go](https://github.com/ikemen-engine/Ikemen-GO/blob/master/src/input.go)：CommandStepKey、方向/按钮按下与释放、蓄力字段、CommandSpec 中的时间及缓冲设置。
- [src/char.go](https://github.com/ikemen-engine/Ikemen-GO/blob/master/src/char.go)：角色状态标记、防御、受击、碰撞框和朝向镜像相关实现。
- [L2DF src](https://github.com/atom-tm/l2df-engine/tree/master/src)：已确认 class、manager、external 与 core.lua 等目录入口，未逐模块阅读或验证功能。

上述文件链接指向可变 master 分支，本次未固定提交。README 中的网络功能仅作为作者声明，不代表本次验证结果。

## 学习站实际位置

当前 `%USERPROFILE%/Documents/ChatGPT/千星开发学习站` 主要是像素工作台；学习资料与检索站实际保存在 `%USERPROFILE%/Documents/ChatGPT/嘟嘟可大冒险`。

- AI 入口：[AI_START.md](../嘟嘟可大冒险/docs/AI_START.md)
- 来源记录：[sources.json](../嘟嘟可大冒险/catalog/sources.json)
- 主查阅稿：[客户端控件API文档.md](../嘟嘟可大冒险/sources/community-v3.1/docs/客户端控件API文档.md)
- 原 PDF：[千星奇域_Lua_API说明书.pdf](../嘟嘟可大冒险/sources/raw/千星奇域_Lua_API说明书.pdf)
- 冲突记录：[conflicts.md](../嘟嘟可大冒险/docs/conflicts.md)
- [官方在线 API](https://act.mihoyo.com/ys/ugc/tutorial/detail/mhtakr07vej4)：本次网页读取未取得正文。

Markdown 自述为 7.1、2026-09-23 离线快照，来自社区随包整理；PDF 编制日期 2026-09-25，是基于官方文档的转述件。以下结论依据本地整理稿，未称为当前官方全文核验。

## 对格斗实现有用的 API

行号对应 `sources/community-v3.1/docs/客户端控件API文档.md`。

| 需求 | 文档接口 / 定义 | 位置 |
|---|---|---|
| 运行环境 | Lua 5.3；禁用 io、coroutine、string.dump，os/debug 仅保留部分能力 | 56 行起 |
| 生命周期 | OnInit、OnStart、OnEnable、OnDisable、OnUpdate、OnLevelUpdate、OnDestroy | 70 行起 |
| 逐帧调度 | script:EnableUpdate；OnUpdate 不受关卡时停影响，OnLevelUpdate 受影响 | 80–88 行 |
| UI 创建 | game.InstantiateClientUIControl、DestroyClientUIControl、FindClientUIRoot | 169 行起 |
| 手柄输入 | game.GetControllerLeftStickAxis、GetControllerRightStickAxis、GetDevice | 181 行起 |
| 通信 | game.ServerSignal、script:RegisterServerSignalHandler、GetGlobalCustomVariableValue | 160、193、272 行起 |
| 位置、大小、镜像 | SetAnchoredPosition、SetSizeDelta、SetLocalScale 等 | 646 行起 |
| 按键 | control:AddKeyEventListener / RemoveKeyEventListener，Enum.KeyEventType 的 Down / Up 项 | 678 行起及按键输入章节 |
| 显示与运行 | SetVisible 只改变显示；SetActive 关闭会停止挂载脚本逻辑 | 630 行起 |

## 适配判断

建议参考 IKEMEN 的战斗规则，参考 L2DF 的 Lua 组织方式，再编写千星适配层。外部引擎的 LÖVE、SDL、文件和网络接口无法由本地千星 API 文档证明可用，不能整套直接运行。

适合提炼成独立 Lua 逻辑的部分：输入历史与指令识别、角色状态机、招式前摇/有效/后摇、攻击框与受击框、血量与回合规则。用千星接口承接输入、显示、音效和通信。固定步长属于拟采用的设计，不是文档规定；OnUpdate(dt) 不保证固定帧率。

客户端 UI API 本身不提供已核验的通用格斗引擎或多人回滚接口。服务器信号只证明存在通信入口，不能据此认定延迟、频率、可靠性或回滚能力。

下一步真机需核验：输入同时按键和抬起行为、事件消费、更新时序、UI 负载、服务器信号时延。已有资料中 id / Id 存在冲突；require 映射与 imageType 写入条件也未完全确定，见 conflicts.md。

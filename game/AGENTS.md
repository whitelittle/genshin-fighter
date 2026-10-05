# 原神格斗 v2（game/）— AI 开发约束

给接手这个目录的 AI（Codex / GPT / Claude）和人看。**先读完本文件再改代码。**
界面规范单独写在 [docs/UI_STYLE.md](docs/UI_STYLE.md)，改任何画面前必须读。

本目录的结论分四类，文档和提交说明里必须分开写，不能混：
- **设计**：打算怎么做；
- **模拟器**：离线桩客户端（`tests/harness.py`）和浏览器预览里验证过；
- **真机**：在原神客户端里实际看到过；
- **推断**：没有验证的判断。

截至本文件编写时，v2 **没有任何一项经过真机验证**。

## 1. 运行环境：硬约束（违反就会在客户端里崩或卡）

千星奇域 7.1 客户端 Lua 5.3 沙盒：

| 约束 | 做法 |
|---|---|
| 没有 `load` / `coroutine` / 文件 IO | 所有模块经 `tools/bundle.py` 打成一个文件，模块用懒加载 `require` |
| 单次回调约 120 万条 VM 指令就会被中止 | 每帧上限按 **100 万** 算。超过 100 万时测试会标出 heavy 帧，必须分帧 |
| 运行时不能大量实例化控件模板 | 只用**预放的控件池**：`GF_IMG_0001..10000`、`GF_TXT_001..160`、`GF_BTN_01..24`，挂在客户端根节点下，和宿主文本框 `GF_HOST` 同级 |
| 首个 `OnUpdate` 之前不能改兄弟顺序 | 启动流程已经分帧（`gf_main.lua` 的 `BOOT_STEPS`），别往 `OnInit` / `OnStart` 里塞工作 |
| 每次改动都会让整张画布重新合批 | 每帧只写变化的值。`gf_gfx.lua` 的 Node 带缓存，**不要绕过 Node 直接调原生 setter** |
| 文字控件很贵（约 9µs 一个，富文本每个字一个四边形） | 文字控件池只有 160 个。不用富文本拼图；大字用 `Layer:label` 自动缩放 |
| 字号超过 80 没验证过 | `Layer:label` 已经把 80 以上改成"80 号字 + 缩放"，不要自己设大字号 |
| 打包后的文件上限约 7.5 MB | `tools/bundle.py` 超限会报错 |

### 帧预算的具体规则

- 一帧之内最多重建**一个**高清角色位图（约 1200 个矩形，约 18 万条指令）。参考 `gf_scene_select.lua:previews()` 和 `gf_scene_title.lua:buildFighters()`。
- 场景的第一帧只创建图层节点。卡片、立绘、背景从第 2、3 帧才开始建（看 `frameN` 的用法）。
- 大批节点的释放走 `G.releaseLater`（每帧回收 400 个），不要在切换场景的那一帧里同步释放上千个节点。
- 背景画（约 1100 个图元）用 `bd:step(n)` 分帧建，解码也分帧（`gf_paint.lua`）。

## 2. 架构速览

```
lua/gf_main.lua        入口：收集控件池 → 分帧启动 → App；联机原生接口（自定义变量 + 服务器信号）
lua/gf_app.lua         场景切换（travel = 斜切转场）、图层、设置、背景、联机心跳
lua/gf_gfx.lua         Node 缓存写入、控件池、Layer（即时模式）、Bitmap（双缓冲位图）
lua/gf_ui.lua          前端组件库（见 UI_STYLE.md）——画界面只能用它
lua/gf_sim.lua         确定性格斗模拟（60Hz，整数）；snapshot / copy / hash 供回滚
lua/gf_net.lua         GGPO 式回滚（移植自泡泡堂 pp_net）
lua/gf_online.lua      两人房间 / 会话 / 心跳 / 掉线
lua/gf_ai.lua          电脑 AI（4 档）
lua/gf_kits.lua        武器招式、技能、爆发、元素反应数据
lua/gf_fview.lua gf_fx.lua gf_hud.lua gf_stage.lua gf_touch.lua   对战画面
lua/gf_scene_*.lua     各场景：intro title menu select vs fight result options howto online gallery(设计样张)
lua/gen/               生成文件（角色位图、背景画、名单），不要手改
tools/                 build_art.py（角色）build_stages.py（背景）bundle.py（打包）preview/（浏览器实时预览）
native/gf-relay.ts     联机服务器中转节点图（genshin-ts）
tests/                 离线测试与截图工具
```

## 3. 模拟（gf_sim）的确定性规则：联机依赖这些规则

联机靠两端各自运行同一个模拟来保持同步，下面任何一条被破坏都会导致不同步：

- 只做整数运算，位置用厘单位（`C = 100`）；除法用 `//` 或 `floor`。
- 模拟里不准用 `pairs` 遍历去影响结果，不准用 `math.random`、`os.*`，也不准读取任何客户端 API；随机数只用 `self:rand(n)`。
- 招式、套装、角色这类表在模拟里是**只读共享**的（`S.copy` 不复制它们），不能往里写。
- 每局新增可变的子表（列表、计数）时，必须同步更新 `S.copy` 里的复制逻辑，并把关键字段加进 `S:hash`。
- 视图层（fview / hud / fx）只读模拟，不写模拟。

改完模拟必须跑 `tests/test_sim.py`（确定性）和 `tests/test_net.py`（回滚一致）。

## 4. 界面：最容易做坏的部分

**不准**自己发明新的盒子、卡片、按钮样式。所有界面用 `gf_ui.lua` 的组件拼：

- `UI.leftPanel` + `UI.screenTitle`：菜单类界面（暂停、设置、说明）
- `UI.menu`：列表菜单（选中斜条扫入；`numbers = true` 显示序号，`accent` 设置强调色）
- `UI.slab` / `UI.stripes` / `UI.chevron` / `UI.constellation`：斜色块、斜线纹理、箭头、星座环
- `UI.element` / `UI.badge`：七元素徽记（**不要再用四角星当图标**）
- `UI.prompt`：键帽按键提示，第 7 个参数传菜单动作即可触屏点击
- `UI.tap`：任意触屏点击区域

完整的视觉规范、禁止事项、配色和字号见 [docs/UI_STYLE.md](docs/UI_STYLE.md)。

### 改界面的必经流程

1. 用 `python -X utf8 game/tests/shot.py <场景名> [--args "<lua 表>"] [--keys "S,J"] [--at 1.5]` 截图，打开 `game/build/shots/scene-<场景名>-0.png` 自己看。**不看截图不算完成。**
2. 对照 UI_STYLE.md 的检查清单逐条核对（重叠、对齐、图层顺序、斜向一致）。
3. 新组件先放进 `gf_scene_gallery.lua`（设计样张）里，看过再用到场景里。
4. 手机比例也要看：`--canvas 1950x900 --device Mobile`。

### 图层顺序（常见错误）

同一图层里，后创建的节点画在上面。背景色块要放在 `app.layers.back`，角色放 `world`，界面放 `ui`。背景画由 `app:backdrop` 统一放在 `back` 的最底下。场景里面板会盖住菜单时，先建面板的 Layer，再建 `UI.menu`（参考 `gf_scene_options.lua`）。

## 5. 联机

- 客户端：`gf_online.lua`（房间、心跳、开局握手、掉线处理）和 `gf_net.lua`（回滚）。对战场景在 `args.online` 时由会话驱动模拟（`gf_scene_fight.lua:netTick`）。
- 包格式固定为 24 个整数，包类型 `-7201`。改 `gf_net.N.F` 时必须同步修改 `native/gf-relay.ts` 的长度检查。
- 服务器侧要装上 `native/gf-relay.ts`，并配好以下变量和信号：
  - 玩家自定义变量（int）：`GF_NONCE`、`GF_SLOT`；
  - 关卡自定义变量（int 列表）：`GF_IN_1..8`、`GF_SLOTS`、`GF_DIAG`；
  - 信号 `SQ_REC_STRIKE_V1`，带一个 int 列表参数。
  **这一步还没做，也没在真机验证过。**
- 回滚时重算出来的帧，事件按帧去重后才播放特效和音效（`onNetFrame`），新加事件类型不用额外处理。

## 6. 测试命令（都在仓库根目录运行）

```bash
python -X utf8 game/tests/test_sim.py        # 模拟：对局能打完、确定性、16 角色、双方同时倒地
python -X utf8 game/tests/test_net.py        # 回滚：三种延迟和丢包下，两端已确认状态一致
python -X utf8 game/tests/test_online.py     # 两个完整客户端经模拟中转：大厅 → 对战 → 掉线 → 结算
python -X utf8 game/tests/test_touch.py      # 触屏：摇杆、按键、多指同时按、暂停、菜单点击
python -X utf8 game/tests/walkthrough.py     # 全流程走查 + 截图 + 指令峰值（加 --device Mobile --canvas 1950x900 测手机）
python -X utf8 game/tests/shot.py menu       # 单个场景截图
python -X utf8 game/tools/preview/server.py  # 浏览器实时预览 http://127.0.0.1:8765/
```

提交前至少跑：`test_sim`、`test_net`、`test_touch`、两种比例的 `walkthrough`。任何一个出现 Lua 错误、heavy 帧（单帧超过 100 万条指令）或 FAIL，都不能提交。

测试不准作弊：断言错了要在提交说明里写清楚原因；布局变了就让测试去读游戏里的实际位置（参考 `test_touch.py` 的 `tapArea`），不要硬编码新坐标。

## 7. 生成与打包

```bash
python -X utf8 game/tools/build_art.py       # 角色：assets/roster-v2 → lua/gen/gf_art_*.lua（--preview 出对照图）
python -X utf8 game/tools/build_stages.py    # 背景：build/bgfit/*.json → lua/gen/gf_bg_*.lua
python -X utf8 game/tools/build_logo.py      # 标题 logo：tools/logo/logo.png → lua/gen/gf_logo.lua（--preview 出对照图）
python -X utf8 game/tools/bundle.py          # 打包 → dist/genshin_fighter.lua（测试会自动打包）
```

- 标题 logo 是图形，不是文字：先在 `tools/logo/logo.html` 里用 Canvas 画（运行预览服务后打开 `http://127.0.0.1:8765/logo`，点"导出 PNG"会写入 `tools/logo/logo.png`），再运行 `build_logo.py` 烘焙。要用纯色分层，不要用柔和渐变；字形要画成正的，倾斜交给游戏里旋转（斜边每一行都会多切出矩形）。高清档控制在 4000 个矩形以内。

- 新增角色：先改 `tools/roster.json`，再在 `assets/roster-v2` 里放齐 12 个姿势图，接着在 `gf_kits.lua` 补技能、爆发、称号和英文名，最后重跑 `build_art.py` 和测试。
- 背景画的拟合输入（`build/bgfit/*.json`）提交在仓库里。拟合工具不在本仓库。

## 8. 文档与隐私（沿用仓库根目录 AGENTS.md）

文档、提交说明、注释里不准出现真实姓名、昵称、UID、联系方式，也不准出现带个人用户名的本机路径（用 `%USERPROFILE%`）。

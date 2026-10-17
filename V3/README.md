# 原神格斗 V3 — 有效开发基线

2026-10-08：匿名玩家表示当前版本“流畅很多”“目前相对满意”，明确作为 V3 保留并继续设计其余角色。本版本不是作废版本。旧 r33 实验归档只作历史，不能据此回滚 V3。

入口：`client/genshin_fighter.lua`。它与已交付的 GF_r33_opt_E.lua 字节一致，运行标识仍为 r33-opt-E-20261008；V3 是项目版本，不为改名字而重新改变已认可代码。

- [统一标准](docs/CHARACTER_STANDARD.md)
- [本轮决策与验证边界](docs/DECISIONS.md)
- [工作流](docs/WORKFLOW.md)
- [角色扩展设计](design/ROSTER_PLAN.md)
- [素材、工具与安装索引](docs/ASSET_INDEX.md)
- [刻晴首轮动作卡](design/keqing.json)、[迪卢克首轮动作卡](design/diluc.json)：设计候选，未制作或实机验收。

当前可运行阵容为雷电将军、纳西妲。没有元素反应、没有本地双人对战入口；E/Q、对战电脑、联机对决保留。场景固定为简单图元训练场。

## 复现

在仓库根目录运行：

```bash
python3 V3/tools/rebuild.py
python3 V3/tools/verify_assets.py
python3 V3/tools/lua_runner.py V3/client/genshin_fighter.lua V3/tests/checks-e.lua
python3 V3/tools/lua_runner.py V3/client/genshin_fighter.lua V3/tests/checks-d.lua
```

Lua runner 使用系统 liblua5.4.so.0 执行离线检查，不代表目标客户端 Lua 5.3 指令预算或手机性能。生产代码没有文件 IO / load / coroutine。已有真实模拟器全流程记录见 verification/full-flow.json；该记录不能证明双设备联机已验收。

新脚本仍须导入已有配套客户端 UI 与图片模板。installation/reference/ 仅保存历史模板和安装结构参考；旧 GIA 内的 r33 Lua 不等于 V3，禁止混装后称为 V3 完整包。

# V2 双图元池 · 方向组合恢复版（2026-10-07）

本版恢复方向组合 + 攻击触发元素战技，保留 E 战技、Q 爆发的键盘与按钮输入；说明同步。含倒地起身修复、左右对齐的全身 VS 页面、原版背景、黑屏进度条。对战入口为对战电脑与联机对决，帮助页去掉元素反应说明。

## 文件与导入

- GF_DUAL_POOL_A.gia：主界面，包含完整新版 Lua。初始 378 控件，其中 256 图片；运行后按场景构建第二池。
- GF_DUAL_POOL_B_ImageTemplate.gia：第二池图片模板。先导入 B，再导入 A；默认布局只放 A。
- GF_DUAL_POOL_Lua_Only.gia：已有 A/B 时可只更新脚本资源，然后将新版 genshin_fighter_dual_pool 挂载到 GF_HOST，保持只挂一份。GF_ROOT 不挂主脚本。
- genshin_fighter_dual_pool.lua：完整 Lua 副本，用于核对或外部脚本方式。
- verification.json：GIA 解码、脚本一致性及控件保留验证。

已有双池界面可保留，仅更新 GF_HOST 的脚本。导入后确认脚本资源内容更新，并检查 GF_HOST 的脚本挂载。

## 模板索引

保留原来的 GF_IMAGE_TEMPLATE_INDEX 参数读取方式，默认值为 1078305000。如果官方编辑器给 B 分配了其他实例化模板索引，填入实际 GF_IMAGE_TEMPLATE_INDEX 参数；也可在 Lua 的 G.configureSecondPool 调用处修改默认值。使用图片模板资源索引，不是普通子图片的控件索引。之前手工配置的实际索引需要继续使用。

## 验证范围

模拟器已验证：E/Q 键盘和快速按钮点击、朝左/右的方向组合触发、跨回合倒地起身、回滚一致性、触屏和菜单到战斗流程。A 的非脚本 protobuf 数据逐字节保持，控件树解码一致；B 原样保留；A 和 Lua-only 解码后的完整 Lua 与发布源一致。

尚未在官方原神客户端验证本发布包的导入、模板索引和运行结果。

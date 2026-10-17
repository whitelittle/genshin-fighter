# 原神格斗 V4：AI 接手入口

## 当前任务已暂停

用户于 2026-10-09 08:05（香港时间）要求停止全部制作，等待已发出的图完成，整理进度并准备 GitHub 提交。不得自动恢复生成、耗用额度、覆盖旧版本或发布。当前批次 016 已完整返回，调度器已终止。停下是用户指令，**不是额度耗尽**。

## 先读这些文件

1. `V4/AGENTS.md`、`V4/docs/CHARACTER_CREATION.md`、`V4/PROGRESS.md`。
2. `V4/docs/STYLE_LOCK.md`、`V4/docs/ROSTER_PLAN.md`、`V4/docs/WORKFLOW_AUDIT.md`（若路径不同，用文件名定位）。
3. `V4/design/FULL_DELIVERY_CURRENT_20261009.json`：当前 350 组设计与实际素材状态。
4. `V4/evidence/full-delivery-20261009/ACTUAL_MANIFEST.json`、`VISUAL_ISSUES.json`：实际产出、哈希与抽样问题。
5. `V4/design/FULL_PRODUCTION_JOBS_20261009.json`：计划并非产出；`batch-001.json` 至 `batch-016.json` 才是实际请求记录。

## 实际进度

本轮请求 64 项，成功生成 63 张身体动作候选，共 252 个显示姿态。light3 新增 12 张，heavy 14 张，crouchlight 13 张，crouchheavy 14 张，airlight 10 张。此前 light3 的钟离、八重神子已在上一轮候选中，因此此组首版覆盖 14 人。

玛薇卡 crouchlight 因服务输出安全检查拒绝而失败，记录在 batch-008；不要把它当额度限制，也不要尝试绕过该拒绝。

**正式验收 0，游戏接入 0。** 本轮都是候选，不能宣称全部游戏动作已完成。武器/助手/特效、真实脚底/握点/身体尺度、60Hz 时间轴、判定、模拟器和真机验证仍未完成。诊断拟合不是正式 V3 painter 编码。矩形像素重建通过仅证明拟合数据一致，不证明画风、动作或性能验收。

## 阵容与硬约束

只推进原阵容隐藏 14 人：furina、zhongli、mavuika、venti、kamisatoayaka、tartaglia、aratakiitto、yaemiko、arlecchino、wanderer、neuvillette、clorinde、navia、skirk。刻晴/迪卢克旧计划不适用。25 动作组以 CHARACTER_CREATION 为准。

保持 V3 雷电/纳西妲画风，拒绝大头 Q 版、角色比例或衣装漂移。身体、武器、助手和特效独立。玛薇卡无眼镜，E 收招仍骑车刹停。芙宁娜空手指挥，三名沙龙成员须符合原参考。荒泷一斗保留瘦而有肌肉的原比例和长衣摆；普攻大剑、Q 鬼王棍分开。

投技与受投技必须成对校验。Q 完整演出仅确认命中后触发；空挥/格挡走短分支。60Hz 逻辑与图片姿态分开；确定性状态、snapshot/copy/hash、hit ID 和高速连续扫描照规范实现。双缓冲原子换帧、池和双角色峰值预算必须实际测量。

## 恢复与验证

完整交接 ZIP 包含原 V4 快照、续作候选、脚本和冻结 V3 E 基线。网页上传版本拆成每片 20 MiB；运行同目录 `restore_v4_handoff.py` 会校验分片/完整包 SHA256，并恢复到独立 `v4-handoff-20261009/`，不覆盖已有游戏目录。恢复后运行 `python3 v4-handoff-20261009/tools/verify_handoff.py`。原恢复 ZIP 中 1607 项逐项校验：修改 0、缺失 0。

诊断可重建：安装 `numpy` 与 `Pillow`，运行 `python3 V4/tools/process_full_production.py`。该脚本不会调用图像生成服务。它会重写诊断输出及父目录 deliverables；历史提示词中的绝对参考路径通过 V4 相对路径解析。源图已经复制到 assets，不能依赖原会话的 generated_images 路径。

最新 HTML 预览可离线打开；不是游戏运行时。每张候选的逐姿 PNG、GIF、fit.json 和对比图都在 evidence 中。

## 下次获得用户恢复指令后

先修 VISUAL_ISSUES 中的动作误解和分层问题，再决定是否继续计划。未请求的新计划从 **0-based 索引 64** 开始：那维莱特、克洛琳德、娜维娅、丝柯克 airlight。278 项计划中剩余 214 项尚未请求。不要只按 cursor 跳过失败项；按实际 receipt 去重。不要运行 `continue_actions.py prepare`，会重置旧队列。

当前批量提示词把部分助手动作错误地施加给身体；应先修提示词的身体/助手分工。武器角色的握点必须按每个动作解释，不可把单一攻击手型套到全部移动、防御、受击动作。不得因图像隐藏 RGB 显示的底色而重复去背景；检查 PNG alpha 和深浅底实际合成。

## GitHub 提交策略

已从网页确认目标仓库为 whitelittle/genshin-fighter，原 master 为 2fc29aec0529f47c8da33f1432ac61ca5ad2a04f。用户明确不用插件，要求网页手动上传。网页已登录；本包只用于交接候选。必须先确定用户的目标仓库，读取其 AGENTS 与当前 HEAD。不要把本地恢复快照强推到旧分支；在远程已有历史的新分支上仅添加独立的 `handoff/v4-20261009/` 目录或等效增量，再创建审查提交。禁止 force push、改写旧 tag、直接覆盖 main 或旧版本目录。

已有旧 V4 文件逐项核对原恢复 ZIP：1607 项，修改 0、缺失 0。校验证据在 BASELINE_VERIFICATION.json。V3 已认可 E 基线另存于 `runtime-baseline/GF_r33_opt_E.lua`，保持冻结；这不代表已恢复完整模拟器/构建链。

没有上传账号凭证、令牌、用户私人配置或会话工具日志。历史请求回执保留生成失败原因和原提示词供追溯。

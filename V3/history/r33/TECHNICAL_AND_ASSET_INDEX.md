# 技术与素材索引

## 原 V2 可复用源

- `game/tools/build_art.py`：12 个母动作、SD/HD 缩放、共享调色板、分层 painter、角色锚点和报告。
- `game/tools/artlib.py`：premultiplied-alpha BOX、重要像素加权 OKLab、去孤点、保护重要细节、透明不覆盖的矩形绘制。
- `assets/roster-v2/`：原始角色姿势 PNG、帧 JSON、talent JSON、头像源。
- `work/`：原始构建脚本和提示/元数据，使用前只提取字段，避免把嵌入数据直接复制进说明。

## r33 归档素材

`deliverables/` 保存 sealed Lua、GIA、zip 和安装说明；`source-snapshots/` 保存 3e 基线与合并审计。原仓库已有的角色素材不重复拷贝，以仓库路径和哈希作为索引。r33 的 SD 两角色素材、304 帧和描边只作为研究样本；草神 2px 描边明确拒绝。

## 资源规则

透明度先做真实 alpha 检查，禁止把棋盘背景当透明图。角色、背景、特效和 UI 分开统计并设并发预算。原 V2 离线覆盖绘制是最终索引图层合成，不等于已验证的 native mask API；不要把两者混为一谈。

# 钟离全动作接续 · 2026-10-11

当前角色是钟离。25组、145显示姿、144独立身体源姿、E岩脊4姿、Q陨星3姿齐备，59张生成原图包含失败稿。当前是完整美术候选；正式战斗、模拟器、浏览器、真机和用户验收未完成。

## 本次修复

旧预览在E第36 tick收招结束后仍保持E末姿到94 tick。本轮改为第36 tick开始使用待机两姿循环，源图、初拟合、优化拟合分别加载同档待机。岩脊仍独立在14..93 tick展示；人物施术36 tick、生成命中19 tick一次，无新增后摇或持续伤害。源图、攻击参数和判定设计未改。

三档素材、25组、Q三分支共3444 tick的JavaScript控制流程检查通过；E逐tick检查282次，离线内嵌脚本与app.js一致。测试使用替身画布和图片加载器，不能替代浏览器或视觉验收。1109项生产文件逐项哈希已核对；单姿图元357..1097，不能推断双人性能合格。

## 恢复

本分支以work/v4-handoff-20261009为基线，保留master。14个zhongli-all-materials ZIP保存第6版全部生产资料与历史；zhongli-preview-fix-20261011.zip保存本次修复、验证脚本与台账。

运行根目录`python3 restore_zhongli_snapshot.py`，先校验15个ZIP的SHA256，再按序恢复至`outputs/zhongli-design-20261011`，恢复重复路径并应用补丁。离线打开`full-actions/offline.html`。

```sh
node outputs/zhongli-design-20261011/download-materials/scripts/verify_zhongli_preview.cjs outputs/zhongli-design-20261011/full-actions
```

重新生成旧查看器后运行`repair_e_neutral_tail.py FULL_ACTIONS目录`，再跑验证。补丁支持重复运行。旧build_zhongli_full等脚本仍依赖原项目布局，未声称任意目录都能完整重建。

## 准确断点

- 美术：逐姿头颈与髋膝踝、步态、握点及枪杆/枪尖连续性待精校。部分持枪PNG仍为身体与武器组合稿，独立武器层未完成。人工投影、足底像素簇和源图提取无触边标记不能当作美术验收。
- 战斗：伤害、硬直、击退仍为null，碰撞盒为设计值。下一步先在隔离训练闭环接轻攻一，标定武器层、握点与攻击盒，再扩展其他招式。E施术与岩脊生命周期分离；Q确认16 tick不扣血，52 tick唯一陨星伤害；落空/防御无完整演出。投技墙边与体型实际验证未做。
- 工程：新状态copy/snapshot/hash、hitId防重复、快速攻击扫掠、池与双缓冲、双人峰值和回合重开待实现及回归。V3 E认可基线保持，候选角色不得直接开放正式阵容。
- 本轮没有新增浏览器/GPU、模拟器、真机或用户通过记录。

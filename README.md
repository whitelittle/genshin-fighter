# 原神格斗维护工程

千星奇域格斗原型、角色素材制作工具与本地验证资料。先读 [工程维护入口](docs/maintenance/README.md) 和 [工作区导航](AI_START.md)，再按任务阅读对应目录的 AGENTS.md。

| 入口 | 内容 |
|---|---|
| [技术与制作标准](docs/maintenance/技术与制作标准.md) | 确定性模拟、输入、连段、母版、拟合、特效与预算 |
| [开发制作与验收流程](docs/maintenance/开发制作与验收流程.md) | 制作、接入、验证、重建与交付 |
| [素材与版本索引](docs/maintenance/素材与版本索引.md) | 当前素材、候选和必要历史来源 |
| [整理与验证记录](docs/maintenance/整理验证记录.md) | 已检查项目与现存限制 |
| [普通维护源码](runtime/README.md) | 未压缩的可编辑主线源码和工具 |
| [风旅行者教学候选](docs/current/风旅行者三向E与挑空追跳_20261017.md) | 独立 v27、三向 E、挑空追跳与连段保护 |
| [六角色冻结基线](docs/current/稳定版资料_20261013/README.md) | 稳定版资料与回退入口 |

原图、提示词、动作编排、标定与拟合数据保留原路径。设计、模拟器验证、真机观察和待验推断分别登记；素材保存状态与美术验收状态分别标注。

本地验证依赖见 [requirements-maintenance.txt](requirements-maintenance.txt)。历史分支通过 `archive/20261018/` 标签保留。待取走的冗余资料留在本地归档目录，移出原因和文件校验见 [归档清单](docs/maintenance/archive-manifest.json)。

本轮保存与分支整理结果见 [Git 上传回执](docs/maintenance/Git上传回执.md)。

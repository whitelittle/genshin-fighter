# V4续作入口

本轮新增素材先查 `design/CODEX_CURRENT_OVERLAY_20261009.json` 与 `evidence/codex-batch-20261009/BATCH_MANIFEST.json`；原FULL交接表保留历史，不能因为旧表没有新增源图而重复制作。固定格限制已撤回、狐灵为粉色，八重合成撤除了额外刃形效果。新增均是候选，验收/游戏接入仍需完成。

本阶段范围仅原隐藏14人。用户授权跨角色持续制作，不等待逐人最终验收；不要刻晴/迪卢克。火神任何动作不得带眼镜；E收招保持骑车制动，不强制车辆离场。芙宁娜空手指挥三沙龙成员，按用户参考身份及朝右侧视锁定，不复活泛用动物。

每轮先读AGENTS.md、README.md、PROGRESS.md、docs/CHARACTER_CREATION.md、STYLE_LOCK.md、WORKFLOW_AUDIT.md、ROSTER_PLAN.md与设计卡。20261009重新恢复并读取的V3新版统一标准是docs/recovered-v3/0973abebfabd03dd8105aa6e4af6f0461a7b7b7e.md；同目录旧提案/历史记录不能覆盖最新用户授权。

最新实际工作清单：design/ACTION_QUEUE_20261009.json。entries是14×25=350项覆盖表；generation_specs只有实际请求或待生成源图，source/fitting/playback/runtime/device/accepted分别记录。design/ROSTER_JOBS.json保留E和早前增量。逐条检查存在与哈希，不把350张设计卡等同350组源图。

新增全提示词：prompts/actions-20261009。新增源图：assets/action-candidates-20261009。拟合/切帧/播放证据：evidence/actions-20261009。tools/continue_actions.py prepare只用于首次准备，会重置清单，续作不得再次运行；register用于保存新输出。tools/fit_action_batch.py提供诊断拟合，原V3 artlib与painter仍缺，不能宣称标准编码/运行时验收。

V3 Git增量归档缺前置提交c7d2c3517e37411b0b0b3675cd152e263656a223，5个delta未解析。已恢复可读取的5份标准/历史Markdown，具体Git blob/SHA256在evidence/v3-bundle-recovery.json。未构造假提交、未修改稳定E客户端。

身体/武器/助手/特效独立；配对接触图只是研究。动作有起手/有效/收招，图片姿势不是逻辑tick；Q只确认命中完整演出，投技双方全过程。新状态加入copy/snapshot/hash、连续扫掠与命中ID去重；双人峰值/池/完整帧原子缓冲/描边标准不变。

生图按真实限制保存错误与准确断点，未报额度限制不得写额度已耗尽；不切付费API。新源图先记录问题并保留，不无休止只返修一人而阻塞其余角色。

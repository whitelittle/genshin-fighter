# V3 素材与技术索引

| 路径 | 用途与可信范围 |
|---|---|
| client/genshin_fighter.lua | 当前正式 E 基线，完整 SD 数据、逻辑、联机与视图 |
| source/modules/、source/order.json | 源码加载块及精确拼接顺序；含完整动画/补帧/特效数据 |
| assets/animation-source/ | 母素材、纳西妲各动作图、取景、兰那罗、眼睛、补帧任务、提示词与 manifest |
| assets/action-reference/ | 两角色原图及已有动作预览页面，safe 帧图与 atlas；历史预览不代表 V3 当前运行效果 |
| tools/legacy-animation/ | 拟合、透明边缘、SD、补帧接入、技能/投技、池与流程测试历史工具；有硬编码旧路径，需先移植 |
| verification/raiden-idle-frame-audit.png | 待机原帧和错误补帧对比；中间图为被排除研究样本 |
| verification/full-flow.json | E 真实模拟器流程记录；没有双设备验证结论 |
| history/r33/ | 旧设计与归档，结论受 V3 最新决定约束 |
| installation/reference/ | 原图片模板及历史安装位置参考，不包含已重新验证的 V3 全套 GIA |
| ../game/tools/build_art.py、artlib.py | 原 V2 painter、共享调色板与 alpha/OKLab 技术，不重复复制 |
| ../assets/roster-v2/ | 原角色素材，可用于续作核对，不能自动认作 V3 已完成动作 |

MANIFEST.json 为全部本目录保留文件记录 SHA-256 与字节数。当前运行素材以正式客户端与源码块为准；源图中仍保留错误/历史补帧，必须按标准逐个验收后选入。未用的大包、历次错误 GIA、下载辅助文件、整个模拟器 vendor 不重复塞入 V3。

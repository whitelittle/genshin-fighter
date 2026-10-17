# 纳西妲正常比例动作版

2026-10-03，独立素材候选，原版保留。打开 http://127.0.0.1:4196/outputs/motion-production/index.html ，选择“纳西妲 · 正常比例”。

设计：以正常比例待机母版为参考，保留儿童身高150，缩小大头效果，统一侧面战斗视角。48张独立姿势覆盖16类动作：待机、移动、蹲伏、上下段防御、跳跃落地、受击、浮空受击、倒地、起身、普攻、下段普攻、空中攻击、特殊技、必杀、胜利收势。普攻与特殊技各8张连接帧，其他状态主要是关键姿势，保持时长不是新增动画帧。入场动画尚未制作。

文件：三张源板为 basic-v1.png、attack-v1.png、connections-v1.png；实际生成提示词为 prompts.json。frames 是48张单帧，manifest.json 为动作与锚点，data 为矩形数据及其gzip副本。addon.js 将独立版本挂入父探针，不覆盖原版数据。

本地数据验证：verification.json 记录48张帧存在、16类动作共656次姿势取样、6组必杀距离/接触分支。池上限2049个矩形，不代表真机帧率；gzip副本不代表运行时已支持解压。

浏览器观察：正常比例入口和48张加载成功；待机、蹲伏、倒地画面已检查。必杀命中后逻辑帧100显示伤害30；防住收招帧58显示伤害0。沿用既有特效参考与判定模型，没有制作新的整套技能特效。

待验证：最终美术一致性、全部动作连续观感、正式战斗接入、GIA导入和手机性能。未改正式战斗、联网协议或GIA。此目录不应作为正式安装包。

重建流程（项目根目录）：先运行 work/audit-motion-production.py 并传入本目录，再运行 work/build-nahida-normal-manifest.py；使用既有Node运行 work/build-motion-production.mjs 并传入本目录，然后运行 work/publish-nahida-normal-probe.mjs 与 work/verify-nahida-normal.mjs。不要删除原图或原版。

# 第一批14位动作交付

2026-10-04。本批已完成动作候选与双端完整测试版接入，第二、三批不在本轮追加。

- kaeya：48状态槽，池峰值1923，来源 outputs/motion-group1/kaeya
- jean：48状态槽，池峰值1529，来源 outputs/motion-group1/jean
- klee：48状态槽，池峰值1164，来源 outputs/motion-group1/klee-approved-v3
- lisa：48状态槽，池峰值1757，来源 outputs/motion-group1/lisa
- ganyu：48状态槽，池峰值1774，来源 outputs/motion-group1/ganyu
- yanfei：48状态槽，池峰值1746，来源 outputs/motion-group1/yanfei
- xiao：48状态槽，池峰值1472，来源 outputs/motion-group1/xiao
- hutao：48状态槽，池峰值1575，来源 outputs/motion-group1/hutao
- lawachurl：48状态槽，池峰值2333，来源 outputs/motion-group1/lawachurl
- yaemiko：48状态槽，池峰值2260，来源 outputs/motion-group1/yaemiko
- kirara：48状态槽，池峰值2246，来源 outputs/motion-group1/kirara
- kamisatoayato：48状态槽，池峰值3349，来源 outputs/motion-group1/kamisatoayato
- aratakiitto：48状态槽，池峰值2259，来源 outputs/motion-group1/aratakiitto
- sangonomiyakokomi：48状态槽，池峰值2577，来源 outputs/motion-group1/sangonomiyakokomi

13位共624张独立姿势；丘丘王使用正确旧版12张，共636张独立源姿势、672状态槽。普攻/E各8帧，待机/走动/防御/跳跃/受击/倒地/起身/胜利等仍以关键姿势为主，不称全部流畅动画。角色帧不烘焙大型特效。

绮良良v5以烟绯修正版为画风基准，可莉采用用户指定正常比例母版，整体等比120%；绫人固定银色刀刃与深蓝刀柄的新母版；弃用版本保留。

探针：http://127.0.0.1:4196/outputs/motion-production/index.html 。只解码当前角色和演示对手，20个版本可选。

完整测试交付见 ../group1-full-test/GIA安装说明.md、节点安装说明.md。素材检查见asset-verification.json；完整流程见verification.json、additional-verification.json，手机比例见mobile-verification.json。以上为本地模拟器证据，手机加载耗时、官方导入及最终美术验收待用户测。探针Q命中演出模型不等于正式联网伤害结算已更换。

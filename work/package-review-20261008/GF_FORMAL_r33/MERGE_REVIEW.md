# r33 归档重合并审查

基线：GF_Online_Repair_3e508011db14.lua，归档原文件保存在 baseline，SHA-256 为 b6623a610eb1596bf71ba6d7dba8c30e24492ee560138da6fea8b8b39c4be464。

没有在未发布的 r32 错误逻辑上回滚。以原始 dual-pool 为共同祖先，逐模块比较确认归档与 r18–r31 后续开发代码，再三方合并。merged.lua 记录自动合并结果，resolved.lua 记录冲突处理及正式版调整；build.py 生成交付源码。素材参考后续开发的数据文件，原两位角色、公共场景和徽标素材已核对与确认归档一致；仅后续动作与特效使用新增素材。

| 修改范围 | 决定 | 合入位置 |
| --- | --- | --- |
| 小原生字号、足够文本框高度、复用可见性、VS 加宽 | 保留确认归档实现 | gf_gfx、gf_scene_vs |
| 根容器适配画布、永久底色 | 保留确认归档实现 | bootstrap、gf_app |
| GFV2 转发协议、F9 联机诊断、场景切换期间网络泵 | 保留确认归档；仅合入必要兼容变化 | gf_transport、gf_scene_online、gf_online、gf_app |
| 换回合不叠字、清理旧技能特写 | 合入，公告只占一个槽并清除旧队列 | gf_scene_fight |
| 雷神命中后多段大招、分刀冲击、雷眼、投技演出 | 合入后续修复 | gf_sim、gf_fview、gf_scene_fight、gf_raiden_eye_r31 |
| 草神漂浮、像素瞄准框前冲、神殿多段演出、兰那罗抓取投掷 | 合入已开发版本；删除重复背景 | gf_fview、gf_sim、gf_viewfinder_data、gf_aranara_data |
| 雷神三段 2/35/70，草神三段 2/28/54 | 合入确认命中后的续段判定；保留起手防御和落空 | gf_sim |
| 双方动作补帧 | 合入原关键帧及补帧，不改打击时间 | gf_animation_data、gf_inbetween_data、gf_fview |
| 草前景小幅根部摆动 | 合入，取消整片绕中心旋转 | gf_stage |
| E/I、Q/O、L 投、方向出招 | 合入；同步出招表 | gf_input、gf_scene_howto |
| 只开放两角色、隐藏收集入口、完整单人/联机/再来 | 合入；默认开场而非双 AI | gf_roster、各场景 |
| 高清包与画质切换 | 不合入；物理删除全部高清层和未开放角色素材 | gf_art_sd、gf_art、gf_app、gf_scene_options |
| 动态图元池 | 合入；默认 14000，极端上限 20000，预警创建，战斗不销毁，结束阶段回收 | gf_gfx、gf_app、gf_scene_fight |
| 拟合后轮廓和内部色块优化 | 按 ART_STANDARD.md 执行全部 304 帧；雷神保持内部色，草神加深内部色 | 标清动作数据 |
| 伤害数字 | 延长爆发数字显示；使用原生 20 字号加视觉缩放，防止大字号文本框问题 | gf_fx、gf_scene_fight |
| 性能探针 | F9 开启后采样回调间隔、UI 写入估计与池状态；关闭时不采样 | gf_app、gf_gfx |

四个冲突模块已人工指定处理：gf_gfx 保留文字和复用修复、采用后续动态池；gf_app 保留场景加载时网络与垃圾处理、接入动态池；gf_scene_fight 采用单公告槽并清除旧待播公告；gf_scene_online 完整保留确认归档。

测试使用真实打包 Lua 的模拟器 Worker。三段大招、对墙/两侧/高连段/防御/无敌/落空/提前 KO、完整流程、公告、投技 AI 和动态池均有对应测试。文字验证覆盖原生字号/行框/可见性配置与伤害数字保持时间，模拟器不能代替官方客户端实测。浏览器保留联机入口和 GFV2 握手，但不宣称已完成两台真机联机验证。

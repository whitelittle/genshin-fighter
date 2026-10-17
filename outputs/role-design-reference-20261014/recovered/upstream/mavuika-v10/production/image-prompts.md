# Imagegen 提示词记录

工具：内置 imagegen。风格/身份参考：此前玛薇卡无眼镜待机候选与雷电、纳西妲V3基线重建图。

第一版：透明2×2四姿势身体图；成人体型、红橙发、黑红骑装，面部与头顶都无眼镜；右向侧视、空握点、身体独立。四姿势为准备、拧身蓄刀、向前下方强斩、低姿势余势收招。武器/车/刀光/太阳球/背景/文字/阴影不画入身体层。像素与矩形风格参照V3，实际拟合验收尚未完成。

第二版编辑：保持原四姿势、身份、成人比例、色彩、透明度；缩小并增加各方向透明边距，整个人物与头发、靴底留在各自格内，无跨格连接；不加武器、车、火焰、文字或背景。实际产出未满足严格等格，渲染按人工核对区域提取。


## 骑乘一体化版本
内置imagegen：身份参考无眼镜玛薇卡待机，车轮/车身参考本次官方视频暂停截图。透明2×2四帧，身体、大剑、驰轮车在每帧共同绘制；四动作分别骑乘准备、抬前轮蓄刀、落车强斩、制动倾斜侧滑铲击。成人比例、右向侧视、无眼镜，整剑与整车无裁切，无独立刀光/太阳球/背景。
修正版提示要求移除第一版不合要求的金棕背景与阴影，缩小四组素材、增加透明格间留白；第三帧长剑必须留在本格内，第四帧剑拖在车侧或后方，双手支撑制动侧滑。


## Version03 / built-in imagegen
Identity reference: dist/assets/mavuika-idle-original.png. Output: dist/assets/mavuika-phase-sheet-v3.png.
Prompt: transparent 1536x1024 side-view 2x2 full-body Mavuika action sheet, no glasses. Top left rider + black-red motorcycle accelerating diagonally upward, top right rider + motorcycle braking low; no sword in either. Bottom left airborne two-handed claymore windup, bottom right strong diagonal-down-right claymore followthrough; no vehicle in either. Coherent anatomy, complete wheel and blade tips, clear margins, no text/scenery/particles. Genuine alpha requested; generated alpha retained unchanged. Equal-grid request was imperfect, so source rectangles follow actual layout.


## Version04 / built-in imagegen

Reference edit attempted on v3 + idle identity reference. Requested actual transparent alpha, complete 2×2 side-view cutouts and no weapon/vehicle overlap. Retained as production/integrated-history/attempt-04-reference-edit.png; not adopted. Original display exposes RGB hidden under alpha0; composited QA corrected the earlier incorrect background claim.

New sheet: idle-only identity reference, genuine transparent alpha, 1536×1024 four right-facing poses: rising motorcycle/no sword; low braking motorcycle/no sword; airborne two-handed overhead claymore/no vehicle; diagonal downward claymore followthrough/no vehicle. Adult proportions, red-orange long hair, black-red-gold costume, no glasses. Complete wheels/boots/blades, no baked slash effects, no scene/text/grid. Equal-cell 80px margin was requested but actual output remains irregular; use explicit provisional ROIs. Saved dist/assets/mavuika-phase-sheet-v4.png.

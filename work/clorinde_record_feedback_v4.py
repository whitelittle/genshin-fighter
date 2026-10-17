from pathlib import Path
import json
r=Path.cwd();o=r/'outputs/clorinde-actions-20261011'
note='''

## 最新反馈修订 v4：大招背景与败北尺度

匿名玩家指出大招背景线条不符合预期、败北比例不对。已移除背景月环、水平线、折线与头像切入边线，改为柔和渐变与漫光；攻击自身分层特效保持独立。

败北四姿源单位由0.57统一调整至0.50，保留原图与支撑锚点，不做横纵异比变形、不按跪姿轮廓等高放大。第一姿自动区域诊断作辅助：躯干约95.19世界单位，母版约94.24；脸部区域跨度约15.54，母版约15.65。区域提案并非精确骨骼测量，最终观感仍需美术验收。

文件验证、矩形像素重建和Lua纯数据载入通过。独立浏览器检查源图/拟合各四姿、Q各演出阶段以及防御/空挥24tick短分支，未记录控制台错误；证据见`browser-feedback-v4.json`及`evidence/defeat-scale-v4.jpg`、`evidence/Q-soft-background-v4.jpg`。正式游戏、模拟器与真机未验收。

重建时在`clorinde_feedback_assets.py`之后、`clorinde_delivery_data.py`之前补运行`python work/clorinde_defeat_background_revision.py`；脚本可重复运行。最新源单位也已保存进反馈重建脚本。
'''
with (o/'本轮反馈修订与交付.md').open('a',encoding='utf-8') as f:f.write(note)
for p in [r/'AI_START.md',r/'docs/current/V4_执行与验收台账_20261009.md']:
 with p.open('a',encoding='utf-8') as f:f.write('\n> 2026-10-11 克洛琳德 v4补修：大招背景装饰线条移除，败北四姿按母版源单位0.50重拟合；源图/拟合播放及Q阶段/短分支检查通过，美术与正式游戏/模拟器/真机仍未验收。见`outputs/clorinde-actions-20261011/本轮反馈修订与交付.md`末尾最新记录。\n')
b=json.loads((o/'browser-feedback-v4.json').read_text(encoding='utf-8'));assert len(b['checks'])==16
assert all(s['ready'] for s in b['checks']);assert all(s['total']==48 for s in b['checks'][:8]);assert all(s['total']==24 and not s['fullStage'] for s in b['checks'][-2:])
print('16 focused browser state assertions passed')

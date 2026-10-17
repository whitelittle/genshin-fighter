from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013';Z=O/'zhongli'
note='''## 2026-10-14 钟离用户反馈修订

匿名玩家反馈地心位置错误、胜利看不出喝茶。本批仅修独立预览候选。

- 实现：岩脊原四等分裁切导致完整立柱顶部截断，固定格子底锚点导致各阶段悬空；按源图四处完整轮廓区域提取，统一实际底座落地，保留前方205显示单位与原14生成/19伤害设计/36回待机/94结束时序。E身体四姿同时校准实际支撑脚。
- 制作：内置 imagegen 重画六姿喝茶，明确白瓷杯、托碟、入口停留与放下；源板、精确提示词及历史素材保留。新拟合沿用钟离色板并补杯具浅色，10对象矩形目标重建精确。
- 浏览器：胜利六姿×三素材、E四姿×三素材、E镜像共31次检查；控制台错误0，白背景实际画面查看通过。初始/优化新素材暂同一拟合候选。31次检查不等于全部特效时间点或美术验收。
- 验收：用户美术待确认；正式战斗接入、确定性模拟器与真机未验证。25组145主状态数不变。旧GIF为历史预览，不包含本次修订。

证据：`zhongli/feedback-fix-20261014.json`、`zhongli/evidence/browser-feedback-checks-20261014.json`、`zhongli/evidence/v9-tea-20261014.jpg`。提示词：`zhongli/sources/victory-tea-v9-20261014.prompt.txt`。历史：`zhongli/history/feedback-20261014/`。

'''
for p in [R/'docs/current/V9_执行与验收台账_20261013.md',O/'本批记录.md']:
 s=p.read_text(encoding='utf8')
 if '## 2026-10-14 钟离用户反馈修订' not in s:p.write_text(note+s,encoding='utf8')
p=R/'AI_START.md';s=p.read_text(encoding='utf8');line='> 2026-10-14 V9钟离反馈修订：地心岩脊完整轮廓/落地锚点及E支撑脚已修候选，胜利重画六姿明确喝茶；31次浏览器检查与10对象拟合重建通过，用户美术/正式接入/真机待验。见[V9台账](docs/current/V9_执行与验收台账_20261013.md)。\n\n'
if not s.startswith('> 2026-10-14 V9钟离反馈修订'):p.write_text(line+s,encoding='utf8')
for name in ['offline.html','size-review.html']:
 p=Z/name;s=p.read_text(encoding='utf8').replace('下载全动作动图','历史动作动图').replace('>台账<','>本次修订<').replace('href="v9-basics-verification.json"','href="feedback-fix-20261014.json"');p.write_text(s,encoding='utf8')
p=O/'delivery.json';d=json.loads(p.read_text(encoding='utf8'));d['latestFeedbackFix']={'date':'2026-10-14','character':'zhongli','groups':25,'states':145,'browserObservations':31,'runtimeIntegrated':False,'artAccepted':False}
d['feedbackFixFiles']=[{'file':f.relative_to(O).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in Z.rglob('*') if f.is_file() and 'history' not in f.parts]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
print('Recorded V9 feedback revision')

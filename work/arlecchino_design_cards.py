from pathlib import Path
import json
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';d=json.loads((r/'work/v4-handoff-20261009-partial/V4/design/cards/arlecchino.json').read_text(encoding='utf-8'))
d['latestDecision']='2026-10-11: single-character production, normal adult proportions; Q unified hit-confirmed cinematic; forearm/shoulder throw';d['status']='design candidate, not battle implementation'
for g in d['groups']:
 k=g['actionId'].split('.')[-1]
 if k=='Q':
  g['visualPoses']=['短切确认','确认收势','头像切入','赤月蓄势','释放','持续冲击一','持续冲击二','持续冲击三','收束','恢复待机'];g['cinematic']={'total':162,'confirmationTick':6,'cutin':[12,42],'charge':[42,52],'releaseTick':52,'hitTicks':[70,94,118],'fade':[132,142],'recover':[142,162],'shortTotal':24,'fullRequires':'confirmed hit','damageDistribution':'待正式逻辑标定，总伤害不因显示保持帧增加'};g['branches']={'hit':'确认后完整演出与对手反应','block':'24tick短收势，不进入领域','whiff':'24tick短收势，不进入领域','interrupt':'按逻辑有效阶段取消尚未释放事件；待接入'};g['background']='柔和赤月色域，禁用装饰折线/横线；攻击特效独立'
 if k in ['throw','victim']:
  g['visualPoses']=['空手接近','前臂/肩接触','下沉压重','转髋前送','释放','收势/落地'];g['contact']='沿用对手现有PNG与尺度；成人/低位由本角色下沉姿势适配；禁止喉部抓握';g['clock']={'total':50,'grabTick':8,'releaseTick':32,'status':'candidate timing only'}
 if k in ['hit_knockdown','wakeup','victim']:g['fallDirection']='头左脚右；世界整体镜像；落地/起身共享边界姿势'
 g['runtimeIntegrated']=False
(o/'动作设计卡.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print('25 action design cards saved:',len(d['groups']))

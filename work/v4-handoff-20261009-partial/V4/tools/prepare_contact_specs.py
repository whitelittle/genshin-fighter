from pathlib import Path
import json
V=Path(__file__).resolve().parents[1]
rules={
'furina':('无武器；E三伙伴独立','两手指挥，不握助手；伙伴固定前方三个不重叠槽位','指令释放时三者协同，同一个hitId','受击前取消；释放后定向，不追踪'),
'zhongli':('E空手；柱/盾独立','前掌落地提示；柱的worldGround不跟手；盾跟bodyRoot','柱生成冲击一次，后续无持续伤害','一柱上限；未生成取消，生成后限时保留'),
'mavuika':('身体/摩托/轮火独立，所有帧无眼镜','leftGrip/rightGrip同车把；seat与骨盆对齐；起乘才切airPivot','车前缘连续扫掠一次，轮火零伤害','墙边制动；仍可受击；旧眼镜版不纳入验收'),
'venti':('E空手，风域独立','双掌上托引导；风域固定地面不跟手','上托姿势释放一次；格序0,1,3,2','落地回待机；风域不续伤'),
'kamisatoayaka':('身体/刀/鞘/冰华独立','左掌稳鞘口；右拳握柄；刀背方向及长度固定；归鞘不能穿掌','第三姿冰华一次；引导刀无第二伤害','下沉起手可打断；冰华不追踪'),
'tartaglia':('身体/左右水刃/水迹独立','leftGrip/rightGrip分别唯一水刃；交叉手不能多一把刃','交叉斩两刃共享一次hitId；快移扫掠','错步拉回；落空不反向追踪'),
'aratakiitto':('身体/阿丑/尘岩独立','双手托点匹配牛腹；松手后牛解绑按固定弧线；不复制第二只','牛接触一次；落场不再反复结算','未松手受击取消；松手后按定轨结束'),
'yaemiko':('身体/樱/雷独立','指尖布点；樱worldRoot不跟身体','每次一樱；明确节拍雷击；上限三，替换最旧','布点前打断取消；已布点限时存在'),
'arlecchino':('身体/镰柄刃/火引导/标记独立','右掌握柄左掌支撑；镰刃不变长；只有两手','切斩一次并标记；引导火不叠伤','有限定向突袭；标记限时，受击仍保留至到期'),
'wanderer':('身体/起跃风/风掌独立','地面footRoot切空中pelvisPivot；显示Y不独自决定受击盒','起跃风冲一次；悬浮仅状态，非持续攻击','有限悬浮；受击落地取消，非全程无敌'),
'neuvillette':('身体/杖/瀑布独立','左掌全程持杖；右掌提示落点；杖底和脚底分别标记','固定前方瀑布一次；不用装饰水滴治疗','落点不追踪；持杖收掌可惩罚'),
'clorinde':('身体/短枪/剑/子弹独立','右掌枪口及扳机，左掌剑柄；两挂点分开；枪收起事件明确','子弹和刺各一个ID；刺快移扫掠','不自动穿背；打断前未发射事件取消'),
'navia':('身体/伞枪/霰弹独立','两手持柄；开合轴与枪口保持；后坐身体先接力','扇面一次ID；多颗视觉不多算','装填收伞空档；弹丸不自动追踪'),
'skirk':('身体/剑/空间斩独立；重攻晶枪另组','右掌剑柄；空掌为独立剑预留；刹停时刀尖不漂移','一闪切斩一次；快移扫掠；重攻枪不能偷换剑图','墙边截止；不整段无敌')}
rows=['# V4 代表招分层与接触说明','\n本项目改编候选。四个显示姿势不等于四个逻辑tick；tick、伤害、攻击盒、接触像素待拟合标定。未写成已实现或已验收。','\n| 角色 | 分层 | 接触与挂点 | 有效事件 | 中断与反制 |','|---|---|---|---|---|']
for key,r in rules.items():
 p=V/'design/cards'/f'{key}.json';d=json.loads(p.read_text())
 d['E_layer_contact_spec']={'status':'design_candidate_unmeasured','layers':r[0],'contact':r[1],'active_event':r[2],'interrupt':r[3],'ticks':None,'pixel_anchors':None,'hitboxes':None}
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 rows.append('| '+key+' | '+' | '.join(r)+' |')
(V/'docs/REPRESENTATIVE_CONTACTS.md').write_text('\n'.join(rows)+'\n')
refs={'kamisatoayaka':'https://genshin.hoyoverse.com/en/news/detail/14437','tartaglia':'https://www.youtube.com/watch?v=RfTgT81cVxE','arlecchino':'https://genshin.hoyoverse.com/en/news/detail/123430','skirk':'https://www.youtube.com/watch?v=8AV1utyVW_Q'}
for key,url in refs.items():
 p=V/'design/cards'/f'{key}-research.md';s=p.read_text();s+='\n2026-10-08 补充：已定位官方拾枝杂谈页面 '+url+'；网页检索仅确认来源，视频抓取受限，未逐帧观看，时间点仍待核对。\n';p.write_text(s)
(V/'evidence/E-source-review.json').write_text(json.dumps({'status':'visual_source_review_only','furina':{'order':[0,1,2,3],'issues':['画风/比例待与V3对照','独立伙伴未制作']},'zhongli':{'order':[0,1,2,3],'issues':['按地手势偏水平推掌，需动作语义更正']},'mavuika':{'order':[0,1,2,3],'blocked':['仍有眼镜，禁止合格派生','摩托接触未做']},'venti':{'order':[0,1,3,2],'reason':'右下为最高上托，左下为收臂，应在有效后播放','status':'顺序更正候选，待过渡与播放'}},ensure_ascii=False,indent=2)+'\n')
print('14 contact specs and 4 source reviews written')

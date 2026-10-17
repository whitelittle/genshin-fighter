from pathlib import Path
import json,hashlib
V=Path(__file__).resolve().parents[1]; R=V.parent
extra=[
('furina','舞台表演气质：自信指挥与被打断后的慌忙收势；不擅自编造剧情事实','礼帽燕尾、空手手势、三个稳定身份的沙龙伙伴','轻巧小步，脚跟轻提但待机双脚不漂；防御收臂护胸，不用剑格挡','海马长水线，身体双手托空位朝前；水线起点绑定海马口，不绑定掌','蟹短钳低打','蟹双钳横扫','空中章鱼向下拍','海马俯射短水束'),
('zhongli','沉稳克制，攻击与回防重心不急躁；岩系能力来自本地技能依据','琥珀岩纹、长枪、岩柱/陨石','长袍随迈步小幅滞后；双脚稳落，防御掌与前臂形成架势','长枪踏步贯刺，枪尖单段伤害','枪尾低点','杆身低扫','空中枪尖短刺','下压岩枪'),
('mavuika','强健果断的骑乘与挥剑气质；面部无遮挡','红橙长发、红黑骑装、大剑与炎轮摩托','大步前行，髋与肩自然交替；双手架防，禁止戴眼镜','大剑双手肩上蓄势下劈','低位剑柄顶击','大剑低扫','空中横斩','双手大剑下劈'),
('venti','轻盈灵巧的吟游表演气质；风与弓来自本地技能依据','羽饰绿帽、弓弦、上升气流','六相位轻快步态，披风有滞后；防御避脸不拿弓当盾','拉弓蓄力风箭，箭头单次命中','低位拨弦风刃','向地前方引风扫脚','空中短箭','下射风箭'),
('kamisatoayaka','端正礼仪与干净居合节奏，动作结束有归鞘','白发马尾、和服甲裙、刀鞘居合','步幅小且脚底稳定，裙甲不穿腿；站防刀鞘在胸前','低身蓄力拔刀横切后归鞘','蹲身短拔刀','低位居合横切','空中短侧斩','冰刀下切'),
('tartaglia','主动抢入、肩髋换向明确；双刃战斗姿态','橙发红围巾、水双刃、水长柄','前压步态，双手有平衡摆臂；回退不复制向前重心','双水刃蓄势交叉重斩','低位反手水刃','双刃剪切低扫','空中换手刃斩','双刃向下交叉'),
('aratakiitto','夸张自信且有重量的鬼族武斗气质','红角白发、强壮肩背、阿丑与鬼王棍','大步落地，角与白发稳定；防御双前臂护面','大剑肩上蓄势重砸；常态禁止鬼王棍替代','蹲身拳柄顶击','大剑扫脚','空中大剑短挥','大剑落砸'),
('yaemiko','优雅从容，袖摆与指印承担发力，不做莽撞拳斗','粉发狐耳、狐印、杀生樱','脚步轻稳，袖摆延迟；防御侧身收袖护胸','双手结狐印召短程狐灵咬；狐灵单层','低位指印狐灵','狐灵贴地扑咬','空中指印短雷','向下点指狐灵扑落'),
('arlecchino','威严精确、低幅准备与突然切入的对比','红黑眼、黑手礼服、红镰/赤月翼','长步稳进，黑手与衣摆独立读形；防御前臂斜架','长柄镰从后上方蓄势大弧钩斩','枪尾低点','镰刃贴地钩扫','空中镰短切','镰刃向下钩落'),
('wanderer','克制尖锐的手势与轻盈切位；不能常态漂浮代替步态','大圆帽、风掌、有限悬浮','正常六相位着地步态，圆帽不弹跳；防御单前掌收后肩','双掌蓄风前推，风刃单层','低位风掌','贴地扇形风刃','空中侧掌风切','向下踏风'),
('neuvillette','庄重审判式站姿与缓慢有力的掌部动作','白长发审判袍、仪式杖、直线水束','六相位持杖行走保持握点；杖尖不用作脚锚','收掌凝聚直线水束，水束前端限定范围','杖尾低点水珠','低位水压扫','空中掌压水珠','向下水压'),
('clorinde','冷静准确的枪剑切换，装填与剑收势可读','三角帽、手枪、单手剑','紧凑步幅与猎手低重心；防御剑架前，枪口避自身','短装填后枪射接剑突刺，两段明确','剑尖低刺','蹲身剑扫','空中手枪短射','空中剑下刺'),
('navia','优雅又有力度，开伞与后坐反应保持礼帽稳定','金发礼帽、伞枪、金花礼炮','伞收拢随身，小步自然；防御开伞只挡姿态不无敌','开伞蓄势顶推，伞面边界单段','闭伞低刺','伞柄低扫','空中闭伞短刺','伞面向下顶压'),
('skirk','冷静利落，窄步剑术，虚空外观不等于伤害元素','浅长发异域装、冰剑、短距空间切位','窄步着地，长发尾随；防御侧身剑位明确','低身错步一闪重斩；光影不额外伤害','低位短剑点刺','逆手低切','空中窄弧剑斩','下刺后落地收剑')]
queue=json.load(open(V/'design/ROSTER_JOBS.json'));basis={j['character']:j for j in queue['jobs']};full=[]
for key,temper,symbols,stance,heavy,cl,ch,al,ah in extra:
 old=(V/f'design/cards/{key}.md').read_text(); title=old.splitlines()[0];job=basis[key];cache=json.load(open(R/job['source_basis'])); norms=old.split('普通攻击三段：')[1].split('。')[0].split('；');core={x:old.split(x+'：')[1].split('。')[0] for x in ['E','Q','投技']}
 acts={
 'idle':['双脚保持基准，呼气肩臂微降','吸气肩臂微升；不是走路补帧'],
 'walk':['接触：前脚跟落下后脚尖支撑','下降：膝弯重心落','经过：后脚经过支撑脚','上升：脚踝推送','另一脚接触','另一脚经过并回到循环'],
 'backwalk':['前掌先承重、后脚探落','膝弯稳身','收前脚靠近支撑位','前掌推出后撤','另一脚探落','收脚恢复；不是正走随意倒放'],
 'jump':['屈膝起跳','蹬地上升','空中顶点收腿','下降准备','屈膝落地回稳'],
 'forwarddash':['前倾蓄脚','后脚推地','身体前移','前脚落地刹停'], 'backdash':['后倾收臂','前脚蹬地','短后撤','后脚落地刹停'],
 'crouch':['屈膝下沉','低姿稳住，头颈不缩入胸腔'],
 'standguard':['抬臂进入角色专属防姿','防姿保持','后脚受力吸收冲击','回待机'],
 'crouchguard':['下沉抬臂','低姿防护','后膝吸收冲击','回蹲下'],
 'light1':[norms[0] if len(norms)>0 else '待补'], 'light2':[norms[1] if len(norms)>1 else '待补'], 'light3':[norms[2] if len(norms)>2 else '待补'],
 'heavy':[heavy], 'crouchlight':[cl], 'crouchheavy':[ch], 'airlight':[al], 'airheavy':[ah],
 'E':[job['prompt'].split('Chronological poses: ')[1].split('. Keep')[0]], 'Q':[core['Q'],'短前置攻击命中确认','确认后双方锁位并进入完整演出','落空/防御短收招，不锁对手'],
 'throw':['前臂探出抓取','抓取成立双方接触点锁位',core['投技'],'释放并回稳'],
 'victim':['抓取接触点被牵引','随施术者轨迹抬起或转体','释放进入抛出','触地受力','起身恢复'],
 'hit_knockdown':['躯干被击向后','空受击失衡','击倒倒下','落地停留'],
 'wakeup':['手肘支撑起身','单膝支撑','双脚承重回待机'], 'victory':['收招平复','角色符号明确的庆祝或谢幕','呼吸保持'], 'defeat':['支撑失力','跪落或倒下','结束停留不抽搐']}
 actioncards=[]
 for g in queue['groups']:
  seq=acts[g];isattack=g.startswith('light') or g in ['heavy','crouchlight','crouchheavy','airlight','airheavy','E','Q','throw'];
  source=seq[0]; hit='低' if g in ['crouchlight','crouchheavy'] else ('空中攻击属性待调' if g.startswith('air') else '中（候选）')
  c={'actionId':key+'.'+g,'status':'design_candidate_not_implemented','input':g+'输入；仅合法角色状态触发','condition':'待机/允许取消状态；被控不可触发','startup':'待调60Hz tick','active':'待调60Hz tick' if isattack else '无攻击有效段','recovery':'待调60Hz tick','damage':'待调' if isattack else 0,'hitstun':'待调' if isattack else 0,'knockback':'待拟合角色体型与墙边设定','attackLevel':hit if isattack else '无','attackBox':{'status':'待标定','space':'面向相对坐标，逻辑Y向上','bind':source if isattack else '无'},'hurtBox':'身体区域独立盒；不得用图片alpha自动生成','movement':'明确位移曲线待标定；高速攻击连续扫掠','cancel':'仅确认命中后允许的取消候选；落空/防御不得走命中分支','invulnerable':False,'hitIds':[key+'.'+g+'.0'] if isattack else [],'visualPoses':seq,'anchor':'站立脚底世界锚点；空中pivot独立；禁止逐帧裁切中心','branches':{'whiff':'收招可反击','block':'短分支；Q不完整演出','hit':'独立命中ID防重复；Q命中确认后演出','interrupt':'未释放事件取消；已释放层是否继续须下方角色规则定义'},'assistantEvents':'角色独立层，未实现','budget':'待测单人平均/峰值与双人并发；不得算已通过'}
  if g=='Q':c['hitIds']=['前置确认段','演出每段编号与tick待调'];c['lock']='仅前置有效命中成立；退出解锁双方；贴墙/体型差异待验证'
  if g=='throw':c['grab']={'distance':'待调','eligible':'地面可抓状态；不可抓/无敌/已有锁位排除','escape':'窗口tick待调','pairAnchor':'腕/腰/肩等实际接触点逐帧标定','victim':'必须有配对victim动作；墙边与不同体型待验证'}
  actioncards.append(c)
 (V/f'design/cards/{key}.json').write_text(json.dumps({'character':key,'status':'design_candidate','source':job['source_basis'],'source_sha256':job['source_sha256'],'identity_note':temper,'symbols':symbols,'stance':stance,'groups':actioncards},ensure_ascii=False,indent=2))
 text=old.split('完整25组覆盖')[0]+'\n人设动作解释（格斗改编解读）：'+temper+'。\n核心识别2—3项：'+symbols+'。\n基础姿态：'+stance+'。\n\n本地原作依据核对：\n\n'+ '\n'.join('- '+cache.get(f'combat{i}',{}).get('name','')+'：使用本地技能文字提炼；未声称已观看官方片段。' for i in range(1,4))+'\n\n专属25组动作方向（草案，尚未验证）\n\n|组|动作意图|\n|---|---|\n'+ '\n'.join('|'+g+'|'+' → '.join(acts[g])+'|' for g in queue['groups'])+'\n\n逐招完整字段见同名JSON：每招含输入、前置、起手/有效/收招、伤害、硬直、击退、盒、低中高、移动、取消、命中ID、助手事件、显示顺序、锚点及四分支。未知数值明确待调，字段存在不代表判定已实现。\n\n分层：身体不烘焙伤害特效；需要武器/道具的招式按握点独立挂层。所有助手有稳定实体身份，装饰无判定。原图→初始拟合→优化拟合需同高度并排，深浅背景、脚底线、动作语义与播放待逐项复核。\n\n状态：设计候选；母版/步态/代表招尚待完整复核；未接入逻辑、未模拟器、未真机、未用户验收。\n'
 if key=='mavuika':text+='\n硬约束：面部与头顶都不得有眼镜/墨镜。旧含眼镜候选保留为失败样本，不作为合格母版。\n'
 (V/f'design/cards/{key}.md').write_text(text);full.append(text)
print('Expanded14cards: exact25groups and350 action schemas with explicit pending fields')

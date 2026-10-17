from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]; V=R/'V4'; src=R.parent/'recovered-v4-originals/原神格斗'
rows=[
('furina','芙宁娜','精巧少女体型，蓝白礼帽与燕尾短礼服；舞台指挥者','中距离伙伴协作；指令有空档，贴身防守弱','空手；不用剑，伙伴单独层','海马定向水弹；章鱼近身拍击；蟹钳低扫','先侧身提腕，再张开两手邀请，右掌向前下达指令，最后双手回胸前；身体全程空手','三沙龙成员分段喷水','舞台谢幕三伙伴接力','牵腕转身引导对手入舞台，蟹横撞送出'),
('zhongli','钟离','高挑成年男性，沉稳长袍，琥珀瞳','长距离控场；柱子起手慢','长枪只在攻击出现','短枪探刺；旋杆横扫；岩枪下压','收掌蓄力，前掌向地按出，双臂展开稳住岩盾，再收掌站直','岩柱与短时护盾','抬首落星陨石','握腕封岩锁位，掌推岩震送出'),
('mavuika','玛薇卡','高挑成年女性，红黑骑装，长发，强健轮廓','冲入压制；高速动作收招大','大剑普通攻击；摩托只在专属招式','肩带横斩；旋身斜挑；踏步下劈','屈膝前探并召车，蹬地起乘，压低身体冲入，骑乘制动并保留车体；下车另设转换','炎轮骑乘突进，车独立层','腾跃骑乘落斩','抓肩转腰投出，火轮追撞'),
('venti','温迪','少年感纤细体型，绿帽羽饰，短披风','远程与上升气流；近战短','弓用于射击，其余空手','短距拨弦风刃；低位快箭；抬弓连射','一手收胸聚风，弯膝抬掌，上托双臂引升，落掌回待机','脚下上升风场','风暴箭形成吸引中心','引腕旋舞，风托后掷'),
('kamisatoayaka','神里绫华','少女体型，蓝白和服甲裙，白发高马尾','突进居合；爆发后有空档','佩刀与鞘分层保握点','短拔刀；鞘身推击转斩；收刀居合','左手稳鞘右手靠柄，屈膝蓄势，踏步拔刀向上引导，再归鞘恢复','冰华上挑','霜见雪关扉前推刀风','扣腕侧步背摔，冰花托起'),
('tartaglia','达达利亚','高挑成年男性，橙发灰红服，进攻姿态','贴身双刃连击；缺远距稳定压制','水双刃攻击显现，不强制常驻','双刃交叉；换手反斩；低步双刺','两手分开凝刃，压低踏步，交叉向前切入，错步拉回双手','水刃交叉突进','水长柄旋身终结','压腕过肩翻投接水刃封位'),
('aratakiitto','荒泷一斗','高大强壮成年男性，红角，白发，裸露上身','重压与近身；攻击慢','常态大剑；Q才用赤鬼棍','大剑平挥；肩撞接斩；抬刃砸地','双腿下沉双手托举空位，向前投掷，身体前倾送力，再叉腰回稳','阿丑投掷，牛独立层','鬼王棍连砸','双臂抱腰举高摔地'),
('yaemiko','八重神子','高挑成年女性，粉发狐耳祭服，优雅','布点陷阱；被贴身需位移','空手狐印，法器按需','食指狐印；袖摆掌拍；转腕狐灵咬','屈腕掩袖，轻踏侧移，向后点指留下樱位，再回身正立','杀生樱最多三个','天狐霆雷消耗樱位','狐印束腕引转，雷击弹出'),
('arlecchino','阿蕾奇诺','高挑成年女性，白黑短发，红黑礼服，威严','标记与镰刃范围；慢招可反制','长柄武器与镰刃状态分开','枪尾短击；斜向镰扫；前踏钩斩','收拢双臂，前脚低步疾进，单臂斜划布下血偿标记，再挺身收手','标记突袭斩','赤月羽翼展开终击','黑手扣喉转身按摔'),
('wanderer','流浪者','少年感纤细体型，大圆帽蓝白服','空中机动风刃；悬浮有限','空手风掌','前掌风刃；反掌切；转身双掌推','压低屈膝收掌，展开双臂起浮，单手向前压风，双脚落回待机','限时低空悬浮','聚风踏压多段','反手牵腕，旋风抛起后踢落'),
('neuvillette','那维莱特','高挑成年男性，白长发蓝黑审判官袍','直线水束；侧向与起手弱','仪式手杖保留步态，水流独立','杖尾点地水波；抬掌水珠；前掌水压','左手稳杖右手收掌，举掌对准前方，下压召瀑，扶杖收势','瀑布落点压制','初始水波与双落瀑','杖定脚旁，单手水牢托举送离'),
('clorinde','克洛琳德','高挑成年女性，紫黑猎装三角帽','枪剑交替；装填与突刺空档','手枪与剑各自层','枪托短击；直刺；枪射接剑斩','右手抬枪瞄准，左脚稳住侧身，扣扳机后转为持剑突刺，回撤收姿','枪击接迅捷突刺','剑枪残影截击','枪托顶肋接剑柄翻投'),
('navia','娜维娅','高挑成年女性，金发黑黄华服礼帽','近中距霰射；装填可惩罚','伞枪特色；大剑按专属招需要','闭伞突刺；伞柄横扫；开伞顶推','闭伞收向肩侧，双手向前瞄准，肩膀承受后坐，收伞恢复','伞枪霰射，伞枪独立层','金花礼炮支援','伞柄扣腕转身，伞面弹开送出'),
('skirk','丝柯克','高挑成年女性，浅色长发紫蓝异域装，冷静','剑术模式切换；连斩需投入','冰剑按出招召出，虚空仅视觉','窄步快切；逆手挑斩；转身贯刺','低身手靠剑位，错步瞬进，单手水平一闪，反向踏步收剑','七相一闪疾进切位','空间冰刃连续斩','制腕绕背，剑柄击背送落')]
groups='idle walk backwalk forwarddash backdash crouch standguard crouchguard jump light1 light2 light3 heavy crouchlight crouchheavy airlight airheavy E Q throw victim hit_airhit knockdown_wakeup victory defeat'.split()
queue=[]
for key,name,identity,role,weapon,normal,poses,E,Q,throw in rows:
 cache=R/f'assets/roster-v2/{key}-talents.json'; data=json.loads(cache.read_text()); names=[data.get(f'combat{i}',{}).get('name','') for i in range(1,4)]
 ref=next((str(p) for p in src.glob('*') if name in p.name and '待机' in p.name),'')
 prompt=f'''Use case: stylized-concept. Asset type: 2D fighting game E body animation source candidate. Character: {name} ({key}), {identity}. Reference 1 locks identity and costume; reference 2 locks the accepted Raiden fighting-sprite rendering style only, not Raiden proportions or outfit. Preserve this character's age and body proportions. Create exactly four readable full-body poses in a spacious 2x2 grid, all facing right, fixed orthographic side fighting view, stable scale, transparent background, no text. Chronological poses: {poses}. Keep every body and loose costume fully inside its cell, broad transparent gutters, consistent standing foot baseline within each row. Clean anime sprite color blocks, restrained highlights, dark colored outline, no chibi exaggeration. Body layer only: omit separate weapon, summoned assistant, projectile, water, lightning, flames, trails, stage or ground shadows. Fingers and contact grips must be anatomically readable. Show anticipation, action onset, active command or strike posture, recovery. Gameplay meaning is {E}; independent layers will be generated separately. No copied generic sword slash. Do not add weapons that this motion does not need.'''
 job={'id':key+'-E-body-v1','character':key,'group':'E','layer':'body','prompt':prompt,'reference':ref,'status':'queued','source_basis':str(cache.relative_to(R)),'source_sha256':hashlib.sha256(cache.read_bytes()).hexdigest()}; queue.append(job)
 card=f'# {name} V4设计卡（重建设计候选）\n\n旧说明未恢复，本卡不冒充原版。\n\n身份与体型：{identity}。\n定位与反制：{role}。\n武器必要性：{weapon}。\n\n本地技能依据：`{cache.relative_to(R)}`；技能名：'+ ' / '.join(names)+f'。内容用于招牌能力依据；没有虚构已观看的官方视频时间点。\n\n普通攻击三段：{normal}。\nE：{E}。身体逐姿：{poses}。\nQ：{Q}；首段命中确认才进入完整演出；落空和防御不锁对手。\n投技：{throw}；施术者与被投者配对，双方锁位与逃脱窗口另行标定。\n\n完整25组覆盖\n\n'+ '\n'.join(f'- `{g}`：待核对源图/制作；以身份、武器与专属核心动作约束，非已完成。' for g in groups)+'\n\n逻辑候选：E起手18 / 有效6 / 收招24个60Hz帧；只是设计起点，不等同原作数值或已接入。伤害、硬直、击退、攻击盒、取消表待拟合后逐招设定。所有事件固定帧与命中ID；不由图像轮廓决定判定。\n\n分层：身体、武器、助手、飞行物、场景效果独立。握持帧记录握点；投技记录双人相对锚点。\n\n状态：设计候选；没有模拟器、真机或用户验收。\n'
 (V/f'design/cards/{key}.md').write_text(card)
(V/'design/ROSTER_JOBS.json').write_text(json.dumps({'groups':groups,'jobs':queue,'policy':'跨角色E身体优先；原图母版步态不重复；后续按组轮转扩展'},ensure_ascii=False,indent=2))
(V/'README.md').write_text('# V4制作入口\n\n本轮重建说明与候选制作，V3 E客户端保持。先读AGENTS、PROGRESS、docs/CHARACTER_CREATION、docs/STYLE_LOCK、docs/ROSTER_PLAN、design/cards与design/ROSTER_JOBS.json。原49张恢复图与新增8张轻攻分开保留，旧图原始提示词未知。\n')
(V/'docs/STYLE_LOCK.md').write_text('# 画风与接入约束\n\n以已认可雷电/纳西妲为画风参考；各人保留年龄体型与服饰，不统一身高头身。身体、武器、助手、特效分层。固定脚底世界锚点，不逐帧裁切居中。premultiplied alpha BOX、重要像素加权OKLab与共享调色板；一像素深色轮廓。\n\n确定性回滚；60Hz起手有效收招；快招扫掠；多段独立命中ID。预分配池、双人并发预算、完整帧原子缓冲切换、失败保留上一完整帧。Q仅确认命中完整演出；投技双人配对。性能与真机必须实测，不从图元推断。\n')
(V/'docs/ROSTER_PLAN.md').write_text('# 原隐藏14人队列\n\n'+ '\n'.join(f'- {r[1]}：design/cards/{r[0]}.md' for r in rows)+'\n\n跨角色轮转候选，问题后期更正；不等待一人最终验收。母版与步态先复用已恢复源图；当前优先缺失E身体四关键姿，助手/武器另层。25组全覆盖目标与已生成状态严格分开。\n')
(V/'docs/FURINA_COMBAT.md').write_text('# 芙宁娜战斗方向\n\n重建候选。空手指挥，三成员分别为章鱼乌瑟勋爵、海马海薇玛夫人、蟹谢贝蕾妲小姐。普攻为伙伴接力，不用通用剑术。E三者协同喷水；Q舞台接力，必须首段命中确认。三伙伴不能烘焙进身体。\n')
(V/'docs/FURINA_ACTIONS.md').write_text('# 芙宁娜动作方向\n\n恢复双帧呼吸待机作为空手候选参考；旧idle-empty-v2文件名尚未可靠对应，不冒称已识别。E四姿：提腕、张臂邀请、右掌前指、收手。伙伴动作与水弹独立。投技牵腕入舞台配蟹撞，被投角色必须制作对应锁位与抛出。原有海马握持候选身份与接触关系待更正，保留不覆盖。\n')
(V/'PROGRESS.md').write_text('# V4实际进度\n\n已恢复49张旧源图，另有8张本轮轻攻候选；旧完整提示词与拟合数据未找到。已重建14张设计候选卡与25组覆盖索引、E身体跨角色队列。新旧候选均未正式验收。\n\n当前执行：E身体四关键姿；待生成结果再更新。旧49张来源见recovered-v4-originals/manifest.json。原提示词未知不补写冒充。\n\n未发生：新素材逻辑接入、模拟器、真机验收。V3客户端未修改。\n')
print('Created14cards,14Ejobs,25group coverage and missing V4 docs')

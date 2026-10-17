from pathlib import Path
import json,shutil,os,hashlib
R=Path(__file__).resolve().parents[1];B=R/'outputs/three-role-basic-20261013';O=R/'outputs/three-role-redesign-20261014';O.mkdir(exist_ok=True)
ids=['idle','walk','backwalk','jump','forwarddash','backdash','crouch','standguard','crouchguard','light1','light2','light3','heavy','crouchlight','crouchheavy','airlight','airheavy','E','Q','throw','victim','hit_knockdown','wakeup','victory','defeat']
labels=['待机','前走','后退','跳跃','前冲','后撤','蹲下','站防','蹲防','轻1','轻2','轻3','站重','蹲轻','蹲重','空轻','空重','E','Q','投技','被投','受击与倒地','起身','胜利','败北']
z=[
 '直立错步站稳→胸廓微呼吸→手指/衣尾低幅松紧→原位循环',
 '短步接触→脚底承重→另一脚低位经过→交替接触→交替承重→低位经过',
 '后脚探落→重心后移→前脚跟进→换脚探落→承重→收稳；目光始终向敌',
 '小幅屈膝→脚踝蹬地→收腿上升→顶点躯干稳直→伸腿下降→屈膝落稳',
 '短前移重心→后脚推地→紧凑滑步→前脚制动→直立归位；避免低头疾跑',
 '前脚预载→短蹬退→低幅短离地→后脚承重→前脚收稳；不大幅后仰',
 '膝髋同步屈曲→重心垂直下降→掌收近身→低姿稳住；保持头颈与躯干骨长',
 '立稳→侧身抬前掌→膝部小幅承压→收掌；肩颈舒展，不作拳击抱头',
 '低姿侧身→前掌护胸腹→后脚承压→回蹲姿；掌和肘保持近身',
 '持枪归位→腰部小幅转向→短直刺→原路收枪；躯干接近直立，肘不锁死',
 '接轻1收枪→短横拨前线→单次拨斩→枪尾回肋侧；不连转身体',
 '枪身回收→后脚短蹬→一记前斜下压枪→前脚制动→竖直收势；不用大跨步前扑',
 '枪横置腰侧→肩髋锁住蓄势→单次短步重刺→停住枪尖→缓慢收枪；力度来自脚底和腰背',
 '低姿持枪→枪尖低位短送→一记点刺→收回低姿；不把头压到双手之间',
 '低位预载→枪尖贴前地面横扫→重心留在双脚支撑范围→缓收回蹲；不做劈叉',
 '空中收枪贴身→单次前点刺→收枪→回下降；不空中转圈',
 '空中收枪→枪尖向前下定向→单次下刺→屈膝准备落地；身体不追加翻滚',
 '直立合掌→双掌向下定式→岩脊完整起立→手臂收回→原位待机；柱体独立存续',
 '直立短确认掌势→命中后交叠双臂/定式→陨星落下→短暂停留→放松回待机；本人不追陨星飞',
 '近身接腕→肩髋稳住→短牵引破坏对手支撑→一掌推出→原位收手；不夸张摔甩',
 '抓取反应→牵引失衡→受控释放→同向落地→倒地；受外力仍正常反应',
 '上身短受力→后脚补一步→失去支撑→侧身下落→肩背落地→同向倒地；重击可以击倒，不假装免硬直',
 '保持同向倒地→撑肘→掌撑地/收膝→单膝承重→起立→整衣收手',
 '端杯与托碟→举杯至唇→饮茶停留→放杯→平静持杯；沿已认可喝茶意图再审',
 '气息下沉→步态失稳→单膝支撑→掌撑膝→垂首保持；不反复摇头甩臂']
m=[
 '直立自然错步→呼吸微动→头发低幅跟随→循环',
 '近腿接触→近腿承重→远腿经过→远腿接触→远腿承重→近腿经过',
 '面向敌人后探脚→接地承重→前脚回收→交替后探→承重→回收',
 '预蹲→支撑腿蹬地→收膝上升→顶点展臂→伸腿下降→屈膝落地→回待机',
 '前倾预载→后脚强推→低位短冲→前脚制动→躯干抬起→回待机；发尾向后跟随',
 '前脚预载→向后蹬开→短离地→后脚落稳→收回前脚→回待机；不倒放前冲',
 '两脚承重→屈膝下沉→双手收近身→蹲伏保持',
 '前臂架起→侧身承压→脚底稳住→收回前臂',
 '从蹲伏架起前臂→护住低位→后脚/髋部承压→回蹲姿',
 '大剑后肩预备→腰髋转动→前斜切→收回武器→持剑归位；旧源提取边界重审',
 '接轻1回收→剑身绕身侧抬起→反向斜上切→收肘制动→持剑归位',
 '接轻2高位→前脚稳踏→剑身前压横斩→停住剑路→两手收回；不是跳跃大招',
 '双手蓄肩→后脚推/腰髋带剑→前下重斩→剑尖停在地面以上→收回持剑态',
 '低姿收剑→短低位横切→前脚稳住→回蹲姿持剑',
 '低位蓄剑→身体短前进→贴前地面重扫→前脚制动→收剑回蹲；不让长剑穿自身腿',
 '继承跳跃root→空中侧身短斜切→收剑→接下降；不重置跳高',
 '空中双手聚势→向前下重斩→收膝→落地缓冲→持剑归位；剑尖不穿地',
 '本体抬手引车→明确上车过渡→骑乘起步→车铲前冲→制动→下车回本体；沿已确认车铲意图',
 '原位近距确认→命中后骑车斜上冲→下车切剑→一刀斩落→直接落回起手点→收刀站稳；落空/格挡原位短收招',
 '近距接臂→髋部转稳→肩侧破坏对手支撑→向前释放→脚底制动→回待机；双方握点同步',
 '被抓→肩髋受牵→释放空中→同向落地→倒地',
 '短站受击→补脚失衡→空受击→侧身下降→落地→同向倒地',
 '同向倒地→撑掌收膝→单膝稳住→推地起身→抬胸→回待机',
 '收剑→轻舒肩→自信短抬头/手势→回自然站；不烘焙火焰',
 '肩部下沉→脚步失稳→单膝落下→手撑腿→低头保持']
n=[
 '扶杖站稳→胸廓微动→眼/衣尾微动→同脚位循环',
 '前脚接触→承重→收腿经过→交替接触→交替承重→经过；杖轻提不过腿',
 '后脚探步→后移承重→前脚回收→交替探步→承重→收脚',
 '屈膝收杖→蹬地→上升收腿→顶点→下降伸腿→双脚落稳',
 '预备承重→后脚推地→低位行进→前脚制动→回扶杖站；已修邻姿混入',
 '前脚预载→短蹬退→空中收腿→后脚承重→回扶杖；发尾惯性必须返修',
 '扶杖贴身→屈膝下降→低位稳身→蹲姿保持；不缩头或缩胸',
 '扶杖→抬前掌→小型水幕承压→收掌；水幕独立',
 '低姿扶杖→抬掌護低位→承压→回收前臂→回蹲',
 '回腕→短送掌→短水波释放→收肘→回杖；不挥杖当剑',
 '托掌→上托聚珠→前送水珠→收臂→回杖',
 '回臂蓄势→脚底跟进→前掌压出宽水压→制动收臂→回杖',
 '扶杖聚势→举自由掌→单掌直线洪流→停束收掌→回杖；保留实际单掌版本',
 '低位扶杖→自由掌短送→低位短水压→收肘→回蹲',
 '低位蓄掌→前掌下压→贴地水浪展开→髋部制动→回收蹲姿；水浪独立',
 '继承跳跃root→单掌推出水珠→收臂→回下降；杖持握持续',
 '空中自由掌聚水→向前下压流→收臂/收膝→下降→落地缓冲；不额外悬停',
 '扶杖收掌→指向固定前方落点→下压召瀑→收掌→原位扶杖；落点预示/瀑布独立',
 '前波确认→命中后短立绘→扶杖庄重聚流→骇浪/双瀑→停束→回杖；落空/格挡短分支',
 '近距接臂→掌控水环托举→对手前移释放→收掌→原位扶杖；不为配对重画别人的身体',
 '被抓取→牵引失衡→释放→落地→同向倒地；持杖/掉杖用明确事件，不突然消失',
 '短站受力→后脚退稳失败→侧身空受击→下落→肩背落地→倒地；杖握持或独立落下必须有过渡',
 '同向倒地→撑肘/护杖→收膝→单膝承重→扶杖起立→回待机',
 '收掌→调整持杖→颔首停留→衣尾落定→平静站立',
 '扶杖呼吸沉重→失去支撑→单膝/杖支地→垂首保持；杖尖触地清晰']
roledata={'zhongli':('钟离',z),'mavuika':('玛薇卡（火神）',m),'neuvillette':('那维莱特（水龙）',n)};allcards=[];summary={}
connections={'idle':'原位待机循环','walk':'松开后回待机','backwalk':'松开后回待机','jump':'上升/顶点/下降 → 空攻或落地缓冲','forwarddash':'制动 → 待机','backdash':'后脚落稳 → 待机','crouch':'低姿保持；松开后起站','standguard':'收臂 → 站立待机','crouchguard':'收臂 → 蹲姿','light1':'按确认规则接轻2，或收回持武器/扶杖待机','light2':'按确认规则接轻3，或收回持武器/扶杖待机','light3':'制动 → 持武器/扶杖待机','heavy':'完整收招 → 持武器/扶杖待机','crouchlight':'回蹲姿','crouchheavy':'回蹲姿','airlight':'回下降 → 落地缓冲；不重启跳跃','airheavy':'回下降 → 落地恢复；不重启跳跃','E':'本体收招 → 待机；独立层按既定事件存续','Q':'完整命中/格挡/落空各自收招 → 待机','throw':'释放对手 → 本体收手；对手落地/倒地另接','victim':'同向倒地 → 起身链','hit_knockdown':'同向倒地 → 起身','wakeup':'稳起 → 待机','victory':'胜利保持 → 回合结算','defeat':'败北保持 → 回合结算'}
for role,(title,specs) in roledata.items():
 bank=json.loads((B/role/'actions.json').read_text(encoding='utf8'))
 present=set(ids) if role=='zhongli' else set(bank)
 cards=[]
 for key,label,spec in zip(ids,labels,specs):
  phases=spec.split('→');status='旧候选存在，按新沉稳设计重审/重画' if role=='zhongli' else ('已有主预览候选，仍待美术' if key in present else '主预览缺失，待制作')
  if role=='mavuika' and key in ['E','Q']:status+='；上游分层演出另存，完整身体/事件仍缺'
  if (role,key) in [('zhongli','standguard'),('zhongli','light1'),('mavuika','heavy'),('neuvillette','E')]:status+='；本批新身体方向小样，不等同完整动作'
  card={'role':role,'actionId':key,'label':label,'phases':phases,'status':status,'existingMainPreview':key in present,'designRevision':'20261014-user-redesign','visualDesignOnly':True,'artAccepted':False,'runtimeIntegrated':False,'minimumUniqueKeyPoses':6 if key in ['walk','backwalk','jump','hit_knockdown','wakeup','throw','victim'] else 4,'continuation':{'jump':'airlight/airheavy or landing','crouchlight':'crouch','crouchheavy':'crouch','crouchguard':'crouch','hit_knockdown':'wakeup','wakeup':'idle','light1':'light2 on confirmed rule, else armed ready','light2':'light3 on confirmed rule, else armed ready'}.get(key,'idle or appropriate armed ready'),'layering':'身体/持握武器保持握点；独立特效/车体/水束/柱体/立绘分别记录','ruleChange':'未改伤害、无敌、取消、硬直或正式演出时序'}
  card['continuation']=connections[key]
  cards.append(card);allcards.append(card)
 (O/f'{role}-design-v2.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf8')
 summary[role]={'name':title,'designCards':25,'existingMainPreviewGroups':len(present),'missingMainPreview':[key for key in ids if key not in present],'redesignAll':role=='zhongli'}
(O/'coverage.json').write_text(json.dumps({'scope':'complete design cards, incomplete production','roles':summary,'cards':75,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf8')
for p in json.loads((R/'work/three_role_redesign_assets_20261014.json').read_text(encoding='utf8')):
 D=O/p['role'];(D/'sources').mkdir(parents=True,exist_ok=True);(D/'prompts').mkdir(exist_ok=True)
 shutil.copy2(os.path.expandvars(p['generatedPath']),D/'sources'/f'{p["key"]}.png')
 (D/'prompts'/f'{p["key"]}.txt').write_text(p['prompt'],encoding='utf8')
 if p.get('firstPath'):
  (D/'history').mkdir(exist_ok=True);shutil.copy2(os.path.expandvars(p['firstPath']),D/'history'/f'{p["key"]}-rejected-lunge.png');(D/'prompts'/f'{p["key"]}-correction.txt').write_text(p['correctionPrompt'],encoding='utf8')
(O/'all-design-cards.json').write_text(json.dumps(allcards,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False))

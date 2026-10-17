"""Prepare and record actual cross-character work; no runtime or acceptance claims."""
from pathlib import Path
import hashlib,json,shutil,sys
from PIL import Image
V=Path(__file__).resolve().parents[1];R=V.parent
PLAN=V/'design/ACTION_QUEUE_20261009.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(d):PLAN.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
motions={
'furina':['双掌在腰前轻托空位，肩膀放松，准备迎接唯一乌瑟','前掌向右送出，后掌松开，身体小步让出伙伴通路','身体在后方停稳，一手朝右指挥乌瑟近身拍击，另一手收胸前','屈腕招回唯一乌瑟，双掌回到腰前接回空位'],
'zhongli':['两只闭合握柄手在右腰与胸前，稳住长枪预备横扫','前脚短进，腰肩带动双臂把杆身从后侧送到前侧','双臂分开维持杆轴，前臂朝右横扫达到有效姿，衣摆随转腰','屈肘收杆回腰侧，两脚重新承重，回到沉稳待机'],
'mavuika':['双手握柄空拳在左腰低位，屈膝蓄旋身斜挑','后脚推地，转腰把双握柄手送过身体前方','双臂沿斜上方向抬到右前方胸肩高度，重心落在前脚','收肘把握柄空拳带回侧腰，双脚稳住，不跳跃'],
'venti':['前手闭合握弓空位向右，后手在胸前准备捏弦','前手稳定，后手拉到近侧脸颊，肩背拉弦','后手指松弦，前手不退，身体保持右向弓射姿','后手回胸前，前臂放低一点恢复，不挥剑'],
'kamisatoayaka':['左掌稳住左腰鞘空位，右手闭合握柄收在身前','左肘把鞘柄空位向右短推，右肘收后准备转斩','腰肩小转，右握柄拳从左腰划到右前方，前脚小落步','右手收至腰鞘口，左手不换位，端正恢复'],
'tartaglia':['双握刃空拳分别靠左右腰，前膝轻屈','腰肩错转，后手先从内侧向右带出，前手撤到侧胸','换手反斩有效姿：前方握刃拳向右平伸，后拳在肋旁，双臂不交叉穿身','两肘收回腰侧，错步拉回重心，保持进攻待势'],
'aratakiitto':['屈膝低重心，双手闭合握大剑空位在右髋，左肩略向前','前脚短进，用肩部向右抢入，双握柄手留在身侧','肩撞后的接斩：转腰双臂向右平送，握柄手间距固定，身体有重量','后脚承重，收肘双拳回右髋，宽站姿回稳'],
'yaemiko':['收袖，一手掩在胸前，近侧手掌藏袖准备','近侧腕从袖中伸出，轻踏小步向右，另一手提住袖摆','近侧掌朝右短拍引狐灵，手指自然并拢，身体优雅微倾','手掌柔和收回袖口，肩胯回稳，脚仍着地'],
'arlecchino':['两只黑手闭合握长柄空位，前手在胸前，后手在低腰','前脚短踏，后腰转动，双握柄手共同带动横向镰扫','前臂朝右横展，后臂屈在肋边，前后握柄点保持同一长柄轴','收杆式收肘，躯干挺直，回到克制站姿'],
'wanderer':['近侧掌朝内收于胸前，另一手下垂，双脚着地','前脚小进，前腕旋转，肘从内侧向右展开','反掌切有效姿：前手手背带动向右短切，后手维持平衡','前手收回胸前，脚不漂浮，大帽不变形'],
'neuvillette':['左手闭合握杖空位稳在身体左侧，右掌收胸前','右掌缓缓举至右肩前，前脚微移但袍下双脚承重','右掌朝右上方托出水珠发射姿，左手仍稳杖，不双手做长水束','右掌自然放回胸前，重心回稳，左杖握点不漂'],
'clorinde':['近侧右手握枪空拳靠右腰，食指在枪柄空位外；左手在胸前','右臂平举向右瞄准，腕肘成直线，左脚稳住侧身','右手握枪拳小幅后坐抬起，肩膀吸收冲击，枪口逻辑仍朝右','右肘屈回腰侧，手指放松回安全握持，左手不多出剑'],
'navia':['双手握闭伞柄空位，前手在胸前，后手靠侧腰','前脚短步，腰肩转动把闭伞杆轴带到前方','双臂朝右横扫，握柄拳间距不变，帽与裙摆轻微跟随','收杆回肩侧，双脚稳住，伞不自动开合'],
'skirk':['右手逆握剑空位收在低腰，左手在身后维持平衡','前脚窄步错入，右腕自低位翻向右上','逆手挑斩有效姿：右前臂斜上伸出，肘不过度锁死，左手保持身后','右手收回低腰，后脚接住重心，冷静收势'],
}
def prepare():
 jobs=json.loads((V/'design/ROSTER_JOBS.json').read_text());entries=[]
 for j in jobs['jobs']:
  k=j['character'];card=json.loads((V/'design/cards'/f'{k}.json').read_text())
  for g in jobs['groups']:
   cg=next(x for x in card['groups'] if x['actionId']==f'{k}.{g}')
   existing=[]
   if g in ['idle','walk']:
    existing=[str(p.relative_to(R)) for p in sorted((V/'evidence'/f'{k}-{g}-review').glob('source-cell-*.png'))]
   if g=='E' and j.get('output') and (R/j['output']).exists():existing=[j['output']]
   if g=='light1':
    existing=[str(p.relative_to(R)) for p in (V/'assets').rglob(f'{k}-light1*.png') if 'wanderer-light1-body-v1' not in p.name]
   entries.append({'actionId':f'{k}.{g}','character':k,'group':g,'design':'candidate','existing_sources':existing,'source_status':'existing_candidate_requires_review' if existing else 'missing','fitting':'pending','runtime':False,'simulator':False,'device':False,'accepted':False,'required_layers':['body']+(['assistant','effect'] if k=='furina' and g in jobs['groups'][:12] else []),'design_card':str((V/'design/cards'/f'{k}.json').relative_to(R)),'visual_direction':cg['visualPoses']})
 specs=[]
 for j in jobs['jobs']:
  k=j['character'];card=json.loads((V/'design/cards'/f'{k}.json').read_text());poses=motions[k]
  reference=V/'evidence'/f'{k}-idle-review/source-cell-0.png'
  if k=='mavuika':reference=V/'assets/master-candidates/mavuika-idle-no-glasses-v2.png'
  prompt=f'''Use case: stylized-concept. Asset type: {k} LIGHT2 BODY-only four-pose source sheet for horizontal 2D fighting game. Image1 locks ONLY character face, identity, age, own proportions and costume; image2 locks ONLY accepted Raiden/Nahida crisp compact cel sprite style. Identity note: {card['identity_note']}. Do not copy the reference backdrop. Exactly FOUR distinct chronological full-body poses in ONE horizontal row, equal cells, generous transparent gutters, locked right-facing side combat view (slight face angle allowed, torso never turns front), same character scale and baseline. Project adaptation choreography: 1 {poses[0]}; 2 {poses[1]}; 3 {poses[2]}; 4 {poses[3]}. True transparent alpha everywhere outside character. BODY ONLY with empty hands shaped for the described grip or gesture. Physical weapons, assistants, projectile and FX are separate later layers: DO NOT draw them or bake glow/mist/halo into body. Clearly readable preparation/onset/active/recovery, no repeated idle, no rotated/rescaled duplicate poses. Whole hair/feet/hands/clothes inside each equal cell. Flat simple cel color blocks, restrained highlights, one thin dark outline, no detailed painted backdrop, shadow, grid, labels or text. Preserve costume and adult/young body category; no standardized big-head chibi. This sheet is candidate display poses, not gameplay ticks.''' 
  if k=='mavuika':prompt+=' HARD USER RULE: no glasses/sunglasses anywhere, face/head/hair/hands bare of eyewear. No motorcycle in this sword-normal body sheet.'
  path=V/'prompts/actions-20261009'/f'{k}-light2-body-v1.txt';path.parent.mkdir(exist_ok=True);path.write_text(prompt+'\n')
  specs.append({'id':f'{k}-light2-body-v1','character':k,'group':'light2','layer':'body','grid':[4,1],'prompt_file':str(path.relative_to(R)),'prompt':prompt,'refs':[str(reference),str(V/'evidence/v3-accepted-contact.png')],'status':'pending','issues':['独立武器/助手/特效尚待配套','真实挂点、判定及60Hz编排尚待标定']})
 save({'scope':'original_hidden_14_only','groups':jobs['groups'],'entries':entries,'generation_specs':specs,'generation_failures':[],'quota_exhausted':False,'completion_policy':'source/fitting/playback/logic/simulator/device/user acceptance tracked separately'})
 print('350 design/source coverage entries; 14 missing light2 body sources prepared')
def register(ident,source):
 d=json.loads(PLAN.read_text());s=next(x for x in d['generation_specs'] if x['id']==ident);out=V/'assets/action-candidates-20261009'/f'{ident}.png';out.parent.mkdir(exist_ok=True);shutil.copyfile(source,out);im=Image.open(out);im.load();s.update(status='source_candidate',output=str(out.relative_to(R)),sha256=sha(out),image_size=list(im.size),alpha_extrema=list(im.getchannel('A').getextrema()))
 for group in s.get('action_groups',[s['group']]):
  e=next(x for x in d['entries'] if x['actionId']==f"{s['character']}.{group}");e.update(source_status='new_candidate',new_source=s['output'],source_pose_indices=s.get('group_pose_indices',{}).get(group,list(range(s['grid'][0]*s['grid'][1]))))
 save(d);print(s['id'],s['image_size'],s['alpha_extrema'])
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='register':register(sys.argv[2],sys.argv[3])

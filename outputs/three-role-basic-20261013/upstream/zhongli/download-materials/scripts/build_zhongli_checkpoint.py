"""Evidence checkpoint: mother, existing sources, and production decisions."""
from pathlib import Path
import json,sys,hashlib,shutil,html
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/zhongli-design-20261011'
# Optional historic checkout. Restored evidence is the default portable source.
LEGACY=ROOT.parent/'v4-handoff-20261009/V4'
sys.path.insert(0,str(ROOT/'game/tools'))
import artlib
from build_zhongli_delivery import LABELS,fit

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def source_stats(p):
 im=Image.open(p).convert('RGBA');a=np.array(im)[:,:,3];yy,xx=np.where(a>=128); labels,n=ndimage.label(a>=64);sizes=np.bincount(labels.ravel())[1:]
 return {'file':str(p.relative_to(OUT)),'sha256':sha(p),'size':list(im.size),'transparentFraction':float((a==0).mean()),'opaqueBBox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'opaqueEdgePixels':[int((a[:,0]>=128).sum()),int((a[:,-1]>=128).sum()),int((a[0]>=128).sum()),int((a[-1]>=128).sum())],'substantialComponentsAtAlpha64':int((sizes>3000).sum()),'interpretation':'组件仅筛查背景粘连/相邻人物接触；不等于动作或比例验收'}

def main():
 current=OUT/'checkpoint.json'
 if current.exists() and json.loads(current.read_text()).get('latestBatch'):
  print('Historical checkpoint preserved; rebuild the resumed batch with build_zhongli_resume_review.py instead.');return
 review=OUT/'review';review.mkdir(exist_ok=True); (review/'legacy').mkdir(exist_ok=True)
 old={'idle':'evidence/zhongli-idle-review','walk':'evidence/zhongli-walk-review','light1':'assets/continuation-batch/zhongli-light1-candidate-v1.png','light2':'assets/action-candidates-20261009/zhongli-light2-body-v1.png','light3':'assets/action-candidates-20261009/zhongli-light3-body-v1.png','heavy':'assets/full-delivery-20261009/zhongli-heavy-body-full-v1.png','crouchlight':'assets/full-delivery-20261009/zhongli-crouchlight-body-full-v1.png','crouchheavy':'assets/full-delivery-20261009/zhongli-crouchheavy-body-full-v1.png','airlight':'assets/full-delivery-20261009/zhongli-airlight-body-full-v1.png','skillE':'assets/skill-candidates/zhongli-E-body-v1.png'}
 rows=[]
 for key,label in LABELS.items():
  partial=[]
  roster={'jump':['jump'],'crouch':['crouch'],'standguard':['guard'],'crouchguard':['crouchGuard'],'skillQ':['qCharge','qRelease'],'hit_knockdown':['hurt','airHurt','down'],'wakeup':['getup']}
  partial=roster.get(key,[])
  if key in old:
   path=LEGACY/old[key]
   if not path.exists():path=review/'legacy'/f'{key}.png'
   n=2 if key=='idle' else 6 if key=='walk' else 4
   decision='复用视觉基准；待机循环需修脚位/比例' if key=='idle' else '保留，修边缘/步态/尺度后复用' if key=='walk' else '保留空手施术，重新对齐岩脊释放' if key=='skillE' else '保留身体关键姿势，返修一体持械'
   reason='主体完整，右手近胸、左手垂下；第二姿脚位和轮廓不同' if key=='idle' else '第1姿右鞋触及格子右边缘；腿链与躯干需单独核对' if key=='walk' else '有四姿与独立岩脊；需确认掌势和释放tick' if key=='skillE' else '旧稿部分空手或仅枪杆；完整持枪、枪长与攻击路线待修'
   if path.is_file():
    if path.resolve()!=(review/'legacy'/f'{key}.png').resolve():shutil.copy(path,review/'legacy'/f'{key}.png')
   else:
    fs=sorted(path.glob('source-cell-*.png'));ims=[Image.open(f).convert('RGBA') for f in fs];cols=3 if key=='walk' else 2;w,h=ims[0].size;sheet=Image.new('RGBA',(cols*w,((n+cols-1)//cols)*h))
    for i,im in enumerate(ims):sheet.paste(im,(i%cols*w,i//cols*h))
    sheet.save(review/'legacy'/f'{key}.png')
   legacy={'status':'已有连续候选','count':n,'reference':old[key],'localFile':f'review/legacy/{key}.png','sha256':sha(review/'legacy'/f'{key}.png')}
  else:
   decision='补连续动作；优先利用旧单姿' if partial else '补缺；不使用普通步态代替该动作'
   reason=('旧roster仅有 '+','.join(partial)+' 单姿，不能算完整动作') if partial else '历史交接包未找到该动作的连续源图'
   legacy={'status':'仅有旧单姿' if partial else '缺连续源图','count':len(partial),'partialPoses':partial}
  source=OUT/f'sources/{key}.png';stats=source_stats(source);new='未通过；背景或相邻姿势粘连' if key not in ('idle','walk') and stats['substantialComponentsAtAlpha64']< (4 if key=='skillE' else 6) else '已生成/整理候选；仍待姿势、尺度、握点复核'
  if key in ('idle','walk','skillE'):new='整理旧源；不是新重画的通过版'
  rows.append({'id':key,'label':label,'legacy':legacy,'current':{'status':new,**stats},'decision':decision,'reason':reason,'accepted':False})
 mother=review/'mother.png';shutil.copy(OUT/'reuse/idle/source-cell-0.png',mother);shutil.copy(OUT/'reuse/idle/source-cell-1.png',review/'idle-second.png')
 im=Image.open(mother).convert('RGBA');second=Image.open(review/'idle-second.png').convert('RGBA');scale=330/(978-58);palette=artlib.build_palette([artlib.downscale(im,.10),artlib.downscale(second,.10)],20,seed=11)+[[40,29,27]]
 fitmeta=[]
 for optimized,name in [(False,'mother-initial.png'),(True,'mother-optimized.png')]:
  image,rects=fit(im,scale,palette,optimized);image.save(review/name);meta={'palette':palette,'width':image.width,'height':image.height,'rects':rects,'sourceSHA256':sha(mother),'fittedSHA256':sha(review/name),'scale':4,'anchor':[500*scale/4,978*scale/4],'rectangleCount':len(rects),'exactQuantizedReconstruction':True,'runtimeBudgetAccepted':False};write(review/(name+'.json'),meta);fitmeta.append(meta)
 anatomy={'coordinateSpace':'旧待机第1姿原格768×1024，人工估计，尚非用户认可标注','sourceFile':'review/mother.png','skull':[505,58],'chin':[523,172],'neck':[500,190],'pelvis':[515,452],'legs':{'left':{'hip':[470,447],'knee':[435,697],'ankle':[403,933]},'right':{'hip':[548,447],'knee':[552,704],'ankle':[545,918]}},'groundRoot':[500,978],'uniformScale':scale,'displayReference':'颅顶到脚底330舞台像素，发梢可超过该高度','rule':'倍率只登记母版；头、躯干、腿链独立比较，冲突返修源图，不折中平均'}
 write(review/'anatomy.json',anatomy)
 assets={k:sha(review/k) for k in ['mother.png','idle-second.png','mother-initial.png','mother-optimized.png','anatomy.json']}
 checkpoint={'character':'zhongli','sourceCommit':'1c21eb57ffb1b8d88b41cbb743c46a34864849df','mother':{'selection':'旧待机第1姿，作为视觉与解剖母版；不采用新画立绘替换','status':'母版候选已定位；轮廓/低清脸部待用户复核','stats':source_stats(mother),'anatomy':anatomy,'fittingCounts':{'initial':fitmeta[0]['rectangleCount'],'optimized':fitmeta[1]['rectangleCount']}},'oldContinuousGroups':sum(r['legacy']['status']=='已有连续候选' for r in rows),'groups':rows,'assets':assets,'verification':{'fileReferences':'checked','quantizedRectangleReconstruction':'checked','browser':'not run: control-browser skill unavailable','runtime':'not integrated','device':'not observed'},'productionState':'母版/库存/后续制作检查点；不是25组动作交付；最新恢复批次见batches/20261011-resume'}
 write(OUT/'checkpoint.json',checkpoint)
 tables=''.join('<tr><td>'+html.escape(r['label'])+'</td><td>'+html.escape(r['legacy']['status']+' · '+str(r['legacy']['count'])+'姿')+'</td><td>'+html.escape(r['decision'])+'</td><td>'+html.escape(r['reason'])+'</td></tr>' for r in rows)
 cards=''.join('<article><h2>'+html.escape(r['label'])+' · 历史源图</h2><p>'+html.escape(r['reason'])+'</p><div class="image"><img loading="lazy" src="'+r['legacy']['localFile']+'" alt="'+html.escape(r['label'])+'历史姿势"></div></article>' for r in rows if r['legacy']['status']=='已有连续候选')
 page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>钟离制作检查</title><style>body{font:16px/1.65 system-ui;margin:24px auto;padding:0 18px;background:#f4f6fa;color:#202a3e;max-width:1200px}button,a{font:inherit}button{padding:8px 14px;cursor:pointer}.image,.compare{background:#e6eaf1;padding:12px}.dark .image,.dark .compare{background:#222638}.dark{background:#141821;color:#e6eaf1}.dark article{background:#202635;border-color:#414b5e}img{max-width:100%;max-height:650px;object-fit:contain;display:block;margin:auto}article{background:white;padding:18px;margin:20px 0;border:1px solid #cbd1dc;border-radius:10px}h2{font-size:20px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd2db;text-align:left;padding:8px}.scroll{overflow:auto}.compare{display:flex;flex-wrap:wrap;gap:12px}.compare figure{margin:0;flex:1;min-width:250px}.compare canvas{width:100%;height:auto;display:block}.status{border-left:4px solid #b67b25;padding:12px 18px;background:#f5e7ca;color:#41321c}a{color:#3e66af}.dark a{color:#a5bfff}.small{font-size:14px;color:#657085}.dark .small{color:#b5bfd0}</style><body>
<h1>钟离 · 制作检查</h1><p class="status">母版、已有内容、后续制作检查点。历史库存检查；制作已恢复；已有候选不等于完整动作已交付。</p><p><a href="checkpoint.json">文件与哈希</a> · <a href="review/anatomy.json">母版尺度登记</a> · <a href="后续制作分析.md">后续制作分析</a></p><button id="bg">切换浅／深底</button>
<article><h2>母版定位 · 旧待机第1姿</h2><p>沿用旧稿的人物身份、发型、棕黑金长衣和空手待机。alpha≥128的主体未触及画布四边；不新增发光或脚下影子。第2姿的脚位和轮廓不同，不能直接宣布待机循环通过。</p><div class="compare"><figure><figcaption>母版源图</figcaption><canvas id="source" width="360" height="450"></canvas></figure><figure><figcaption>初始拟合</figcaption><canvas id="initial" width="360" height="450"></canvas></figure><figure><figcaption>优化拟合 · 一逻辑像素棕黑内侧轮廓</figcaption><canvas id="optimized" width="360" height="450"></canvas></figure></div><p class="small">三者共用世界尺度和根坐标；拟合是量化还原，不是原图无损。母版头、躯干和腿链已作人工坐标登记，尚需复核。轮廓规则不会沿每个矩形画边。</p></article>
<article><h2>母版另一待机姿 · 尚未作为通过帧</h2><div class="image"><img src="review/idle-second.png" alt="旧待机第二姿"></div><p>需把脚底固定到母版根，检查头长、颈到骨盆、髋膝踝链；若各段倍率冲突，应修源姿势，不能靠每帧等高或折中缩放掩盖。</p></article>
<article><h2>已有内容 · 25组逐项登记</h2><p>历史包中找到10组连续身体候选，其他动作有部分旧单姿或缺连续源图。岩脊与头像另计。刚生成的候选保留为工作材料，但背景粘连、裁切和持械仍有未通过项，不登记成完成。</p><div class="scroll"><table><thead><tr><th>动作</th><th>历史覆盖</th><th>处理</th><th>证据／原因</th></tr></thead><tbody>'''+tables+'''</tbody></table></div></article>
<article><h2>后续顺序</h2><ol><li>锁旧待机第1姿母版；修另一待机姿脚位与解剖尺度，完成深浅底低清检查。</li><li>复核前走，修右鞋格边；登记真实六相接地，不整体重画母版。</li><li>先修一组轻攻的手、枪杆、枪头为一体，检查准备／出手／有效／恢复、枪长和尺度，再扩其余持枪动作。</li><li>采用已有或已生成的防御、跳跃和受击候选逐组检查；只补缺姿和失败姿，倒地末姿与起身首姿共用。</li><li>E复用旧施术与岩脊；Q只在命中确认后天星演出；投技双人锁腕、掌推、落地配套。去除装饰闪光和地面阴影。</li><li>完整源图通过后统一色板、artlib拟合、动作网页与事件/锚点数据交付；游戏逻辑、模拟器与真机另列验收。</li></ol></article>'''+cards+'''
<script>document.getElementById('bg').onclick=()=>document.body.classList.toggle('dark');const files={source:'review/mother.png',initial:'review/mother-initial.png',optimized:'review/mother-optimized.png'};const scale='''+str(scale)+''';for(const [id,file]of Object.entries(files)){const im=new Image();im.onload=()=>{const c=document.getElementById(id).getContext('2d'),s=id==='source'?scale:4,anchor=id==='source'?[500,978]:[500*scale/4,978*scale/4];c.imageSmoothingEnabled=false;c.drawImage(im,180-anchor[0]*s,420-anchor[1]*s,im.width*s,im.height*s);c.strokeStyle='#8490a5';c.beginPath();c.moveTo(15,420);c.lineTo(345,420);c.stroke()};im.src=file}</script></body></html>'''
 (OUT/'制作检查.html').write_text(page,encoding='utf-8')
 text='''# 钟离后续制作分析

依据最新分支1c21eb5，以及用户提供的克洛琳德制作检查示例。示例结构用于展示证据，不继承克洛琳德的未验收结论。

母版采用V4旧待机第1姿作为视觉与解剖基准。它的主体完整，alpha>=128的身体没有触及原格四边。源图、初拟合与优化拟合按同一坐标尺度比较；使用仓库artlib，不添加装饰闪光、脚下影子或厚边。另一个旧待机姿脚位和轮廓有变化，完整循环尚未通过。

已核对10组历史连续身体候选：待机2、前走6、轻攻一/二/三、站重、蹲轻/重、空轻和E各4姿。完整候选不等于通过：前走第一姿右鞋碰到格边；部分攻击空手或只有杆，不能继续按旧版独立手持武器流程交付。旧roster其他单姿只能帮助补帧。

岩脊、E的旧独立效果和官方头像已存在。岩脊与头像优先复用；旧E碎光不是必需层，暂不添加。刚生成的新图和局部修复结果保留历史，不因文件已生成就自动采用。

后续按检查页的六步顺序完成。每组记录来源、源ROI、实际脚底或骨盆根、人工颅顶/下巴/颈骨盆/髋膝踝、统一倍率、共享色板、图元数、源/拟合哈希、tick与hitId。多段比例不一致时返修源图，不按包围盒等高、不使用非均匀缩放、不将头与躯干所需倍率平均。

Q先短命中确认，完整演出仅命中分支；落空和防御短恢复。天星一击与固定石化作为格斗改编候选。E单岩脊，生成一次命中，无自动持续伤害。投技空手抓腕与掌推，需要对手锁位、释放、落地和起身，不能只交施术者动画。

当前结论：完成母版定位、库存登记和后续分析；不是25组动作交付。当前浏览器画面未实测，未接正式战斗、模拟器或真机。用户已要求继续；最新恢复批次另存batches/20261011-resume，旧母版外部晕染问题已登记。
'''
 (OUT/'后续制作分析.md').write_text(text,encoding='utf-8')
 print(json.dumps({'oldContinuousGroups':checkpoint['oldContinuousGroups'],'groups':len(rows),'motherCounts':checkpoint['mother']['fittingCounts'],'motherOpaqueEdges':checkpoint['mother']['stats']['opaqueEdgePixels']},ensure_ascii=False))

if __name__=='__main__':main()

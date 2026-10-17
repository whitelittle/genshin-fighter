"""Archive this local candidate, sources, generated art, prompts and verification."""
from pathlib import Path
import json,hashlib,shutil,zipfile,argparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-complete-v9-20261015';ART=ROOT/'outputs/tutorial-complete-art-20261015'
def review():
 meta=json.loads((ART/'import.json').read_text(encoding='utf-8'));assert not meta['partial']
 labels={'crouchLight':'荧 · 蹲轻','crouchHeavy':'荧 · 蹲重','airLight':'荧 · 空轻','airHeavy':'荧 · 空重','skill':'荧 · 普通E','skillUp':'荧 · 上E','skillDown':'荧 · 下E','burst':'荧 · 大招','throwTech':'荧 · 投／受投／拆投姿势','lumineHurt':'荧 · 受击／倒地／起身姿势','lawThrown':'丘丘王 · 被投姿势','lawGrab':'丘丘王 · 抓投','aether':'空 · 专属支援'}
 entries=[]
 for role,data in meta['roles'].items():
  for group,times in data['groups'].items():entries.append({'role':role,'group':group,'prefix':'assist' if role=='aether' else group,'times':times,'label':labels[group]})
 html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>教学完整候选 · 新动作素材</title>
<style>body{max-width:1100px;margin:30px auto;padding:16px;background:#151c30;color:#eee;font:17px system-ui}a{color:#b9d9ff}button,select{font:inherit;padding:8px;margin:5px}canvas{width:100%;background:#29364f;image-rendering:pixelated}img{max-width:100%;background:repeating-conic-gradient(#30394c 0% 25%,#424c63 0% 50%) 0/24px 24px}table{border-collapse:collapse}td,th{border:1px solid #637597;padding:10px}</style>
<h1>教学新动作 · 可逐帧修改的候选</h1><p>内置 image_gen 生成，52张新姿势已接入游戏。投、受击组是状态姿势集合，预览轮播不代表实际投技时间线。美术与真机体验待验收。</p>
<select id="motion"></select><button id="toggle">暂停</button><button id="prev">上一姿</button><button id="next">下一姿</button><p id="info"></p><canvas id="stage" width="1000" height="620"></canvas>
<p><a href="prompts.json">首批提示词</a> · <a href="revised-prompts.json">下段／空中重生成提示词</a> · <a href="reaction-prompts.json">受击／抓投提示词</a> · <a href="import.json">切帧、锚点、预算与来源哈希</a></p>
<table><tr><th>角色身体</th><th>独立帧均值</th><th>峰值</th></tr><tr><td>荧 · 88帧</td><td>979.07</td><td>1529</td></tr><tr><td>丘丘王 · 16帧</td><td>983.19</td><td>1106</td></tr><tr><td>空支援 · 4帧</td><td>955.00</td><td>1051</td></tr></table><p>均值不是整场总图元或按播放时长加权值。早期低段/空中8姿拼图保留为布局不合格记录，未接入；本页显示重生成的独立动作组。原图仍有少数剑尖贴边及连续性问题，留待后续修订。</p>
<h2>生成原图</h2><img id="source"><script>
const meta=__META__,entries=__ENTRIES__;const select=document.getElementById('motion'),canvas=document.getElementById('stage');let frame=0,ticks=0,playing=true,images={};
for(let i=0;i<entries.length;i++){let o=document.createElement('option');o.value=i;o.textContent=entries[i].label;select.append(o);let e=entries[i];for(let j=0;j<4;j++){let key=e.role+'-'+e.prefix+'_'+j,im=new Image;im.src='fit/'+key+'.png';im.onload=draw;images[key]=im}}
function draw(){let e=entries[+select.value],m=meta.roles[e.role].newFrames[e.prefix+'_'+frame],im=images[e.role+'-'+e.prefix+'_'+frame],ctx=canvas.getContext('2d');ctx.clearRect(0,0,1000,620);ctx.strokeStyle='#7183a3';ctx.beginPath();ctx.moveTo(0,550);ctx.lineTo(1000,550);ctx.stroke();ctx.imageSmoothingEnabled=false;if(im&&im.complete)ctx.drawImage(im,500-m.anchor[0]*m.u,550-m.anchor[1]*m.u,m.w*m.u,m.h*m.u);document.getElementById('info').textContent=e.label+' · 姿势 '+(frame+1)+'/4 · '+e.times[frame]+'拍/60Hz · '+m.n+'图元';document.getElementById('source').src='source/'+e.group+'-v1.png'}
select.onchange=()=>{frame=0;ticks=0;draw()};document.getElementById('toggle').onclick=()=>{playing=!playing;document.getElementById('toggle').textContent=playing?'暂停':'播放'};function change(n){playing=false;document.getElementById('toggle').textContent='播放';frame=(frame+n+4)%4;draw()}document.getElementById('prev').onclick=()=>change(-1);document.getElementById('next').onclick=()=>change(1);setInterval(()=>{let e=entries[+select.value];if(playing&&++ticks>=e.times[frame]){ticks=0;frame=(frame+1)%4;draw()}},1000/60);draw();</script></html>'''
 (ART/'index.html').write_text(html.replace('__META__',json.dumps(meta,ensure_ascii=False)).replace('__ENTRIES__',json.dumps(entries,ensure_ascii=False)),encoding='utf-8')
 refs=ART/'references';refs.mkdir(exist_ok=True)
 for origin,dest in [('outputs/lumine-basic-20261015/source/master-v1.png','lumine-master-v1.png'),('assets/roster-v2/lawachurl-idle.png','lawachurl-idle-reference.png')]:shutil.copy2(ROOT/origin,refs/dest)
 (ART/'素材记录.md').write_text('# 教学素材候选\n\n原图全部使用内置 image_gen 生成。`source/low-v1.png` 与 `source/air-v1.png` 相邻姿势碰接，作为未采用历史保留；实际接入分别使用 crouchLight、crouchHeavy、airLight、airHeavy 四个独立组。\n\n`index.html` 可逐帧查看，三个 prompts 文件保存完整提示词，`import.json` 保存切帧、尺度、锚点、图元与来源哈希。原图、旧身体数据未覆盖；拟合只处理新帧并核验量化目标逐像素一致。丘丘王被投原图朝左，导入时镜像到统一朝右母版，游戏按面向再翻转。\n\n美术候选尚待精修：部分空重剑尖贴边，姿势之间的武器长度、握持、服装细节和抓投贴合可后续逐帧改。固定反应伤害与持续时间为格斗教学改编，不是原作完整精通、抗性、附着量或月反应系统。\n',encoding='utf-8')
def package():
 review();digest=hashlib.sha256((OUT/'genshin_fighter.lua').read_bytes()).hexdigest()
 evidence=OUT/'verification'
 for name,key in [('complete-rules.json','clientSha256'),('complete-art-checks.json','clientSha256'),('attack-checks.json','sha256'),('guard-checks.json','sha256'),('flow-passed.json','sha256'),('tutorial-passed.json','sha256')]+[(p.name,'clientSha256')for p in evidence.glob('complete-native-*.json')]:
  assert json.loads((evidence/name).read_text(encoding='utf-8'))[key]==digest,name+' stale evidence'
 assert json.loads((OUT/'logic.json').read_text(encoding='utf-8'))['clientSha256']==digest
 shutil.copytree(ART,OUT/'art',dirs_exist_ok=True)
 shutil.copy2(ROOT/'outputs/tutorial-windup-v7-20261015/rebuild_snapshot.py',OUT/'rebuild_snapshot.py')
 shutil.copy2(ROOT/'docs/current/完整教学课程与七元素反应_20261015.md',OUT/'交付说明.md')
 recipes=OUT/'recipes';recipes.mkdir(exist_ok=True)
 for name in ['build_lumine_training.py','merge_tutorial_v15.py','import_complete_teaching_art.py','package_complete_teaching.py','preview_tutorial_v15.py']:shutil.copy2(ROOT/'runtime/tools'/name,recipes/name)
 for name in ['teaching_complete.py','teaching_complete_rules.lua','teaching_complete_native.py','tutorial_v15_merge.py','lumine_courses.py','lumine_guard.py','lumine_attack.py']:shutil.copy2(ROOT/'runtime/tests'/name,recipes/name)
 history=evidence/'history-single-pointer-test'
 for p in evidence.glob('FAILED-*.png'):
  history.mkdir(exist_ok=True);shutil.move(str(p),str(history/p.name))
 if history.exists():(history/'说明.md').write_text('历史测试截图：触屏模拟最初把摇杆与技能按钮使用同一触点编号，导致方向未释放。已改为摇杆0号、按钮1号，最终四种设备情境全部通过；这些截图不是当前候选的未修复缺陷。\n',encoding='utf-8')
 manifest={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in OUT.rglob('*')if p.is_file() and p.name!='package-manifest.json'}
 (OUT/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 target=ROOT/'outputs/tutorial-complete-v9-20261015.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED)as z:
  for p in OUT.rglob('*'):
   if p.is_file():z.write(p,OUT.name+'/'+p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(target)as z:
  assert z.testzip()is None
  for name,sha in manifest.items():assert hashlib.sha256(z.read(OUT.name+'/'+name)).hexdigest()==sha,name
 print(json.dumps({'zip':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'files':len(manifest)+1,'sha256':digest,'verified':True}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--review-only',action='store_true');args=ap.parse_args();review()if args.review_only else package()

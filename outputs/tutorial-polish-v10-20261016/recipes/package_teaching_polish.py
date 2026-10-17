"""Save the two local teaching polish changes and the unchanged mother reference."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v10-20261016';ART=ROOT/'outputs/lumine-walk-fix-20261016'
def main():
 meta=json.loads((ART/'import.json').read_text(encoding='utf-8'))
 refs=ART/'references';refs.mkdir(exist_ok=True);shutil.copy2(ROOT/meta['canonicalMother'],refs/'mother-v1.png')
 html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>旅行者步态与母版对照</title><style>body{max-width:1100px;margin:25px auto;padding:16px;background:#192238;color:#eee;font:18px system-ui}a{color:#b8d9ff}img,canvas{max-width:100%;image-rendering:pixelated}button,select{font:inherit;padding:8px;margin:5px}canvas{background:#29354d}</style><h1>母版不变 · 旅行者行走候选</h1><p>前进、后退各8帧。初版大头候选未接入，采用单独头部比例修订后的素材。步态与头身比例仍可后续微调。</p><img src="mother-comparison.png"><select id="motion"><option value="walk">前进</option><option value="back">后退</option></select><button id="play">暂停</button><button id="next">下一帧</button><p id="info"></p><canvas id="stage" width="1000" height="460"></canvas><p><a href="references/mother-v1.png">原始持剑母版</a> · <a href="prompts.json">内置生图提示词与头部修订提示</a> · <a href="import.json">来源、锚点、图元与时长记录</a></p><p>荧全部92张身体帧均值967.28图元，峰值1529；新行走帧峰值982。均值不是整场总图元或真机帧率。旧76张非行走身体帧不变。</p><script>const data=__META__;let frame=0,tick=0,running=true,images={};for(const group of ['walk','back'])for(let i=0;i<8;i++){let im=new Image;im.src='fit/'+group+'_'+i+'.png';im.onload=draw;images[group+'_'+i]=im}function draw(){const key=motion.value+'_'+frame,m=data.newFrames[key],im=images[key],c=stage.getContext('2d');c.clearRect(0,0,1000,460);c.strokeStyle='#8b9cb8';c.beginPath();c.moveTo(0,400);c.lineTo(1000,400);c.stroke();c.imageSmoothingEnabled=false;if(im&&im.complete)c.drawImage(im,500-m.anchor[0]*4,400-m.anchor[1]*4,m.w*4,m.h*4);info.textContent=(frame+1)+'/8 · '+data.durations[motion.value][frame]+'拍/60Hz · '+m.n+'图元'}motion.onchange=()=>{frame=0;tick=0;draw()};play.onclick=()=>{running=!running;play.textContent=running?'暂停':'播放'};next.onclick=()=>{running=false;play.textContent='播放';frame=(frame+1)%8;draw()};setInterval(()=>{if(running&&++tick>=data.durations[motion.value][frame]){tick=0;frame=(frame+1)%8;draw()}},1000/60);draw();</script></html>'''
 (ART/'index.html').write_text(html.replace('__META__',json.dumps(meta,ensure_ascii=False)),encoding='utf-8')
 digest=hashlib.sha256((OUT/'genshin_fighter.lua').read_bytes()).hexdigest()
 for name,key in [('dialogue-checks.json','clientSha256'),('walk-checks.json','clientSha256'),('complete-rules.json','clientSha256'),('attack-checks.json','sha256'),('guard-checks.json','sha256'),('tutorial-passed.json','sha256'),('flow-passed.json','sha256')]+[(p.name,'clientSha256')for p in (OUT/'verification').glob('complete-native-*.json')]:assert json.loads((OUT/'verification'/name).read_text(encoding='utf-8'))[key]==digest,name
 assert json.loads((OUT/'logic.json').read_text(encoding='utf-8'))['clientSha256']==digest
 shutil.copytree(ART,OUT/'walking-art',dirs_exist_ok=True)
 shutil.copytree(ROOT/'outputs/tutorial-complete-art-20261015',OUT/'previous-teaching-art',dirs_exist_ok=True)
 shutil.copy2(ROOT/'outputs/tutorial-complete-v9-20261015/rebuild_snapshot.py',OUT/'rebuild_snapshot.py')
 shutil.copy2(ROOT/'docs/current/旅行者步态与派蒙收起_20261016.md',OUT/'交付说明.md')
 recipes=OUT/'recipes';recipes.mkdir(exist_ok=True)
 for name in ['build_lumine_training.py','merge_tutorial_v15.py','import_lumine_walk_fix.py','package_teaching_polish.py','preview_tutorial_v15.py']:shutil.copy2(ROOT/'runtime/tools'/name,recipes/name)
 for name in ['lumine_walk_fix.py','teaching_dialogue.py','teaching_complete.py','teaching_complete_rules.lua','teaching_complete_native.py','tutorial_v15_merge.py','lumine_guard.py','lumine_attack.py']:shutil.copy2(ROOT/'runtime/tests'/name,recipes/name)
 manifest={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in OUT.rglob('*')if p.is_file()and p.name!='package-manifest.json'}
 (OUT/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 target=ROOT/'outputs/tutorial-polish-v10-20261016.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED)as z:
  for p in OUT.rglob('*'):
   if p.is_file():z.write(p,OUT.name+'/'+p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(target)as z:
  assert z.testzip()is None
  for name,sha in manifest.items():assert hashlib.sha256(z.read(OUT.name+'/'+name)).hexdigest()==sha,name
 print(json.dumps({'zip':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'files':len(manifest)+1,'sha256':digest,'verified':True}))
if __name__=='__main__':main()

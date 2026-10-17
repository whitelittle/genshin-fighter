"""Replace four legacy attack groups at the approved master's fixed source scale."""
from pathlib import Path
import sys,json,hashlib,copy,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-jump-normal-v20-20261017'
OUT=ROOT/'outputs/tutorial-low-air-v21-20261017'
ART=ROOT/'outputs/lumine-low-air-20261017'
GROUPS=['airLight','airHeavy','crouchLight','crouchHeavy']
sys.path.insert(0,str(ROOT/'runtime/tools'))
import build_teaching_unified as U
from build_teaching_jump_crouch import board
from compact_assets import LuaRuntime,python_table
from export_furina import lua
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 (ART/'fit').mkdir(parents=True,exist_ok=True)
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 rt=LuaRuntime();rt.execute('__loaders={};'+(BASE/'source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']());old=copy.deepcopy(data)
 cal=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/report.json').read_text(encoding='utf-8'))
 contrast=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/fit/master-contrast.json').read_text(encoding='utf-8'))['palette']
 U.ART=ART;rows={}
 for g in GROUPS:
  for key in data['groups'][g]['frames']:
   p=ART/'source'/f'{key}.png';im=Image.open(p).convert('RGBA');assert im.size==(1024,1536),(key,im.size)
   bb=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
   # At least one clear source pixel on every edge; reject actual clipped blades.
   assert bb and bb[0]>0 and bb[1]>0 and bb[2]<im.width and bb[3]<im.height,(key,bb)
   root=[520,bb[3] if g.startswith('crouch') else 1435]
   data['frames'][key],rows[key]=U.fit(im,root,cal['sourceUnit'],key,cal,contrast)
   rows[key].update(source=f'source/{key}.png',sourceSha256=sha(p),sourceBounds=bb,grounded=g.startswith('crouch'),noPerPoseStretchOrHeadResize=True)
 assert all(data['frames'][k]==v for k,v in old['frames'].items()if k not in rows)
 assert data['groups']==old['groups'] and data['aliases']==old['aliases']
 data['bodyPeak']=max(v['n']for v in data['frames'].values());unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()};mean=sum(v['n']for v in unique.values())/len(unique);assert mean<1000
 p=OUT/'source/teaching/gf_lumine_training_data.lua';p.write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'));changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)];assert changed==['source/teaching/gf_lumine_training_data.lua'],changed
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8')for p in order),encoding='utf-8');(OUT/'verification').mkdir(exist_ok=True)
 manifest={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'sourceFiles':{p:sha(OUT/p)for p in order},'frames':rows,'bodyUniqueMean':mean,'bodyPeak':data['bodyPeak'],'renderingInputPaimonRulesAndOtherFramesUnchanged':True,'sourceScaleAuthority':'actual approved master; fixed sourceUnit; no generated standing calibration','artAcceptance':'pending user review'}
 for p in [OUT/'build-manifest.json',ART/'import.json']:p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 names=GROUPS+['idle','walk','back','dash','jump','crouch','light1','light2','light3','heavy']
 groups={g:data['groups'][g]for g in names};keys={k for g in groups.values()for k in g['frames']}
 (ART/'review-data.json').write_text(json.dumps({'frames':{k:data['frames'][k]for k in keys},'groups':groups},ensure_ascii=False),encoding='utf-8')
 for g in GROUPS:
  board(ART/f'{g}-runtime-review.png',['teaching_master']+groups[g]['frames'],data['frames'])
  for key in groups[g]['frames']:board(ART/f'{key}-before-after.png',['teaching_master','legacy-v20','new-v21'],{'teaching_master':data['frames']['teaching_master'],'legacy-v20':old['frames'][key],'new-v21':data['frames'][key]})
 html=(ROOT/'outputs/lumine-jump-normal-20261017/index.html').read_text(encoding='utf-8')
 start=html.index('<select');end=html.index('<p>留档：')
 controls=html[start:html.index('<section>',start)] if '<section>' in html[start:end] else html[start:end]
 # Keep the established player but rebuild review sections for this batch.
 script=html[html.index('<script>'):]
 script=script.replace("crouch:'下蹲与蹲防'","crouch:'下蹲与蹲防',airLight:'空轻',airHeavy:'空重',crouchLight:'蹲轻',crouchHeavy:'蹲重'")
 script=script.replace("['jump','crouch','dash','light1','light2','light3','heavy']",json.dumps(GROUPS))
 comparisons=''.join(f'<section><h2>{key} · 母版／旧稿／新稿</h2><img src="{key}-before-after.png"></section>'for key in rows)
 head=html[:html.index('<h1>')].replace('荧 · 跳蹲头身返修','荧 · 空攻与蹲攻返修')
 (ART/'index.html').write_text(head+'<h1>荧 · 空攻与蹲攻返修</h1><p>空轻、空重、蹲轻、蹲重16张独立源图按已选母版固定源单位拟合。其余帧与渲染、输入、派蒙贴底、规则均保持。新造型待验。</p>'+controls+comparisons+'<p>留档：<a href="prompts.json">提示词</a> · <a href="import.json">拟合与保留项</a></p>'+script,encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items()if k not in ['frames','sourceFiles']},ensure_ascii=False))
if __name__=='__main__':build()

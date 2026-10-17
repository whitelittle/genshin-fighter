"""Replace rejected big-head jump/crouch drawings using the actual approved master's fixed scale."""
from pathlib import Path
import sys,json,hashlib,copy,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-jump-v19-20261017'
OUT=ROOT/'outputs/tutorial-jump-normal-v20-20261017'
ART=ROOT/'outputs/lumine-jump-normal-20261017'
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
 for key in [*[f'jump_{i}'for i in range(6)],'crouch']:
  path=ART/'source'/f'{key}.png';im=Image.open(path).convert('RGBA')
  assert im.size==(1024,1536),(key,im.size)
  bb=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
  assert bb and bb[0]>1 and bb[1]>1 and bb[2]<im.width-1 and bb[3]<im.height-1,(key,bb)
  grounded=key in ('jump_0','jump_1','jump_5','crouch')
  # There is no newly generated standing calibration to enlarge a stylized model.
  # All drawings use the chosen master's actual 1024x1536 source units directly.
  root=[520,bb[3] if grounded else 1435]
  dest='cblock_0' if key=='crouch' else key
  data['frames'][dest],rows[dest]=U.fit(im,root,cal['sourceUnit'],dest,cal,contrast)
  rows[dest].update(source=f'source/{key}.png',sourceSha256=sha(path),sourceBounds=bb,grounded=grounded,sourceScaleAuthority='approved original master only; no regenerated calibration figure',noPerPoseStretchOrHeadResize=True)
 data['frames']['cblock_1']=copy.deepcopy(data['frames']['cblock_0'])
 changed=set(rows)|{'cblock_1'}
 assert all(data['frames'][k]==v for k,v in old['frames'].items()if k not in changed)
 assert data['groups']==old['groups'] and data['aliases']==old['aliases']
 data['bodyPeak']=max(v['n']for v in data['frames'].values());unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()};mean=sum(v['n']for v in unique.values())/len(unique)
 assert mean<1000,mean
 p=OUT/'source/teaching/gf_lumine_training_data.lua';p.write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'));changedFiles=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert changedFiles==['source/teaching/gf_lumine_training_data.lua'],changedFiles
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8')for p in order),encoding='utf-8');(OUT/'verification').mkdir(exist_ok=True)
 manifest={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changedFiles,'sourceFiles':{p:sha(OUT/p)for p in order},'frames':rows,'bodyUniqueMean':mean,'bodyPeak':data['bodyPeak'],'renderingInputAndPaimonByteUnchanged':True,'previousV19Art':'rejected as big-head by user; rendering confirmed correct'}
 (OUT/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(ART/'import.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 groups={g:data['groups'][g]for g in ['idle','walk','back','dash','jump','crouch','light1','light2','light3','heavy']};keys={k for g in groups.values()for k in g['frames']}
 (ART/'review-data.json').write_text(json.dumps({'frames':{k:data['frames'][k]for k in keys},'groups':groups},ensure_ascii=False),encoding='utf-8')
 for group in ['jump','crouch','dash','light1','light2','light3','heavy']:board(ART/f'{group}-runtime-review.png',['teaching_master']+groups[group]['frames'],data['frames'])
 for key in rows:board(ART/f'{key}-before-after.png',['teaching_master','rejected-v19','new-v20'],{'teaching_master':data['frames']['teaching_master'],'rejected-v19':old['frames'][key],'new-v20':data['frames'][key]})
 html=(ROOT/'outputs/lumine-jump-crouch-20261017/index.html').read_text(encoding='utf-8')
 html=html.replace('荧 · 跳跃、蹲下与派蒙贴底','荧 · 跳蹲头身返修')
 start=html.index('<p>');end=html.index('</p>',start)+4
 html=html[:start]+'<p>上一版跳蹲大头造型已退回；这次七张独立源图直接沿用已选原母版源单位，不再用新生成站姿重新定比例。渲染、输入、派蒙贴底等代码逐文件保持。新造型待验。</p>'+html[end:]
 start=html.index('<p>留档：');end=html.index('</p>',start)+4
 html=html[:start]+'<p>留档：<a href="prompts.json">七张源图提示词</a> · <a href="import.json">比例、拟合与保留项</a></p>'+html[end:]
 comparisons=''.join(f'<section><h2>{key} · 母版／已退回v19／本批返修</h2><img src="{key}-before-after.png"></section>'for key in rows)
 html=html.replace('<div id="boards"></div>',comparisons+'<div id="boards"></div>')
 (ART/'index.html').write_text(html,encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items()if k not in ['frames','sourceFiles']},ensure_ascii=False))

if __name__=='__main__':build()

"""Replace the actually used standing block body; preserve v22 input repair."""
from pathlib import Path
import sys,json,copy,shutil,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/tools'))
import build_teaching_unified as U
from build_teaching_jump_crouch import board
from compact_assets import LuaRuntime,python_table
from export_furina import lua
BASE=ROOT/'outputs/tutorial-air-input-v22-20261017'
OUT=ROOT/'outputs/tutorial-guard-v23-20261017'
ART=ROOT/'outputs/lumine-guard-20261017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 (OUT/'verification').mkdir(exist_ok=True);(ART/'fit').mkdir(exist_ok=True)
 rt=LuaRuntime();rt.execute('__loaders={};'+(BASE/'source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']());old=copy.deepcopy(data)
 cal=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/report.json').read_text(encoding='utf-8'))
 pal=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/fit/master-contrast.json').read_text(encoding='utf-8'))['palette']
 p=ART/'source/block_1.png';im=Image.open(p).convert('RGBA');assert im.size==(1024,1536)
 bb=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
 assert bb and bb[0]>0 and bb[1]>0 and bb[2]<im.width and bb[3]<im.height
 U.ART=ART
 data['frames']['block_1'],info=U.fit(im,[520,bb[3]],cal['sourceUnit'],'block_1',cal,pal)
 assert all(data['frames'][k]==v for k,v in old['frames'].items() if k!='block_1')
 assert data['groups']==old['groups'] and data['aliases']==old['aliases']
 unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()}
 mean=sum(v['n'] for v in unique.values())/len(unique);assert mean<1000
 data['bodyPeak']=max(v['n'] for v in data['frames'].values())
 (OUT/'source/teaching/gf_lumine_training_data.lua').write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert changed==['source/teaching/gf_lumine_training_data.lua']
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8') for p in order),encoding='utf-8')
 result={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'changedFrames':['block_1'],'sourceSha256':sha(p),'sourceBounds':bb,'fit':info,'bodyUniqueMean':mean,'bodyPeak':data['bodyPeak'],'newRectangles':data['frames']['block_1']['n'],'allOtherFramesAndSourcesUnchanged':True,'artAcceptance':'pending','scope':'actual standing block pose only; unused block_0/2/3 remain historical'}
 for p in [OUT/'build-manifest.json',ART/'import.json']:p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 board(ART/'before-after.png',['master','old','new'],{'master':data['frames']['teaching_master'],'old':old['frames']['block_1'],'new':data['frames']['block_1']})
 (ART/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>荧站防返修</title><style>body{background:#263454;color:white;font:18px sans-serif}img{max-width:100%;image-rendering:pixelated}</style><h1>荧站防返修</h1><p>相同世界尺度：母版／旧站防／新站防。只替换实际使用的 block_1，造型待验。</p><img src="before-after.png"><p><a href="source/block_1.png">源图</a> · <a href="prompts.json">提示词</a> · <a href="import.json">拟合记录</a></p>',encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':build()

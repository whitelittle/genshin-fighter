from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,numpy as np
import clorinde_assets as ca
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';ca.O=o
palette=[[255,241,213],[255,189,91],[255,110,49],[240,48,37],[184,19,37],[123,10,29],[65,5,18],[28,4,12]]
recipes={}
for key,size in [('guide',32),('impact',32),('mark',24),('release',48)]:
 im=Image.new('RGBA',(size,size));d=ImageDraw.Draw(im);c=size/2
 if key=='mark':
  d.polygon([(c,1),(c+5,c-5),(size-2,c),(c+5,c+5),(c,size-2),(c-5,c+5),(2,c),(c-5,c-5)],fill=(220,28,44,255));d.polygon([(c,6),(c+3,c),(c,size-7),(c-3,c)],fill=(255,198,128,255))
 elif key=='impact':
  d.polygon([(c,0),(c+3,c-4),(size-1,c),(c+4,c+3),(c,size-1),(c-3,c+4),(0,c),(c-4,c-3)],fill=(244,63,42,255));d.ellipse((c-4,c-4,c+4,c+4),fill=(255,237,199,255))
 else:
  for radius,alpha in [(size*.43,35),(size*.3,90),(size*.2,170),(size*.1,255)]:d.ellipse((c-radius,c-radius,c+radius,c+radius),fill=(255,int(50+alpha*.55),int(35+alpha*.3),alpha))
 padded=Image.new('RGBA',(size+8,size+8));padded.alpha_composite(im,(4,4));im=padded
 file=f'source/fx-{key}-recipe-v1.png';im.save(o/file);recipes[key]={'file':file,'method':'code-native pixel shape recipe, no image editing','size':im.width,'scale':2 if key!='release' else 3}
(o/'fx-recipes.json').write_text(json.dumps(recipes,ensure_ascii=False,indent=2),encoding='utf-8')
plans={'horizontal':('source/fx-slash-horizontal-v1.png',.17),'up':('source/fx-slash-up-v1.png',.18),'down':('source/fx-slash-down-v1.png',.18),'wings':('source/fx-bloodfire-wings-v1.png',.26)}
plans.update({k:(v['file'],v['scale']) for k,v in recipes.items()});effects={}
for key,(file,scale) in plans.items():
 im=Image.open(o/file).convert('RGBA');anchor=[im.width/2,im.height/2];fit,_=ca.canonical_fit(im,anchor,scale,palette,'fx-'+key);a=np.array(im)[:,:,3]
 effects[key]={'source':{'file':file,'anchor':anchor,'scale':scale},'fit':fit,'independentLayer':True,'damageSource':'events only, not visual alpha','outerAlpha128Pixels':int((a[[0,-1],:]>=128).sum()+(a[:,[0,-1]]>=128).sum())}
(o/'effects.json').write_text(json.dumps(effects,ensure_ascii=False,indent=2),encoding='utf-8');(o/'effect-data.js').write_text('window.ARLECCHINO_FX='+json.dumps(effects,ensure_ascii=False)+';',encoding='utf-8')
shutil.copy2(r/'assets/roster-v2/arlecchino-official-head.png',o/'portrait.png');im=Image.open(o/'portrait.png').convert('RGBA');pal=ca.artlib.build_palette([ca.artlib.downscale(im,.25)],28,seed=31)+[[246,213,197],[239,237,245],[16,22,37]];fit,_=ca.canonical_fit(im,[im.width/2,im.height/2],.75,pal,'portrait');(o/'portrait-fit.json').write_text(json.dumps(fit),encoding='utf-8')
source=r/'outputs/clorinde-actions-20261011';shutil.copytree(source/'opponent',o/'opponent',dirs_exist_ok=True);models=json.loads((source/'opponent-models.json').read_text(encoding='utf-8'))
baseline=r/'outputs/v4-one-character-20261010/baseline-actions';params=json.loads((baseline/'parameters.json').read_text(encoding='utf-8'))
for model,char in [('raiden','raidenshogun'),('nahida','nahida')]:
 for pose in params['characters'][char]['poses']:
  if pose['origin']!='keyframes' or pose['pose'] not in ['guard_1','guard_2']:continue
  key=pose['pose'];dest=o/'opponent'/model/(key+'.png');shutil.copy2(baseline/pose['file'],dest);models[model][key]={'file':dest.relative_to(o).as_posix(),'ax':pose['ax'],'ay':pose['ay'],'scale':pose['u'],'nativeUnitRetained':True,'width':pose['w'],'height':pose['h'],'sourceHash':pose['png_sha256']}
(o/'opponent-models.json').write_text(json.dumps(models,ensure_ascii=False,indent=2),encoding='utf-8');(o/'opponent-data.js').write_text('window.ARLECCHINO_OPPONENT_MODELS='+json.dumps(models,ensure_ascii=False)+';',encoding='utf-8')
print(json.dumps({'effects':len(effects),'peakFX':max(x['fit']['rectangles'] for x in effects.values()),'outerAlpha128':{k:v['outerAlpha128Pixels'] for k,v in effects.items()},'opponents':'unchanged baseline copies'}))

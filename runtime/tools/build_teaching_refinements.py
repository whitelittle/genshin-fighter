"""Targeted walk00/light2-third redraws and higher-detail, larger Paimon portrait."""
from pathlib import Path
import json,sys,copy,shutil,hashlib
from PIL import Image,ImageDraw
import base64,struct
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-unified-v17-20261017'
OUT=ROOT/'outputs/tutorial-refine-v18-20261017'
ART=ROOT/'outputs/lumine-refine-20261017'
sys.path.insert(0,str(ROOT/'runtime/tools'))
import build_teaching_unified as U
from compact_assets import LuaRuntime,python_table
from export_furina import lua
from build_lumine_training import encode,build_palette

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def portrait():
 (ART/'fit').mkdir(parents=True,exist_ok=True)
 im=Image.open(ROOT/'outputs/tutorial-paimon-20261015/paimon-avatar-v1.png').convert('RGBA')
 im.thumbnail((96,96),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(100,100));canvas.alpha_composite(im,((100-im.width)//2,(100-im.height)//2))
 data,target=encode(canvas,build_palette([canvas],20,seed=21),1,anchor=[50,100])
 target.save(ART/'fit/paimon.png')
 return data

def build():
 (ART/'fit').mkdir(parents=True,exist_ok=True)
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 rt=LuaRuntime();rt.execute('__loaders={};'+(BASE/'source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']());old=copy.deepcopy(data)
 calibration=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/report.json').read_text(encoding='utf-8'))
 contrast=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/fit/master-contrast.json').read_text(encoding='utf-8'))['palette']
 U.ART=ART;rows={}
 for key,file in [('walk_00','walk00.png'),('light2_2','light2third.png')]:
  path=ART/'source'/file;im=Image.open(path).convert('RGBA')
  assert im.size==(1024,1536),(key,im.size)
  bb=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
  assert bb and bb[0]>1 and bb[2]<im.width-1 and bb[1]>1 and bb[3]<im.height-1,(key,bb)
  root=[520,bb[3]]
  data['frames'][key],rows[key]=U.fit(im,root,calibration['sourceUnit'],key,calibration,contrast)
  rows[key].update(source=f'source/{file}',sourceSha256=sha(path),sourceBounds=bb,masterScalePreserved=True)
 for key,value in old['frames'].items():
  if key not in ['walk_00','light2_2']:assert data['frames'][key]==value,key
 assert data['groups']==old['groups'] and data['aliases']==old['aliases']
 data['bodyPeak']=max(f['n']for f in data['frames'].values())
 unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()};mean=sum(f['n']for f in unique.values())/len(unique)
 assert mean<1000,mean
 (OUT/'source/teaching/gf_lumine_training_data.lua').write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 paimon=portrait()
 (OUT/'source/teaching/gf_paimon_training_avatar.lua').write_text("__loaders['gf_paimon_training_avatar']=function() return "+lua(paimon)+' end\n',encoding='utf-8')
 p=OUT/'source/teaching/gf_training_lesson.lua';code=p.read_text(encoding='utf-8')
 before="self.avatar=G.bitmap(scene.app.layers.hud);self.avatar:draw(img,'paimon-guide')"
 after="self.avatar=G.bitmap(scene.app.layers.hud);self.avatar:start(img,'paimon-guide');self.avatar.node:on(false);self.avatarReady=false"
 assert code.count(before)==1;code=code.replace(before,after)
 code=code.replace('local speaking=self:isSpeaking()\n L.node:on(speaking);self.avatar.node:on(speaking)',
  'local speaking=self:isSpeaking()\n if not self.avatarReady then self.avatarReady=self.avatar:step(160) end\n L.node:on(speaking);self.avatar.node:on(speaking and self.avatarReady)')
 code=code.replace('local avatarSize=248','local avatarSize=310')
 code=code.replace('self.avatar.node:pos(avatarX,y-88):scale(avatarSize/self.avatarImage.w,avatarSize/self.avatarImage.w):on(true)',
  'self.avatar.node:pos(avatarX,y-72):scale(avatarSize/self.avatarImage.w,avatarSize/self.avatarImage.w):on(self.avatarReady)')
 p.write_text(code,encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert set(changed)=={'source/teaching/gf_lumine_training_data.lua','source/teaching/gf_paimon_training_avatar.lua','source/teaching/gf_training_lesson.lua'},changed
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8') for p in order),encoding='utf-8')
 (OUT/'verification').mkdir(exist_ok=True)
 manifest={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'sourceFiles':{p:sha(OUT/p)for p in order},'frames':rows,'bodyUniqueMean':mean,'bodyPeak':data['bodyPeak'],'paimon':{'oldDisplay':248,'display':310,'oldSampleMax':48,'sampleMax':96,'oldColors':12,'colors':20,'rectangles':paimon['n'],'preparationBudget':160,'bottomPanelGap':34}}
 (OUT/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (ART/'import.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 reviewkeys={k for g in ['idle','walk','back','dash','light1','light2','light3','heavy']for k in data['groups'][g]['frames']}
 (ART/'review-data.json').write_text(json.dumps({'frames':{k:data['frames'][k]for k in reviewkeys},'groups':{g:data['groups'][g]for g in ['idle','walk','back','dash','light1','light2','light3','heavy']}},ensure_ascii=False),encoding='utf-8')
 def board(group,keys,bank):
  img=Image.new('RGB',(520*len(keys),430),'#263454');draw=ImageDraw.Draw(img)
  for i,key in enumerate(keys):
   f=bank[key];raw=base64.b64decode(f['d'])[:f['n']*10];rects=struct.unpack('<'+'H'*(f['n']*5),raw)
   draw.text((i*520+12,12),key,fill='white');draw.line((i*520,375,(i+1)*520,375),fill='#a2b5d2')
   for j in range(f['n']):
    x,y,w,h,c=rects[j*5:j*5+5];px=i*520+170+(x-f['ax'])*f['u'];py=375+(y-f['ay'])*f['u']
    draw.rectangle((px,py,px+w*f['u']-.01,py+h*f['u']-.01),fill=tuple(f['pal'][c][:3]))
  img.save(ART/f'{group}-runtime-review.png')
 for group in ['walk','dash','light1','light2','light3','heavy']:
  board(group,['teaching_master']+data['groups'][group]['frames'],data['frames'])
 board('walk00-before-after',['teaching_master','before','after'],{'teaching_master':data['frames']['teaching_master'],'before':old['frames']['walk_00'],'after':data['frames']['walk_00']})
 board('light2third-before-after',['teaching_master','before','after'],{'teaching_master':data['frames']['teaching_master'],'before':old['frames']['light2_2'],'after':data['frames']['light2_2']})
 html=(ROOT/'outputs/lumine-unified-20261017/index.html').read_text(encoding='utf-8')
 html=html.replace('荧 · 同母版动作核对','荧 · 步态与轻二第三帧返修').replace('荧 · 前后走、前冲、三轻与重击核对','荧 · 步态与轻二第三帧返修')
 start=html.index('<p>');end=html.index('</p>',start)+4
 html=html[:start]+'<p>只返修截图对应walk_00与轻攻击2第三帧；母版、另外三张步态及其余攻击保持。前后走仍共用四姿。下方先列母版／返修前／返修后，全部同一源单位与脚底参考，动作与观感待验。</p>'+html[end:]
 html=html.replace('<div id="boards"></div>','<section><h2>前后走首姿 · 母版／返修前／返修后</h2><img src="walk00-before-after-runtime-review.png"></section><section><h2>轻二第三姿 · 母版／返修前／返修后</h2><img src="light2third-before-after-runtime-review.png"></section><div id="boards"></div>')
 start=html.index('<p>留档：');end=html.index('</p>',start)+4
 html=html[:start]+'<p>留档：<a href="source/walk00.png">步态源图</a> · <a href="source/light2third.png">轻二第三姿源图</a> · <a href="prompts.json">返修提示词</a> · <a href="import.json">拟合与保留项</a></p>'+html[end:]
 (ART/'index.html').write_text(html,encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items()if k!='sourceFiles'},ensure_ascii=False))

if __name__=='__main__':build()

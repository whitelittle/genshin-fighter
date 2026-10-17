from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';rows=[]
for p in sorted((o/'source').glob('*.png')):
 a=np.array(Image.open(p).convert('RGBA'))[:,:,3];ys,xs=np.where(a>=250)
 rows.append({'file':p.relative_to(o).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':[a.shape[1],a.shape[0]],'clearPixels':int((a==0).sum()),'corePixels':int((a>=250).sum()),'softPixels':int(((a>0)&(a<250)).sum()),'alphaMax':int(a.max()),'coreBounds':None if not len(xs) else [int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1],'status':'candidate; visible external halo, not production-ready'})
report={'character':'arlecchino','sourceGeneration':'built-in image_gen','userFeedback':'母版过于修长；恢复正常成年比例，不能机械压缩图片','currentProportionCandidate':'source/master-compact-v5.png','cutoutCandidate':'source/master-cutout-v6.png','proportionReview':'shorter leg chains and wider torso visually improved; user acceptance pending','transparency':'FAIL: soft external gray/red halo remains; no fitted animation production from these mothers yet','runtimeIntegrated':False,'simulator':'not run','device':'not observed','files':rows}
(o/'mother-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);board=Image.new('RGBA',(860,540),(242,244,248,255));draw=ImageDraw.Draw(board)
for i,(name,label) in enumerate([('master-v1.png','首版：过于修长，停用'),('master-compact-v5.png','重画比例候选：待确认，光晕未通过')]):
 im=Image.open(o/'source'/name).convert('RGBA');im.thumbnail((400,480));board.alpha_composite(im,(i*430+(430-im.width)//2,44));draw.text((i*430+12,10),label,font=font,fill=(30,35,50))
board.convert('RGB').save(o/'evidence/mother-proportion-comparison.jpg')
# Use existing inventory builder by executing an isolated sibling adapted to this output.
s=(r/'work/build_clorinde_delivery.py').read_text(encoding='utf-8').replace("OUT=ROOT/'outputs/clorinde-actions-20261011'","OUT=ROOT/'outputs/arlecchino-actions-20261011'").replace("!='clorinde'","!='arlecchino'").replace("'character':'clorinde'","'character':'arlecchino'")
(r/'work/build_arlecchino_inventory.py').write_text(s,encoding='utf-8')
with (o/'制作与交付.md').open('a',encoding='utf-8') as f:f.write('\n## 母版比例返修与接续\n\n匿名玩家指出首版过于修长。首版及继承轮廓的返修均停用；v5重新绘制，缩短腿部并恢复头部/躯干宽度，未用横纵不同比例压图。v6仅尝试去背景，仍有外侧灰红光晕，不登记透明边界通过，不以此母版批量制作动作。源图、六份完整提示词、哈希、alpha统计及等画布尺度对照已保存。\n\n下一步：继续修透明边界并核对母版比例；母版稳定后做两姿真实待机、六相步态及枪尾短击代表招。随后扩展其余25组与独立特效/统一Q/投技配对。旧图目录清单仅供后续核对，不能作为新动作完成。\n')
print('Mother sources, prompts, alpha diagnostics, and next steps saved')

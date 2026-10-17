from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw,ImageFont
import numpy as np,json,hashlib
from clorinde_assets import components,area,bounds
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';p=o/'source/master-cutout-v6.png';im=Image.open(p).convert('RGBA');a=np.array(im)
core=a[:,:,3]>=250;groups=components(core);large=[g for g in groups if area(g)>1200]
assert len(large)==1, 'multiple character cores require review'
# Production extraction: preserve original RGBA inside 2-source-pixel antialias margin.
# No painting, recoloring, alpha amplification or body deformation.
keep=np.asarray(Image.fromarray(core.astype('uint8')*255).filter(ImageFilter.MaxFilter(5)))>0
out=a.copy();out[~keep]=0
# Pad the original full canvas to protect hair margin; source coordinates recorded.
cut=Image.new('RGBA',(im.width+64,im.height+64));cut.alpha_composite(Image.fromarray(out),(32,32));cut.save(o/'frames/mother-extracted-v6.png')
report={'source':'source/master-cutout-v6.png','file':'frames/mother-extracted-v6.png','sourceOffset':[32,32],'method':'alpha250 opaque support plus 2-source-pixel antialias margin; original RGBA unchanged inside support','sourceHash':hashlib.sha256(p.read_bytes()).hexdigest(),'extractedHash':hashlib.sha256((o/'frames/mother-extracted-v6.png').read_bytes()).hexdigest(),'retainedPixels':int((out[:,:,3]>0).sum()),'removedFringePixels':int(((a[:,:,3]>0)&~keep).sum()),'corePreserved':bool(np.array_equal(out[core],a[core])),'scaleCandidate':.23,'anchorCandidate':[620,1557],'artAccepted':False,'runtimeIntegrated':False}
assert report['corePreserved'];assert not np.any(out[[0,-1],:,3]);assert not np.any(out[:,[0,-1],3])
(o/'mother-extraction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
board=Image.new('RGBA',(900,520),(242,244,248,255));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for i,bg in enumerate([(242,244,248,255),(30,33,48,255)]):
 panel=Image.new('RGBA',(450,520),bg);v=cut.copy();v.thumbnail((420,470));panel.alpha_composite(v,((450-v.width)//2,36));board.alpha_composite(panel,(i*450,0));draw.text((i*450+8,8),'v6 提取后：比例候选，浅/深底核对',font=font,fill=(70,80,100) if i==0 else (235,238,248))
board.convert('RGB').save(o/'evidence/mother-extracted-light-dark.jpg')
print(json.dumps(report,ensure_ascii=False))

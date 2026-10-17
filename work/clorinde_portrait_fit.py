from clorinde_assets import O,canonical_fit,artlib
from PIL import Image
import json
im=Image.open(O/'portrait.png').convert('RGBA')
palette=artlib.build_palette([artlib.downscale(im,.25)],28,seed=31)+[[246,213,197],[239,237,245],[16,22,37]]
fit,_=canonical_fit(im,[im.width/2,im.height/2],.75,palette,'portrait')
(O/'portrait-fit.json').write_text(json.dumps(fit,ensure_ascii=False,indent=2),encoding='utf-8')

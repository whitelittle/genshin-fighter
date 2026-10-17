from PIL import Image,ImageDraw
import numpy as np
from pathlib import Path
p=Path('outputs/arlecchino-actions-20261011');im=Image.open(p/'source/master-cutout-v6.png').convert('RGBA');a=np.asarray(im);out=Image.new('RGB',(1024,1536),'white');alpha=a[:,:,3];vis=np.zeros_like(a);vis[:,:,:3]=a[:,:,:3];vis[:,:,3]=np.where(alpha>=250,255,0);out.paste(Image.fromarray(vis),mask=Image.fromarray(vis[:,:,3]));out.resize((512,768)).save(p/'evidence/alpha-core-diagnostic.png');print('diagnostic only; source not replaced')

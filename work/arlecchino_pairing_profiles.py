from pathlib import Path
import json,numpy as np
from PIL import Image
p=Path('outputs/arlecchino-actions-20261011');d=json.loads((p/'actions.json').read_text(encoding='utf-8'));models=json.loads((p/'opponent-models.json').read_text(encoding='utf-8'))
def match(sf,hint,native,base):
 im=np.array(Image.open(p/sf['file']).convert('RGBA'));rawhint=[hint[0]-sf['sourceOrigin'][0],hint[1]-sf['sourceOrigin'][1]];ni=np.array(Image.open(p/native['file']).convert('RGBA'));best=None
 nyRange=range(max(0,base[1]-10),min(ni.shape[0],base[1]+11))
 if '/nahida/victim_0' in native['file']:nyRange=range(23,28)
 if '/raiden/victim_0' in native['file']:nyRange=range(20,27)
 for ny in nyRange:
  ay=sf['anchor'][1]+(ny-native['ay'])*native['scale']/sf['scale'];row=round(ay)
  if not 0<=row<im.shape[0] or abs(row-rawhint[1])>65:continue
  for nx in range(max(0,base[0]-3),min(ni.shape[1],base[0]+4)):
   if ni[ny,nx,3]<180:continue
   xs=np.where((im[row,:,3]>=180)&(im[row,:,:3].max(axis=1)<135)&(abs(np.arange(im.shape[1])-rawhint[0])<65))[0]
   if not len(xs):continue
   ax=int(xs[np.argmin(abs(xs-rawhint[0]))]);score=(ax-rawhint[0])**2+(ay-rawhint[1])**2+10*((nx-base[0])**2+(ny-base[1])**2)
   if best is None or score<best[0]:best=(score,[ax,ay],[nx,ny])
 if best is None:raise ValueError(('no grounded opaque contact',sf['file'],hint,native['file']))
 return {'caster':best[1],'target':best[2],'targetKey':'victim_0','kind':'forearm control','groundedOpponent':True}
profiles={}
for model,hints,base in [('raiden',[(617,143),(1075,180),(658,800)],[36,21]),('nahida',[(567,346),(567,346),(566,1090)],[38,24])]:
 a={**d['throw'],**d['throw'].get('variants',{}).get(model,{})};pr={}
 for i,h in zip([1,2,3],hints):pr[str(i)]=match(a['sourceFrames'][i],h,models[model]['victim_0'],base)
 profiles[model]=pr
profiles['victim']={}
for model,bases in [('raiden',[[45,12],[36,15]]),('nahida',[[44,21],[44,22]])]:
 pr={}
 for i,h in enumerate([(490,150),(885,210)] if model=='raiden' else [(567,346),(566,1090)]):
  key='throw_'+str(i);v=match(({**d['victim'],**d['victim'].get('variants',{}).get(model,{})})['sourceFrames'][[0,2][i]],h,models[model][key],bases[i]);v['targetKey']=key;v['kind']='victim forearm';pr[str(i)]=v
 profiles['victim'][model]=pr
(p/'pairing-profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2),encoding='utf-8');(p/'pairing-data.js').write_text('window.ARLECCHINO_PAIRING='+json.dumps(profiles)+';',encoding='utf-8');print(json.dumps(profiles))

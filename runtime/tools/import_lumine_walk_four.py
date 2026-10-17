"""Import mother-proportioned half-cycles; keep every non-walking body unchanged."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/tools'));sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
from compact_assets import LuaRuntime,python_table
from build_lumine_training import sheet,encode,build_palette,write_module
import numpy as np
from PIL import Image
ART=ROOT/'outputs/lumine-walk-four-20261016'
def main():
 (ART/'fit').mkdir(exist_ok=True)
 rt=LuaRuntime();rt.execute('__loaders={};'+(ROOT/'outputs/tutorial-complete-v9-20261015/source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']())
 # Keep the existing idle head's horizontal offset from the simulation root.
 idle=Image.open(ROOT/'outputs/lumine-training-20261015/fit/lumine-idle_0.png').convert('RGBA')
 yy,xx=np.nonzero(np.asarray(idle)[:16,:,3]>127)
 offset=data['frames']['idle_0']['ax']-float(np.median(xx))
 raw={};metadata={};durations={'walk':[8]*4,'back':[10]*4}
 path=ART/'source/walk-v3-candidate.png'
 from build_lumine_training import components
 im=Image.open(path).convert('RGBA');bodies=components(np.asarray(im)[:,:,3]>127)[:4]
 assert len(bodies)==4
 standing=float(np.median([b[3]-b[1]for n,b in bodies]))
 extracted=sheet(path,4,4,standing)
 for group in ['walk','back']:
  # Reversing this planted walk cycle moves backward while facing the opponent.
  order=[0,1,2,3] if group=='walk' else [0,3,2,1]
  for i,sourceIndex in enumerate(order):
   frame,details=extracted[sourceIndex];key=f'{group}_{i}';raw[key]=frame
   rows=max(3,round(frame.height*.18));ys,xs=np.nonzero(np.asarray(frame)[:rows,:,3]>127)
   anchor=[float(np.median(xs))+offset,frame.height]
   metadata[key]=dict(details,anchor=anchor,standingSourcePixels=standing,phase=sourceIndex)
 for key in list(data['frames']):
  if key.startswith('walk_') or key.startswith('back_'):del data['frames'][key]
 chosen=None
 for colors in [16,14,12,10,8]:
  pal=build_palette(list(raw.values()),colors,seed=21);new={};targets={}
  for key,frame in raw.items():new[key],targets[key]=encode(frame,pal,4,metadata[key]['anchor'])
  counts=[f['n']for f in data['frames'].values()]+[f['n']for f in new.values()]
  mean=sum(counts)/len(counts)
  if mean<1000 and max(f['n']for f in new.values())<=1200:chosen=colors,new,targets,mean;break
 assert chosen is not None,mean
 colors,new,targets,mean=chosen;data['frames'].update(new)
 for group in ['walk','back']:
  data['groups'][group]={'frames':[f'{group}_{i}'for i in range(4)],'durations':durations[group]}
 data['aliases']['walk1']='walk_0';data['aliases']['walk2']='walk_2'
 data['groups']['dash']['frames']=[f'walk_{i}' for i in [0,1,2,3,0,1]]
 data['bodyPeak']=max(f['n']for f in data['frames'].values());write_module('gf_lumine_training_data',data)
 for key,im in targets.items():im.save(ART/'fit'/f'{key}.png')
 report={'scope':'candidate, human aesthetic and native device acceptance pending','generator':'built-in image_gen','canonicalMother':'outputs/lumine-basic-20261015/source/master-v1.png','motherUnchangedSha256':hashlib.sha256((ROOT/'outputs/lumine-basic-20261015/source/master-v1.png').read_bytes()).hexdigest(),'oldNonWalkFramesUnchanged':76,'uniqueBodyFrames':len(data['frames']),'uniqueFrameMean':mean,'peak':data['bodyPeak'],'newFramePeak':max(f['n']for f in new.values()),'newPalette':colors,'durations':durations,'anchorMethod':'stable head-column offset calibrated to original idle; fixed foot plane','newFrames':{k:dict(metadata[k],n=f['n'],w=f['w'],h=f['h'],u=f['u'])for k,f in new.items()},'pixelReconstructionToQuantizedTarget':True,'sources':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in (ART/'source').glob('*.png')}}
 (ART/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items()if k not in ['newFrames','sources']},ensure_ascii=True))
if __name__=='__main__':main()

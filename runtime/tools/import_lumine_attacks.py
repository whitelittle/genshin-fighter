"""Fit generated second/third light and heavy animations, preserving the v7 bank."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/optimization-test-deps'));sys.path.insert(0,str(ROOT/'runtime/tools'))
from compact_assets import LuaRuntime,python_table
from build_lumine_training import sheet,encode,build_palette,write_module
ART=ROOT/'outputs/lumine-attacks-20261015';TRAIN=ROOT/'outputs/lumine-training-20261015'

def main():
 (ART/'fit').mkdir(exist_ok=True)
 baseline=ROOT/'outputs/tutorial-windup-v7-20261015/source/teaching/gf_lumine_training_data.lua'
 rt=LuaRuntime(unpack_returned_tuples=True);rt.execute('__loaders={};'+baseline.read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']())
 from PIL import Image
 from build_lumine_training import components
 import numpy as np
 raw={};meta={};groups={'light2':[8,4,9,9],'light3':[12,5,12,12],'heavy':[26,6,15,15]}
 for name,durations in groups.items():
  source=ART/'source'/f'{name}-v1.png';im=Image.open(source).convert('RGBA')
  # Ready stance is the bottom-right main silhouette; its anatomy sets this sheet's unit.
  bodies=components(np.asarray(im)[:,:,3]>=128)[:4]
  ready=max((b for n,b in bodies),key=lambda b:(b[1]>im.height/2,b[0]))
  standing=ready[3]-ready[1]
  frames=sheet(source,4,2,standing)
  for i,(frame,details) in enumerate(frames):
   key=f'{name}_{i}';raw[key]=frame;meta[key]=dict(details,standingSourcePixels=standing)
  data['groups'][name]={'frames':[f'{name}_{i}' for i in range(4)],'durations':durations}
  data['aliases'][name]=name+'_0'
 chosen=None
 for colors in [16,14,12]:
  pal=build_palette(list(raw.values()),colors,seed=21);new={};targets={}
  for key,im in raw.items():new[key],targets[key]=encode(im,pal,4)
  mean=(sum(f['n'] for f in data['frames'].values())+sum(f['n'] for f in new.values()))/(len(data['frames'])+len(new))
  if mean<1000:chosen=(colors,new,targets,mean);break
 assert chosen is not None,'no budget-compliant candidate; preserve source art'
 colors,new,targets,mean=chosen
 data['frames'].update(new);data['bodyPeak']=max(f['n'] for f in data['frames'].values())
 write_module('gf_lumine_training_data',data)
 for key,im in targets.items():im.save(ART/'fit'/f'{key}.png')
 report={'scope':'generated candidates, not final art/device acceptance','generator':'built-in image_gen','old36BodiesUnchanged':True,'uniqueBodyFrames':len(data['frames']),'uniqueFrameMean':mean,'bodyPeak':data['bodyPeak'],'newPaletteColors':colors,'newFrames':{key:dict(meta[key],n=frame['n'],w=frame['w'],h=frame['h'],anchor=[frame['ax'],frame['ay']],u=frame['u']) for key,frame in new.items()},'pixelReconstructionToQuantizedTarget':True,'groups':groups,'sources':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ART/'source').glob('*.png'))}}
 (ART/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 old=json.loads((TRAIN/'import.json').read_text(encoding='utf-8'))
 old['bodyStats']['lumine']={'uniqueFrameMean':mean,'peak':data['bodyPeak'],'frameRects':{key:f['n'] for key,f in data['frames'].items()}}
 old['bodyPeak']['lumine']=data['bodyPeak'];old['generatedAttackImport']='outputs/lumine-attacks-20261015/import.json'
 (TRAIN/'import.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['newFrames','sources']},ensure_ascii=True,indent=2))

if __name__=='__main__':main()

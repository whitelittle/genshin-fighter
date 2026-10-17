"""Fit new master/walk/dash with ONE source scale and canvas root; no per-frame stretching."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'outputs/lumine-rebuild-20261016'
sys.path.insert(0,str(ROOT/'runtime/tools'));sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
from compact_assets import LuaRuntime,python_table
from build_lumine_training import encode,build_palette,write_module
from PIL import Image
import numpy as np
def main():
 rt=LuaRuntime();rt.execute('__loaders={};'+(ROOT/'outputs/tutorial-polish-v12-20261016/source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']())
 master=Image.open(ART/'source/master-v1.png').convert('RGBA');a=np.asarray(master);ys,xs=np.nonzero(a[:,:,3]>127);standing=int(ys.max()-ys.min()+1);factor=84/standing
 raw={};meta={};(ART/'fit').mkdir(exist_ok=True)
 files={'idle_0':'master-v1.png',**{f'{g}_{i}':f'{g}_{i}-selected.png'for g in ['walk','dash']for i in range(4)}}
 for key,file in files.items():
  path=ART/'source'/file;im=Image.open(path).convert('RGBA');a=np.asarray(im);ys,xs=np.nonzero(a[:,:,3]>127);bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
  assert bbox[0]>0 and bbox[2]<im.width and bbox[1]>0 and bbox[3]<im.height,(key,bbox,'cropped')
  crop=im.crop(bbox);w,h=round(crop.width*factor),round(crop.height*factor);raw[key]=crop.resize((w,h),Image.Resampling.NEAREST)
  meta[key]={'source':file,'bbox':bbox,'factor':factor,'anchor':[(520-bbox[0])*factor,(1430-bbox[1])*factor],'framePixelSize':[w,h]}
 for key in list(data['frames']):
  if key.startswith(('walk_','back_','idle_','dash_')):del data['frames'][key]
 for colors in [16,14,12,10]:
  pal=build_palette(list(raw.values()),colors,seed=21);frames={};targets={}
  for key,im in raw.items():frames[key],targets[key]=encode(im,pal,4,meta[key]['anchor'])
  allFrames={**data['frames'],**frames};unique={json.dumps({k:v for k,v in f.items()if k not in ['name']},sort_keys=True):f for f in allFrames.values()}
  mean=sum(f['n']for f in unique.values())/len(unique)
  if mean<1000 and max(f['n']for f in frames.values())<=1450:break
 else:raise AssertionError(mean)
 data['frames'].update(frames);data['frames']['idle_1']=frames['idle_0']
 data['groups']['idle']={'frames':['idle_0'],'durations':[60]}
 data['groups']['walk']={'frames':[f'walk_{i}'for i in range(4)],'durations':[12,11,12,11]}
 data['groups']['back']={'frames':[f'walk_{i}'for i in [0,3,2,1]],'durations':[14]*4}
 data['groups']['dash']={'frames':[f'dash_{i}'for i in range(4)],'durations':[3,4,4,3]}
 data['aliases'].update(walk1='walk_0',walk2='walk_2');data['bodyPeak']=max(f['n']for f in data['frames'].values());write_module('gf_lumine_training_data',data)
 for key,im in targets.items():im.save(ART/'fit'/(key+'.png'))
 report={'scope':'new master and locomotion candidate, user aesthetic acceptance pending','bodyUniqueFrames':len(unique),'bodyUniqueMean':mean,'peak':data['bodyPeak'],'newPeak':max(f['n']for f in frames.values()),'newPalette':colors,'fixedSourceScale':factor,'fixedCanvasRoot':[520,1430],'masterHeightSourcePixels':standing,'groups':{k:data['groups'][k]for k in ['idle','walk','back','dash']},'frames':{k:{**meta[k],'rectangles':frames[k]['n']}for k in frames},'sourceSha256':{file:hashlib.sha256((ART/'source'/file).read_bytes()).hexdigest()for file in files.values()},'preserved':'existing attacks/jump/guard etc not redrawn in this locomotion batch; await unified-master revision','backward':'reuses four new poses in reverse, no old walking image; needs aesthetic review','noPerFrameHeadOrBodyRescale':True,'quantizedPixelReconstruction':True}
 (ART/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items()if k not in ['frames','sourceSha256','groups']}))
if __name__=='__main__':main()

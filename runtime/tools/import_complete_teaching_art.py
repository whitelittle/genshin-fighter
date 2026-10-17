"""Import generated candidates non-destructively on the frozen v8 body banks."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/optimization-test-deps'));sys.path.insert(0,str(ROOT/'runtime/tools'))
from compact_assets import LuaRuntime,python_table
from build_lumine_training import sheet,components,encode,build_palette,write_module
from PIL import Image
import numpy as np
ART=ROOT/'outputs/tutorial-complete-art-20261015';BASE=ROOT/'outputs/tutorial-attack-v8-20261015/source/teaching'
def bank(name):
 rt=LuaRuntime(unpack_returned_tuples=True);rt.execute('__loaders={};'+(BASE/(name+'.lua')).read_text(encoding='utf-8'))
 return python_table(rt.globals().__loaders[name]())
def main(partial=False):
 (ART/'fit').mkdir(exist_ok=True);report={'scope':'generated candidates; native and aesthetic acceptance pending','generator':'built-in image_gen','partial':partial,'roles':{}}
 groups={'crouchLight':[9,4,8,8],'crouchHeavy':[22,5,14,14],'airLight':[7,8,6,6],'airHeavy':[14,10,10,10],'skill':[18,6,12,12],'skillUp':[20,6,12,12],'skillDown':[24,6,12,12],'burst':[32,8,17,17],'throwTech':[18,30,12,20],'lumineHurt':[20,20,30,20]}
 for role,module,plans in [('lumine','gf_lumine_training_data',groups),('lawachurl','gf_lawachurl_training_data',{'lawThrown':[12,18,20,20],'lawGrab':[18,30,20,20]}),('aether','gf_aether_support_data',{'aether':[20,6,19,19]})]:
  data=bank(module) if role!='aether' else {'frames':{},'groups':{},'aliases':{}}
  raw={};meta={}
  for name,durations in plans.items():
   source=ART/'source'/f'{name}-v1.png'
   if not source.exists():
    assert partial,source
    continue
   im=Image.open(source).convert('RGBA');bodies=components(np.asarray(im)[:,:,3]>=128)[:4]
   assert len(bodies)==4 and min(n for n,b in bodies)>1000,(name,bodies)
   ready=max((b for n,b in bodies),key=lambda b:(b[1]>im.height/2,b[0]))
   standing=ready[3]-ready[1]
   pairs=sheet(source,4,2,standing)
   group='assist' if role=='aether' else name
   for i,(frame,details) in enumerate(pairs):
    # Crouches remain lower than the 80px standing mother; air silhouettes are slightly tucked.
    scale=.68 if name.startswith('crouch') or name=='lumineHurt' else .93 if name.startswith('air') else 1
    if scale!=1:frame=frame.resize((round(frame.width*scale),round(frame.height*scale)),Image.Resampling.NEAREST)
    if role=='lawachurl' and name=='lawThrown':frame=frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    key=f'{group}_{i}';raw[key]=frame;meta[key]=dict(details,anatomyScale=scale,canonicalMirror=role=='lawachurl' and name=='lawThrown')
   data['groups'][group]={'frames':[f'{group}_{i}' for i in range(4)],'durations':durations}
   data['aliases'][group]=f'{group}_0'
  chosen=None
  for colors in [14,12,10,8,6]:
   palette=build_palette(list(raw.values()),colors,seed=21);new={};targets={}
   for key,frame in raw.items():new[key],targets[key]=encode(frame,palette,5.6 if role=='lawachurl' else 4)
   counts=[f['n'] for f in data['frames'].values()]+[f['n'] for f in new.values()]
   mean=sum(counts)/len(counts)
   if mean<1000:chosen=colors,new,targets,mean;break
  assert chosen is not None,(role,mean)
  colors,new,targets,mean=chosen
  data['frames'].update(new);data['bodyPeak']=max(f['n'] for f in data['frames'].values())
  write_module(module,data)
  for key,target in targets.items():target.save(ART/'fit'/f'{role}-{key}.png')
  report['roles'][role]={'frames':len(data['frames']),'mean':mean,'peak':data['bodyPeak'],'newPaletteColors':colors,'newFrames':{key:dict(meta[key],n=f['n'],w=f['w'],h=f['h'],u=f['u'],anchor=[f['ax'],f['ay']]) for key,f in new.items()},'groups':plans,'oldFramesUnchanged':role!='aether','exactQuantizedPixelReconstruction':True}
 report['sources']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in (ART/'source').glob('*.png')}
 (ART/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({r:{k:v for k,v in d.items()if k not in ['newFrames','groups']}for r,d in report['roles'].items()},indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--partial',action='store_true');main(ap.parse_args().partial)

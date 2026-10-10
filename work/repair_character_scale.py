"""Final anatomical calibration after legacy extraction; source images remain intact.

Explicit reviewed landmarks compensate source art size variation. Never normalize
each pose's body bbox height (crouches and airborne silhouettes must stay different).
"""
from pathlib import Path
import json, shutil, sys, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'game/tools'))
import artlib
LANDMARKS=json.loads((R/'work/character_scale_landmarks.json').read_text(encoding='utf-8'))
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
FOLDERS={'ayaka':R/'outputs/v4-one-character-20261010/ayaka-armed-v2','furina':R/'outputs/furina-design-20261010'}

def fit(folder,source,palette,name,outline):
 im=Image.open(folder/source['file']).convert('RGBA');ratio=source['scale']/4.5
 small=artlib.downscale(im,ratio);idx=artlib.apply_palette(small,palette)
 # Inner one-cell contour keeps silhouette, white hair and skin. No dilation.
 if outline:
  mask=idx>=0
  erosion=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MinFilter(3)))>0
  border=mask&~erosion
  rgb=np.asarray(small)[:,:,:3].astype(float)
  skin=(rgb[:,:,0]>rgb[:,:,1]*1.025)&(rgb[:,:,1]>rgb[:,:,2]*1.025)&(rgb[:,:,0]>150)
  pale=rgb.mean(axis=2)>195
  border&=~(skin|pale)
  dark=[22,25,49]
  if dark not in palette:palette=palette+[dark]
  idx[border]=palette.index(dark)
 rects=artlib.painter(idx);pixels=np.zeros((small.height,small.width,4),dtype=np.uint8)
 for x,y,w,h,c in rects:pixels[y:y+h,x:x+w]=palette[c][:3]+[255]
 expected=np.zeros_like(pixels)
 for c,color in enumerate(palette):expected[idx==c]=color[:3]+[255]
 assert np.array_equal(pixels,expected)
 path=folder/name;Image.fromarray(pixels).save(path)
 # Actual rounded resampling ratios, not requested nominal ratio.
 rx=small.width/im.width;ry=small.height/im.height
 f={**source,'file':name,'anchor':[source['anchor'][0]*rx,source['anchor'][1]*ry],
    'scale':4.5,'scaleX':source['scale']/rx,'scaleY':source['scale']/ry}
 record={'palette':palette,'rects':rects,'anchor':f['anchor'],'scale':f['scale'],
         'scaleX':f['scaleX'],'scaleY':f['scaleY'],'runtimeIntegrated':False,
         'reconstruction':'quantized target exact','outline':'protected inner 1-cell' if outline else 'existing source contour'}
 path.with_suffix('.rects.json').write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
 return f,len(rects)

def main():
 for character,folder in FOLDERS.items():
  original=folder/'actions-before-scale-20261011.json'
  if not original.exists():shutil.copy2(folder/'actions.json',original)
  data=json.loads(original.read_text(encoding='utf-8'))
  foe=json.loads((folder/'foe-fitted.json').read_text(encoding='utf-8'))['basic_0']
  foeim=Image.open(folder/foe['file']).convert('RGBA');b=foeim.getbbox();target=(b[3]-b[1])*foe['scale']
  idle=Image.open(folder/data['待机']['sourceFrames'][0]['file']).convert('RGBA');ib=idle.getbbox()
  contact_ratio=min(210/(ib[2]-ib[0]),240/(ib[3]-ib[1]))
  target_head=LANDMARKS[character]['待机'][0]/contact_ratio*target/(ib[3]-ib[1])
  reference=R/f'work/v4-handoff-20261009-partial/V4/evidence/{"kamisatoayaka" if character=="ayaka" else "furina"}-idle-review/fit.json'
  palette=json.loads(reference.read_text(encoding='utf-8'))['palette']
  report={'baselineVisibleHeight':target,'targetHeadLength':target_head,'method':LANDMARKS['policy'],'actions':{},'simulation':'not run','device':'not observed','visualAcceptance':'pending user'}
  for action,d in data.items():
   if character=='furina' and action=='空重':continue
   source=d.get('sourceFrames') or d['frames']
   original_fits=d['frames']
   lengths=LANDMARKS[character].get(action)
   if not lengths or len(lengths)!=len(source):raise ValueError((character,action,len(source),lengths))
   frames=[];checks=[]
   for i,(f,head) in enumerate(zip(source,lengths)):
    im=Image.open(folder/f['file']).convert('RGBA');b=im.getbbox()
    display_ratio=min(210/(b[2]-b[0]),240/(b[3]-b[1]))
    measured=head/display_ratio;old=f['scale'];f['scale']=target_head/measured
    f['anatomy']={'headLengthSourcePx':measured,'contactSheetHeadLengthPx':head,'targetHeadLengthWorld':target_head,'review':'manual estimate; montage verified'}
    # Body and embedded companion use one contact composite palette.
    usepal=list(palette)
    if d.get('heldCompanion'):
     for helper in ['chevalmarin','crabaletta']:
      hp=json.loads((R/f'work/v4-handoff-20261009-partial/V4/evidence/furina-salon-side-v3/{helper}/fit.json').read_text(encoding='utf-8'))['palette']
      for c in hp:
       if c[:3] not in usepal:usepal.append(c[:3])
    if character=='furina' and action=='待机':
     # Approved idle pixels are the mother reference. Resize their display only;
     # never repaint their contour or replace them with a newly quantized idle.
     fitted=dict(original_fits[i]);fitted['scale']*=f['scale']/old
     n=0
    else:
     fitted,n=fit(folder,f,usepal,f'calibrated-{list(data).index(action)}-{i}.png',outline=not(character=='ayaka' and action=='站立格挡'))
    frames.append(fitted);checks.append({'source':f['file'],'oldScale':old,'scale':f['scale'],'headLength':measured*f['scale'],'rectangles':n})
    if d.get('effects',{}).get('nozzles'):
     d['effects']['nozzles'][i]=[v*f['scale']/old for v in d['effects']['nozzles'][i]]
   d['sourceFrames']=source;d['frames']=frames
   d['displayCalibration']={'method':'reviewed anatomical landmark','targetHeadLength':target_head,'baselineVisibleHeight':target,'bboxNormalization':False,'manualTolerance':0.08}
   report['actions'][action]=checks
  (folder/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  (folder/'scale-calibration-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  # True world-scale contact sheets: each cell uses the same world display factor.
  for mode in ['source','fit']:
   rows=[]
   for action,d in data.items():
    fs=d['sourceFrames'] if mode=='source' else d['frames'];strip=Image.new('RGBA',(len(fs)*300,430),'#777780');draw=ImageDraw.Draw(strip)
    draw.line((0,390,strip.width,390),fill='#ffffff')
    for i,f in enumerate(fs):
     im=Image.open(folder/f['file']).convert('RGBA');sx=f.get('scaleX',f['scale']);sy=f.get('scaleY',f['scale'])
     im=im.resize((max(1,round(im.width*sx*.75)),max(1,round(im.height*sy*.75))),Image.Resampling.NEAREST)
     x=150+i*300-round(f['anchor'][0]*sx*.75);y=390-round(f['anchor'][1]*sy*.75)
     strip.alpha_composite(im,(x,y));draw.text((i*300+5,5),f'{action} {i}',font=FONT,fill='white')
    rows.append(strip)
   for page in range((len(rows)+5)//6):
    subset=rows[page*6:page*6+6];sheet=Image.new('RGBA',(max(x.width for x in subset),len(subset)*430),'#777780')
    for j,row in enumerate(subset):sheet.alpha_composite(row,(0,j*430))
    sheet.convert('RGB').save(folder/f'scale-calibrated-{mode}-{page}.jpg')
  print(character,len(report['actions']),target,target_head)

if __name__=='__main__':main()

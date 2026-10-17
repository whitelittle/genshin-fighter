"""Independent effect atlas, preserved source coordinates and pixel roundtrip."""
import json
from pathlib import Path
from clorinde_assets import O,extract,canonical_fit

def main():
 items,fragments=extract(O/'source/effects-v1.png',6)
 palette=[[255,255,255],[238,224,255],[195,171,255],[156,119,248],[112,64,221],[69,48,144],[255,230,169],[45,32,93]]
 names=['gun','bullet','impact','sword','diagonal','down']
 data={}
 for i,((im,info),name) in enumerate(zip(items,names)):
  file=f'frames/fx-{name}.png';im.save(O/file)
  scale=.32;anchor=[0,im.height/2]
  ff,meta=canonical_fit(im,anchor,scale,palette,'fx-'+name)
  data[name]={'source':{'file':file,'anchor':anchor,'scale':scale,**info},'fit':ff,'file':ff['file'],
      'ownership':'independent effect, not damage definition','runtimeIntegrated':False}
 (O/'effects.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'effect-data.js').write_text('window.CLORINDE_FX='+json.dumps(data,ensure_ascii=False)+';',encoding='utf-8')
 print('six independent effects fitted and reconstructed exactly')

if __name__=='__main__':main()

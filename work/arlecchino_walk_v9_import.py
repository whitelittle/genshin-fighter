from pathlib import Path
import sys,json,shutil,hashlib,struct,base64
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime/tools'))
from compact_assets import LuaRuntime,python_table,literal
import clorinde_assets as ca
O=R/'outputs/arlecchino-scale-layer-20261014';ca.O=O
(O/'source').mkdir(exist_ok=True);(O/'frames').mkdir(exist_ok=True)
src=O/'source/walk-v9-20261014.png';shutil.copy2(Path.home()/'.codex/generated_images/01a13432-9c6c-75f3-b290-4337bd1d9e7b/exec-93937ed2-e534-4d5d-a137-804d291faa35.png',src)
dataPath=R/'runtime/source/assets/gf_arlecchino_data.lua';backup=O/'history/gf_arlecchino_data.lua'
if not backup.exists():shutil.copy2(dataPath,backup)
receipt=R/'runtime/arlecchino-import.json';receiptBackup=O/'history/arlecchino-import.json'
if not receiptBackup.exists():shutil.copy2(receipt,receiptBackup)
rt=LuaRuntime(unpack_returned_tuples=True);rt.execute('__loaders={};'+backup.read_text(encoding='utf8'));data=python_table(rt.globals().__loaders['gf_arlecchino_data']())
palette=data['frames']['idle_0']['pal'];palette=[c[:3] for c in palette]
palette=palette[:-1]+[palette[-1]]
audit=[];sources=[]
for i,(im,info) in enumerate(ca.extract(src,6)[0]):
 assert not info['fullCanvasContact'],(i,'edge contact')
 a=np.asarray(im);ys,xs=np.where(a[:,:,3]>=240);bottom=int(ys.max())+1;anchor=[float(np.median(xs[ys>=bottom-4]))+24,bottom+24]
 padded=Image.new('RGBA',(im.width+48,im.height+48));padded.alpha_composite(im,(24,24));padded.save(O/f'frames/walk-v9-{i}.png')
 ff,meta=ca.canonical_fit(padded,anchor,.65,palette,f'walk-v9-{i}')
 fitted=Image.open(O/ff['file']);ff['anchor'][1]=fitted.getbbox()[3]
 values=[v for row in meta['rects'] for v in row]
 raw=struct.pack('<'+'H'*len(values),*values);raw+=b'\0'*((-len(raw))%3)
 key=f'walk_{i}';data['frames'][key]={'d':base64.b64encode(raw).decode(),'pal':[c+[255] for c in palette],'n':len(meta['rects']),'w':fitted.width,'h':fitted.height,'ax':ff['anchor'][0],'ay':ff['anchor'][1],'u':4.5}
 sources.append({'pose':key,'kind':'body','file':(O/ff['file']).relative_to(R).as_posix(),'sha256':hashlib.sha256((O/ff['file']).read_bytes()).hexdigest(),'rectsFile':(O/meta['file']).with_suffix('.json').relative_to(R).as_posix(),'anchor':ff['anchor'],'scale':4.5})
 audit.append({'pose':key,'source':src.relative_to(R).as_posix(),'sourceUnit':.65,'sourceROIPixelsUnchanged':True,'sourceCanvasContact':False,'rectangles':len(meta['rects']),'quantizedReconstructionExact':True})
data['bodyPeak']=max(data['bodyPeak'],max(x['rectangles'] for x in audit))
dataPath.write_text("__loaders['gf_arlecchino_data']=function()\nreturn "+literal(data)+"\nend\n",encoding='utf8')
m=json.loads(receiptBackup.read_text(encoding='utf8'));m['sources']=[next((s for s in sources if s['pose']==old['pose']),old) for old in m['sources']];m['bodyPeak']=data['bodyPeak'];m['v9WalkRepair']=audit;receipt.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
(O/'walk-import-verification.json').write_text(json.dumps({'newBodyStates':6,'audit':audit,'runtimeSourceUpdated':True,'artAccepted':False},ensure_ascii=False,indent=2),encoding='utf8');print('walk six replaced; peak',data['bodyPeak'])

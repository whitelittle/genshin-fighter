"""Import independently authored wind sheets to a bounded pixel effect bank."""
from pathlib import Path
import sys,json,base64,struct,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'game/tools'),str(ROOT/'runtime/tools')]
import artlib
from export_furina import lua
ART=ROOT/'outputs/lumine-wind-fx-20261017'
PALETTE=[[5,57,64],[7,96,100],[15,144,139],[44,190,168],[99,230,197],[170,251,227],[235,255,248]]
def build(out):
 (ART/'fit').mkdir(exist_ok=True);data={'frames':{},'aliases':{},'bodyPeak':0};rows={}
 for group in ['orb','blade','impact']:
  p=ART/'source'/f'{group}.png';im=Image.open(p).convert('RGBA');assert im.width==im.height and im.width%2==0
  cell=im.width//2;grid=28 if group=='impact' else 24
  for i in range(4):
   crop=im.crop((i%2*cell,i//2*cell,(i%2+1)*cell,(i//2+1)*cell))
   # Uniform area sampling keeps all detached authored fragments in each cell.
   small=crop.resize((grid,grid),Image.Resampling.BOX);idx=artlib.apply_palette(small,PALETTE);rects=artlib.painter(idx)
   target=artlib.render(rects,PALETTE,grid,grid);key=f'{group}_{i}';target.save(ART/'fit'/f'{key}.png')
   raw=struct.pack('<'+'H'*(len(rects)*5),*(v for r in rects for v in r));raw+=b'\0'*((-len(raw))%3)
   data['frames'][key]={'n':len(rects),'d':base64.b64encode(raw).decode(),'pal':[c+[255]for c in PALETTE],'w':grid,'h':grid,'ax':grid/2,'ay':grid/2,'u':1}
   rows[key]={'rectangles':len(rects),'grid':grid,'source':f'source/{group}.png','sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 data['bodyPeak']=max(f['n']for f in data['frames'].values());assert data['bodyPeak']<=400,data['bodyPeak']
 (out/'source/teaching/gf_wind_skill_fx_data.lua').write_text("__loaders['gf_wind_skill_fx_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 (ART/'import.json').write_text(json.dumps({'frames':rows,'effectPeak':data['bodyPeak'],'bodyBudgetSeparate':True,'palette':PALETTE,'artAcceptance':'pending'},indent=2),encoding='utf-8')
 (ART/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>风E独立特效</title><style>body{background:#263454;color:white}img{width:180px;height:180px;image-rendering:pixelated}</style><h1>风球／风刃／命中 · 独立特效</h1><p>四帧从左到右。内置image_gen生成源图，固定7色像素拟合；实际大小见试玩。</p>'+''.join('<h2>'+g+'</h2>'+''.join(f'<img src="fit/{g}_{i}.png">'for i in range(4))for g in ['orb','blade','impact'])+'<p><a href="prompts.json">提示词</a> · <a href="import.json">预算与源图记录</a></p>',encoding='utf-8')
 return data['bodyPeak']
if __name__=='__main__':print(build(ROOT/'outputs/tutorial-wind-fx-v27-20261017'))

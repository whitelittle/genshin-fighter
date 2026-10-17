"""Use archive portraits; restore the v11 body bank while rejected walks are held."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/tools'));sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
from compact_assets import LuaRuntime,python_table
from build_lumine_training import encode,build_palette,write_module
from PIL import Image,ImageDraw
ART=ROOT/'outputs/tutorial-standard-icons-20261016'
SOURCES={'lumine':('lumine-circle.png','https://enka.network/ui/UI_AvatarIcon_PlayerGirl_Circle.png','UI_AvatarIcon_PlayerGirl_Circle','https://wiki.hoyolab.com/pc/genshin/aggregate/character?lang=zh-cn'),'lawachurl':('lawachurl.png','https://gi.yatta.moe/assets/UI/monster/UI_MonsterIcon_Brute_Rock_None.png','UI_MonsterIcon_Brute_Rock_None','https://wiki.hoyolab.com/pc/genshin/entry/2103?lang=zh-cn')}
def main():
 (ART/'fit').mkdir(exist_ok=True);records={}
 for key,(file,url,resource,archive)in SOURCES.items():
  rt=LuaRuntime();rt.execute('__loaders={};'+(ROOT/f'outputs/tutorial-polish-v11-20261016/source/teaching/gf_{key}_training_data.lua').read_text(encoding='utf-8'))
  data=python_table(rt.globals().__loaders[f'gf_{key}_training_data']())
  original=ART/'source'/file;im=Image.open(original).convert('RGBA').resize((34,34),Image.Resampling.LANCZOS)
  mask=Image.new('L',(34,34));ImageDraw.Draw(mask).ellipse((0,0,33,33),fill=255)
  from PIL import ImageChops
  im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
  icon,target=encode(im,build_palette([im],16,seed=21),1,anchor=[17,34]);data['icons']=icon
  write_module(f'gf_{key}_training_data',data);target.save(ART/'fit'/f'{key}-hud.png')
  records[key]={'source':file,'url':url,'resource':resource,'archive':archive,'sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'size':[34,34],'rectangles':icon['n'],'bodyFramesRestoredFrom':'outputs/tutorial-polish-v11-20261016','bodyFramesUnchanged':True}
 (ART/'import.json').write_text(json.dumps({'scope':'original game portrait assets from CDN/mirror, no AI generation; fitted HUD candidate','records':records},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(records))
if __name__=='__main__':main()

import sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'video-deps'))
import cv2
from PIL import Image, ImageDraw
files=[Path('E:/11.BiliBili相关/Captures/原神 2026-10-03 07-04-55.mp4'),*[Path('C:/Users/Cheng/Downloads')/f'SVID_20261003_{s}_1.mp4' for s in ['070444','070829','071109','064534']]]
out=Path('outputs/video-check');out.mkdir(parents=True,exist_ok=True)
metadata=[]
for index,path in enumerate(files):
 cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS);count=cap.get(cv2.CAP_PROP_FRAME_COUNT);duration=count/fps
 info={'id':index,'file':str(path),'fps':fps,'frames':count,'seconds':duration,'width':cap.get(3),'height':cap.get(4),'samples':[]}
 sheet=Image.new('RGB',(1280,4*390),'#202020');draw=ImageDraw.Draw(sheet)
 for j,ratio in enumerate([.2,.4,.6,.8]):
  t=duration*ratio;cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));target=out/f'v{index}-{t:.2f}s.png';im.save(target)
  info['samples'].append({'seconds':t,'path':str(target)})
  im.thumbnail((1280,360));sheet.paste(im,((1280-im.width)//2,j*390+30));draw.text((15,j*390+8),f'Video {index} / {t:.2f}s / {ratio*100:.0f}%',fill='white')
 sheet.save(out/f'v{index}-sheet.jpg');cap.release();metadata.append(info)
(out/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(metadata,ensure_ascii=False,indent=2))

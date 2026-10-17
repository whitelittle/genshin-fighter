from pathlib import Path
import urllib.request, json, sys
sys.path.insert(0, 'work/video-deps')
import cv2
from PIL import Image, ImageDraw
root=Path('assets/references-vNext');root.mkdir(parents=True,exist_ok=True)
sources=[
 ('diluc-a','https://wotpack.ru/wp-content/uploads/2020/12/skill1_576.mp4','https://wotpack.ru/en/genshin-Impact-gajd-na-diljuka-bild-vozvyshenie-i-osnovnye-sborki/'),
 ('diluc-e','https://wotpack.ru/wp-content/uploads/2020/12/ezgif.com-gif-maker38.webm','https://wotpack.ru/en/genshin-Impact-gajd-na-diljuka-bild-vozvyshenie-i-osnovnye-sborki/'),
 ('diluc-q','https://wotpack.ru/wp-content/uploads/2020/12/ezgif.com-gif-maker39.webm','https://wotpack.ru/en/genshin-Impact-gajd-na-diljuka-bild-vozvyshenie-i-osnovnye-sborki/'),
 ('keqing-a','https://upload-os-bbs.hoyolab.com/upload/2022/01/22/8459597/9437835edf7a05e503a2efb26af16aaf_8555470612047828951.gif','https://www.hoyolab.com/article/1995687'),
 ('keqing-e','https://wotpack.ru/wp-content/uploads/2024/03/kje-cin-navyk.mp4','https://wotpack.ru/gajd-dlja-kje-cin-v-genshin-impact/'),
 ('keqing-q','https://wotpack.ru/wp-content/uploads/2024/03/kje-cin-ulta.mp4','https://wotpack.ru/gajd-dlja-kje-cin-v-genshin-impact/')]
report=[]
for name,url,page in sources:
 try:
  dest=root/(name+Path(url).suffix)
  if not dest.exists():
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=30) as r: dest.write_bytes(r.read())
  frames=[]
  if dest.suffix=='.gif':
   im=Image.open(dest); total=im.n_frames
   for n in range(12):
    i=round(n*(total-1)/11); im.seek(i); frames.append((f'frame {i}',im.convert('RGB').copy()))
  else:
   cap=cv2.VideoCapture(str(dest));total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS)
   for n in range(12):
    i=round(n*(total-1)/11); cap.set(cv2.CAP_PROP_POS_FRAMES,i);ok,f=cap.read()
    if ok: frames.append((f'{i/fps:.2f}s',Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))))
   cap.release()
  if not frames: raise ValueError('no decodable frames')
  sheet=Image.new('RGB',(1280,3*220),(20,24,32));draw=ImageDraw.Draw(sheet)
  for i,(label,im) in enumerate(frames):
   im.thumbnail((320,192));x=(i%4)*320;y=(i//4)*220;sheet.paste(im,(x,y));draw.text((x+8,y+195),name+' '+label,fill='white')
  sheet.save(root/(name+'-contact.jpg'),quality=92)
  report.append({'id':name,'source':page,'media':url,'local':str(dest),'frames':len(frames),'evidence':'community-hosted original-game footage; not official skill documentation'})
  print(name,len(frames),flush=True)
 except Exception as e:
  report.append({'id':name,'source':page,'error':str(e)});print(name,str(e),flush=True)
(root/'sources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

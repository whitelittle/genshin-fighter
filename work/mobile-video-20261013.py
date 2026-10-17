from pathlib import Path
import sys,json
sys.path.insert(0,'work/video-deps')
import cv2
from PIL import Image,ImageDraw
video=Path('C:/Users/Cheng/Downloads/SVID_20261013_032008_1.mp4')
out=Path('outputs/mobile-performance-20261013');out.mkdir(exist_ok=True)
cap=cv2.VideoCapture(str(video));fps=cap.get(5);frames=cap.get(7);w=int(cap.get(3));h=int(cap.get(4));seconds=frames/fps
metadata={'source':'匿名玩家手机录屏','recordingFPS':fps,'frames':frames,'seconds':seconds,'width':w,'height':h}
(out/'video-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print(metadata)
times=list(range(0,int(seconds),10))
for page in range((len(times)+7)//8):
    sheet=Image.new('RGB',(1280,4*320),'#252525');draw=ImageDraw.Draw(sheet)
    for n,t in enumerate(times[page*8:page*8+8]):
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
        if not ok:continue
        # Mask lower identifiers in the recording before saving review artifacts.
        f[int(h*.88):]=0
        im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.thumbnail((640,290))
        x=(n%2)*640;y=(n//2)*320
        sheet.paste(im,(x,y+25));draw.text((x+8,y+5),f'{t}s',fill='white')
    sheet.save(out/f'video-sheet-{page}.jpg')
for t in [30,40,60,80,100,120,140,150,160]:
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
    if ok:
        Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).crop((190,110,690,265)).resize((600,186)).save(out/f'hud-{t}s.png')
cap.release()

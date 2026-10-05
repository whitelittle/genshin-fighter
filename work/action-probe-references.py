import sys,json,concurrent.futures
from pathlib import Path
sys.path.insert(0,str(Path('work/video-deps').resolve()))
import yt_dlp,cv2
from PIL import Image,ImageDraw
out=Path('assets/action-probe/references');out.mkdir(parents=True,exist_ok=True)
videos={'keqing':'lf_b7_5oAZk','diluc':'1TfbiDo7N4k','neuvillette':'wFhtWrlveIw','nahida':'6dgE-mC4peA','raidenshogun':'oBrEFOdSfy8','hutao':'2dcaQiLBqEo','navia':'qbwe6FZyTwk','xiao':'kCmvCpYL34U','zhongli':'NRXhkjan52A','yaemiko':'xJ5CzR58TP0'}
def one(item):
 key,vid=item;url='https://www.youtube.com/watch?v='+vid
 try:
  matches=list(out.glob(key+'-official.*'));matches=[p for p in matches if p.suffix in ['.mp4','.webm','.mkv']]
  if not matches:
   with yt_dlp.YoutubeDL({'quiet':True,'noprogress':True,'format':'bestvideo[height<=480][ext=mp4]/bestvideo[height<=480]','outtmpl':str(out/(key+'-official.%(ext)s')),'socket_timeout':18,'retries':1,'extractor_retries':1,'noplaylist':True,'js_runtimes':{'node':{'path':'C:/Users/Cheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'}}}) as y:
    d=y.extract_info(url,download=False)
    if d.get('uploader')!='Genshin Impact':raise RuntimeError('Unexpected uploader: '+str(d.get('uploader')))
    y.download([url])
   matches=[p for p in out.glob(key+'-official.*') if p.suffix in ['.mp4','.webm','.mkv']]
  if not matches:raise RuntimeError('no downloaded video')
  path=matches[0];cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS);seconds=cap.get(cv2.CAP_PROP_FRAME_COUNT)/fps
  shots=[];sheet=Image.new('RGB',(960,6*210),'#101822');dr=ImageDraw.Draw(sheet)
  # Uniform samples are contact-sheet candidates, not yet manually classified attacks.
  for i in range(18):
   t=seconds*(.12+i*.045);cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
   if not ok:continue
   im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));file=out/f'{key}-{i:02d}-{t:.1f}s.jpg';im.save(file,quality=90)
   im.thumbnail((320,180));x=i%3*320;y=i//3*210;sheet.paste(im,(x,y+25));dr.text((x+8,y+6),f'{key} {t:.1f}s',fill='white');shots.append({'seconds':round(t,2),'path':file.as_posix()})
  cap.release();sheet.save(out/(key+'-contact.jpg'),quality=92)
  print('REFERENCE_OK',key,len(shots),flush=True)
  return{'key':key,'url':url,'type':'official gameplay video','path':path.as_posix(),'seconds':seconds,'samples':shots,'classification':'sampled; manual visual review separate'}
 except Exception as e:print('REFERENCE_FAILED',key,str(e)[:160],flush=True);return{'key':key,'url':url,'error':str(e)[:400]}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(one,videos.items()))
(out/'video-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

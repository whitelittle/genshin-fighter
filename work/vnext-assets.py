"""Deterministic component extraction and indexing; source sheets retained intact."""
from pathlib import Path
import sys,json
sys.path.insert(0,'work/video-deps')
import cv2,numpy as np
from PIL import Image,ImageDraw
out=Path('assets/vnext');out.mkdir(parents=True,exist_ok=True)
manifest=[]
def sheet(role,file,definitions,body_height):
 p=Path('assets/fighters')/role/'source'/file
 rgba=np.array(Image.open(p).convert('RGBA'))
 _,labels,stats,_=cv2.connectedComponentsWithStats((rgba[:,:,3]>=220).astype('uint8'),8)
 candidates=[i for i,s in enumerate(stats) if i and s[4]>1500]
 for name,sx,sy,anchor,override in definitions:
  selected=min(candidates,key=lambda i:(stats[i][0]+stats[i][2]/2-sx)**2+(stats[i][1]+stats[i][3]/2-sy)**2)
  x,y,w,h,area=map(int,stats[selected]);crop=rgba[y:y+h,x:x+w].copy()
  crop[:,:,3]=np.where(labels[y:y+h,x:x+w]==selected,255,0)
  path=out/f'{role}-{name}-source.png';Image.fromarray(crop).save(path)
  manifest.append(dict(role=role,pose=name,path=str(path).replace('\\','/'),source=str(p).replace('\\','/'),component=selected,bbox=[x,y,w,h],anchor=[anchor[0]-x,anchor[1]-y],bodyHeight=override or body_height))
names=['walk1','walk2','crouch','crouchGuard','guard','hurt','airHurt','down']
for role,body,seeds,anchors in [
 ('keqing',438,[(215,230),(668,230),(1130,285),(1565,280),(186,635),(620,680),(1080,634),(1480,805)],[(275,453),(680,453),(1150,453),(1590,453),(220,870),(670,866),(1110,770),(1500,870)]),
 ('diluc',380,[(245,233),(690,240),(1140,270),(1560,226),(205,650),(660,690),(1115,622),(1545,812)],[(235,438),(685,440),(1140,440),(1560,440),(210,870),(680,868),(1110,780),(1550,872)])]:
 sheet(role,role+'-status-v2.png',[(n,*s,a,None)for n,s,a in zip(names,seeds,anchors)],body)
sheet('keqing','keqing-skills-v3.png',[
 ('low',480,335,(490,508),None),('jump',1180,260,(1240,493),None),
 ('teleport',420,775,(450,998),None),('qRelease',1170,770,(1150,1007),None)],620)
sheet('keqing','keqing-skills-v2-candidate.png',[
 ('getup',1080,300,(1100,435),438),('eThrow',1460,235,(1470,431),438)],438)
sheet('diluc','diluc-skills-v2-candidate.png',[
 ('low',310,385,(285,511),380),('jump',760,255,(765,503),390),('getup',1290,395,(1260,511),380),
 ('e1',250,765,(260,962),380),('e2',810,745,(780,960),380),('e3Windup',1260,760,(1260,962),380)],380)
sheet('diluc','diluc-burst-v2.png',[
 ('idle2',450,310,(365,585),460),('qCharge',1150,300,(1160,585),460),
 ('qRelease',490,800,(390,1008),400),('e3',1200,790,(1140,994),400)],460)
# Portraits use the approved character masters, with no invented faces.
for role,box in [('keqing',(400,40,670,365)),('diluc',(440,45,705,335))]:
 p=Path('assets/fighters')/role/'source'/('keqing-half-side-v1.png' if role=='keqing' else 'diluc-wolfs-gravestone-v6-candidate.png')
 im=Image.open(p).convert('RGBA').crop(box);im.save(out/f'{role}-portrait-source.png')
(out/'pose-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('indexed',len(manifest),'poses and 2 portraits')

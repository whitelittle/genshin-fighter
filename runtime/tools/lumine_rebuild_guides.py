"""Abstract joint guides, not generated character art. Stable limb lengths and identities."""
from pathlib import Path
import math,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/lumine-rebuild-20261016/guides'
def knee(hip,ankle):
 dx,dy=ankle[0]-hip[0],ankle[1]-hip[1];r=math.hypot(dx,dy);assert r<590
 a=r/2;b=math.sqrt(295**2-a*a)
 return hip[0]+a*dx/r+b*dy/r,hip[1]+a*dy/r-b*dx/r
plans=[('walk_0','left contact',(690,1400),(370,1400)),('walk_1','left support/right passing',(520,1400),(560,1370)),('walk_2','right contact',(370,1400),(690,1400)),('walk_3','right support/left passing',(560,1370),(520,1400))]
def main():
 OUT.mkdir(exist_ok=True);rows=[]
 for key,title,left,right in plans:
  passing=key in ['walk_1','walk_3'];lift=35 if passing else 0
  im=Image.new('RGB',(1024,1536),'#f6f5f0');d=ImageDraw.Draw(im)
  d.line((80,1430,950,1430),fill='#929292',width=5);d.ellipse((410,115-lift,635,360-lift),outline='#969696',width=14)
  d.line((520,365-lift,520,850-lift),fill='#999999',width=35);d.line((430,430-lift,620,455-lift),fill='#999999',width=14)
  joints={}
  for name,hip,ankle,c in [('right',(545,850-lift),right,'#e1843d'),('left',(495,850-lift),left,'#238d9b')]:
   k=knee(hip,ankle);pts=[hip,k,ankle];joints[name]={'hip':hip,'knee':k,'ankle':ankle,'boneLengths':[295,295]}
   d.line([tuple(map(round,v))for v in pts],fill=c,width=24,joint='curve')
   for x,y in pts:d.ellipse((x-16,y-16,x+16,y+16),fill=c)
   d.line((ankle[0]-15,ankle[1]+28,ankle[0]+75,ankle[1]+28),fill=c,width=20)
  im.save(OUT/(key+'.png'));rows.append({'key':key,'phase':title,'joints':joints})
 (OUT/'poses.json').write_text(json.dumps({'scope':'abstract pose reference only, character art not yet validated','left':'near camera cyan','right':'far camera orange','poses':rows},indent=2),encoding='utf-8')
if __name__=='__main__':main()

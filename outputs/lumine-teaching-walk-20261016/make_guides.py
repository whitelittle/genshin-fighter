from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent
for name,legs in {
 'contact-cross': [[(440,890),(570,1140),(680,1428)],[(590,890),(460,1150),(355,1428)]],
 'passing-cross': [[(440,890),(510,1150),(540,1428)],[(590,890),(620,1120),(475,1320)]]
}.items():
 im=Image.new('RGB',(1024,1536),'white');d=ImageDraw.Draw(im)
 d.ellipse((410,115,640,350),outline='gray',width=8)
 d.line([(520,350),(520,750),(515,890)],fill='gray',width=20)
 d.line([(440,890),(590,890)],fill='gray',width=16)
 for i in [1,0]:
  p=legs[i];c=['#df2349','#176ed1'][i];d.line(p,fill=c,width=42)
  for x,y in p:d.ellipse((x-22,y-22,x+22,y+22),fill=c)
  x,y=p[-1];d.line([(x-12,y),(x+70,y)],fill=c,width=22)
 d.line((150,1438,880,1438),fill='#777777',width=3)
 d.text((50,30),'RED = sword-side hip, in FRONT. BLUE = free-hand-side hip, BEHIND.',fill='black')
 im.save(OUT/(name+'-guide.png'))

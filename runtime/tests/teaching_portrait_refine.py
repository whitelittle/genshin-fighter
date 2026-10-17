"""Larger portrait must load hidden in bounded batches and fit the dialogue layout."""
from pathlib import Path
import sys,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-refine-v18-20261017'
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait
ap=argparse.ArgumentParser();ap.add_argument('--target');ap.add_argument('--flush-bottom',action='store_true');args=ap.parse_args()
if args.target:OUT=ROOT/args.target
RuntimeClient.source=OUT/'genshin_fighter.lua'
rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1950,900)),('Mobile',(1600,900)),('Mobile',(2832,1280)),('Mobile',(900,1600))]:
 c=RuntimeClient(device=device,canvas=canvas);c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'movement','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.lesson and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 for _ in range(20):
  assert c.lua('(function()local l=GF_APP().scene.lesson;return not l.avatar.job or not l.avatar.node.act end)()')
  c.step()
 assert c.lua('GF_APP().scene.lesson.avatarReady')
 dims=c.lua('''(function()local a=GF_APP();local l=a.scene.lesson;local n=l.avatar.node;local img=l.avatarImage;local y=a:isMobile() and a.H/2-450 or -a.H/2+112;local left=-math.min(a.W-60,1280)/2;local right=n.x+155;local textLeft=math.max(left+170,right+22);return {img.n,img.w,img.h,n.sx*img.w,n.y-(y-106),textLeft-right,n.x-155+a.W/2}end)()''')
 assert dims[1]==1528 and dims[2]==100 and dims[3]==100
 visibleGap=c.lua('''(function()local a=GF_APP();local l=a.scene.lesson;local n=l.avatar.node;local low=math.huge;for i=1,l.avatar.used do local k=l.avatar.kids[i];if k.act then low=math.min(low,k.y-k.h/2)end end;local y=a:isMobile() and a.H/2-450 or -a.H/2+112;return n.y+low*n.sy-(y-106)end)()''')
 assert abs(dims[4]-310)<.1 and dims[6]>=21.9 and dims[7]>=19,(device,canvas,[dims[i]for i in range(1,8)])
 if args.flush_bottom:assert abs(visibleGap)<.05,(device,canvas,visibleGap)
 else:assert dims[5]>=33.9
 c.render(OUT/'verification'/f'paimon-{device}-{canvas[0]}x{canvas[1]}.png')
 c.press('J');c.run(.2)
 assert not c.lua('GF_APP().scene.lesson.avatar.node.act')
 assert c.max_instr<1000000,c.max_instr
 rows.append({'device':device,'canvas':canvas,'displayWidth':dims[4],'rootPanelGap':dims[5],'visiblePixelPanelGap':visibleGap,'textGap':dims[6],'viewportLeftGap':dims[7],'partialBufferHidden':True,'maxInstructions':c.max_instr})
result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'results':rows,'offlineOnly':True}
(OUT/'verification/portrait-refine.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))

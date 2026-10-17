"""Native event variants through real title/input listeners, without real-device claims."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
def setup(source,device,canvas,early=False):
 RuntimeClient.source=source;c=RuntimeClient(device=device,canvas=canvas)
 wait(c,"GF_APP() and GF_APP().sceneName=='title' and GF_APP().scene.area~=nil")
 if not early:wait(c,"GF_APP().sceneName=='title' and GF_APP().scene.t>.8 and not GF_APP().trans")
 return c
def fire(c,kind,event):
 c.lua("(function()local node=GF_APP().scene.area.node.c;for _,fn in ipairs(node._cursor['"+kind+"'] or {})do fn("+event+")end;return true end)()")
def arrived(c):
 for _ in range(160):
  c.step()
  if c.lua("GF_APP().sceneName=='menu' and not GF_APP().trans"):return True
 return False
rows=[]
for kind,event,label in [('CursorClick','{touchId=0}','click-missing-coordinates'),('CursorClick',"{GetUIPos=function()error('unsupported position')end,touchId=0}",'click-coordinate-error'),('CursorUp','{touchId=0}','release-without-click')]:
 c=setup(args.before,'Mobile',(1600,900));fire(c,kind,event);assert not arrived(c);assert not list(c.H.err.values());rows.append({'version':'before','case':label,'reproducedCannotStart':True})
for device,canvas in [('Mobile',(1600,900)),('Mobile',(900,1600)),('KeyboardAndMouse',(1600,900))]:
 for kind,event,label in [('CursorClick','{touchId=0}','click-missing-coordinates'),('CursorClick',"{GetUIPos=function()error('unsupported position')end,touchId=0}",'click-coordinate-error'),('CursorUp','{touchId=0}','release-without-click')]:
  c=setup(args.after,device,canvas);fire(c,kind,event);fire(c,kind,event);assert arrived(c);assert not list(c.H.err.values());rows.append({'version':'after','device':device,'canvas':canvas,'case':label,'enteredMenuOnce':True})
 c=setup(args.after,device,canvas,True);fire(c,'CursorUp','{touchId=0}');assert arrived(c);rows.append({'version':'after','device':device,'case':'early-release-queued','enteredMenuOnce':True})
 if device=='Mobile':
  c=setup(args.after,device,canvas);c.touch('down',canvas[0]/2,canvas[1]/2);c.step();c.touch('up',canvas[0]/2,canvas[1]/2);assert arrived(c)
  c.render(args.out.parent/f'menu-{canvas[0]}x{canvas[1]}.png');rows.append({'version':'after','device':device,'case':'native-hit-test-tap','enteredMenuOnce':True})
 # Normal spatial handlers must still reject events without coordinates.
 c=setup(args.after,device,canvas);c.lua("(function()local a=GF_APP();a.testSpatialCalls=0;a.testSpatial=a.input:area(0,0,50,50,{up=function()a.testSpatialCalls=a.testSpatialCalls+1 end});for _,fn in ipairs(a.testSpatial.node.c._cursor.CursorUp)do fn({})end;assert(a.testSpatialCalls==0);return true end)()")
 rows.append({'version':'after','device':device,'case':'spatial-area-requires-coordinates','passed':True})
data={'scope':'isolated native UI approximation, not affected-user device','rows':rows,'source':str(args.after.name)};args.out.write_text(json.dumps(data,indent=2),encoding='utf8');print(json.dumps({'cases':len(rows),'beforeReproductions':3,'afterPassed':len(rows)-3}))

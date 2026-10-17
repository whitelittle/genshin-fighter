"""Interrupted prefetch must never publish partly overwritten body geometry."""
from pathlib import Path
import sys,argparse,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/tutorial-render-v16-20261017'
sys.path.insert(0,str(ROOT/'runtime/tests'))
sys.path.insert(0,str(ROOT/'runtime/tools'))
from mock_flow import RuntimeClient,wait
from compact_assets import python_table

def client(device='KeyboardAndMouse'):
 c=RuntimeClient(device=device)
 c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.run(.4)
 return c

CHECK=r"""
function checkBody(v)
 local s=v.front;local img=v.poseImg
 assert(s and not s.job,'published unfinished frame')
 assert(s.used==img.n,'wrong body primitive count')
 -- Compare actual rectangles as a set: walking may permute control assignments.
 local expected={}
 local function id(x,y,w,h,r,g,b,a)return string.format('%.5f,%.5f,%.5f,%.5f,%d,%d,%d,%d',x,y,w,h,r,g,b,a)end
 local function add(t,k)t[k]=(t[k] or 0)+1 end
 for i=1,img.n do
  local o=(i-1)*5;local x,y,w,h,ci=table.unpack(img.bytes,o+1,o+5);local col=img.pal[ci+1]
  add(expected,id((img.ox or 0)-(img.ax or 0)+x+w*.5,(img.oy or 0)+(img.ay or 0)-y-h*.5,w+(img.seam or .08),h+(img.seam or .08),col[1],col[2],col[3],col[4] or 255))
 end
 for i=1,s.used do
  local n=s.kids[i];assert(n.act,'missing body rectangle')
  local ck=n.ck;local a=ck%256;ck=ck//256;local b=ck%256;ck=ck//256;local g=ck%256;local r=ck//256
  local k=id(n.x,n.y,n.w,n.h,r,g,b,a)
  assert((expected[k] or 0)>0,'mixed or stale rectangle in '..tostring(s.key)..' at '..i)
  expected[k]=expected[k]-1
 end
 for _,s2 in ipairs(v.slots)do if s2~=s then assert(not s2.node.act,'two body buffers visible')end end
 return true
end
"""

def interruption(c):
 return c.lua('(function()'+CHECK+r"""
 local v=GF_APP().scene.views[1];local f=v.f
 f.state='idle';f.t=0;for i=1,30 do v:updatePose(520)end
 checkBody(v)
 f.state='walk';v.walkT=0
 for i=1,10 do v:updatePose(520);if v.front.key=='walk_00' then break end end
 assert(v.front.key=='walk_00')
 v:updatePose(1) -- overwrite one rectangle in the old idle slot by prefetch
 f.state='idle';f.t=0
 for i=1,30 do v:updatePose(520)end
 assert(v.front.key=='teaching_master')
 return checkBody(v)
 end)()""")

def physical(device,hz):
 c=client(device)
 # Keyboard input on both desktop and mobile renderer; touch confirmation is covered separately.
 c.lua('(function()'+CHECK+'return true end)()')
 rows=[]
 for repeat in range(3):
  c.key('A',True);c.run(.12)
  c.press('U');c.key('A',False)
  seen=[]
  for tick in range(40 if hz==60 else 20):
   c.step(1/hz)
   c.lua('checkBody(GF_APP().scene.views[1])')
   key=c.lua('GF_APP().scene.views[1].front.key')
   if key not in seen:seen.append(key)
   if repeat==0 and tick in (2,6,12):c.render(OUT/'verification'/f'backdash-{device}-{hz}-{tick}.png')
  assert any(k.startswith('backdash_') for k in seen),seen
  assert c.lua('GF_APP().scene.views[1].front.key')=='teaching_master'
  rows.append(seen)
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'sequences':rows,'everyPublishedRectangleChecked':True,'maxInstructions':c.max_instr}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',action='store_true');args=ap.parse_args()
 RuntimeClient.source=ROOT/('outputs/tutorial-input-v15-20261016/genshin_fighter.lua' if args.baseline else 'outputs/tutorial-render-v16-20261017/genshin_fighter.lua')
 assert interruption(client())
 results=[physical(d,hz) for d in ['KeyboardAndMouse','Mobile'] for hz in (60,30)]
 report={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'interruptedPrefetchExact':True,'offlineOnly':True,'results':results}
 (OUT/'verification/backdash-render.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))

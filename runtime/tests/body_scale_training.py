"""Paired idle/action review through the real FView in the offline training scene.

Pose locking is a diagnostic fixture only. Combat rules and providers are intact.
"""
from pathlib import Path
import sys,json,hashlib,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient,wait
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'runtime/tools'))
from body_scale_review import KEYS,LEGACY
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--keys',default=','.join(KEYS));a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 from lupa.lua53 import LuaRuntime
 before=LuaRuntime(unpack_returned_tuples=True);before.execute(a.baseline.read_text(encoding='utf-8'))
 after=LuaRuntime(unpack_returned_tuples=True);after.execute(a.source.read_text(encoding='utf-8'))
 ba=before.globals().GF_REQUIRE('gf_art');aa=after.globals().GF_REQUIRE('gf_art');reg=after.globals().GF_REQUIRE('gf_character_registry')
 results=[];pixel=[];font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
 for key in a.keys.split(','):
  p=reg.provider(key);groups={g:list(v.frames.values()) for g,v in p.data.groups.items()} if p else dict(LEGACY)
  if key=='nahida':groups['burst']=[f'skill_{i}' for i in range(4,8)]
  poses=set(x for seq in groups.values() for x in seq)
  if p:
   poses.update(p.data.frames.keys())
  for pose in poses:
   b=ba.pose(key,'lo',pose);img=aa.pose(key,'lo',pose);k=img.bodyUnitCorrection or 1
   assert img.n==b.n and len(img.bytes)==len(b.bytes),(key,pose,'count')
   assert abs(img.ax-b.ax*k)<1e-7 and abs(img.ay-b.ay*k)<1e-7,(key,pose,'anchor')
   for n in range(img.n*5):
    assert abs(img.bytes[n+1]-b.bytes[n+1]*(1 if n%5==4 else k))<1e-7,(key,pose,n)
   assert list(img.pal.keys())==list(b.pal.keys())
   for n,col in img.pal.items():assert list(col.values())==list(b.pal[n].values())
   assert aa.pose(key,'lo',pose).w==img.w,(key,pose,'repeat decode')
  pixel.append({'key':key,'images':len(poses),'geometryAndAnchorsScaleTogether':True,'paletteAndRectangleCountUnchanged':True})
  c=BenchClient(a.source);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,key],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
  wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
  c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=100000;for i,f in ipairs(s.sim.f) do f.x=(i==1 and -19000 or 19000);f.y=0;f.face=1;f.state='idle';f.t=0;f.coat=0;f.hitstop=0;f.frozen=0;f.airMove=nil end;return true end)()")
  idle=groups['idle'][0];records=[];animation=[]
  for group in LEGACY:
   seq=groups[group]
   for index,pose in enumerate(seq):
    c.lua(f"(function()local s=GF_APP().scene;s.views[1].poseFor=function()return '{idle}' end;s.views[2].poseFor=function()return '{pose}' end;s.views[1].nextLocomotion=function()return nil end;s.views[2].nextLocomotion=function()return nil end;return true end)()")
    c.run(.25)
    assert c.lua('GF_APP().scene.views[1].front.key')==idle
    assert c.lua('GF_APP().scene.views[2].front.key')==pose,(key,pose)
    for i in [1,2]:
     assert c.lua(f'GF_APP().scene.views[{i}].root.sx')==1
     assert c.lua(f'GF_APP().scene.views[{i}].root.sy')==1
    assert c.lua('GF_APP().scene.zoom')==1
    shot=a.out/f'{key}-{group}-{index}.png';c.render(shot)
    im=Image.open(shot).convert('RGB');ImageDraw.Draw(im).text((460,220),f'左：固定待机  /  右：{group} {index}',font=font,fill='white');im.save(shot)
    if key=='furina' and group in ['idle','walk','back','hurt','getup']:animation.append(im.resize((1000,562)))
    records.append({'action':group,'frame':index,'pose':pose,'shot':shot.name})
   # Revisit the idle frame after each sequence, including mirror, using both buffers.
   c.lua(f"(function()local s=GF_APP().scene;s.sim.f[2].face=-1;s.views[2].poseFor=function()return '{idle}' end;return true end)()")
   c.run(.2);assert c.lua('GF_APP().scene.views[2].front.key')==idle
   assert c.lua('GF_APP().scene.views[2].root.sx')==-1
   c.lua('(function()GF_APP().scene.sim.f[2].face=1;return true end)()')
  # Restore production pose selection and exercise actual input-driven movement.
  c.lua('(function()local s=GF_APP().scene;for _,v in ipairs(s.views) do v.poseFor=nil;v.nextLocomotion=nil end;s.sim.freeze=0;return true end)()')
  c.key('D',True);c.run(.3)
  assert c.lua("GF_APP().scene.sim.f[1].state=='walk'"),(key,'live input walk')
  c.key('D',False);c.run(.2)
  assert c.lua("GF_APP().scene.sim.f[1].state=='idle'"),(key,'live input release')
  c.key('A',True);c.run(.3);c.key('A',False);c.run(.2)
  assert c.lua("GF_APP().scene.sim.f[1].state=='idle'")
  if animation:animation[0].save(a.out/'furina-training.gif',save_all=True,append_images=animation[1:],duration=160,loop=0)
  results.append({'key':key,'sameCharacterTraining':True,'cameraZoom':1,'idleReentryAndMirror':True,'productionInputWalkAndReturn':True,'shots':records,'stats':c.stats()})
  print(key,len(records),'paired training poses',flush=True)
 (a.out/'verification.json').write_text(json.dumps({'mockOnly':True,'diagnosticPoseLock':True,'sourceSha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'pixelGeometry':pixel,'training':results},indent=2),encoding='utf-8')
if __name__=='__main__':main()

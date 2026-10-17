"""Raw desktop bodies are prepared before fight; mobile keeps lazy loading."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import Client,wait
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
rows=[]
for device,key in [('KeyboardAndMouse','clorinde'),('KeyboardAndMouse','nahida'),('Mobile','clorinde')]:
 c=Client(script=a.source,build=False,pools={'img':256,'txt':96,'btn':24},device=device,canvas=(1600,900))
 c.rt.execute("local H=...;H.game.InstantiateClientUIControl=function(index,parent)return H.newControl('image','dynamic',parent,nil)end",c.H)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,key],'mode':'training','cpu':[False,False],'infinite':True})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 jobs=[c.lua(f'GF_APP().scene.prep[{i}].total') for i in (1,2)]
 if device=='KeyboardAndMouse':
  assert jobs[0]>0,(device,key,jobs)
  if key=='clorinde':assert c.lua("(function()for _,f in pairs(GF_REQUIRE('gf_character_registry').provider('clorinde').data.frames)do if not f.bytes then return false end end;return true end)()")
 else:assert jobs==[0,0],jobs
 assert c.lua("GF_REQUIRE('gf_util').compressionStats.blocks")==0
 c.lua("(function()GF_APP().acc=0;return true end)()")
 before=c.lua('GF_APP().frame');c.step(.2);steps=c.lua('GF_APP().frame')-before
 assert steps==(8 if device=='Mobile' else 4),(device,steps)
 assert not list(c.H.err.values()),list(c.H.err.values())
 rows.append({'device':device,'key':key,'preparedFrames':jobs,'stepsOn200msCallback':steps,'LZ4Blocks':0});print(rows[-1],flush=True)
a.out.write_text(json.dumps({'mockOnly':True,'cases':rows},indent=2),encoding='utf-8')

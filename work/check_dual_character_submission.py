"""Packaging closure/privacy audit only, not art or game acceptance."""
from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parents[1]
folders={'ayaka':R/'outputs/v4-one-character-20261010/ayaka-armed-v2','furina':R/'outputs/furina-design-20261010'}
counts={}
def walk(value,folder):
 if isinstance(value,dict):
  if 'file' in value and isinstance(value['file'],str):assert (folder/value['file']).is_file(),value['file']
  for child in value.values():walk(child,folder)
 elif isinstance(value,list):
  for child in value:walk(child,folder)
for name,folder in folders.items():
 for file in ['actions.json','foe-fitted.json']+(['actions-size-candidate.json','helpers.json'] if name=='furina' else []):walk(json.loads((folder/file).read_text(encoding='utf-8')),folder)
 fs=list(folder.rglob('*'));files=[p for p in fs if p.is_file()]
 for p in files:
  assert p.stat().st_size<100*1024*1024,p.name
  if p.suffix in ['.md','.json','.html']:
   text=p.read_text(encoding='utf-8');assert not re.search(r'C:[/\\]+Users[/\\]',text,re.I),p.name
 counts[name]={'files':len(files),'bytes':sum(p.stat().st_size for p in files)}
refs=R/'outputs/dual-character-reference-20261011'
for role in ['raiden','nahida']:
 atlas=json.loads((refs/role/'atlas.json').read_text(encoding='utf-8'))
 for sheet in atlas.values():assert (refs/role/sheet['url']).is_file(),sheet['url']
assert (refs/'action-wrap.css').is_file()
import importlib.util,threading,urllib.request
spec=importlib.util.spec_from_file_location('preview_server',R/'work/serve_original_action_pages.py');server_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(server_module)
server=server_module.ThreadingHTTPServer(('127.0.0.1',0),server_module.Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 for url in ['/actions/furina/size-review.html','/actions/ayaka/actions.json','/actions/raiden/atlas.json','/actions/nahida/atlas.json']:
  with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}'+url) as response:assert response.status==200
finally:server.shutdown();server.server_close();thread.join()
print(json.dumps({'packageChecks':'pass','packages':counts,'atlasClosure':True,'artAcceptance':False},ensure_ascii=False))

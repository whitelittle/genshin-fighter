"""Restore verified upstream files, including complete entries in partial ZIPs."""
from pathlib import Path
import json,hashlib,zipfile,struct,zlib
R=Path(__file__).resolve().parents[1];U=R/'work/three-role-upstream-20261013';O=R/'outputs/three-role-basic-20261013/upstream'
records=[]
def save(base,name,data,archive,expected=None):
 target=(base/name).resolve();assert target.is_relative_to(base.resolve())
 digest=hashlib.sha256(data).hexdigest()
 if expected:assert digest==expected['sha256'] and len(data)==expected['bytes'],name
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert target.read_bytes()==data,name
 else:target.write_bytes(data)
 records.append({'file':target.relative_to(R).as_posix(),'archive':archive,'bytes':len(data),'sha256':digest,'manifestHashVerified':bool(expected)})
m=json.loads((U/'mavuika/work/MAVUIKA_V10_MANIFEST.json').read_text());files={x['path']:x for x in m['files']}
for p in (U/'mavuika/work').glob('*'):
 if p.suffix!='.zip' and '.partial-' not in p.name:continue
 try:
  with zipfile.ZipFile(p) as z:
   for name in z.namelist():
    if name in files:save(O,name,z.read(name),p.name,files[name])
 except zipfile.BadZipFile:
  raw=p.read_bytes();offset=0
  while raw[offset:offset+4]==b'PK\x03\x04' and len(raw)>=offset+30:
   h=struct.unpack_from('<4s5H3I2H',raw,offset);flags,method,crc,compressed,size,nl,el=h[2],h[3],h[6],h[7],h[8],h[9],h[10]
   if flags&8:break
   start=offset+30+nl+el;end=start+compressed
   if end>len(raw):break
   name=raw[offset+30:offset+30+nl].decode('utf-8' if flags&2048 else 'cp437');data=raw[start:end]
   if method==8:data=zlib.decompress(data,-15)
   elif method!=0:break
   assert len(data)==size and zlib.crc32(data)==crc
   if name in files:save(O,name,data,p.name,files[name])
   offset=end
zm=json.loads((U/'zhongli/zhongli-git-manifest.json').read_text());zb=O/'zhongli'
for e in zm['volumes']:
 p=U/'zhongli'/e['name']
 if not p.exists() or p.stat().st_size!=e['bytes']:continue
 assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
 # The final patch intentionally overrides its matching source files, later.
 if 'preview-fix' in p.name:continue
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  for name in z.namelist():
   if not name.endswith('/'):save(zb,name,z.read(name),p.name)
(O/'restoration-files.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified restored files',len(records),'Mavuika',sum(r['manifestHashVerified'] for r in records),'Zhongli',sum(not r['manifestHashVerified'] for r in records))

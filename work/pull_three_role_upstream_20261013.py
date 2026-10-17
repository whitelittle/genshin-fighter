"""Read immutable GitHub branch snapshots without changing the working checkout."""
from pathlib import Path
import subprocess,json,hashlib,os,urllib.parse,urllib.request,concurrent.futures,base64,time
R=Path(__file__).resolve().parents[1];O=R/'work/three-role-upstream-20261013';O.mkdir(exist_ok=True)
SNAPSHOTS={'zhongli':('ab8368dffdd6a31dc133575c3fde0dad216fb3f1',['ZHONGLI_PROGRESS_20261011.md','zhongli-git-manifest.json','restore_zhongli_snapshot.py']),
 'mavuika':('f0ab595f216b627014ce7e0170a12412792d71e2',['work/MAVUIKA_V10_README.md','work/MAVUIKA_V10_HANDOFF.md','work/MAVUIKA_V10_MANIFEST.json','work/restore-mavuika-v10.py'])}
env=dict(os.environ)
for k in list(env):
 if k.lower() in ['http_proxy','https_proxy','all_proxy']:env[k]=''
TOKEN=None
def ranged(url,size):
 step=256*1024
 def chunk(span):
  start,end=span;request=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','User-Agent':'V9-role-source'})
  for attempt in range(3):
   try:
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=45) as response:
     if response.status!=206:raise ValueError('Range unsupported')
     data=response.read(end-start+2)
     assert len(data)==end-start+1
     return data
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
  return b''.join(pool.map(chunk,[(i,min(size-1,i+step-1)) for i in range(0,size,step)]))
def get(key,commit,path,expected=None):
 target=O/key/path;target.parent.mkdir(parents=True,exist_ok=True)
 endpoint='repos/whitelittle/genshin-fighter/contents/'+urllib.parse.quote(path,safe='/')+'?ref='+commit
 if expected and target.exists() and (target.stat().st_size!=expected['bytes'] or hashlib.sha256(target.read_bytes()).hexdigest()!=expected['sha256']):
  partial=target.with_suffix('.partial-'+str(time.time_ns()));assert partial.resolve().is_relative_to(R)
  target.rename(partial)
 if not target.exists():
  binary=path.endswith('.zip')
  if binary:
   entry=subprocess.check_output(['git','ls-tree',commit,path],cwd=R,env=env).decode().strip()
   blob=entry.split()[2];endpoint='repos/whitelittle/genshin-fighter/git/blobs/'+blob
  if binary:
   # Read binary HTTP bytes directly; Windows gh stdout performs text conversion.
   endpoint='repos/whitelittle/genshin-fighter/contents/'+urllib.parse.quote(path,safe='/')+'?ref='+commit
   url='https://raw.githubusercontent.com/whitelittle/genshin-fighter/'+commit+'/'+urllib.parse.quote(path,safe='/')
   req=urllib.request.Request(url,headers={'User-Agent':'role-source-review'})
   if expected and '--ranged' in __import__('sys').argv:data=ranged(url,expected['bytes'])
   else:
    for attempt in range(3):
     try:
      with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=45) as response:data=response.read()
      break
     except Exception:
      if attempt==2:raise RuntimeError('Archive HTTP retrieval failed: '+key+'/'+path) from None
      time.sleep(1)
  else:
   result=subprocess.run(['gh','api',endpoint,'-H','Accept: application/vnd.github.raw+json'],env=env,capture_output=True,timeout=180)
   if result.returncode:raise RuntimeError(key+'/'+path+': '+result.stderr.decode(errors='replace')[:300])
   data=result.stdout
  if binary:assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob
  target.write_bytes(data)
 return {'character':key,'commit':commit,'file':path,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
def main():
 global TOKEN
 jobs=[(key,commit,p) for key,(commit,paths) in SNAPSHOTS.items() for p in paths]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(lambda x:get(*x),jobs))
 (O/'documents.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 print([(r['character'],r['file'],r['bytes']) for r in records])
 if '--archives' in __import__('sys').argv:
  TOKEN=subprocess.check_output(['gh','auth','token'],env=env,text=True).strip()
  jobs=[];expected={}
  zm=json.loads((O/'zhongli/zhongli-git-manifest.json').read_text())
  mm=json.loads((O/'mavuika/work/MAVUIKA_V10_MANIFEST.json').read_text())
  for key,commit,entries,prefix in [('zhongli',SNAPSHOTS['zhongli'][0],zm['volumes'],''),('mavuika',SNAPSHOTS['mavuika'][0],mm['archives'],'work/')]:
   argv=__import__('sys').argv
   if '--only' in argv and key!=argv[argv.index('--only')+1]:continue
   for e in entries:
    p=prefix+e.get('name',e.get('file'));jobs.append((key,commit,p));expected[(key,p)]=e
  def archive(job):
   e=expected[(job[0],job[2])];r=get(*job,expected=e)
   assert r['sha256']==e['sha256'] and r['bytes']==e['bytes'],r['file']
   print('verified',r['character'],r['file'],r['bytes'],flush=True);return r
  with concurrent.futures.ThreadPoolExecutor(max_workers=1 if '--ranged' in __import__('sys').argv else 4) as pool:records.extend(pool.map(archive,jobs))
  (O/'download-verification.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
if __name__=='__main__':main()

"""Create bounded LOCAL commits for retained files. Does not contact a remote."""
from pathlib import Path
import subprocess,json

ROOT=Path(__file__).resolve().parents[1]

def git(*args,**kw):return subprocess.run(['git',*args],cwd=ROOT,check=True,**kw)

def main():
    raw=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT)
    files=[x.decode('utf8') for x in raw.split(b'\0') if x]
    files=[x for x in files if (ROOT/x).is_file()]
    # Preserve source identities; no binary may exceed the host's 100 MiB file limit.
    assert all((ROOT/x).stat().st_size<95*1024**2 for x in files)
    batches=[];batch=[];total=0
    for x in sorted(files):
        n=(ROOT/x).stat().st_size
        if batch and total+n>300*1024**2:batches.append(batch);batch=[];total=0
        batch.append(x);total+=n
    if batch:batches.append(batch)
    receipts=[]
    for i,batch in enumerate(batches,1):
        git('add','--pathspec-from-file=-','--pathspec-file-nul',input=b'\0'.join(x.encode('utf8')for x in batch)+b'\0',stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        git('commit','--quiet','-m',f'保存有效素材、制作源与历史依赖 {i:02d}/{len(batches):02d}',stdout=subprocess.DEVNULL)
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        row={'commit':head,'files':len(batch),'bytes':sum((ROOT/x).stat().st_size for x in batch)}
        receipts.append(row);print(json.dumps(row),flush=True)
    (ROOT/'docs/maintenance/local-batch-commits.json').write_text(json.dumps(receipts,indent=2),encoding='utf8')

if __name__=='__main__':main()

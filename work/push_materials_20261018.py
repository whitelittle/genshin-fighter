"""Resume authorized bounded Git transfers; final master publication is a separate step."""
from pathlib import Path
import subprocess,os,json,time

ROOT=Path(__file__).resolve().parents[1]
BRANCH='refs/heads/codex/material-transfer-20261018'
TARGET='https://github.com/whitelittle/genshin-fighter.git'
APPROVED_HEAD='c8ac0b9f2b592bf7ed28ca347468b6e4474bb8b0'
env=os.environ.copy()
for name in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY']:
    env.pop(name,None)
BASE=['git','-c','http.version=HTTP/1.1','-c','http.postBuffer=524288000',
      '-c','pack.threads=2','-c','pack.windowMemory=64m']

def run(args):
    return subprocess.run(BASE+args,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def remote_tip():
    result=run(['ls-remote',TARGET,BRANCH])
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace')[-1000:])
    rows=result.stdout.decode().split()
    return rows[0] if rows else None

def main():
    # The human explicitly approved this PUBLIC repository and this completed snapshot.
    # Never send uncommitted working files, the take-away archive, or a different tip.
    actual_url=subprocess.check_output(['git','remote','get-url','--push','origin'],cwd=ROOT,text=True).strip()
    actual_head=subprocess.check_output(['git','rev-parse','master'],cwd=ROOT,text=True).strip()
    assert actual_url==TARGET and actual_head==APPROVED_HEAD,(actual_url,actual_head)
    assert not subprocess.check_output(['git','ls-tree','-r',APPROVED_HEAD,'--','_takeaway_20261018'],cwd=ROOT)
    batches=json.loads((ROOT/'docs/maintenance/local-batch-commits.json').read_text(encoding='utf8'))
    tip=remote_tip()
    commits=[row['commit']for row in batches]
    assert tip in commits,('unexpected temporary transfer tip',tip)
    start=commits.index(tip)+1
    receipt=[]
    for i in range(start,len(batches)):
        oid=commits[i]
        assert subprocess.run(['git','merge-base','--is-ancestor',oid,APPROVED_HEAD],cwd=ROOT).returncode==0
        for attempt in range(1,4):
            print(json.dumps({'batch':i+1,'total':len(batches),'attempt':attempt,'status':'uploading','commit':oid}),flush=True)
            result=run(['push','--porcelain',TARGET,oid+':'+BRANCH])
            with (ROOT/'work/material-transfer-20261018.log').open('ab') as log:
                log.write(result.stdout+result.stderr)
            # A successful receive-pack reply already acknowledges this exact ref.
            # Query separately only when transport failed and the outcome is uncertain.
            if result.returncode==0:
                actual=oid
            else:
                try:actual=remote_tip()
                except RuntimeError:actual=None
            if actual==oid:
                receipt.append({'batch':i+1,'commit':oid,'verifiedRemote':True})
                print(json.dumps(receipt[-1]),flush=True)
                break
            if attempt==3:
                raise RuntimeError(result.stderr.decode(errors='replace')[-1500:])
            print(json.dumps({'batch':i+1,'status':'retry','reason':'connection or remote acknowledgment failed'}),flush=True)
            time.sleep(2)
    assert remote_tip()==commits[-1]
    (ROOT/'docs/maintenance/material-transfer-receipt.json').write_text(json.dumps(
        {'initialRemoteTip':tip,'completedThrough':commits[-1],'resumedBatches':receipt,
         'masterUnchangedByThisTool':True},indent=2),encoding='utf8')
    print('All material batches verified on temporary branch; ready to publish complete master.',flush=True)

if __name__=='__main__':main()

"""Restore five damaged local Git blobs from byte-identical working files; no remote writes."""
from pathlib import Path
import json,hashlib,subprocess,shutil,zlib

ROOT=Path(__file__).resolve().parents[1]
mapping=json.loads((ROOT/'docs/maintenance/git-object-paths.json').read_text(encoding='utf8'))
backup=ROOT/'_takeaway_20261018/git-corrupt-objects'
backup.mkdir(exist_ok=True)
rows=[]
for oid,paths in mapping.items():
    data=(ROOT/paths[0]).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid
    obj=(ROOT/'.git/objects'/oid[:2]/oid[2:]).resolve()
    dest=(backup/oid).resolve()
    assert obj.is_relative_to(ROOT/'.git/objects') and dest.is_relative_to(backup)
    old=obj.read_bytes();oldhash=hashlib.sha256(old).hexdigest()
    if dest.exists():
        index=1
        while (backup/(oid+'.retry-'+str(index))).exists():index+=1
        dest=backup/(oid+'.retry-'+str(index))
    shutil.move(str(obj),str(dest))
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==oldhash
    # Native Git re-created a damaged compressed stream for one object.
    # Write the documented loose-object format using Python zlib, then verify with Git.
    raw=b'blob '+str(len(data)).encode()+b'\0'+data
    packed=zlib.compress(raw)
    assert zlib.decompress(packed)==raw
    temp=obj.with_name('tmp_codex_repair_'+oid);temp.write_bytes(packed);temp.replace(obj)
    restored=subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT)
    assert restored==data
    rows.append({'oid':oid,'source':paths[0],'sourceSha256':hashlib.sha256(data).hexdigest(),
        'badCompressedBackup':dest.relative_to(ROOT).as_posix(),
        'badCompressedSha256':oldhash,'restoredExactly':True})
(ROOT/'docs/maintenance/git-object-repair.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print('restored',len(rows),'objects; damaged compressed originals preserved')

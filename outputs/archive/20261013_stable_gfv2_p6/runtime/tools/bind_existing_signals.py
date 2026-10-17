"""Bind stable GF3 protocol names to a current map's actual imported names."""
from pathlib import Path
import argparse,json,hashlib

def bind(source,manifest,correction):
    data=source.read_bytes();build=json.loads(manifest.read_text(encoding='utf-8'))
    assert hashlib.sha256(data).hexdigest()==build['sha256']
    report=json.loads(correction.read_text(encoding='utf-8'))
    bindings={logical:actual for actual,logical in report['bindings'].items()}
    assert len(bindings)==12 and all(name.startswith('GF3') for name in bindings)
    assert b'GF_SIGNAL_BINDINGS={' not in data,'Refuse rebinding an already configured release'
    prefix=('GF_SIGNAL_BINDINGS={'+','.join("['"+k+"']='"+v+"'" for k,v in bindings.items())+'}\n').encode()
    result=prefix+data
    build.update(bytes=len(result),sha256=hashlib.sha256(result).hexdigest(),signalBindings=bindings,sameMapOnly=True,signalSourceSha256=report['sourceSha256'])
    return result,build,bindings

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ['source','build','correction','out']:parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();result,build,bindings=bind(a.source,a.build,a.correction)
    a.out.mkdir(parents=True,exist_ok=True)
    target=a.out/'genshin_fighter.lua';assert not target.exists(),'Refuse overwriting release'
    target.write_bytes(result)
    (a.out/'build.json').write_text(json.dumps(build,ensure_ascii=False,indent=2),encoding='utf-8')
    (a.out/'signal-bindings.json').write_text(json.dumps(bindings,ensure_ascii=False,indent=2),encoding='utf-8')
    print(build['sha256'])

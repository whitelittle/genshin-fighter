"""Check frozen old art and the twelve independently generated attack frames."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
sys.path.insert(0,str(ROOT/'runtime/tools'))
from compact_assets import LuaRuntime,python_table
OUT=ROOT/'outputs/tutorial-attack-v8-20261015'
def load(path):
    rt=LuaRuntime(unpack_returned_tuples=True)
    rt.execute('__loaders={};'+path.read_text(encoding='utf-8'))
    return python_table(rt.globals().__loaders['gf_lumine_training_data']())
old=load(ROOT/'outputs/tutorial-windup-v7-20261015/source/teaching/gf_lumine_training_data.lua')
new=load(OUT/'source/teaching/gf_lumine_training_data.lua')
for key,frame in old['frames'].items():assert new['frames'][key]==frame,key
assert len(old['frames'])==36 and len(new['frames'])==48
digests=[]
for move,durations in [('light2',[8,4,9,9]),('light3',[12,5,12,12]),('heavy',[26,6,15,15])]:
    group=new['groups'][move]
    assert list(group['durations'].values())==durations if isinstance(group['durations'],dict) else group['durations']==durations
    for i in range(4):
        key=f'{move}_{i}'
        assert key in new['frames'] and key not in old['frames']
        digests.append(hashlib.sha256((ROOT/'outputs/lumine-attacks-20261015/fit'/f'{key}.png').read_bytes()).hexdigest())
assert len(set(digests))==12,'new poses unexpectedly duplicated'
mean=sum(f['n'] for f in new['frames'].values())/48
assert mean<1000
report={'clientSha256':hashlib.sha256((OUT/'genshin_fighter.lua').read_bytes()).hexdigest(),'old36FramesUnchanged':True,'new12FittedImagesDistinct':True,'ownGroupsAndTimings':True,'uniqueFrameMean':mean,'peak':new['bodyPeak'],'scope':'asset and source verification; aesthetic and native device acceptance pending'}
(OUT/'verification/attack-art-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))

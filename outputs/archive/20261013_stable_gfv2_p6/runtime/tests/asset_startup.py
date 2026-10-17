"""Both variants prepare before intro; no later general decompression."""
import base64,json,random,sys
from pathlib import Path
from performance import BenchClient
from mock_flow import ROOT,wait
sys.path.insert(0,str(ROOT/'tools'))
from lz4_block import compress,decompress
from lupa.lua53 import LuaRuntime
import argparse,hashlib
ap=argparse.ArgumentParser();ap.add_argument('--compact-source',type=Path,default=ROOT/'dist-compact/genshin_fighter.lua');ap.add_argument('--compressed-source',type=Path,default=ROOT/'dist-compressed/genshin_fighter.lua');ap.add_argument('--out',type=Path,default=ROOT/'verification/asset-startup.json');ap.add_argument('--prefix',default='');args=ap.parse_args()

# Independent incremental Lua path, including overlap and extended lengths.
rt=LuaRuntime(unpack_returned_tuples=True)
rt.execute("__loaders={};"+(ROOT/'source/core/gf_util.lua').read_text(encoding='utf-8'))
u=rt.globals().__loaders['gf_util']()
rng=random.Random(913)
for raw in [b'',b'a',bytes(range(256)),b'a'*1400,b'abcde'*1200,bytes(rng.randrange(256) for _ in range(1600))]:
    # Test payloads have whole rectangles and zero padding.
    raw+=b'\0'*((-len(raw))%5);n=len(raw)//5
    packed=raw+b'\0'*((-len(raw))%3);z=compress(packed)
    assert decompress(z)==packed
    for budget in [4,7,32,9000]:
        img=rt.table_from({'n':n,'codec':'r8','compression':'lz4','zlen':len(z),'d':base64.b64encode(z+b'\0'*((-len(z))%3)).decode()})
        job=u.imageDecoder(img);steps=0
        while not job.step(job,budget):
            steps+=1;assert steps<20000
        assert bytes(job.bytes[i] for i in range(1,len(packed)+1))==packed
bad=b'\x00\x00\x00'
img=rt.table_from({'n':1,'codec':'r8','compression':'lz4','zlen':3,'d':base64.b64encode(bad).decode()})
try:
    job=u.imageDecoder(img)
    while not job.step(job,4):pass
    raise AssertionError('invalid offset accepted')
except Exception as e:
    assert 'invalid LZ4 offset' in str(e)

cases=[]
for label in ['compact','compressed']:
    source=args.compact_source if label=='compact' else args.compressed_source
    c=BenchClient(source)
    wait(c,'GF_APP() and GF_APP().initialAssets')
    c.run(.3);c.render(ROOT/f'verification/{args.prefix}{label}-initial-loading.png')
    wait(c,"GF_APP().sceneName=='intro' and not GF_APP().initialAssets and not GF_APP().poolNext")
    elapsed=c.lua('GF_APP().assetPreparationSeconds')
    blocks=c.lua("GF_REQUIRE('gf_util').compressionStats.blocks")
    assert elapsed>0 and (blocks>0 if label=='compressed' else blocks==0)
    c.lua("(function()local A=GF_REQUIRE('gf_art');for _,key in ipairs({'raidenshogun','nahida','furina','kamisatoayaka'})do local j=A.prepare(key,'lo');assert(j:step(9000))end;return true end)()")
    wait(c,"GF_APP().sceneName=='title' and not GF_APP().trans and GF_APP().scene.logoT and GF_APP().scene.logoT>1")
    c.lua("""(function()local a=GF_APP();local pair=a:getMenuPair();assert(pair[1]~=pair[2])
local R=GF_REQUIRE('gf_roster');assert(a.scene.pair[1]==R[pair[1]].key and a.scene.pair[2]==R[pair[2]].key)
local App=GF_REQUIRE('gf_app');local seen={};for i=1,80 do local t=setmetatable({},App);local p=t:getMenuPair();assert(p[1]~=p[2]);seen[p[1]]=true;seen[p[2]]=true;assert(t:getMenuPair()==p)end
for i=1,#R do assert(seen[i])end;return true end)()""")
    c.lua("(function()GF_APP():go('menu');return true end)()")
    wait(c,"GF_APP().sceneName=='menu' and not GF_APP().poolNext")
    for _ in range(2):
        c.run(6.2)
        assert c.lua("(function()local a=GF_APP();local p=a:getMenuPair();return a.scene.showI==p[1] or a.scene.showI==p[2] end)()")
    c.lua("(function()GF_APP():go('select');return true end)()")
    wait(c,"GF_APP().sceneName=='select' and not GF_APP().poolNext and GF_APP().scene.built==4")
    c.lua("(function()local s=GF_APP().scene;s.cur={3,4};s:confirm(1);s:confirm(2);return true end)()")
    wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    c.run(2)
    for seat in [1,2]:
        c.lua(f"""(function()local s=GF_APP().scene.sim;s.phase='fight';s.freeze=0
for i,p in ipairs(s.f)do s:setState(p,'idle');p.x=i==1 and -15000 or 15000;p.y=0;p.hitstop=0;p.invul=0;p.frozen=0;p.coat=0;p.hp=p.maxhp;p.energy=100 end
assert(s:startBurst(s.f[{seat}]));return true end)()""")
        c.run(3.5)
    assert c.lua("GF_REQUIRE('gf_util').compressionStats.blocks")==blocks
    assert c.lua('GF_SECOND_POOL_STATUS().total')==16000
    c.render(ROOT/f'verification/{args.prefix}{label}-startup-fight.png')
    cases.append({'profile':label,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'mockInitialPreparationSeconds':elapsed,'initialLz4Blocks':blocks,'postStartupLz4Blocks':blocks,'pool':16000,'preparationCompleteBeforeIntro':True,'bothBurstsNoNewDecompression':True})
report={'mockOnly':True,'incrementalCodecVectors':True,'badOffsetRejected':True,'allFourCharactersPrepared':True,'randomDistinctTitlePair':True,'menuRestrictedToTitlePair':True,'cases':cases}
args.out.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

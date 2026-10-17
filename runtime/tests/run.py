"""Regression, baseline differential replay, fitted pixels and mock-client checks."""
from pathlib import Path
import hashlib,json,random,sys
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
sys.path.insert(0,str(REPO/'work/optimization-test-deps'))
sys.path.insert(0,str(ROOT/'tools'))
from lupa.lua53 import LuaRuntime
from build import build
CLIENT_OVERRIDE=None

def runtime(root):
    rt=LuaRuntime(unpack_returned_tuples=True)
    order=json.loads((root/'source/order.json').read_text(encoding='utf-8'))
    rt.execute(CLIENT_OVERRIDE.read_text(encoding='utf-8') if CLIENT_OVERRIDE and root==ROOT else '\n'.join((root/p).read_text(encoding='utf-8') for p in order if p!='source/bootstrap.lua'))
    rt.globals().print=lambda *args:None
    return rt

DUMP='''
function dump(v,seen)
 if type(v)~='table' then return type(v)..':'..tostring(v) end
 seen=seen or {};if seen[v] then return '<cycle>' end;seen[v]=true
 local keys={};for k,x in pairs(v) do if type(x)~='function' then keys[#keys+1]=k end end
 table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
 local out={};for _,k in ipairs(keys) do out[#out+1]=dump(k,seen)..'='..dump(v[k],seen) end
 seen[v]=nil;return '{'..table.concat(out,',')..'}'
end
'''

def logic():
    results={}
    for name in ['checks-d.lua','checks-e.lua','skill-feedback.lua','clorinde-ballistics.lua','clorinde-shot-transition.lua','clorinde-legacy-melee.lua','clorinde-q-fx.lua']:
        rt=runtime(ROOT);rt.execute((ROOT/'tests'/name).read_text(encoding='utf-8'));results[name]=True
    rt=runtime(ROOT);rt.execute(DUMP);rt.execute((ROOT/'tests/furina-timeline.lua').read_text(encoding='utf-8'));results['furinaDeliveredTimeline']=True
    rt=runtime(ROOT);rt.execute(DUMP);rt.execute((ROOT/'tests/ayaka-timeline.lua').read_text(encoding='utf-8'));results['ayakaDeliveredTimeline']=True
    baseline=REPO/'work/github-review-20261009/V3'
    a,b=runtime(baseline),runtime(ROOT)
    for rt in [a,b]:
        rt.execute(DUMP+"S=GF_REQUIRE('gf_sim');R=GF_REQUIRE('gf_roster');GF_REQUIRE('gf_art')")
    rng=random.Random(42011);ticks=0
    for seed in [21,73,905]:
        for rt in [a,b]:rt.execute(f"sim=S.new({{chars={{R[1],R[2]}},rounds=2,time=60,seed={seed}}})")
        for tick in range(1200):
            if tick in [65,210,460,800]:
                for rt in [a,b]:rt.execute("for _,f in ipairs(sim.f) do f.energy=100;sim:setState(f,'idle') end")
            # Protocol 8 intentionally changes Q reach. Keep legacy differential for
            # non-Q combat; six-role Q boundaries and full-state replay have their own tests.
            masks=[rng.choice([0,1,2,4,8,16,32,64,256,512,8|16,4|32,2|16,2|32]) for _ in range(2)]
            for rt in [a,b]:rt.globals().sim.step(rt.globals().sim,*masks)
            for rt in [a,b]:
                rt.execute("comparison=S.copy(sim);comparison.events={};for _,e in ipairs(sim.events) do if e.type~='skillFeedback' then comparison.events[#comparison.events+1]=e end end")
            assert a.eval('dump(comparison)')==b.eval('dump(comparison)'),f'non-Q baseline diverged seed {seed} tick {tick}'
            ticks+=1
    # Snapshot replay must include every mutable field, not only the compact hash.
    b.execute("sim=S.new({chars={R[3],R[1]},rounds=2,time=99,seed=73,training=true,infinite=true})")
    for _ in range(360):b.globals().sim.step(b.globals().sim,rng.choice([0,1,8,16,32,64,128,512]),0)
    b.execute('copy=S.copy(sim)')
    for _ in range(240):
        masks=[rng.choice([0,1,2,4,8,16,32,64,128,512]),rng.choice([0,4,8,16,32])]
        b.globals().sim.step(b.globals().sim,*masks);b.globals().copy.step(b.globals().copy,*masks)
        assert b.eval('dump(sim)')==b.eval('dump(copy)'),'Furina replay diverged'
    # Exercise the old rules now reachable through Furina's roster registration.
    b.execute('''
sim=S.new({chars={R[3],R[1]},rounds=2,time=99,seed=73})
for i=1,60 do sim:step(0,0) end
for _,id in ipairs({'light1','light2','light3','heavy','crouchLight','crouchHeavy','airLight','airHeavy'}) do
 sim:setState(sim.f[1],id:match('^air') and 'air' or 'idle')
 assert(sim:startMove(sim.f[1],id),id)
end
sim:setState(sim.f[1],'idle');assert(sim:startSkill(sim.f[1]))
sim:setState(sim.f[1],'idle');sim.f[1].energy=100;assert(sim:startBurst(sim.f[1]))
local O=GF_REQUIRE('gf_online');assert(O.parseLobby(O.lobbyWord(3,true,true)).char==3)
assert(O.VERSION==8)
local io={now=function()return 0 end};local o=O.new(io)
o.slot=1;o.peers[2]={seen=0,lobby={version=7}};assert(not O.alive(o,2,0),'previous matchmaking protocol must not join')
o.peers[2].lobby.version=8;assert(O.alive(o,2,0))
local M=GF_REQUIRE('gf_mode_arcade');local ar=M.new(R[1].key,{R[1],R[2]},1)
assert(#ar.ladder==1 and ar.ladder[1]==R[2].key)
local args,boss=M.battle(ar,{'mondstadt'});assert(boss and args.cpu[2]==4)
assert(M.recordWin(ar,{maxCombo=4}) and ar.score==1200)
''')
    results.update(baselineNonBurstFullStateTicks=ticks,baselineScope='non-Q rules; presentation feedback events excluded; changed Q boundaries tested separately',furinaSnapshotTicks=240,legacyRulesEnabled=True,rosterProtocolIsolation=True)
    return results

def pixels_and_views():
    import numpy as np
    from PIL import Image
    rt=runtime(ROOT)
    # Reuse the established mock setters and baseline pool tests.
    rt.execute((ROOT/'tests/checks-e.lua').read_text(encoding='utf-8'))
    rt.execute((ROOT/'tests/furina-view.lua').read_text(encoding='utf-8'))
    art=rt.globals().GF_REQUIRE('gf_art')
    receipt=json.loads((ROOT/'furina-import.json').read_text(encoding='utf-8'))
    asset_root=REPO/'outputs/furina-design-20261010'
    for kind in ['bank','script']:
        assert hashlib.sha256((asset_root/receipt['version'][kind]).read_bytes()).hexdigest()==receipt['version'][kind+'Sha256'],'delivery changed; re-export its actual animation data'
    for row in receipt['sources']:
        src=REPO/row['file'];assert hashlib.sha256(src.read_bytes()).hexdigest()==row['imageSha256']
        img=art.pose('furina','lo',row['pose']);original=np.array(Image.open(src).convert('RGBA'))
        if row['facingCorrection']==-1:original=original[:,::-1]
        # Source pixels remain exact; the separately reviewed import-unit correction
        # scales rectangles and anchors together, outside the immutable art receipt.
        correction=img.bodyUnitCorrection or 1
        rebuilt=np.zeros_like(original);ux=row.get('scaleX',row['scale'])*correction;uy=row.get('scaleY',row['scale'])*correction
        assert abs(img.ax-row['anchor'][0]*ux)<1e-8 or row['facingCorrection']==-1
        assert abs(img.ay-row['anchor'][1]*uy)<1e-8
        for n in range(int(img.n)):
            off=n*5;x,y,w,h=[round(img.bytes[off+i]/(ux if i in [1,3] else uy)) for i in range(1,5)]
            col=img.pal[int(img.bytes[off+5])+1]
            rebuilt[y:y+h,x:x+w]=[col[i] for i in range(1,5)]
        assert np.array_equal(original,rebuilt),row['file']
    furina_count=len(receipt['sources'])
    receipt=json.loads((ROOT/'ayaka-import.json').read_text(encoding='utf-8'))
    source=REPO/'outputs/v4-one-character-20261010/ayaka-armed-v2'
    for kind in ['bank','script']:
        assert hashlib.sha256((source/receipt['version'][kind]).read_bytes()).hexdigest()==receipt['version'][kind+'Sha256']
    for row in receipt['sources']:
        original=np.array(Image.open(REPO/row['file']).convert('RGBA'));rebuilt=np.zeros_like(original)
        assert hashlib.sha256((REPO/row['file']).read_bytes()).hexdigest()==row['imageSha256']
        img=art.pose('kamisatoayaka','lo',row['pose']);u=row['scale']*(img.bodyUnitCorrection or 1)
        assert abs(img.ax-row['anchor'][0]*u)<1e-8 and abs(img.ay-row['anchor'][1]*u)<1e-8
        for n in range(int(img.n)):
            off=n*5;x,y,w,h=[round(img.bytes[off+i]/u) for i in range(1,5)];col=img.pal[int(img.bytes[off+5])+1]
            rebuilt[y:y+h,x:x+w]=[col[i] for i in range(1,5)]
        assert np.array_equal(original,rebuilt),row['file']
    rt.execute((ROOT/'tests/ayaka-view.lua').read_text(encoding='utf-8'))
    rt.execute((ROOT/'tests/bitmap-opacity.lua').read_text(encoding='utf-8'))
    return {'exactPixelStates':furina_count,'ayakaExactPixelStates':len(receipt['sources']),'viewBudgetAndFlash':True}


def main():
    import argparse
    global CLIENT_OVERRIDE
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path);ap.add_argument('--out',type=Path,default=ROOT/'verification/logic.json');args=ap.parse_args()
    CLIENT_OVERRIDE=args.source
    manifest={'sha256':hashlib.sha256(args.source.read_bytes()).hexdigest()} if args.source else build()
    results={'logic':logic(),'pixelsAndViews':pixels_and_views(),
        'scope':'Lua 5.3 offline and mock UI; no native device acceptance',
        'sourceReassembled':not bool(args.source),'clientSha256':manifest['sha256']}
    # Check the accepted client against its original source, without writing either.
    base=REPO/'work/github-review-20261009/V3'
    order=json.loads((base/'source/order.json').read_text())
    assert b''.join((base/p).read_bytes() for p in order)==(base/'client/genshin_fighter.lua').read_bytes()
    results['frozenBaselineByteIdentical']=True
    (ROOT/'verification').mkdir(exist_ok=True)
    args.out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

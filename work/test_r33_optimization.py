"""Candidate verification against the supplied r33, not the repository's older bundle."""
from pathlib import Path
import sys
import json
import hashlib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'work/optimization-test-deps'))
sys.path.insert(0, str(ROOT / 'game/tests'))
from lupa.lua53 import LuaRuntime

OUT = ROOT / 'outputs/r33-opt-20261008'
BASE = ROOT / 'work/package-review-20261008/GF_FORMAL_r33/genshin_fighter.lua'

def runtime(path):
    rt = LuaRuntime(unpack_returned_tuples=True)
    rt.execute(path.read_text(encoding='utf-8-sig'))
    rt.execute('require = GF_REQUIRE')
    return rt

POSES = '''
local A=require('gf_art'); local D=require('gf_animation_data'); local E=require('gf_inbetween_data')
local out={}
for _, pair in ipairs({{'raidenshogun','raiden'},{'nahida','nahida'}}) do
 for _,bank in ipairs({D[pair[2]].lo,E.poses[pair[2]].lo}) do
  for pose,img in pairs(bank) do
   if type(img)=='table' and img.n then out[#out+1]={key=pair[1],pose=pose,img=img} end
  end
 end
end
table.sort(out,function(a,b) return a.key..a.pose<b.key..b.pose end)
return out
'''

def pixels(rt):
    a = rt.globals().GF_REQUIRE('gf_art')
    h = hashlib.sha256()
    poses = rt.execute(POSES)
    for p in poses.values():
        img = a.animation(p.key, 'lo', p.pose)
        data = [p.key, p.pose] + [img[k] for k in ('n','ax','ay','u','w','h','seam')]
        data += list(img.bytes.values())
        data += [list(c.values()) for c in img.pal.values()]
        h.update(json.dumps(data).encode())
    return h.hexdigest(), len(poses)

def prepare(rt):
    return dict(rt.execute('''
local A=require('gf_art'); local U=require('gf_util')
local maxInstructions, steps, total = 0,0,0
for _,key in ipairs({'raidenshogun','nahida'}) do
 local j=A.prepare(key,'lo'); total=total+j.total
 repeat
  local n=0; debug.sethook(function() n=n+100 end,'',100)
  local done=j:step(9000)
  debug.sethook(); maxInstructions=math.max(maxInstructions,n); steps=steps+1
 until done
 assert(j.completed==j.total)
 assert(A.prepare(key,'lo').total==0, 'repeat load must reuse baked poses')
end
return {max_prepare_step_instructions=maxInstructions,prepare_steps=steps,prepared_poses=total}
'''))

MATCH = r'''
local S=require('gf_sim'); local AI=require('gf_ai'); local R=require('gf_roster')
local s=S.new({chars={R[1],R[2]},rounds=2,time=99,seed=73})
local a,b=AI.new(s,1,3,74),AI.new(s,2,3,75)
local function dump(v,seen)
 if type(v)~='table' then return type(v)..':'..tostring(v) end
 seen=seen or {}; if seen[v] then return '<cycle>' end; seen[v]=true
 local keys={};for k in pairs(v) do keys[#keys+1]=k end
 table.sort(keys,function(x,y)return tostring(x)<tostring(y) end)
 local out={};for _,k in ipairs(keys) do
  if type(v[k])~='function' then out[#out+1]=dump(k,seen)..'='..dump(v[k],seen) end
 end
 seen[v]=nil; return '{'..table.concat(out,',')..'}'
end
local trace={}; local hits=0
for i=1,2400 do
 s:step(a:tick(),b:tick())
 for _,e in ipairs(s.events) do if e.type=='hit' then hits=hits+1 end end
 if i%60==0 then trace[#trace+1]=dump(s) end
end
return table.concat(trace,'\n'),hits
'''

def main():
    report = {}
    ref = runtime(BASE)
    ref_pixels = pixels(ref)
    ref_trace, hits = ref.execute(MATCH)
    assert hits > 0
    for label in ('A','B'):
        rt=runtime(OUT / f'GF_r33_opt_{label}.lua')
        compressed=sum(1 for p in rt.execute(POSES).values() if p.img.d is not None)
        report[label]=prepare(rt)
        report[label]['compressed_body_poses_before_prepare']=compressed
        # A warmed body animation must not fall back to synchronous decoding.
        rt.execute("require('gf_util').decodeAll=function() error('unexpected body decode after loading') end")
        assert pixels(rt)==ref_pixels
        trace, actual_hits=rt.execute(MATCH)
        assert trace==ref_trace and actual_hits==hits
        report[label].update(pixel_data_identical=True,pose_count=ref_pixels[1],simulation_trace_identical=True,simulation_ticks=2400,hits=hits)
        from test_net import RUN
        net_code=RUN.replace('clients[1].me.char, clients[2].me.char = 3, 9',
                             'clients[1].me.char, clients[2].me.char = 1, 2')
        net_code=net_code.replace('c.me.ready = true', 'c.me.ready = true; c.me.selecting = true')
        net=rt.execute('return function(...) '+net_code+' end')
        network=[]
        for latency,jitter,loss,seed in [(0.02,0.01,0,3),(0.06,0.04,0.05,7),(0.10,0.08,0.10,11)]:
            r=net(latency,jitter,loss,3000,seed)
            assert r[0]=='ok' and r[1] and r[2]>=3 and r[3:6]==(0,0,0) and r[6] and r[7]>1800,r
            network.append({'latency':latency,'jitter':jitter,'loss':loss,'confirmed_frames':r[7],
                            'rollback_replay_equal':r[6],'stalls':r[10]})
        report[label]['network']=network
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()

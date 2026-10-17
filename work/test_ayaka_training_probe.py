"""Lua data, inherited regression, candidate view and rollback checks with mocked UI."""
import json,hashlib
import sys
import numpy as np
from PIL import Image
from v3_runtime_harness import ROOT,BASE,load_runtime
sys.path.insert(0,str(ROOT/'work/github-review-20261009/game/tools'))
import artlib
OUT=ROOT/'outputs/v4-one-character-20261010/ayaka-training-probe'
results={}
for name in ['checks-d.lua','checks-e.lua']:
    rt=load_runtime(OUT);logs=[]
    rt.globals().print=lambda *args:logs.append(' '.join(str(x) for x in args))
    code=(BASE/'tests'/name).read_text(encoding='utf-8')
    if name=='checks-e.lua':
        code+='''
local P=GF_REQUIRE('gf_candidate_ayaka');local c=P.character
local j=Art.prepare(c.key,'lo');local steps=0
repeat steps=steps+1;assert(steps<500) until j:step(9000)
assert(j.completed==j.total and Art.prepare(c.key,'lo').total==0)
local cs=Sim.new({chars={c,R[1]},rounds=2,time=99,seed=73})
local ca={frame=0,t=0,scene={sim=cs},layers={front={}}}
local cv=V.new(ca,{body={},fx={},ghost={},shadow={}},cs.f[1],'lo')
local reserved=0;repeat reserved=reserved+1;assert(reserved<30)until cv:reserveBody(320)
assert(#cv.slots[1].kids==1078 and #cv.slots[2].kids==1078)
for _,state in ipairs({'idle','walk','back','crouch','jumpsq','air','land','block','hit','airhit','down','getup'})do
 cv.f.state=state;cv.f.coat=0;cv.f.frozen=0;cv.f.hitstop=0
 for tick=1,100 do
  cs.tick=tick;ca.frame=tick;ca.t=tick/60;cv.f.t=tick
  local before=G.N.bitmap or 0;cv:draw(320)
  assert((G.N.bitmap or 0)-before<=320*5,'candidate body slice budget')
  assert(#cv.slots[1].kids==1078 and #cv.slots[2].kids==1078,'candidate body grows during draw')
 end
 assert(cv.front~=nil and cv.root.sx==cv.f.face and cv.root.sy==1,'candidate grounded no extra squash')
end
cv.f.state='idle';cv.f.t=0;for i=1,12 do cv:draw(320)end
local published=cv.front.key;cv.f.state='hit';cv:onHit({heavy=false});cv:draw(1)
assert(cv.front.key==published and cv.flash.used==cv.poseImg.n,'candidate flash uses published frame')
cs=Sim.new({chars={c,R[1]},rounds=2,time=99,seed=73})
for i=1,60 do cs:step(0,0)end
assert(not cs:startMove(cs.f[1],'light1') and not cs:startSkill(cs.f[1]) and not cs:startBurst(cs.f[1]))
cs:tryThrow(cs.f[1]);assert(cs.f[1].state=='idle','unfinished candidate throw disabled')
local log={}
for i=1,360 do log[i]={(i%120<40 and 8 or i%120<80 and 4 or 2),(i%100==0 and 16 or 0)};cs:step(log[i][1],log[i][2])end
local copy=Sim.copy(cs)
local function dump(v,seen)
 if type(v)~='table' then return type(v)..':'..tostring(v)end
 seen=seen or {};if seen[v]then return '<cycle>'end;seen[v]=true
 local keys={};for k,x in pairs(v)do if type(x)~='function'then keys[#keys+1]=k end end
 table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
 local out={};for _,k in ipairs(keys)do out[#out+1]=dump(k,seen)..'='..dump(v[k],seen)end
 seen[v]=nil;return '{'..table.concat(out,',')..'}'
end
for i=1,180 do cs:step(log[i][1],log[i][2]);copy:step(log[i][1],log[i][2]);assert(cs:hash()==copy:hash() and dump(cs)==dump(copy),'candidate full-state snapshot replay')end
-- Baseline-specific attacks must remain enabled under candidate wrappers.
local bs=Sim.new({chars={R[1],R[2]},rounds=2,time=99,seed=73});for i=1,60 do bs:step(0,0)end
assert(bs:startMove(bs.f[1],'light1') and bs:startMove(bs.f[2],'light1'))
print('PASS candidate 36 poses preparation, body buffers, slice budget, current-image flash, disabled unfinished actions, snapshot replay, baseline attacks')
'''
    rt.execute(code)
    results[name]={'passed':True,'assertions_log':logs}
receipt=json.loads((OUT/'build-receipt.json').read_text(encoding='utf-8'))
art=rt.globals().GF_REQUIRE('gf_art');u=receipt['scale_design_units_per_pixel']
for item in receipt['provenance']:
    img=art.pose('kamisatoayaka','lo',item['pose'])
    original=Image.open(ROOT/item['image']).convert('RGBA')
    rects=[]
    for n in range(int(img.n)):
        off=n*5;rects.append(tuple(round(img.bytes[off+j]/u) for j in range(1,5))+(int(img.bytes[off+5]),))
    palette=[[int(c[k]) for k in range(1,5)] for c in img.pal.values()]
    rebuilt=artlib.render(rects,palette,*original.size)
    assert np.array_equal(np.asarray(original),np.asarray(rebuilt)),item['pose']
client=OUT/'GF_V4_Ayaka_Training_Probe.lua'
order=json.loads((OUT/'source/order.json').read_text(encoding='utf-8'))
assert client.read_bytes()==b''.join((OUT/p).read_bytes() for p in order)
result={'checks':results,'source_reassembly_passed':True,'client_sha256':hashlib.sha256(client.read_bytes()).hexdigest(),
        'scope':'Lua logic/data/view methods with mocked native UI; not full simulator screenshots or true-device testing',
        'native_device_tested':False,'formal_role_accepted':False,'candidate_36_decoded_target_frames_exact':True,
        'full_state_snapshot_replay_ticks':180}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'baseline_d_passed':True,'baseline_e_passed':True,'candidate_checks_passed':True,'source_reassembly_passed':True,'device_tested':False}))

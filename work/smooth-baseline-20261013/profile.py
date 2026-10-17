from compare import *
from lupa.lua53 import LuaRuntime

def new(script,baseline=False):
    c=Mock(script=script,build=False,pools={'img':10000 if baseline else 256,'txt':160 if baseline else 96,'btn':24},device='Mobile')
    c.env.GF_SETTINGS=c._to_lua({'quality':'lo'})
    c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':['raidenshogun','nahida'],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
    wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and not GF_APP().trans");c.run(2)
    return c

current=ROOT/'outputs/all-codec-comparison-20261012_053101/保留的普通可读版.lua'
old=OLD/'game/dist/genshin_fighter.lua'
def main():
    syntax={}
    rt=LuaRuntime(unpack_returned_tuples=True)
    for p in [OUT/'working-source.lua',ROOT/'runtime/dist/genshin_fighter.lua',current,old,*sorted((ROOT/'outputs/all-codec-comparison-20261012_053101').glob('gpt*.lua'))]:
        ok,error=rt.eval("function(s)local fn,e=load(s);return fn~=nil,e end")(p.read_text(encoding='utf-8'))
        syntax[p.relative_to(ROOT).as_posix()]={'valid':ok,'error':error}
    write('syntax-identities.json',syntax)

    assets={}
    for label,script,baseline in [('baseline',old,True),('current',current,False)]:
        c=new(script,baseline)
        summary=c.lua("""(function()
    local out={};local Art=GF_REQUIRE('gf_art')
    local function collect(bank)
     local r={count=0,totalRects=0,peakRects=0,minW=1e9,maxW=0,minH=1e9,maxH=0,paletteEntries=0}
     for k,img in pairs(bank) do if type(img)=='table' and img.n then
      r.count=r.count+1;r.totalRects=r.totalRects+img.n
      if img.n>r.peakRects then r.peakRects=img.n;r.peakFrame=k end
      r.minW=math.min(r.minW,img.w or 0);r.maxW=math.max(r.maxW,img.w or 0)
      r.minH=math.min(r.minH,img.h or 0);r.maxH=math.max(r.maxH,img.h or 0)
      r.paletteEntries=math.max(r.paletteEntries,#(img.pal or bank.pal or {}))
     end end return r end
    for _,key in ipairs({'raidenshogun','nahida','furina','kamisatoayaka'}) do
     local row={};out[key]=row;local m=Art.mod(key)
     if m.lo then row.legacyLo=collect(m.lo) end;if m.hi then row.legacyHi=collect(m.hi) end
    end
    return out end)()""")
        def plain(v):return {str(k):plain(x) if hasattr(x,'items') else x for k,x in v.items()}
        assets[label]=plain(summary)
        if not baseline:
            banks=c.lua("""(function()
    local out={};local A=GF_REQUIRE('gf_animation_data');local I=GF_REQUIRE('gf_inbetween_data');local E=GF_REQUIRE('gf_animation_effects')
    local banks={raidenBody=A.raiden.lo,nahidaBody=A.nahida.lo,raidenInbetween=I.poses.raiden.lo,nahidaInbetween=I.poses.nahida.lo,
    furinaAll=GF_REQUIRE('gf_furina_data').frames,ayakaAll=GF_REQUIRE('gf_ayaka_data').frames,
    raidenEffects=E.raiden,nahidaEffects=E.nahida,raidenEye=GF_REQUIRE('gf_raiden_eye_r31').lo}
    for name,bank in pairs(banks) do local r={count=0,totalRects=0,peakRects=0,maxW=0,maxH=0,paletteEntries=0};out[name]=r
    for k,img in pairs(bank) do if type(img)=='table' and img.n then r.count=r.count+1;r.totalRects=r.totalRects+img.n
    if img.n>r.peakRects then r.peakRects=img.n;r.peakFrame=k end
    r.maxW=math.max(r.maxW,img.w or 0);r.maxH=math.max(r.maxH,img.h or 0);r.paletteEntries=math.max(r.paletteEntries,#(img.pal or bank.pal or {})) end end end
    return out end)()""")
            assets['currentAnimationBanks']=plain(banks)
    write('asset-counts.json',assets)

    c=new(current)
    # Read the meter at function boundaries; nested totals overlap and must not be summed.
    c.rt.execute("""local H,env=...;local s=env.GF_APP().scene;H.profile={}
    local function wrap(o,k,label)
     local fn=o[k];if not fn then return end
     o[k]=function(self,...)local start=H.instr;local results=table.pack(fn(self,...));local n=H.instr-start
     local p=H.profile[label] or {sum=0,max=0,calls=0};H.profile[label]=p;p.sum=p.sum+n;p.max=math.max(p.max,n);p.calls=p.calls+1
     return table.unpack(results,1,results.n) end
    end
    for _,k in ipairs({'tick','draw','drawBurstBackdrop','events','burstStart','cineDraw','camera','drawProj'}) do wrap(s,k,'scene.'..k) end
    for i,v in ipairs(s.views) do for _,k in ipairs({'draw','updatePose','drawAnimatedFx','drawCapture'}) do wrap(v,k,'view'..i..'.'..k) end end
    local B=env.GF_REQUIRE('gf_gfx').Bitmap
    for _,k in ipairs({'step','drawMany','draw'}) do wrap(B,k,'bitmap.'..k) end
    """,c.H,c.env)
    c.lua("(function()local s=GF_APP().scene;local sim=s.sim;sim.phase='fight';sim.freeze=0;for i,f in ipairs(sim.f)do f.x=i==1 and -10000 or 10000;f.y=0;f.face=i==1 and 1 or -1;f.energy=100;f.hitstop=0;f.invul=0;sim:setState(f,'idle')end;assert(sim:startBurst(sim.f[1]));return true end)()")
    frames=[]
    for t in range(210):
        c.H.profile=c.rt.table();c.max_instr=0;c.step()
        if t in (24,40,70):c.render(OUT/f'current-raiden-Q-callback-{t}.png')
        frames.append({'callback':t,'instructions':c.max_instr,'calls':c.calls[-1],'phase':c.lua('GF_APP().scene.sim.f[1].state'),'actionTick':c.lua('GF_APP().scene.sim.f[1].t'),
                       'functionInstructions':{k:dict(v.items()) for k,v in c.H.profile.items()}})
    write('Q-function-profile.json',{'scope':'instrumented mock, overhead included; nested function totals overlap','largestInstructions':sorted(frames,key=lambda x:x['instructions'],reverse=True)[:8]})
    print(json.dumps({'syntax':syntax,'Qpeak':max(x['instructions'] for x in frames)},ensure_ascii=False),flush=True)


if __name__ == '__main__': main()

from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if "GF_RELEASE_ID='dual-scale-throw-r22'" not in s:
    s=s.replace("key=='raidenshogun' and (aliases[pose] or pose):match('^qburst_')", "not img.baked and key=='raidenshogun' and (aliases[pose] or pose):match('^qburst_')")
    needle='    return img\nend\nfunction A.pose'
    baked="""    if img and not img.baked then
        local u=img.u;local bytes={}
        for i=1,#img.bytes,5 do
            for k=0,3 do bytes[i+k]=img.bytes[i+k]*u end
            bytes[i+4]=img.bytes[i+4]
        end
        img.bytes=bytes;img.ax=img.ax*u;img.ay=img.ay*u;img.w=img.w*u;img.h=img.h*u
        img.seam=0.08*u;img.u=1;img.baked=true
    end
    return img
end
function A.pose"""
    assert needle in s;s=s.replace(needle,baked,1)
    s=s.replace('local sw, sh = w + SEAM, h + SEAM', 'local seam=img.seam or SEAM\n        local sw, sh = w + seam, h + seam')
    s=s.replace('(w + SEAM) * s, (h + SEAM) * s', '(w + (img.seam or SEAM)) * s, (h + (img.seam or SEAM)) * s')
    s=s.replace('bmp:drawMany({{img = img, ox = 0, oy = 0, s = 1}})', 'bmp:drawMany({{img = img, ox = 0, oy = 0, s = 5.2}})')
    s=s.replace(':scale(5.2, 5.2):on(true)', ':scale(1, 1):on(true)')
    s=s.replace('self.animFx:draw(img,tostring(idx));local scale=width/img.w', 'local scale=width/img.w\n    self.animFx:drawMany({{img=img,ox=0,oy=0,s=scale}})')
    s=s.replace(':scale(scale*f.face,scale):on(true)', ':scale(f.face,1):on(true)')
    s=s.replace('function S:tryThrow(p)', """function S:throwRange(p)
    return math.max(K.throw.range*C,math.floor(70*C*p.size)+math.floor(70*C*p.foe.size)+18*C)
end
function S:tryThrow(p)""")
    s=s.replace('dist <= th.range * C and grounded(d)', 'dist <= self:throwRange(p) and grounded(d)')
    s=s.replace('abs(p.foe.x - p.x) <= K.throw.range * C', 'abs(p.foe.x - p.x) <= self:throwRange(p)')
    s=s.replace("        self:setState(d, 'thrown')\n        d.vx, d.vy = 0, 0", """        self:setState(d, 'thrown')
        p.stats.throws=(p.stats.throws or 0)+1
        d.face=-p.face
        d.vx, d.vy = 0, 0""")
    start=s.index("    elseif st == 'throw' then\n        local d = p.foe")
    end=s.index("    elseif st == 'hit' or st == 'block'",start)
    old=s[start:end];new=old.replace('p.t == 10','p.t == 30').replace('d.vy = 16 * C', 'd.vy = -12 * C\n            d.y=math.max(d.y,40*C)').replace('p.t < 10','p.t < 30').replace('p.face * 90 * C', 'p.face * 120 * C').replace('            d.y = 0', """            d.t=p.t;d.face=-p.face
            local lift=p.t<12 and 0 or p.t<24 and (p.t-12)/12 or (30-p.t)/6
            d.y=math.max(0,lift)*160*C""").replace('p.t >= 34','p.t >= 50')
    s=s[:start]+new+s[end:]
    s=s.replace("frameName('throw',t<5 and 0 or t<10 and 1 or t<20 and 2 or 3)", "frameName('throw',t<12 and 0 or t<24 and 1 or t<36 and 2 or 3)")
    s=s.replace("frameName('victim',t<5 and 0 or t<10 and 1 or 2)", "frameName('victim',t<12 and 0 or t<24 and 1 or 2)")
    s=s.replace("elseif st == 'hit' or st == 'thrown' then", "elseif st == 'thrown' then\n        tilt,ox=0,0\n    elseif st == 'hit' then")
    ai="""    if p.y<=0 and foe.y<=0 and foe.invul==0 and dist*C<=sim:throwRange(p)
        and (foe.state=='idle' or foe.state=='walk' or foe.state=='back' or foe.state=='block' or foe.state=='crouch')
        and sim.tick>=(self.throwReadyAt or 0) and self:rand()<0.05 then
        self.throwReadyAt=sim.tick+240;return self:edge(B.TH)
    end

"""
    s=s.replace('    if attacking(o) and dist < 380',ai+'    if attacking(o) and dist < 380')
    s=s.replace("GF_RELEASE_ID='dual-burst-polish-r21'", "GF_RELEASE_ID='dual-scale-throw-r22'")
j['meta']['name']='雷电与纳西妲 · 大招释放与投技 r22';j['assets']['scripts'][0]['source']=s
p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(ROOT/'project-inputs/dual-character.lua').write_text(s)
print('Prepared r22: baked geometry scale, contact throw range and visible grab/lift/slam')

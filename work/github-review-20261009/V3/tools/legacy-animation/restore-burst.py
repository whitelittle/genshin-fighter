from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'dist/projects/raiden-nahida.json'
project=json.loads(path.read_text());source=project['assets']['scripts'][0]['source']
original=json.loads((ROOT/'dist/projects/confirmed-v15.json').read_text())['assets']['scripts'][0]['source']
def body(text,name):
    m="__loaders['"+name+"'] = function()";a=text.index(m)+len(m);b=text.find("__loaders['",a)
    return text[a:b].rsplit('\nend',1)[0]
def replace(name,text):
    global source
    m="__loaders['"+name+"'] = function()";a=source.index(m)+len(m);b=source.find("__loaders['",a)
    source=source[:a]+'\n'+text+'\nend\n'+source[b:]
if "function S:drawBurstBackdrop()" not in source:
    sim=body(source,'gf_sim');base=body(original,'gf_sim')
    a=sim.index('function S:startBurst(p)');b=sim.index('function S:tryThrow(p)',a)
    start=base[base.index('function S:startBurst(p)'):base.index('function S:tryThrow(p)')]
    start=start.replace('    p.invul = 70\n    self.freeze = 56', """    p.cinematicConfirmed=false
    p.invul = p.key=='raidenshogun' and 24 or 70
    self.freeze = p.key=='raidenshogun' and 0 or 56""")
    start=start.replace("self:emit({type = 'burst',", "self:emit({type = p.key=='raidenshogun' and 'burstAttempt' or 'burst',")
    sim=sim[:a]+start+sim[b:]
    a=sim.index('function S:burstUpdate(p)');b=sim.index('function S:physics(p)',a)
    update=base[base.index('function S:burstUpdate(p)'):base.index('function S:physics(p)')]
    update=update.replace('function S:burstUpdate(p)', """function S:burstUpdate(p)
    if p.key=='raidenshogun' then
        local t,d,bu=p.t,p.foe,p.move
        local per={damage=bu.damage//bu.hits,hitstun=80,blockstun=18,push=3,level='mid',energy=0,shake=12,launch=22}
        if t==2 then
            if math.abs(d.x-p.x)<=bu.range*C and d.y<420*C then
                local result=self:hit(p,d,per,'burst',{unblockable=false})
                if result=='hit' then
                    p.cinematicConfirmed=true;p.invul=160
                    d.y=math.max(d.y,130*C);d.vx=0
                    self.freeze=56;self.freezeBy=p.id
                    self:emit({type='burst',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
                    self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
                end
            end
        end
        if p.cinematicConfirmed then
            -- Hold the caught opponent in the cinematic until the final launch.
            if t<70 then d.y=math.max(d.y,130*C);d.vx=0 end
            if t==35 or t==70 then
                per.launch=t==70 and 28 or 18;per.knockdown=t==70
                self:hit(p,d,per,'burst',{unblockable=true})
                self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
            end
            if t>=100 then p.cinematicConfirmed=false;self:setState(p,p.y>0 and 'air' or 'idle') end
        elseif t>=32 then self:setState(p,p.y>0 and 'air' or 'idle') end
        return
    end""")
    sim=sim[:a]+update+sim[b:];replace('gf_sim',sim)
    art=body(source,'gf_art').replace("function A.portrait(key) return A.animation(key,'hi','basic_0') or picture(key, 'portrait') end", "function A.portrait(key) return picture(key, 'portrait') end");replace('gf_art',art)
    view=body(source,'gf_fview')
    view=view.replace("if f.key=='raidenshogun' then return frameName('qburst',t<9 and 0 or t<16 and 1 or t<20 and 2 or 3) end", """if f.key=='raidenshogun' then
            if not f.cinematicConfirmed then return frameName('qburst',0) end
            if t<16 then return frameName('qburst',t<9 and 1 or 2) end
            local beat=(t-16)%35;return frameName('qburst',beat<12 and 2 or 3)
        end""")
    a=view.index("            if t<20 then idx,width,offset,up=5,250,0,110")
    b=view.index("        else idx,width,offset,up=9,630,0,0 end",a)
    view=view[:a]+"""            if f.cinematicConfirmed then
                if t<16 then idx,width,offset,up=5,250,0,110
                elseif t<76 then idx,width,offset,up=9,640,200,10
                elseif t<94 then idx,width,offset,up=10,460,200,0 end
            end
"""+view[b:];replace('gf_fview',view)
    scene=body(source,'gf_scene_fight')
    scene=scene.replace('        self.annL = G.layer(app.layers.top)', '        self.annL = G.layer(app.layers.top)\n        self.burstBg = G.layer(app.layers.back)')
    scene=scene.replace('    self.cine = {p = e.p,', '    self.banners={};self.annL:clear()\n    self.cine = {p = e.p,')
    scene=scene.replace('    self.zoomPunch = 0.12', "    self.zoomPunch = p.key=='raidenshogun' and 0 or 0.12")
    scene=scene.replace('    if self.cine then\n        local p = sim.f[self.cine.p]', "    if self.cine and self.cine.char.key~='raidenshogun' then\n        local p = sim.f[self.cine.p]")
    marker='function S:draw()\n    local app = self.app'
    bg="""function S:drawBurstBackdrop()
    local L=self.burstBg;if not L then return end
    L:begin()
    local p
    for _,f in ipairs(self.sim.f) do if f.key=='raidenshogun' and f.state=='burst' and f.cinematicConfirmed then p=f end end
    if p then
        local W,H=self.app.W,self.app.H
        L:rect(0,0,W+40,H+40,{10,5,28},0.94)
        L:shape(G.ELLIPSE,0,70,W*0.8,H*0.7,{88,35,150},0.7,0,0.4)
        L:shape(G.ELLIPSE,0,90,600,190,{120,58,205},0.7)
        L:shape(G.ELLIPSE,0,90,150,150,{205,155,255},0.8)
        L:shape(G.ELLIPSE,0,90,55,120,{25,8,50},1)
        for i=1,7 do
            local x=-W/2+i*W/8
            L:rect(x,0,5,H,{165,95,250},0.3,-22+(i%3)*12)
        end
    end
    L:finish()
end

"""
    scene=scene.replace(marker,bg+marker)
    scene=scene.replace("    local urgent = self.sim.phase ~= 'intro'", "    self:drawBurstBackdrop()\n    local urgent = self.sim.phase ~= 'intro'")
    scene=scene.replace('    if self.hud then self.hud:free() end', '    if self.hud then self.hud:free() end\n    if self.burstBg then self.burstBg:free() end')
    replace('gf_scene_fight',scene)
    source=source.replace("GF_RELEASE_ID='dual-ai-demo-r19'", "GF_RELEASE_ID='dual-burst-cinema-r20'")
# The Q sheet is taller than the neutral sheet; preserve the body's apparent size.
source=source.replace("if img then img.pal=bank.pal end", "if img then img.pal=bank.pal; if key=='raidenshogun' and (aliases[pose] or pose):match('^qburst_') then img.originalU=img.originalU or img.u;img.u=img.originalU*0.77 end end")
project['meta']['name']='雷电与纳西妲 · 大招演出 r20';project['assets']['scripts'][0]['source']=source
path.write_text(json.dumps(project,ensure_ascii=False,separators=(',',':')))
(ROOT/'project-inputs/dual-character.lua').write_text(source)
print('Prepared r20: hit-confirmed Raiden cinematic; original portraits; Nahida burst unchanged')

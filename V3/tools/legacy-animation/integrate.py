from pathlib import Path
import json,re,shutil
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'dist/projects/dual-pool.json';archive=json.loads(p.read_text());source=archive['assets']['scripts'][0]['source'];(ROOT/'dist/projects/confirmed-v15.json').write_text(p.read_text())
def body(name):
 m="__loaders['"+name+"'] = function()";i=source.index(m)+len(m);j=source.index("__loaders['",i);return source[i:j].rsplit('\nend',1)[0]
def replace(name,text):
 global source
 m="__loaders['"+name+"'] = function()";i=source.index(m);j=source.index("__loaders['",i+len(m));source=source[:i]+m+'\n'+text+'\nend\n'+source[j:]
gfx=body('gf_gfx').replace('if not nd.act then nd.act = true; c:SetActive(true); writes = writes + 1 end','if not nd.act then nd.act = true; c:SetVisible(true); c:SetActive(true); writes = writes + 2 end');replace('gf_gfx',gfx)
art=body('gf_art');art=art.replace('function A.pose(key, tier, pose)','''local animations
function A.animation(key,tier,pose)
    if key ~= 'raidenshogun' and key ~= 'nahida' then return nil end
    animations = animations or require('gf_animation_data')
    local char=animations[key=='raidenshogun' and 'raiden' or 'nahida']
    local bank=char and char[tier]
    local img=bank and bank[pose]
    if img then img.pal=bank.pal end
    return img
end
function A.pose(key, tier, pose)
    local animated=A.animation(key,tier,pose)
    if animated then return animated end''')
art=art.replace('function A.silhouette(key, pose)','''function A.silhouette(key, pose)
    local animated=A.animation(key,'lo',pose)
    if animated then return animated end''');replace('gf_art',art)
fview=body('gf_fview');fview=fview.replace('function V:poseFor()','''local function frameName(sheet,index) return sheet .. '_' .. index end
local function attackPose(m,t,id)
    local sheet,frames='light',{0,1,2,3}
    if id=='light2' then frames={4,5,6,7}
    elseif id=='light3' then sheet='heavy'
    elseif id=='heavy' then sheet,frames='heavy',{4,5,6,7}
    elseif id=='crouchLight' then sheet,frames='air',{0,0,1,0}
    elseif id=='crouchHeavy' then sheet,frames='air',{2,2,3,2}
    elseif id=='airLight' then sheet,frames='air',{4,4,5,4}
    elseif id=='airHeavy' then sheet,frames='air',{6,6,7,6} end
    local phase=t<m.startup and (t<m.startup/2 and 1 or 2) or t<m.startup+m.active and 3 or 4
    return frameName(sheet,frames[phase])
end
function V:animatedPose()
    local f=self.f;local st,t=f.state,f.t
    if f.airMove then return attackPose(f.airMove,f.airT or 0,f.airMoveId or 'airLight') end
    if st=='idle' or st=='intro' then return frameName('basic',self.app.frame//25%2) end
    if st=='walk' or st=='back' then local i=self.walkT//8%6;return frameName('basic',st=='back' and 7-i or 2+i) end
    if st=='crouch' or st=='jumpsq' or st=='land' then return frameName('guard',t<5 and 0 or 1) end
    if st=='air' then return frameName('move',f.vy>0 and 1 or f.vy==0 and 2 or 3) end
    if st=='dash' then return frameName('move',t<5 and 4 or 5) end
    if st=='backdash' then return frameName('move',t<5 and 6 or 7) end
    if st=='attack' then return attackPose(f.move,t,f.moveId) end
    if st=='skill' then local startup=f.move.startup;return frameName('skill',t<startup/2 and 0 or t<startup and 1 or t<startup+6 and 2 or 3) end
    if st=='burst' then
        if f.key=='raidenshogun' then return frameName('qburst',t<9 and 0 or t<16 and 1 or t<20 and 2 or 3) end
        return frameName('skill',t<8 and 4 or t<16 and 5 or t<36 and 6 or 7)
    end
    if st=='throw' then return frameName('throw',t<5 and 0 or t<10 and 1 or t<20 and 2 or 3) end
    if st=='thrown' then return frameName('victim',t<5 and 0 or t<10 and 1 or 2) end
    if st=='airhit' then return frameName('victim',3) end
    if st=='hit' then return frameName('hurt',0) end
    if st=='down' then return frameName('hurt',3) end
    if st=='getup' then return frameName('hurt',t<8 and 4 or 5) end
    if st=='block' then return frameName('guard',6) end
    if st=='cblock' then return frameName('guard',7) end
    if st=='win' then return frameName('hurt',6) end
    if st=='lose' then return frameName('hurt',7) end
    return frameName('basic',0)
end
function V:poseFor()
    if self.key=='raidenshogun' or self.key=='nahida' then return self:animatedPose() end''')
fview=fview.replace('back:step(budget)','back:step((self.key==\'raidenshogun\' or self.key==\'nahida\') and 1600 or budget)')
fview=fview.replace('function V:spawnGhost()','function V:spawnGhost()\n    if self.key==\'raidenshogun\' or self.key==\'nahida\' then return end')
fview=fview.replace('self.front = nil',"self.animFx=G.bitmap(layers.ghost);self.animFx.node:on(false)\n    self.front = nil")
fview=fview.replace('function V:free()',"function V:free()\n    if self.animFx then self.animFx:free() end")
fxmethod = r"""
local effectData
function V:drawAnimatedFx()
    if not self.animFx then return end
    if self.key~='raidenshogun' and self.key~='nahida' then self.animFx.node:on(false);return end
    local f=self.f;local t,st=f.t,f.state;local idx,width,offset,up
    if st=='attack' and f.move and t>=f.move.startup and t<f.move.startup+f.move.active then idx,width,offset,up=0,210,170,160
    elseif st=='skill' then
        idx,width,offset,up=4,130,25,260
        if t>=f.move.startup then idx,width,offset,up=6,180,(f.foe.x-f.x)/100*f.face,0 end
    elseif st=='burst' then
        if f.key=='raidenshogun' then
            if t<20 then idx,width,offset,up=5,250,0,110
            elseif t<23 then idx,width,offset,up=9,640,200,10
            elseif t<29 then idx,width,offset,up=10,460,200,0 end
        else idx,width,offset,up=9,630,0,0 end
    end
    if not idx then self.animFx.node:on(false);return end
    effectData=effectData or require('gf_animation_effects')
    local bank=effectData[f.key=='raidenshogun' and 'raiden' or 'nahida']
    if not bank then self.animFx.node:on(false);return end
    local img=bank[tostring(idx)]
    self.animFx:draw(img,tostring(idx));local scale=width/img.w
    self.animFx.node:pos(f.x/100+offset*f.face,f.y/100+up):scale(scale*f.face,scale):on(true)
end
"""
fview=fview.replace('function V:draw(budget)',fxmethod+'\nfunction V:draw(budget)')
fview=fview.replace('self:updatePose(budget)','self:updatePose(budget)\n    self:drawAnimatedFx()')
replace('gf_fview',fview)
sim=body('gf_sim');sim=sim.replace('p.invul = 70\n    self.freeze = 56',"p.invul = p.key=='raidenshogun' and 23 or 70\n    self.freeze = p.key=='raidenshogun' and 0 or 56")
sim=sim.replace('function S:burstUpdate(p)','''function S:burstUpdate(p)
    if p.key=='raidenshogun' then
        local t,d,bu=p.t,p.foe,p.move
        if t==20 then self:emit({type='burstActive',p=p.id,fx=bu.fx,style=bu.style,element=p.element}) end
        if t>=20 and t<23 and not p.burstConnected then
            if math.abs(d.x-p.x)<=bu.range*C and d.y<420*C then
                local hit=self:hit(p,d,{damage=bu.damage,hitstun=30,blockstun=18,push=8,level='mid',energy=0,shake=12,launch=24,knockdown=true},'burst',{unblockable=false})
                p.burstConnected=hit and true or false
            end
        end
        if t>=32 then self:setState(p,p.y>0 and 'air' or 'idle') end
        return
    end''')
sim=sim.replace("self:setState(p, 'burst', bu, 'burst')","self:setState(p, 'burst', bu, 'burst')\n    p.burstConnected=false")
replace('gf_sim',sim)
marker="__loaders['gf_animation_data'] = function()\n"+(ROOT/'project-inputs/gf_animation_data.lua').read_text()+'\nend\n'
marker += "__loaders['gf_animation_effects'] = function()\n"+(ROOT/'project-inputs/gf_animation_effects.lua').read_text()+'\nend\n'
source=source.replace("__loaders['gf_art'] = function()",marker+"__loaders['gf_art'] = function()")
# Keep main editor's confirmed project. The separate experimental match begins with the two requested fighters.
source="GF_FIRST_SCENE='fight'\nGF_FIRST_ARGS={chars={'raidenshogun','nahida'},mode='versus',cpu={false,2},rounds=2,time=99,seed=21}\nGF_SETTINGS={quality='lo'}\n"+source
archive['meta']['name']='雷电与纳西妲 · 动作测试版';archive['assets']['scripts'][0]['source']=source
(ROOT/'dist/projects/raiden-nahida.json').write_text(json.dumps(archive,separators=(',',':'),ensure_ascii=False))
(ROOT/'project-inputs/dual-character.lua').write_text(source)
(ROOT/'animation-tools/freeze.json').write_text(json.dumps({'confirmed_simulator_commit':'62e15e4c7fe9d9350765b63f1047b4f19db08418','confirmed_project':'dist/projects/confirmed-v15.json','raiden_preview_commit':'6c268627fed663c67114f22e0ce0a349c58a2ee8','experimental_project':'dist/projects/raiden-nahida.json','official_client_verified':False},indent=2))
print('Prepared experimental match, preserving confirmed project')

# Apply the delivery regression fixes to every regenerated experimental project.
import runpy
runpy.run_path(str(ROOT/'animation-tools/fix-delivery.py'))

runpy.run_path(str(ROOT/'animation-tools/restore-burst.py'))

runpy.run_path(str(ROOT/'animation-tools/polish-burst.py'))

runpy.run_path(str(ROOT/'animation-tools/fix-scale-throw.py'))

runpy.run_path(str(ROOT/'animation-tools/pool-preview-release.py'))

runpy.run_path(str(ROOT/'animation-tools/boundary-pool-r24.py'))

runpy.run_path(str(ROOT/'animation-tools/integrate-nahida-r25.py'))

runpy.run_path(str(ROOT/'animation-tools/nahida-frame-strike-r26.py'))

runpy.run_path(str(ROOT/'animation-tools/pixel-strike-ai-r27.py'))

runpy.run_path(str(ROOT/'animation-tools/prepare-inbetweens-r28.py'))
runpy.run_path(str(ROOT/'animation-tools/integrate-inbetweens-r28.py'))

runpy.run_path(str(ROOT/"animation-tools/fit-raiden-eye-r31.py"))
runpy.run_path(str(ROOT/"animation-tools/finalize-r31.py"))
runpy.run_path(str(ROOT/"animation-tools/fit-hd-r31.py"))
runpy.run_path(str(ROOT/"animation-tools/quality-input-r31.py"))

runpy.run_path(str(ROOT/"animation-tools/full-demo-r31.py"))
runpy.run_path(str(ROOT/"animation-tools/high-pool-r31.py"))

runpy.run_path(str(ROOT/"animation-tools/split-art-r31.py"))

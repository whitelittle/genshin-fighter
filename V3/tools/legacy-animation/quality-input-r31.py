from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
loader="__loaders['gf_hd_r31'] = function()\n"+(R/'project-inputs/gf_hd_r31.lua').read_text()+"end\n"
if "__loaders['gf_hd_r31'] = function()" in s:
 a=s.index("__loaders['gf_hd_r31'] = function()");b=s.index('__loaders[',a+10);s=s[:a]+loader+s[b:]
else:s=s.replace("__loaders['gf_art'] = function()",loader+"__loaders['gf_art'] = function()",1)
if 'if img and img.d then' not in s:
 s=s.replace('    if img then img.pal=bank.pal;', '''    if img and img.d then
        local raw=U.decodeAll(img.d);local values={}
        for i=1,img.n*5 do values[i]=raw[i*2-1]+raw[i*2]*256 end
        img.bytes=values;img.d=nil
    end
    if img then img.pal=bank.pal;''',1)
if 'function App:advanceQualityLoad()' not in s:
 s=s.replace('local bank=char and char[tier]',"local bank=char and char[tier]\n    if tier=='hi' then bank=require('gf_hd_r31')[key=='raidenshogun' and 'raiden' or 'nahida'] end",1)
 s=s.replace("self.settings = {quality = 'auto'", "self.settings = {quality = 'lo'",1)
 a=s.index('function App:detectQuality()');b=s.index('\nfunction App:fit',a)
 s=s[:a]+'''function App:isMobile()
    local ok,d=pcall(self.env.game.GetDevice);local D=self.env.Enum.Device
    return ok and (d==D.Mobile or d==D.MobileController)
end
function App:detectQuality()
    if self:isMobile() then return 'lo' end
    return self.settings.quality=='hi' and 'hi' or 'lo'
end
function App:setQuality(q)
    if self.qualityLoad or (q=='hi' and self:isMobile()) or q==self.quality then return false end
    local entries={};local hd=require('gf_hd_r31')
    for _,key in ipairs({'raidenshogun','nahida'}) do
        local bank=hd[key=='raidenshogun' and 'raiden' or 'nahida'];local names={}
        for name in pairs(bank) do if name~='pal' then names[#names+1]=name end end
        table.sort(names);for _,name in ipairs(names) do entries[#entries+1]={key,name} end
    end
    self.qualityLoad={target=q,entries=entries,i=0}
    if self.scene and self.scene.exit then self.scene:exit() end
    self.scene=nil;self.sceneName='quality_loading';self:dropBackdrop();self.input:clearUI()
    self.qualityLoadingL=G.layer(self.layers.curtain)
    return true
end
function App:advanceQualityLoad()
    local job=self.qualityLoad;if not job then return false end
    local A=require('gf_art')
    for _=1,2 do
        local e=job.entries[job.i+1];if not e then break end
        A.animation(e[1],job.target,e[2]);job.i=job.i+1
    end
    local progress=job.i/math.max(1,#job.entries);local L=self.qualityLoadingL;local w=math.min(560,self.W-160)
    L:begin();L:rect(0,0,self.W+40,self.H+40,{8,12,24},1)
    L:label(job.target=='hi' and '正在加载高级画质' or '正在加载简单画质',0,65,w,50,30,{236,229,216})
    L:rect(0,0,w,10,{45,45,60},1);L:rect((progress-1)*w/2,0,w*progress,10,{120,196,245},1)
    L:label(('%d%%'):format(math.floor(progress*100)),0,-45,w,40,24,{210,210,220});L:finish()
    if job.i>=#job.entries then
        self.settings.quality=job.target;self.quality=job.target;self.qualityLoad=nil
        L:free();self.qualityLoadingL=nil;self:go('options')
    end
    return true
end
''' +s[b:]
 s=s.replace('function App:update(dt)\n', 'function App:update(dt)\n    if self:advanceQualityLoad() then return end\n',1)
 s=s.replace("local QN = {auto = '自动', hi = '高', lo = '低（手机推荐）'}", "local QN = {hi = '高级画质', lo = '简单画质'}")
 s=s.replace("left = function() st.quality = cycle({'auto', 'hi', 'lo'}, st.quality, -1); app.quality = app:detectQuality() end,", "left = function() app:setQuality(app.quality=='lo' and 'hi' or 'lo') end,")
 s=s.replace("right = function() st.quality = cycle({'auto', 'hi', 'lo'}, st.quality, 1); app.quality = app:detectQuality() end},", "right = function() app:setQuality(app.quality=='lo' and 'hi' or 'lo') end},")
 a=s.index("__loaders['gf_scene_options']");b=s.index('    self.items = items',a)
 s=s[:b]+"    if app:isMobile() then table.remove(items,1) end\n"+s[b:]
 a=s.index("__loaders['gf_scene_options']");b=s.index('    self.menu:input(self.app.input:menu())',a)
 s=s[:b]+s[b:].replace('    self.menu:input(self.app.input:menu())', "    if self.app:isMobile() and self.items[1] and self.items[1].id=='quality' then self.app:go('options');return end\n    self.menu:input(self.app.input:menu())",1)
 s=s.replace('自动：手机用低画质、电脑用高画质。低画质减少角色与背景的图元数量，帧率更稳。', '默认简单画质。电脑可切换高级画质，读条后重新加载更细的角色拟合与背景；手机固定简单画质。')
 s=s.replace("{ck('L'), 0, 0, 'alt'}, {ck('I'), 0, 0, 'alt2'},", "{ck('I'), 1, B.SK, 'alt'}, {ck('O'), 1, B.BU, 'alt2'},")
 s=s.replace("{ck('U'), 1, B.DA}, {ck('O'), 1, B.TH}", "{ck('U'), 1, B.DA}, {ck('L'), 1, B.TH}")
 s=s.replace('E / E 按钮 /', 'E / I / E 按钮 /').replace('E 键 / E 按钮 /','E / I 键 / E 按钮 /')
 s=s.replace('Q 键 / Q 按钮','Q / O 键 / Q 按钮').replace('Q 键或点击 Q 按钮','Q / O 键或点击 Q 按钮')
 s=s.replace('O 或 →K 投','L 或 →K 投').replace('O 或 →+K 近身投','L 或 →+K 近身投')
 s=s.replace('E skill, Q burst, U dash, O throw','E/I skill, Q/O burst, U dash, L throw')
j['assets']['scripts'][0]['source']=s;p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
print('r31 quality load, mobile low lock and I/O backup bindings integrated')

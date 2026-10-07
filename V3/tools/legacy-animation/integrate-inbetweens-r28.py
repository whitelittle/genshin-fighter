from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if "GF_RELEASE_ID='dual-inbetweens-r28'" not in s:
 data=(R/'project-inputs/gf_inbetween_data.lua').read_text()
 s=s.replace("__loaders['gf_art'] = function()","__loaders['gf_inbetween_data'] = function()\n"+data+"end\n__loaders['gf_art'] = function()",1)
 s=s.replace('    local img=bank and bank[aliases[pose] or pose]',"    local img=bank and bank[aliases[pose] or pose]\n    if not img and bank then local extra=require('gf_inbetween_data');local c=extra.poses[key=='raidenshogun' and 'raiden' or 'nahida'];img=c and c[tier] and c[tier][pose] end",1)
 s=s.replace('function V:animatedPose()','function V:keyPose()',1)
 method='''local inbetweenKeys
function V:middle(sheet,i,j)
    inbetweenKeys=inbetweenKeys or require('gf_inbetween_data').keys
    local k=inbetweenKeys[self.key=='raidenshogun' and 'raiden' or 'nahida']
    return k[sheet..'_'..i..'_'..j] or k[sheet..'_'..j..'_'..i] or frameName(sheet,i)
end
function V:sequence(sheet,frames,ends,t)
    local start=0
    for i,finish in ipairs(ends) do
        if t<finish then
            local span=finish-start;local window=math.min(3,math.max(1,math.floor(span*0.35)))
            if span>1 and t>=finish-window then return self:middle(sheet,frames[i],frames[i%#frames+1]) end
            return frameName(sheet,frames[i])
        end
        start=finish
    end
    return frameName(sheet,frames[#frames])
end
function V:attackFrames(m,t,id)
    local sheet,frames='light',{0,1,2,3}
    if id=='light2' then frames={4,5,6,7} elseif id=='light3' then sheet='heavy'
    elseif id=='heavy' then sheet,frames='heavy',{4,5,6,7}
    elseif id=='crouchLight' then sheet,frames='air',{0,0,1,0}
    elseif id=='crouchHeavy' then sheet,frames='air',{2,2,3,2}
    elseif id=='airLight' then sheet,frames='air',{4,4,5,4}
    elseif id=='airHeavy' then sheet,frames='air',{6,6,7,6} end
    return self:sequence(sheet,frames,{math.ceil(m.startup/2),m.startup,m.startup+m.active,m.startup+m.active+m.recovery},t)
end
function V:animatedPose()
    local f=self.f;local st,t=f.state,f.t
    if f.airMove then return self:attackFrames(f.airMove,f.airT or 0,f.airMoveId or 'airLight') end
    if st=='idle' or st=='intro' then return self:sequence('basic',{0,1},{25,50},self.app.frame%50) end
    if st=='walk' or st=='back' then
        if f.key=='nahida' then return self:sequence('move',{1,2},{16,32},self.walkT%32) end
        return self:sequence('basic',st=='back' and {7,6,5,4,3,2} or {2,3,4,5,6,7},{8,16,24,32,40,48},self.walkT%48)
    end
    if st=='attack' then return self:attackFrames(f.move,t,f.moveId) end
    if st=='crouch' or st=='jumpsq' or st=='land' then return self:sequence('guard',{0,1},{5,12},math.min(t,11)) end
    if st=='dash' then return self:sequence('move',{4,5},{5,14},t) end
    if st=='backdash' then return self:sequence('move',{6,7},{5,18},t) end
    if st=='air' then
        if f.vy>0 and f.vy<3*C then return self:middle('move',1,2) end
        if f.vy<=0 and f.vy>-3*C then return self:middle('move',2,3) end
    end
    if st=='skill' then
        if f.key=='nahida' then
            if f.connected then return self:sequence('skill',{3,0},{27,30},t) end
            return self:sequence('skill',{0,1,2,3},{4,8,14,30},t)
        end
        local su=f.move.startup
        return self:sequence('skill',{0,1,2,3},{math.ceil(su/2),su,su+6,su+f.move.recovery},t)
    end
    if st=='burst' then
        if f.key=='nahida' then return self:sequence('skill',{4,5,6,7},{8,22,74,90},t) end
        if f.cinematicConfirmed then return self:sequence('qburst',{1,2,3,2,3,2,3,0},{9,16,24,35,44,70,85,94},t) end
    end
    if st=='throw' then
        if f.key=='nahida' then return self:sequence('skill',{4,5,6,7},{12,30,58,76},t) end
        return self:sequence('throw',{0,1,2,3},{12,24,36,50},t)
    end
    if st=='thrown' and f.foe.key~='nahida' then return self:sequence('victim',{0,1,2},{12,24,30},t) end
    if st=='thrown' then return self:sequence('basic',{0,1},{18,36},t%36) end
    if st=='airhit' and t>=3 and t<=5 then return self:middle('victim',2,3) end
    if st=='hit' and t>=3 and t<=5 then return self:middle('hurt',0,1) end
    if st=='down' and not f.ko and t>=35 then return self:middle('hurt',3,4) end
    if st=='getup' then return self:sequence('hurt',{4,5},{8,16},t) end
    if st=='block' and t>=3 and t<=5 then return self:middle('guard',6,2) end
    if st=='cblock' and t>=3 and t<=5 then return self:middle('guard',7,4) end
    if st=='win' and t%30>=22 then return self:middle('hurt',6,6) end
    if st=='lose' and t%30>=22 then return self:middle('hurt',7,7) end
    return self:keyPose()
end

'''
 s=s.replace('function V:poseFor()',method+'function V:poseFor()',1)
 s=s.replace("GF_RELEASE_ID='nahida-pixel-viewfinder-r27'","GF_RELEASE_ID='dual-inbetweens-r28'")
 j['meta']['name']='雷电与纳西妲 · 全动作过渡帧 r28';j['assets']['scripts'][0]['source']=s
 p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
# Preview timelines retain the existing phase lengths and contact timing.
for file in [R/'animation-tools/preview-engine-r23.js',R/'dist/actions/nahida/app.js',R/'dist/actions/raiden/app.js']:
 text=file.read_text()
 if 'function previewMiddle(' not in text:
  method='''function previewMiddle(bank,sheet,i,j){const s=bank[sheet+'_between'];if(!s)return null;let k=s.next.findIndex((v,n)=>n===i&&v===j);if(k<0)k=s.next.findIndex((v,n)=>n===j&&v===i);if(k<0&&i===j)k=s.next.findIndex((v,n)=>n===i&&v===i);return k<0?null:[sheet+'_between',k];}
'''
  text=text.replace('function pose(sheet,i,x,y,h=330,flip=false,c=ctx){sprite(atlas,images,sheet,i,x,y,h,flip,c);}',method+'''function pose(sheet,i,x,y,h=330,flip=false,c=ctx){
 if(c===ctx&&sheet===a.sheet){const p=phaseAt(time),span=a.dur[p],next=a.frames[p+1]??a.frames[0];if(i===a.frames[p]&&localAt(p)>=span-Math.min(3,Math.max(1,Math.floor(span*.35)))){const middle=previewMiddle(atlas,sheet,i,next);if(middle)[sheet,i]=middle;}}
 sprite(atlas,images,sheet,i,x,y,h,flip,c);}
''')
 text=text.replace('v=r27','v=r28');file.write_text(text)
for file in [R/'dist/actions/nahida/index.html',R/'dist/actions/raiden/index.html']:
 file.write_text(file.read_text().replace('v=r27','v=r28'))
for file in [R/'editor-entry.js',R/'dist/editor/editor.js',R/'editor-bootstrap.js',R/'dist/editor/bootstrap.js',R/'dist/editor/play.js',R/'dist/index.html']:
 file.write_text(file.read_text().replace('nahida-pixel-viewfinder-r27','dual-inbetweens-r28').replace('草神像素取景框 · 投技 AI 修正 r27','双方全动作补帧 r28'))
print('r28: authored inbetween poses in preview and actual fighter views; simulation timing unchanged')

# Refresh generated bitmap data when the release is already integrated.
j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source'];a=s.index("__loaders['gf_inbetween_data'] = function()")+len("__loaders['gf_inbetween_data'] = function()\n");b=s.index("end\n__loaders['gf_art'] = function()",a);s=s[:a]+(R/'project-inputs/gf_inbetween_data.lua').read_text()+s[b:];j['assets']['scripts'][0]['source']=s;p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)

# New end-of-round poses can leave a second dormant bitmap after the first cleanup.
old="if not growth.reclaimed then G.reclaimDormant();growth.reclaimed=true end"
new="growth.boundaryTicks=(growth.boundaryTicks or 0)+1\n    if not growth.reclaimed or growth.boundaryTicks%30==0 then G.reclaimDormant();growth.reclaimed=true end"
s=s.replace(old,new,1);j['assets']['scripts'][0]['source']=s;p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)

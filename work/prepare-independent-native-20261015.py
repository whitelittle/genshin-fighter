from pathlib import Path
p=Path('work/build-nahida-two-action-gia-20261015.mjs').read_text(encoding='utf-8')
p=p.replace('outputs/nahida-two-actions-20261015','outputs/nahida-independent-actions-20261015').replace('草神_994图元_两组动作.gia','草神_994图元_独立帧变换.gia')
p=p.replace('994 pooled images / no background / art not approved','994 matched images / independent keyframes / art not approved')
p=p.replace("f.elements.map(e=>", "[...f.elements].sort((a,b)=>a.poolId-b.poolId).map(e=>")
p=p.replace("parseInt(e.color.slice(i,i+2),16))]", "parseInt(e.color.slice(i,i+2),16)),f.elements.indexOf(e)]")
start=p.index('local controls,actor,status,last=')
end=p.index('const template=',start)
p=p[:start]+'''local controls,actor,status,last={},nil,nil,nil
local action,index,clock,paused,smooth='idle',1,0,true,true
local function publish()
 local rows=frames[action][index];local following=frames[action][index%4+1]
 local t=(not paused and smooth) and math.max(0,math.min(1,(clock-.18)/.32)) or 0
 local orderRows=t>=.5 and following or rows
 if last~=orderRows then
  local order={}
  for i,p in ipairs(orderRows) do order[p[9]+1]=controls[i] end
  for _,c in ipairs(order) do c:SetAsLastSibling() end
  last=orderRows
 end
 for i,a in ipairs(rows) do
  local b=following[i];local c=controls[i]
  c:SetAnchoredPosition(a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t)
  c:SetSizeDelta(a[3]+(b[3]-a[3])*t,a[4]+(b[4]-a[4])*t)
  c:SetLocalRotation(0,0,a[5]+((b[5]-a[5]+90)%180-90)*t)
  c.imageColor=Color(math.floor(a[6]+(b[6]-a[6])*t+.5),math.floor(a[7]+(b[7]-a[7])*t+.5),math.floor(a[8]+(b[8]-a[8])*t+.5),255)
 end
 status.text=action..' '..index..'/4'..(paused and ' paused' or '')..(smooth and ' morph' or ' keys')
end
local function command(op,value)
 if op=='action' then action=value=='move' and 'move' or 'idle';index=1;clock=0
 elseif op=='pause' then paused=value==1;clock=0
 elseif op=='smooth' then smooth=value==1;clock=0
 elseif op=='step' then paused=true;index=index%4+1;clock=0
 elseif op=='frame' then paused=true;index=math.max(1,math.min(4,tonumber(value) or 1));clock=0
 elseif op=='mirror' then actor:SetLocalScale(value==-1 and -1.35 or 1.35,1.35,1)
 elseif op=='position' then actor:SetAnchoredPosition(math.max(-400,math.min(400,tonumber(value) or 0)),-15)
 end
 publish()
end
function OnStart()
 actor=script.object:FindChild('Actor');status=script.object:FindChild('Status')
 for i=1,${first.length} do controls[i]=actor:FindChild('S'..string.format('%04d',i-1)) end
 script:RegisterServerSignalHandler('AnimationControl',function(_,p)command(p[1],p[2])end)
 publish();script:EnableUpdate(true)
end
function OnUpdate(dt)
 if paused then return end
 clock=clock+(dt or 1/60)
 if clock>=.5 then clock=clock%.5;index=index%4+1 end
 publish()
end
`;
''' + p[end:]
p=p.replace('const expected=action.frames[i-1].elements;', 'const expected=[...action.frames[i-1].elements].sort((a,b)=>a.poolId-b.poolId);')
p=p.replace('i<13','i<32')
# Preview controls are outside the native image; no unverified native click handlers.
begin=p.index("for(const [name,text,x] of")
end=p.index('actor.children.reverse()',begin)
p=p[:begin]+p[end:]
Path('work/build-nahida-independent-gia-20261015.mjs').write_text(p,encoding='utf-8')
s=Path('work/serve-nahida-two-actions-20261015.mjs').read_text(encoding='utf-8')
s=s.replace('outputs/nahida-two-actions-20261015','outputs/nahida-independent-actions-20261015').replace('草神_994图元_两组动作.gia','草神_994图元_独立帧变换.gia')
s=s.replace('8827','8828')
s=s.replace("let paused=true,position=0,mirror=1;", "let paused=true,position=0,mirror=1;")
s=s.replace("setInterval(()=>{if(!paused)studio.playStep(.03,{observe:false})},30);", "setInterval(()=>{if(!paused)studio.playStep(.05,{observe:false})},50);")
s=s.replace('<label>帧 ', '<label><input type="checkbox" checked onchange="act(\'smooth\',this.checked?1:0)">图元变换</label><label>帧 ')
s=s.replace('每组4个源姿势，共用994个角色图片控件。','每张高清帧独立拟合一次；按位置、尺寸、颜色匹配后，共用994个图元控件变换。没有叠加第二套角色。')
s=s.replace('美术未验收：移动组屈腿和迈步仍明显偏离原图，固定站姿图元的匹配不足；本页用于检验操作与换帧。不是已完成的正式角色动画，真机未验证。','候选演示：关键帧可暂停逐张检查；图元对应由自动匹配确定，尚未加入身体部位约束，过渡可能变形。美术与真机未验收。')
s=s.replace("['action','pause','step','frame','mirror','position']", "['action','pause','step','frame','mirror','position','smooth']")
s=s.replace("screen.onclick=e=>{", "/* obsolete in-image button mapping */ screen.onclick=e=>{return;")
Path('work/serve-nahida-independent-20261015.mjs').write_text(s,encoding='utf-8')
print('Native builder and preview prepared')

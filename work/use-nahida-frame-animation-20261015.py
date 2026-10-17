from pathlib import Path
import json,re
builder=Path('work/build-nahida-independent-gia-20261015.mjs')
s=builder.read_text(encoding='utf-8')
start=s.index('local action,index,clock,paused,smooth=')
end=s.index('local function command(op,value)',start)
s=s[:start]+'''local action,index,clock,paused='idle',1,0,true
local function publish()
 local rows=frames[action][index]
 if last~=rows then
  local order={}
  for i,p in ipairs(rows) do order[p[9]+1]=controls[i] end
  for _,c in ipairs(order) do c:SetAsLastSibling() end
  for i,p in ipairs(rows) do
   local c=controls[i]
   c:SetAnchoredPosition(p[1],p[2]);c:SetSizeDelta(p[3],p[4])
   c:SetLocalRotation(0,0,p[5]);c.imageColor=Color(p[6],p[7],p[8],255)
  end
  last=rows
 end
 status.text=action..' '..index..'/4'..(paused and ' paused' or '')..' frames'
end
''' + s[end:]
s=s.replace(" elseif op=='smooth' then smooth=value==1;clock=0\n",'')
s=s.replace('if clock>=.5 then clock=clock%.5;index=index%4+1 end\n publish()', 'if clock>=.18 then\n  local steps=math.floor(clock/.18);clock=clock%.18;index=(index-1+steps)%4+1;publish()\n end')
s=s.replace('i<32','i<13').replace('independent keyframes','frame animation')
builder.write_text(s,encoding='utf-8')
server=Path('work/serve-nahida-independent-20261015.mjs');s=server.read_text(encoding='utf-8')
s=s.replace('<label><input type="checkbox" checked onchange="act(\'smooth\',this.checked?1:0)">图元变换</label>','')
s=s.replace("'position','smooth'", "'position'")
s=s.replace('按位置、尺寸、颜色匹配后，共用994个图元控件变换。没有叠加第二套角色。','共用994个图元控件，每180毫秒直接切至下一张完整姿势。')
s=s.replace('候选演示：关键帧可暂停逐张检查；图元对应由自动匹配确定，尚未加入身体部位约束，过渡可能变形。美术与真机未验收。','帧动画：只显示独立拟合的完整姿势，不生成中间过渡。可暂停逐帧检查。美术细节与真机未验收。')
s=s.replace('两组图元动作试验','两组图元帧动画')
s=re.sub(r'/\* obsolete in-image button mapping \*/ screen.onclick=.*?;update\(\);', 'update();',s)
server.write_text(s,encoding='utf-8')
p=Path('outputs/nahida-independent-actions-20261015/animation.json');d=json.loads(p.read_text(encoding='utf-8'))
d['transition']='discrete frame replacement; no interpolation or alpha crossfade'
for a in d['actions']:
 for f in a['frames']:f['durationMs']=180
p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Frame-only playback prepared')

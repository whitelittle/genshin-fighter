from pathlib import Path
p=Path('outputs/motion-production/index.html')
s=p.read_text(encoding='utf-8')
panel='''<details id="fxPanel" open><summary>独立特效预览 / 位置绑定</summary><div class="settings">
<label>角色等比缩放<input aria-label="角色等比缩放" id="actorScale" type="range" min="80" max="140" value="120"><output id="actorScaleValue">120%</output></label><button id="scaleOriginal">原尺寸</button><button id="scalePreview">放大20%</button>
<label>特效模式<select aria-label="特效模式" id="fxMode"><option value="compact">紧凑结构预览</option><option value="independent">独立播放特效</option><option value="legacy">旧特效对照</option><option value="off">关闭</option></select></label>
<label>特效样式<select aria-label="特效样式" id="fxType"><option value="seal">印记 / 施法</option><option value="orb">魔法弹</option><option value="slash">短斩击</option><option value="ground">地面波纹</option></select></label>
<label>绑定位置<select aria-label="绑定位置" id="fxSocket"><option value="hand">施法手</option><option value="chest">胸前</option><option value="feet">脚底</option><option value="target">对手中心</option><option value="world">场地固定点</option></select></label>
<label>横向偏移<input aria-label="横向偏移" id="fxX" type="number" min="-300" max="300" value="0"></label><label>纵向偏移<input aria-label="纵向偏移" id="fxY" type="number" min="-300" max="300" value="0"></label>
<label>特效缩放<input aria-label="特效缩放" id="fxScale" type="range" min="25" max="150" value="70"></label>
<label>特效层<select aria-label="特效层" id="fxLayer"><option value="all">主体与接触</option><option value="body">仅主体</option><option value="contact">仅接触</option></select></label>
<label>接触反馈<select aria-label="接触反馈" id="fxContact"><option value="none">无</option><option value="hit">命中</option><option value="guard">防住</option></select></label>
<label>显示方式<select aria-label="显示方式" id="fxView"><option value="both">角色与特效</option><option value="only">只看特效</option></select></label>
<label><input id="attackGuides" type="checkbox">上下段视觉参考线</label><label><input id="socketGuides" type="checkbox" checked>绑定点</label>
<label>独立特效时间<input aria-label="独立特效时间" id="fxScrub" type="range" min="0" max="59" value="20"></label><button id="fxPlay">播放特效</button><button id="fxReset">特效重播</button><button id="fxExport">导出绑定配置</button></div><p id="fxReadout">特效形状是结构试验，具体技能效果待讨论。绑定点是逐姿势估计，可用偏移校准。等比缩放只用于当前预览。</p></details>'''
if 'id="fxPanel"' not in s:s=s.replace('<p class="notice">',panel+'<p class="notice">').replace('<script src="probe.js">','<script src="effect-lab.js"></script><script src="probe.js">')
p.write_text(s,encoding='utf-8')
p=Path('outputs/motion-production/probe.js');s=p.read_text(encoding='utf-8')
s=s.replace('last=0,ready=false;','last=0,ready=false,fxFrame=20,fxPlaying=false;')
s=s.replace('role=r;reset()','role=r;$(\'actorScale\').value=r.key===\'nahida-normal-v2\'?120:100;reset()')
s=s.replace('function actor(r,id,x,y,dir=1){','function actor(r,id,x,y,dir=1){')
s=s.replace("ctx.scale(dir,1);ctx.imageSmoothingEnabled", "const scale=r===role?+$('actorScale').value/100:1;ctx.scale(dir*scale,scale);ctx.imageSmoothingEnabled")
s=s.replace('actor(role,state.pose,base+dir*dx,floor+dy,dir);',"if($('fxView').value!=='only')actor(role,state.pose,base+dir*dx,floor+dy,dir);")
s=s.replace('actor(other,vid,enemy,floor,-dir);',"if($('fxView').value!=='only')actor(other,vid,enemy,floor,-dir);")
s=s.replace("if($('fx').checked&&move&&window.ProbeFX)","if($('fx').checked&&$('fxMode').value==='legacy'&&move&&window.ProbeFX)")
marker="ctx.fillStyle='#e6d6b4';ctx.font='18px sans-serif';"
extra="""const hs=role.height*+$('actorScale').value/100,mode=$('fxMode').value,sock=$('fxSocket').value,local=window.EffectLab.socket(state.pose,hs,sock),world=sock==='world',target=sock==='target';let sx=world?550:target?enemy:base+dir*dx+dir*local[0],sy=world?floor-100:target?floor-other.height*.55:floor+dy+local[1];sx+=dir*+$('fxX').value;sy+=+$('fxY').value;
if($('fx').checked&&(mode==='independent'||mode==='compact'&&move)){const et=mode==='independent'?fxFrame:Math.max(0,t-move.startup+10),contact=mode==='independent'?$('fxContact').value:state.victim==='guard'?'guard':state.damage||state.phase==='命中演出'?'hit':'none';window.EffectLab.draw(ctx,{type:$('fxType').value,frame:et,x:sx,y:sy,dir,scale:+$('fxScale').value/100,colorKey:role.visualKey||role.key,contact,layer:$('fxLayer').value});}
if($('socketGuides').checked&&mode!=='off'){ctx.strokeStyle='#e7c979';ctx.beginPath();ctx.moveTo(sx-6,sy);ctx.lineTo(sx+6,sy);ctx.moveTo(sx,sy-6);ctx.lineTo(sx,sy+6);ctx.stroke();}
if($('attackGuides').checked){for(const[y,label]of [[floor-125,'上段视觉参考'],[floor-48,'下段视觉参考']]){ctx.strokeStyle='#e4cb7a77';ctx.setLineDash([5,6]);ctx.beginPath();ctx.moveTo(base-55,y);ctx.lineTo(enemy+55,y);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#c9b488';ctx.font='12px sans-serif';ctx.fillText(label,base-70,y-5);}}
$('actorScaleValue').textContent=$('actorScale').value+'%';$('fxReadout').textContent=`特效逻辑帧 ${Math.floor(fxFrame)} / 60 · 绑定 ${sock} · 等比缩放 ${$('actorScale').value}%（预览）· 不改变伤害/判定；具体特效待讨论。`;
"""
if 'const hs=role.height' not in s:s=s.replace(marker,extra+marker)
s=s.replace('function tick(now){if(last&&playing&&ready)',"function tick(now){if(last&&fxPlaying&&ready){fxFrame=(fxFrame+(now-last)/1000*60*+$('speed').value)%60;$('fxScrub').value=Math.floor(fxFrame);}if(last&&playing&&ready)")
hooks="""$('scaleOriginal').onclick=()=>{$('actorScale').value=100};$('scalePreview').onclick=()=>{$('actorScale').value=120};$('fxPlay').onclick=()=>{fxPlaying=!fxPlaying;$('fxPlay').textContent=fxPlaying?'暂停特效':'播放特效'};$('fxReset').onclick=()=>{fxFrame=0};$('fxScrub').oninput=()=>{fxFrame=+$('fxScrub').value;fxPlaying=false;$('fxPlay').textContent='播放特效'};$('fxExport').onclick=()=>download(new Blob([JSON.stringify({version:window.EffectLab.version,role:role.key,pose:M.pose(role,action,frame),type:$('fxType').value,socket:$('fxSocket').value,offset:[+$('fxX').value,+$('fxY').value],scale:+$('fxScale').value/100,actorPreviewScale:+$('actorScale').value/100,approximateSocket:true,productionCombatChanged:false},null,2)],{type:'application/json'}),role.key+'-fx-binding.json');
"""
if "$('scaleOriginal').onclick" not in s:s=s.replace('reset();Promise.all',hooks+'reset();Promise.all')
p.write_text(s,encoding='utf-8')

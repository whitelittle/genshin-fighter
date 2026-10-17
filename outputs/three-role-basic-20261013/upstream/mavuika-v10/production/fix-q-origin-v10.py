from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/'dist';p=d/'q-model.js';s=p.read_text().replace("origin={x:430,y:450}){","origin={x:430,y:450},target){",1)
s=s.replace("  return {tick:-1", "  target=target||{x:origin.x+(outcome==='range'?500:action==='q'?80:action==='dash'?245:165),y:origin.y};\n  if(!Number.isFinite(target.x)||!Number.isFinite(target.y))throw Error('Invalid target');\n  return {target:{...target},rejectReason:null,tick:-1")
s=s.replace(" function emit(s,h)"," function nearby(s){const dx=s.target.x-s.origin.x,dy=s.target.y-s.origin.y;return dx>=0&&dx<=120&&Math.abs(dy)<=40;}\n function emit(s,h)")
s=s.replace("s.confirmed=s.outcome==='hit';s.failed=!s.confirmed;if(s.outcome==='block')", "s.confirmed=s.outcome==='hit'&&nearby(s);s.failed=!s.confirmed;s.rejectReason=s.failed?(nearby(s)?s.outcome:'range'):null;if(s.outcome==='block'&&nearby(s))")
s=s.replace("if(s.failed){const p=clamp((t-8)/16);return {x:o.x+18*(1-p),y:o.y,pose:t>=24?'idle':'brake'};}","if(s.failed)return {...o,pose:'idle'};")
s=s.replace("if(t<=8)return {x:o.x+18*clamp(t/8),y:o.y,pose:'ride'};", "if(t<=8)return {...o,pose:'idle'};")
s=s.replace("mix(o.x+18,o.x+220,p)","mix(o.x,o.x+220,p)")
s=s.replace("const p=clamp((t-55)/18);return {x:mix(o.x+220,o.x+330,p),y:mix(o.y-220,o.y-40,p),pose:'slash'};", "const p=clamp((t-55)/19);return {x:mix(o.x+220,o.x,p),y:mix(o.y-220,o.y,p),pose:'slash'};")
s=s.replace("const p=clamp((t-74)/24);return {x:mix(o.x+330,o.x,p),y:o.y,pose:t>=98?'idle':'slash'};", "return {...o,pose:t>=86?'idle':'slash'};")
s=s.replace("function seek(outcome,tick,action='q',origin)","function seek(outcome,tick,action='q',origin,target)").replace("create(outcome,action,origin);while", "create(outcome,action,origin,target);while")
s=s.replace("if(s.failed)return s.tick<24?(s.outcome==='block'?'被挡 · 制动收招':'未确认 · 制动收招'):'原地恢复';", "if(s.failed)return s.rejectReason==='range'?'非近距离 · 不进入演出':'未命中确认 · 原地短收招';")
s=s.replace("起手 · 无伤害确认", "起手 · 近距离命中确认").replace("强烈斩击 · 单次伤害", "一刀斩落 · 单次伤害").replace("if(s.tick<98)return '收刀 · 回到起手位置';", "if(s.tick<86)return '原位落地 · 收刀';")
s=s.replace("api={hits,create", "api={hits,nearby,create");p.write_text(s)
s=(d/'q-fx-model-v9.js').read_text()
s=s.replace("const p=s.action==='q'&&contact.kind==='hit'?point(at,'tip'):point(at,'contact');", "const p=s.action==='q'?(contact.kind==='hit'?point(at,'tip'):{x:s.target.x,y:s.target.y-95}):point(at,'contact');")
start=s.index(' let receiver=');end=s.index('\n return {body:',start)
s=s[:start]+''' let receiver={pose:s.outcome==='block'?'guard_2':'idle_0',x:s.target.x,y:s.target.y,flash:false};
 if(contact&&age<18&&age>=0){receiver.pose=contact.kind==='hit'?'hurt_0':'guard_6';receiver.flash=contact.kind==='hit'&&age<2;if(contact.kind==='hit'&&s.action!=='q')receiver.x+=Math.min(24,age*2);}
 if(s.action==='q'&&s.confirmed&&t>=9){
  const tip=point(Q.choreography(Q.seek('hit',55,'q',s.origin)),'tip'),peak={x:tip.x,y:tip.y+90},mix=(a,b,p)=>a+(b-a)*p;
  if(t<32){const p=Math.min(1,(t-8)/23);receiver.x=mix(s.target.x,peak.x,p);receiver.y=mix(s.target.y,peak.y,p);}
  else if(t<55){receiver.x=peak.x;receiver.y=peak.y;}
  else if(t<74){const p=(t-55)/19;receiver.x=mix(peak.x,s.target.x+40,p);receiver.y=mix(peak.y,s.target.y,p);}
  else{receiver.x=s.target.x+40;receiver.y=s.target.y;}
 }
''' +s[end:]
(d/'q-fx-model-v10.js').write_text(s)
p=d/'index.html';s=p.read_text().replace('候选 · 09','候选 · 10').replace('q-fx-model-v9.js','q-fx-model-v10.js').replace('mavuika-q-fx-offline-v9','mavuika-q-fx-offline-v10').replace('mavuika-q-fx-v9.gif','mavuika-q-fx-v10.gif').replace('mavuika-bike-fx-v9.gif','mavuika-bike-fx-v10.gif').replace('斩击后回到起手坐标','斩落时直接落回起手坐标').replace('第8帧以预览选项做无伤害确认','第8帧同时检查预览目标坐标的近距离范围及命中结果选项').replace('未确认则制动短收招','未确认则原地短收招').replace('暂不接入正式碰撞与伤害','尚未接入正式游戏碰撞与伤害').replace('命中结果由选项模拟','命中结果由选项模拟，近距离条件由预览坐标检查');p.write_text(s)
p=d/'app.js';s=p.read_text().replace('V9 后景太阳与火尾／剑身刀光／低位接触层／徒步落地','V10 近距离确认 → 骑车冲上 → 下车一刀 → 原位落地').replace('未确认则制动短收招','未确认则原地短收招').replace('斩击后回到起手坐标','出刀下降直接落回起手坐标');p.write_text(s)

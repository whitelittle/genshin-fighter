(function(root){
 const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
 function duration(m){return m.startup+Math.max(m.active+m.recovery,m.projectile?(m.flight||30):0,m.effectDuration||0);}
 function stateAt(m,frame){const attackEnd=m.startup+m.active,recoveryEnd=attackEnd+m.recovery;return frame<=m.startup?'起手':frame<=attackEnd?'有效':frame<=recoveryEnd?'收招':frame<=duration(m)?m.projectile?'投射物飞行':m.effectDuration?'领域持续':'完成':'完成';}
 function actorOffset(m,frame){if(!m.dash)return 0;if(m.fx==='stiletto')return frame>=m.startup+2?m.dash:0;return m.dash*clamp((frame-m.startup+4)/8,0,1);}
 function hitboxes(m,frame){
  if(m.support)return[];
  const t=frame-m.startup;if(t<=0)return[];
  const y=m.height==='low'?12:65,h=m.heightRange||100;
  if(m.projectile){if(t>(m.flight||30))return[];const radius=m.fx==='bomb'?12:26,x=radius+(m.reach-radius*2)*t/(m.flight||30),cy=['bomb','bounce'].includes(m.fx)?60+Math.sin(t/(m.flight||30)*Math.PI)*135:110;return[{x:x-radius,y:cy-(m.fx==='phoenix'?45:radius),w:radius*2,h:m.fx==='phoenix'?90:radius*2}];}
  if(t>m.active)return[];
  if(m.fx==='stiletto'&&t<2)return[];
  if(m.fx==='shrine'||m.fx==='totem')return[];
  const offset=actorOffset(m,frame);return[{x:offset+20,y,w:Math.max(10,m.reach-offset-20),h}];
 }
 function sample(m,frame,distance,dummy){const hurt={x:distance-22,y:dummy==='jump'?225:0,w:44,h:232};const box=hitboxes(m,frame);const overlap=box.some(b=>b.x<hurt.x+hurt.w&&b.x+b.w>hurt.x&&b.y<hurt.y+hurt.h&&b.y+b.h>hurt.y);const reacted=frame>=18;const guarded=dummy==='guard'||(dummy==='ai'&&reacted);return{phase:stateAt(m,frame),box,hurt,overlap,result:m.support?'领域布置 · 无直接伤害':overlap?(guarded?'防御':'命中'):'未命中',guarded};}
 function trace(m,frame,distance,dummy){const events=[],windows=new Set();for(let f=m.startup+1;f<=Math.min(frame,duration(m));f++){const s=sample(m,f,distance,dummy),window=Math.floor((f-m.startup-1)/(m.interval||Math.max(m.active,m.flight||0)));if(s.overlap&&!windows.has(window)&&events.length<(m.hitCount||1)){windows.add(window);events.push({frame:f,result:s.result,damage:s.guarded?0:m.damage/(m.hitCount||1)});}}return{events,damage:events.reduce((n,e)=>n+e.damage,0)};}
 root.ProbeModel={duration,stateAt,actorOffset,hitboxes,sample,trace,clamp};
})(typeof window==='undefined'?globalThis:window);

/* 60Hz isolated choreography candidate. Combat integration remains pending. */
(function(root){
 'use strict';
 const hits=[{tick:55,id:'q-slash',weight:3,stop:12}];
 const outcomes=['hit','block','miss','invulnerable','downed','range'];
 function create(outcome='hit',action='q',origin={x:430,y:450},target){
  if(!outcomes.includes(outcome)||!['q','heavy','dash'].includes(action))throw Error('Invalid action/outcome');
  if(!Number.isFinite(origin.x)||!Number.isFinite(origin.y))throw Error('Invalid origin');
  target=target||{x:origin.x+(outcome==='range'?500:action==='q'?80:action==='dash'?245:165),y:origin.y};
  if(!Number.isFinite(target.x)||!Number.isFinite(target.y))throw Error('Invalid target');
  return {target:{...target},rejectReason:null,tick:-1,wallTick:0,stop:0,confirmed:false,confirmationChecked:false,failed:false,ended:false,outcome,action,origin:{...origin},events:[],contacts:[],hits:0,spent:[]};
 }
 function nearby(s){const dx=s.target.x-s.origin.x,dy=s.target.y-s.origin.y;return dx>=0&&dx<=120&&Math.abs(dy)<=40;}
 function emit(s,h){if(s.spent.includes(h.id))return;s.spent.push(h.id);s.hits++;s.events.push({...h,atWall:s.wallTick});s.stop=h.stop;}
 function step(s){
  if(s.ended)return s;s.wallTick++;
  if(s.stop>0){s.stop--;return s;}s.tick++;
  if(s.action==='q'){
   // Nondamaging confirmation selects the branch before the cinematic starts.
   if(s.tick===8){s.confirmationChecked=true;s.confirmed=s.outcome==='hit'&&nearby(s);s.failed=!s.confirmed;s.rejectReason=s.failed?(nearby(s)?s.outcome:'range'):null;if(s.outcome==='block'&&nearby(s))s.contacts.push({kind:'block',atWall:s.wallTick,tick:8});}
   if(s.tick===55&&s.confirmed)emit(s,hits[0]);
   if(s.tick>=(s.failed?28:104))s.ended=true;
  }else{
   if(s.tick===20){s.confirmationChecked=true;s.confirmed=s.outcome==='hit';if(s.outcome==='block')s.contacts.push({kind:'block',atWall:s.wallTick,tick:20});if(s.confirmed)emit(s,{tick:20,id:s.action+'-brake',weight:2,stop:8});}
   if(s.tick>=54)s.ended=true;
  }
  return s;
 }
 const clamp=v=>Math.max(0,Math.min(1,v)),mix=(a,b,p)=>a+(b-a)*p;
 function choreography(s){
  const t=Math.max(0,s.tick),o=s.origin;
  if(s.action!=='q'){
   const dash=s.action==='dash';return {x:o.x+Math.min(t,20)*(dash?12:8),y:o.y,pose:t>=12?'brake':'ride'};
  }
  if(s.failed)return {...o,pose:'idle'};
  if(t<=8)return {...o,pose:'idle'};
  if(t<32){const p=clamp((t-8)/23);return {x:mix(o.x,o.x+220,p),y:mix(o.y,o.y-220,p),pose:'ride'};}
  if(t<55)return {x:o.x+220,y:o.y-220,pose:'windup'};
  if(t<74){const p=clamp((t-55)/19);return {x:mix(o.x+220,o.x,p),y:mix(o.y-220,o.y,p),pose:'slash'};}
  return {...o,pose:t>=86?'idle':'slash'};
 }
 function endTick(s){return s.action==='q'?(s.failed?28:104):54;}
 function seek(outcome,tick,action='q',origin,target){
  if(!Number.isFinite(tick)||tick<-1)throw Error('Invalid seek tick');
  const s=create(outcome,action,origin,target);while(!s.ended&&s.tick<Math.floor(tick))step(s);return s;
 }
 function phase(s){
  if(s.action!=='q'){if(s.tick<12)return '骑车冲入';if(s.tick<20)return '制动 · 侧滑';if(s.tick<32)return s.confirmed?'车铲命中':'车铲 · 未命中';return '刹停收势';}
  if(s.failed)return s.rejectReason==='range'?'非近距离 · 不进入演出':'未命中确认 · 原地短收招';
  if(s.tick<=8)return '起手 · 近距离命中确认';
  if(s.tick<32)return '驰轮车 · 斜上冲向太阳';if(s.tick<55)return '离车切剑 · 蓄力';if(s.tick<74)return '一刀斩落 · 单次伤害';if(s.tick<86)return '原位落地 · 收刀';return '原地恢复';
 }
 function snapshot(s){return JSON.parse(JSON.stringify(s));}
 const api={hits,nearby,create,step,seek,phase,snapshot,choreography,endTick};if(typeof module==='object'&&module.exports)module.exports=api;else root.QModel=api;
})(typeof globalThis==='object'?globalThis:this);

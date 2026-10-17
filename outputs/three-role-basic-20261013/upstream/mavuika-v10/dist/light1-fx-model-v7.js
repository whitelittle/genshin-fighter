(function(root){'use strict';
 const bindings=[{support:[520,552],hand:[480,150],bladeRoot:[440,120],tip:[125,15]},{support:[1200,567],hand:[1280,170],bladeRoot:[1240,130],tip:[920,15]},{support:[340,997],hand:[500,731],bladeRoot:[540,732],tip:[894,735]},{support:[1170,1003],hand:[1270,795],bladeRoot:[1300,811],tip:[1520,986]}];
 function pose(s){if(s.ended)return -1;return s.tick<10?0:s.tick<14?1:s.tick<=16?2:3;}
 function landmarks(s,index=pose(s)){const b=bindings[index],point=k=>({x:s.x+s.facing*(b[k][0]-b.support[0])*.4,y:s.y+(b.support[1]-b[k][1])*.4});return{hand:point('hand'),bladeRoot:point('bladeRoot'),tip:point('tip')};}
 function sample(s){if(s.interrupted||s.ended)return[];const out=[],p=landmarks(s),add=(index,point,alpha=1,rotation=0,layer='blade')=>out.push({index,x:point.x,y:point.y,alpha,rotation,facing:s.facing,layer});
  if(s.tick>=6&&s.tick<10)add(0,{x:(p.tip.x+p.bladeRoot.x)/2,y:(p.tip.y+p.bladeRoot.y)/2},.45+(s.tick-6)*.1);
  if(s.tick>=10&&s.tick<14)add(1,p.tip,.35+(s.tick-10)*.12,14);
  if(s.tick>=14&&s.tick<=16)add(2,p.bladeRoot,s.blocked?.4:.78,-4);
  if(s.tick>=17&&s.tick<=23)add(3,landmarks(s,2).bladeRoot,1-(s.tick-17)/7,-4,'residue');
  for(const event of s.events){const age=s.wallTick-event.atWall;if(age<0)continue;
   if(event.kind==='hit'&&age<=9)add(age===0?4:age<=2?5:age<=5?6:7,event.contact,age>=6?(10-age)/4:1,0,'contact');
   if(event.kind==='block'&&age<=9)add(age===0?8:age<=2?9:age<=5?10:11,event.contact,age>=6?(10-age)/4:1,0,'contact');
  }return out;
 }
 function receiver(s){const event=s.events[0];if(!event)return{pose:s.target.guard?'guard_2':'idle_0',x:s.target.x,y:s.target.y,flash:0};const age=Math.max(0,s.tick-event.tick),wallAge=s.wallTick-event.atWall;
  if(event.kind==='block')return{pose:age<7?'guard_6':'guard_2',x:s.target.x,y:s.target.y,flash:0};
  return{pose:age<18?'hurt_0':'idle_0',x:s.target.x+s.facing*Math.min(1,age/12)*20,y:s.target.y,flash:wallAge<2?.28:0};
 }
 const api={bindings,landmarks,sample,receiver,pose};root.Light1FX=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);

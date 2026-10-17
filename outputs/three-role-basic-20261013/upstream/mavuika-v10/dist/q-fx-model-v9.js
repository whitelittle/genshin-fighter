/* Presentation only; contacts are preview-selected, not combat collision. */
(function(root){
'use strict';const Q=typeof module==='object'?require('./q-model.js'):root.QModel;
const bindings={ride:{wheel:[155,501],contact:[700,280]},brake:{wheel:[650,510],contact:[680,450]},windup:{grip:[413,24],guard:[333,28],tip:[15,80]},slash:{grip:[386,350],guard:[433,360],tip:[734,486]}};
const refs={ride:[155,501],brake:[650,510],windup:[500,476],slash:[407,478]};
function point(c,kind){const b=bindings[c.pose][kind],r=refs[c.pose];return{x:c.x+(b[0]-r[0])*.42,y:c.y+(b[1]-r[1])*.42};}
function frame(s){const t=Math.max(0,s.tick),c=Q.choreography(s),layers=[];const add=(id,p,alpha=1,bank='q',mult=1,plane='rear',rotation=0)=>layers.push({id,...p,alpha,bank,mult,plane,rotation});
 const blade=(body)=>{const g=point(body,'guard'),tip=point(body,'tip');return {g,rotation:Math.atan2(tip.y-g.y,tip.x-g.x)-Math.atan2(290,340)};};
 if(!s.ended){
  if(s.action==='q'&&s.confirmed){
   if(t<70)add(t<15?'sun-open':t<55?'sun-full':'sun-fade',{x:650,y:110},t<55?.78:Math.max(0,(70-t)/15)*.65,'q',1);
   if(t>=9&&t<32)add('wheel-trail',point(c,'wheel'),.55,'q',.72);
   if(t>=36&&t<55)add('charge',point(c,'guard'),.35+(t-36)/19*.35,'q',.65,'front');
   
   if(t>=55&&t<62){const b=blade(c);add('slash',b.g,.65-(t-55)*.06,'q',.50,'rear',b.rotation);}
   if(t>=62&&t<74){const start=Q.choreography(Q.seek('hit',61,'q',s.origin));const b=blade(start);add('slash-residue',b.g,(74-t)/12*.3,'q',.5,'rear',b.rotation);}
  }
  if((s.action!=='q'||s.failed)&&c.pose!=='idle'){
   const wheel=point(c,'wheel');if(t<12)add('wheel-trail',wheel,.55,'q',.72);
   if(t>=12&&t<25)add('brake-sparks',wheel,.6-(t-12)*.03,'q',.75,'ground');
   if(t>=25&&t<42)add('skid-residue',wheel,(42-t)/17*.35,'q',.75,'ground');
  }
  const contact=s.events.length?{kind:'hit',...s.events[0]}:s.contacts[0];
  if(contact){const age=s.wallTick-contact.atWall;
   // Choreographed receiver contact; this is not a collision proof.
   const at=Q.choreography(Q.seek('hit',contact.tick,s.action,s.origin));const p=s.action==='q'&&contact.kind==='hit'?point(at,'tip'):point(at,'contact');
   if(age>=0&&age<10){if(contact.kind==='block')add(['block-start','block-peak','block-fragments','block-fade'][age===0?0:age<3?1:age<6?2:3],p,(10-age)/10*.75,'light',.8,'front');else add(age<4?'impact':'impact-fade',p,(10-age)/10*.65,'q',s.action==='q'?.55:.4,'front');}
  }
 }
 const contact=s.events.length?{kind:'hit',...s.events[0]}:s.contacts[0],age=contact?s.wallTick-contact.atWall:999;
 let receiver={pose:s.outcome==='block'?'guard_2':'idle_0',x:s.origin.x+(s.action==='q'?290:s.action==='dash'?245:165),y:s.origin.y,flash:false};
 if(s.action==='q'&&s.outcome==='block')receiver.x=point(Q.choreography(Q.seek('hit',8,'q',s.origin)),'contact').x;
 if(s.outcome==='range')receiver.x=1100;
 if(contact&&age<18&&age>=0){receiver.pose=contact.kind==='hit'?'hurt_0':'guard_6';receiver.flash=contact.kind==='hit'&&age<2;if(contact.kind==='hit')receiver.x+=Math.min(24,age*2);}
 if(s.action==='q'&&s.confirmed&&t>=9&&t<74){const tip=point(Q.choreography(Q.seek('hit',55,'q',s.origin)),'tip');receiver.x=tip.x+(t>=55?Math.min(60,age*2.5):0);const p=t<32?Math.min(1,(t-8)/23):t<55?1:Math.max(0,1-(t-55)/18);receiver.y=s.origin.y+(tip.y+90-s.origin.y)*p;}
 if(s.action==='q'&&s.confirmed&&t>=74){receiver.x=point(Q.choreography(Q.seek('hit',55,'q',s.origin)),'tip').x+60;}
 return {body:c,layers,receiver,bindings,contactKind:contact?.kind||null};}
const api={frame,point,bindings};if(typeof module==='object'&&module.exports)module.exports=api;else root.QFX=api;
})(typeof globalThis==='object'?globalThis:this);

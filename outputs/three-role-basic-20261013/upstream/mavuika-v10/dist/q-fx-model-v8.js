/* Presentation only; contacts are preview-selected, not combat collision. */
(function(root){
'use strict';const Q=typeof module==='object'?require('./q-model.js'):root.QModel;
const bindings={ride:{wheel:[155,488]},brake:{wheel:[645,500]},windup:{grip:[413,24],tip:[15,80]},slash:{grip:[413,357],tip:[733,487]}};
const refs={ride:[280,496],brake:[645,500],windup:[500,476],slash:[407,478]};
function point(c,kind){const b=bindings[c.pose][kind],r=refs[c.pose];return{x:c.x+(b[0]-r[0])*.42,y:c.y+(b[1]-r[1])*.42};}
function frame(s){const t=Math.max(0,s.tick),c=Q.choreography(s),layers=[];const add=(id,p,alpha=1,bank='q',mult=1)=>layers.push({id,...p,alpha,bank,mult});
 if(!s.ended){
  if(s.action==='q'&&s.confirmed){
   if(t<70)add(t<15?'sun-open':t<55?'sun-full':'sun-fade',{x:650,y:110},t<55?.78:Math.max(0,(70-t)/15)*.65,'q',1);
   if(t>=9&&t<32)add('wheel-trail',point(c,'wheel'),.72);
   if(t>=36&&t<55)add('charge',point(c,'grip'),.4+(t-36)/19*.5);
   if(t>=49&&t<55)add('blade-prepare',point(c,'grip'),.5);
   if(t>=55&&t<62)add('slash',point(c,'grip'),.85-(t-55)*.07);
   if(t>=62&&t<74){const start=Q.choreography(Q.seek('hit',61,'q',s.origin));add('slash-residue',point(start,'grip'),(74-t)/12*.5);}
  }
  if((s.action!=='q'||s.failed)&&c.pose!=='idle'){
   const wheel=point(c,'wheel');if(t<12)add('wheel-trail',wheel,.65);
   if(t>=12&&t<25)add('brake-sparks',wheel,.7-(t-12)*.03);
   if(t>=25&&t<42)add('skid-residue',wheel,(42-t)/17*.45);
  }
  const contact=s.events.length?{kind:'hit',...s.events[0]}:s.contacts[0];
  if(contact){const age=s.wallTick-contact.atWall;
   // Choreographed receiver contact; this is not a collision proof.
   const p=s.action==='q'&&contact.kind==='hit'?point(Q.choreography(Q.seek('hit',55,'q',s.origin)),'tip'):s.action==='q'?{x:s.origin.x+50,y:s.origin.y-30}:{x:s.origin.x+(s.action==='dash'?245:165),y:s.origin.y-28};
   if(age>=0&&age<10){if(contact.kind==='block')add(['block-start','block-peak','block-fragments','block-fade'][age===0?0:age<3?1:age<6?2:3],p,(10-age)/10,'light');else add(age<4?'impact':'impact-fade',p,(10-age)/10,'q',s.action==='q'?1:.7);}
  }
 }
 const contact=s.events.length?{kind:'hit',...s.events[0]}:s.contacts[0],age=contact?s.wallTick-contact.atWall:999;
 let receiver={pose:s.outcome==='block'?'guard_2':'idle_0',x:s.origin.x+(s.action==='q'?290:s.action==='dash'?245:165),y:s.origin.y,flash:false};
 if(s.outcome==='range')receiver.x=1100;
 if(contact&&age<18&&age>=0){receiver.pose=contact.kind==='hit'?'hurt_0':'guard_6';receiver.flash=contact.kind==='hit'&&age<2;if(contact.kind==='hit')receiver.x+=Math.min(24,age*2);}
 if(s.action==='q'&&s.confirmed&&t>=9&&t<74){const tip=point(Q.choreography(Q.seek('hit',55,'q',s.origin)),'tip');receiver.x=tip.x+(t>=55?Math.min(24,age*2):0);const p=t<32?Math.min(1,(t-8)/23):t<55?1:Math.max(0,1-(t-55)/18);receiver.y=s.origin.y+(tip.y+90-s.origin.y)*p;}
 return {body:c,layers,receiver,bindings,contactKind:contact?.kind||null};}
const api={frame,point,bindings};if(typeof module==='object'&&module.exports)module.exports=api;else root.QFX=api;
})(typeof globalThis==='object'?globalThis:this);

(function(root){'use strict';
 const CARD=Object.freeze({id:'mavuika-light1',startup:14,active:[14,16],end:36,damage:32,hitstop:6,blockstop:3,hitstun:18,knockback:20,attack:{x0:83,x1:226,y0:91,y1:118},status:'independent geometry candidate; formal engine pending'});
 function create(options={}){return{tick:0,wallTick:0,stop:0,ended:false,interrupted:false,facing:options.facing===-1?-1:1,x:options.x||0,y:options.y||0,hits:0,blocked:0,spent:[],events:[],target:Object.assign({x:150,y:0,width:36,height:180,guard:false,invulnerable:false,downed:false},options.target||{})};}
 function copy(s){return JSON.parse(JSON.stringify(s));}
 function attackBox(s){const b=CARD.attack;return{x0:s.x+(s.facing===1?b.x0:-b.x1),x1:s.x+(s.facing===1?b.x1:-b.x0),y0:s.y+b.y0,y1:s.y+b.y1};}
 function targetBox(s){const t=s.target;return{x0:t.x-t.width/2,x1:t.x+t.width/2,y0:t.y,y1:t.y+t.height};}
 function overlap(a,b){return a.x0<b.x1&&a.x1>b.x0&&a.y0<b.y1&&a.y1>b.y0;}
 function phase(s){if(s.interrupted)return'interrupted';if(s.ended)return'ended';if(s.tick<10)return'prepare';if(s.tick<14)return'release';if(s.tick<=16)return'active';return'recover';}
 function pose(s){return s.tick<10?0:s.tick<14?1:s.tick<=16?2:3;}
 function step(s){if(s.ended)return s;s.wallTick++;if(s.stop>0){s.stop--;return s;}s.tick++;
  if(s.tick>=14&&s.tick<=16&&!s.spent.includes('light1:0')&&!s.target.invulnerable&&!s.target.downed&&overlap(attackBox(s),targetBox(s))){
   s.spent.push('light1:0');const block=!!s.target.guard;s.blocked+=block?1:0;s.hits+=block?0:1;s.stop=block?CARD.blockstop:CARD.hitstop;
   const a=attackBox(s),b=targetBox(s);const contact={x:s.facing===1?Math.max(a.x0,b.x0):Math.min(a.x1,b.x1),y:Math.round((Math.max(a.y0,b.y0)+Math.min(a.y1,b.y1))/2)};s.events.push({id:'light1:0',tick:s.tick,atWall:s.wallTick,contact,kind:block?'block':'hit',damage:block?0:CARD.damage,hitstun:block?0:CARD.hitstun,knockback:block?0:s.facing*CARD.knockback});
  }
  if(s.tick>=CARD.end)s.ended=true;return s;
 }
 function interrupt(s){s.interrupted=true;s.ended=true;s.stop=0;return s;}
 function seek(options,tick){const s=create(options);while(s.tick<Math.min(tick,CARD.end)&&!s.ended)step(s);return s;}
 function hash(s){let h=2166136261;for(const c of JSON.stringify(s)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return(h>>>0).toString(16).padStart(8,'0');}
 const api={CARD,create,copy,snapshot:copy,restore:copy,step,phase,pose,attackBox,targetBox,overlap,interrupt,seek,hash};root.Light1Model=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);

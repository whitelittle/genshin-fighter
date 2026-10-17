/* Independent visual preview. No collision or damage mutation. */
(()=>{'use strict';
const palette={nahida:['#6dae55','#d3f6a2'],kaeya:['#67b9e6','#e2fbff'],kamisatoayaka:['#89c5f3','#efffff'],diluc:['#e66331','#ffdda1'],neuvillette:['#409cd4','#d0fbff'],keqing:['#ac7fea','#f3dcff']};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function socket(pose,h,type){const low=/basic[567]|attack[345]/.test(pose),air=/basic(9|10|13)|attack[67]/.test(pose);let hand=[h*.20,-h*(low?.37:air?.60:.59)];if(/^connections/.test(pose)){const i=+pose.slice(11)%8;hand=[h*(.16+Math.sin(i/7*Math.PI)*.18),-h*(.59+Math.sin(i/7*Math.PI)*.07)];}return type==='hand'?hand:type==='chest'?[0,-h*(low?.34:.57)]:type==='feet'?[0,0]:[0,-h*.5];}
function draw(ctx,{type,frame,x,y,dir=1,scale=1,colorKey='nahida',contact='none',layer='all'}){const f=clamp(frame,0,59),u=f/60,p=palette[colorKey]||palette.nahida;ctx.save();ctx.translate(x,y);ctx.scale(dir*scale,scale);ctx.globalAlpha=f<10?f/10:f>42?(60-f)/18:1;ctx.lineCap='round';ctx.lineJoin='round';
const line=(pts,col,w=2)=>{ctx.strokeStyle=col;ctx.lineWidth=w;ctx.beginPath();pts.forEach((q,i)=>i?ctx.lineTo(...q):ctx.moveTo(...q));ctx.stroke();};
const oval=(cx,cy,rx,ry,col,fill=false)=>{ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx[fill?'fillStyle':'strokeStyle']=col;fill?ctx.fill():ctx.stroke();};
const spark=(cx,cy,r)=>{line([[cx-r,cy],[cx+r,cy]],p[1],2);line([[cx,cy-r],[cx,cy+r]],p[1],2);};
if(layer==='all'||layer==='body'){
 if(type==='orb'){const travel=Math.max(0,(f-12)/30)*110;oval(travel,0,12+Math.sin(u*Math.PI)*5,12,p[0],true);oval(travel,0,7,7,p[1],true);line([[travel-32,-3],[travel-12,0]],p[0]+'88',4);}
 if(type==='slash'){ctx.strokeStyle=p[0];ctx.lineWidth=6;ctx.beginPath();ctx.arc(5,0,35,-1.3+u*.7,1.1+u*.7);ctx.stroke();ctx.strokeStyle=p[1];ctx.lineWidth=2;ctx.stroke();}
 if(type==='seal'){oval(0,0,24+u*9,24+u*9,p[0]);for(let i=0;i<4;i++){const a=i*Math.PI/2+u*.4,cx=Math.cos(a)*18,cy=Math.sin(a)*18;oval(cx,cy,10,5,p[1]);}spark(0,0,7);}
 if(type==='ground'){oval(0,0,50,10,p[0]);for(let i=0;i<5;i++)line([[-40+i*20,0],[-38+i*20,-Math.sin(u*Math.PI)*(18+i%2*12)],[-34+i*20,-4]],p[1],2);}
}
if((layer==='all'||layer==='contact')&&contact!=='none'&&f>=20&&f<=28){const cx=type==='orb'?Math.max(0,(f-12)/30)*110:0;for(let i=0;i<6;i++){const a=i*Math.PI/3;line([[cx+Math.cos(a)*8,Math.sin(a)*8],[cx+Math.cos(a)*22,Math.sin(a)*22]],contact==='guard'?'#8dbde8':p[1],2);}if(contact==='guard')oval(cx,0,22,26,'#8dbde8');}
ctx.restore();}
window.EffectLab={socket,draw,duration:60,version:'attachment-study-v1'};
})();

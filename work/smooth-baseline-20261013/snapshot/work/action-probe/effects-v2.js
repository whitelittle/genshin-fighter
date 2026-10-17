/* Reference-constrained visual studies. No battle state, randomness or hitbox mutation. */
(()=>{'use strict';
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),mix=(a,b,t)=>a+(b-a)*t;
const palettes={hydro:['#143e97','#27a8fb','#8feaff','#effeff'],electro:['#432873','#9864eb','#d7b2ff','#fff0ff'],dendro:['#21583c','#63ae62','#bcea84','#f0ffd0'],cryo:['#366db4','#90caff','#d4f4ff','#fff'],pyro:['#a23425','#ff8040','#ffc767','#fff3cc'],anemo:['#226b6b','#55c9ad','#a3f7d7','#f0fff5'],geo:['#694322','#bc873b','#edd18e','#fff4cf']};
const elements={neuvillette:'hydro',tartaglia:'hydro',nahida:'dendro',kamisatoayaka:'cryo',raidenshogun:'electro',yaemiko:'electro',zhongli:'geo',navia:'geo',hutao:'pyro',klee:'pyro',xiao:'anemo',venti:'anemo',keqing:'electro',diluc:'pyro'};
function draw({ctx,move:m,frame:f,role,model:M,low=false,action='A',contact=null,distance=240,motion=null}){
 const t=f-m.startup,life=Math.max(m.active,m.flight||0,m.effectDuration||0),tail=m.projectile?0:12;
 if(f<=0||t>life+tail)return true;
 const hit=contact?.overlap===true;const fx=m.fx,p=palettes[elements[role.key]||'electro'],end=m.reach,offset=M.actorOffset(m,f),progress=clamp(t/Math.max(1,life)),fade=t>life?1-(t-life)/tail:1;
 ctx.save();ctx.beginPath();ctx.rect(-m.effectExtent,-360,m.effectExtent*2,390);ctx.clip();ctx.globalAlpha=Math.max(0,fade);ctx.lineJoin='round';ctx.lineCap='round';
 const stroke=(pts,col,width=2,closed=false)=>{ctx.strokeStyle=col;ctx.lineWidth=width;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));if(closed)ctx.closePath();ctx.stroke();};
 const poly=(pts,col)=>{ctx.fillStyle=col;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();ctx.fill();};
 const ell=(x,y,rx,ry,col)=>{ctx.fillStyle=col;ctx.beginPath();ctx.ellipse(x,y,Math.max(.1,rx),Math.max(.1,ry),0,0,Math.PI*2);ctx.fill();};
 const ring=(x,y,rx,ry,col,width=2)=>{ctx.strokeStyle=col;ctx.lineWidth=width;ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.stroke();};
 const diamond=(x,y,size,col)=>poly([[x,y-size],[x+size*.65,y],[x,y+size],[x-size*.65,y]],col);
 const leaf=(x,y,size,a,col)=>{ctx.save();ctx.translate(x,y);ctx.rotate(a);ctx.fillStyle=col;ctx.beginPath();ctx.moveTo(-size,0);ctx.quadraticCurveTo(0,-size,size,0);ctx.quadraticCurveTo(0,size,-size,0);ctx.fill();stroke([[-size,0],[size,0]],p[3]+'88',1);ctx.restore();};
 const glow=(x,y,r,col)=>{if(low)return;const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,col+'a0');g.addColorStop(1,col+'00');ell(x,y,r,r,g);};
 const sparks=(cx,cy,n,r,col,stretch=1)=>{for(let i=0;i<(low?Math.ceil(n/3):n);i++){const seed=(i*73+19)%127/127,a=i*2.399+f*.024,rr=r*(.3+seed*.7),x=cx+Math.cos(a)*rr,y=cy+Math.sin(a)*rr/stretch;diamond(x,y,1.3+seed*2.3,col);}};
 const bolt=(x,y,ex,ey,col,width=3,seed=0)=>{const pts=[[x,y]];for(let i=1;i<9;i++){const q=i/9,wave=Math.sin(i*13+seed+Math.floor(f/3))*10;pts.push([mix(x,ex,q)+(ey!==y?wave:0),mix(y,ey,q)+(ey===y?wave:0)]);}pts.push([ex,ey]);stroke(pts,col,width);};
 const blossom=(x,y,r,col)=>{for(let i=0;i<4;i++)leaf(x+Math.cos(i*Math.PI/2)*r*.65,y+Math.sin(i*Math.PI/2)*r*.65,r*.6,i*Math.PI/2,col);diamond(x,y,r*.3,p[3]);};
 const telegraph=()=>{const at=Math.min(end-25,160),u=clamp(f/m.startup);ring(at,-4,30+u*18,6,p[2]+'88',1.5);if(['waterpillar','icepillar','thunder','cannon','meteor','windpillar','pillar'].includes(fx)){stroke([[at,-8],[at,-220]],p[1]+'44',1);diamond(at,-220,6+u*6,p[2]+'88');}else{glow(offset+36,-134,28+u*24,p[1]);ring(offset+36,-134,12+u*13,18+u*18,p[2]+'aa');sparks(offset+36,-134,8,28,p[2]+'88');}};
 if(t<=0){if(fx==='beam'){const q=motion?.pose(role,action,m,f,M),hx=q?.hand[0]??28,hy=q?.hand[1]??-143;glow(offset+hx,hy,24+clamp(f/m.startup)*18,p[1]);ring(offset+hx,hy,13,17,p[2]+'bb',2);sparks(offset+hx,hy,8,24,p[2]+'88');}else telegraph();ctx.restore();return true;}
 // Primary bodies stay within candidate ranges; ornamental fades never create hitboxes.
 // Sword trails follow the same hand and blade geometry as the motion study.
 if(role.key==='keqing'&&['slash','afterimage','stiletto'].includes(fx)&&motion){
  const age=Math.max(0,t-m.active),alpha=1-clamp(age/8);ctx.globalAlpha*=alpha;
  const recent=[];for(let i=0;i<(low?3:7);i++){const pf=Math.max(m.startup+1,Math.min(f-i*.65,m.startup+m.active));const q=motion.pose(role,action,m,pf,M);recent.push([offset+q.tip[0],q.tip[1]]);}
  if(t<=m.active+8){stroke(recent,p[1]+'55',14);stroke(recent,p[2]+'dd',5);stroke(recent,p[3],1.8);}
  if(fx==='stiletto'){const at=m.reach-14;diamond(at,-141,12,p[2]);diamond(at,-141,5,p[3]);if(t<2)stroke([[28,-141],[at,-141]],p[2]+'88',2);else{for(let i=0;i<3;i++)stroke([[offset-45-i*22,-178+i*22],[offset-12-i*18,-172+i*22]],p[2]+'66',3);}}
  if(fx==='afterimage'&&t<=m.active){for(let i=0;i<3;i++){const dx=offset-(i+1)*25;stroke([[dx,-194],[dx+12,-155],[dx,-100]],p[2]+'44',8);stroke([[dx-12,-94],[dx-25,-6]],p[2]+'33',5);}}
  if(hit){const cy=-126,cx=Math.min(m.reach,distance);stroke([[cx-15,cy-22],[cx+17,cy+21]],contact.guarded?p[2]:p[3],3);stroke([[cx-18,cy+13],[cx+20,cy-15]],p[2],2);sparks(cx,cy,9,25,p[2]);}
  ctx.restore();return true;
 }

 if(fx==='beam'){
  const x=offset+28,len=Math.max(1,end-x),open=clamp(t/7)*clamp((life+7-t)/9),cy=-143,half=25*open;
  const g=ctx.createLinearGradient(x,0,end,0);g.addColorStop(0,p[3]+'ec');g.addColorStop(.18,p[2]+'cc');g.addColorStop(.8,p[1]+'a0');g.addColorStop(1,p[0]+'00');
  const upper=[],lower=[];for(let i=0;i<=32;i++){const q=i/32,xx=x+q*len,wave=Math.sin(q*19-f*.23)*4;upper.push([xx,cy-half-wave]);lower.unshift([xx,cy+half+wave]);}poly([...upper,...lower],g);
  for(let j=0;j<(low?3:9);j++){const pts=[];for(let i=0;i<=28;i++){const q=i/28;pts.push([x+q*len,cy+(j/(low?2:8)-.5)*half*1.6+Math.sin(q*22-f*.32+j)*3]);}stroke(pts,j%3===0?p[3]+'c0':p[2]+'85',j%3===0?2.3:1.1);}
  glow(x,cy,50,p[1]);ring(x,cy,11,half+8,p[3]+'cc',3);ring(x+8,cy,19,half+14,p[2]+'70',1.5);if(hit){const cx=Math.min(end,distance);sparks(cx,cy,18,38,p[2]+'d0',1.6);ring(cx,cy,10+(t%10)*2,24,p[3]+'99',2);}else{for(let i=0;i<5;i++)ell(end-12+i*2,cy+Math.sin(f*.2+i)*17,2,4,p[2]+'66');}
  for(let i=0;i<(low?3:10);i++){const q=((f*9+i*47)%Math.max(1,len))/len;ell(x+q*len,cy+Math.sin(i*7+f*.08)*half*.8,8,1,p[3]+'88');}
 }else if(fx==='shrine'){
  const grow=clamp(t/18),r=end*grow,h=265*grow;const g=ctx.createLinearGradient(0,-h,0,0);g.addColorStop(0,'#80d99012');g.addColorStop(.7,'#70b86e16');g.addColorStop(1,'#b9ed8528');
  ctx.fillStyle=g;ctx.beginPath();ctx.moveTo(-r,0);ctx.bezierCurveTo(-r,-h*.45,-r*.25,-h,0,-h);ctx.bezierCurveTo(r*.25,-h,r,-h*.45,r,0);ctx.closePath();ctx.fill();
  ring(0,-3,r,17,p[2]+'a0',2.2);ring(0,-5,r*.94,14,p[1]+'80',1);
  for(let i=0;i<(low?5:9);i++){const x=(i/((low?5:9)-1)*2-1)*r*.9,top=-h*Math.sqrt(Math.max(0,1-(x/r)**2));ctx.strokeStyle=p[2]+'88';ctx.lineWidth=1.6;ctx.beginPath();ctx.moveTo(x,0);ctx.bezierCurveTo(x*.96,top*.4,x*.35,top*.85,0,-h);ctx.stroke();const rr=r/(low?5:9)*.82;ctx.beginPath();ctx.moveTo(x-rr,0);ctx.quadraticCurveTo(x-rr,top*.64,x,top*.77);ctx.quadraticCurveTo(x+rr,top*.64,x+rr,0);ctx.stroke();blossom(x,top*.72,8,p[2]+'a0');}
  blossom(0,-h+24,19,p[2]+'cc');sparks(0,-120,22,r*.75,p[2]+'77',1.6);
 }else if(fx==='mark'||fx==='leaf'){
  if(fx==='mark'){const x1=30,x2=end-12,y1=-184,y2=-58,s=17;for(const[x,y,a,b]of[[x1,y1,1,1],[x2,y1,-1,1],[x1,y2,1,-1],[x2,y2,-1,-1]])stroke([[x+a*s,y],[x,y],[x,y+b*s]],p[2],2.4);const at=end*.72;blossom(at,-122,26,p[1]+'99');ring(at,-122,38,38,p[2]+'80',1.2);stroke([[x1,-122],[at-30,-122]],p[1]+'70',1);sparks(at,-122,9,44,p[2]+'c0');}
  else{for(let i=0;i<5;i++)leaf(26+i*(end-35)/5,-102+Math.sin(t*.22+i)*16,8,t*.1+i,p[2]+'c0');blossom(end-22,-105,17*clamp(t/3),p[2]+'99');}
 }else if(['blizzard','vortex','windpillar'].includes(fx)){
  const box=M.hitboxes(m,f)[0],at=fx==='windpillar'?Math.min(end-25,120):box?box.x+box.w/2:end-60,h=fx==='windpillar'?220:175;
  for(let j=0;j<(low?3:8);j++){const pts=[];for(let i=0;i<30;i++){const q=i/29,a=q*Math.PI*3+f*.18+j*.8,w=(24+q*26)*(fx==='vortex'?1.3:1);pts.push([at+Math.cos(a)*w,-q*h-8]);}stroke(pts,j%2?p[2]+'aa':p[1]+'88',j%2?1.4:3);}
  glow(at,-h*.5,76,p[1]);ring(at,-6,48,9,p[2]+'c0');for(let i=0;i<(low?5:18);i++){const q=(i/18+f*.013)%1,a=i*2.4+f*.13,x=at+Math.cos(a)*(30+q*18),y=-q*h;if(fx==='blizzard'){diamond(x,y,5,p[2]+'cc');stroke([[x-5,y],[x+5,y]],p[3],1);}else leaf(x,y,5,a,p[2]+'99');}
 }else if(['waterpillar','icepillar','pillar','meteor','thunder','cannon'].includes(fx)){
  const at=Math.min(end-30,160),isStrike=fx==='thunder'||fx==='cannon',tick=isStrike?(t-1)%(m.interval||18):t,pulse=isStrike?clamp(1-tick/11):clamp(t/3)*clamp((m.active+8-t)/8);
  if(fx==='waterpillar'){const hh=200*pulse,gg=ctx.createLinearGradient(0,-hh,0,0);gg.addColorStop(0,p[3]+'00');gg.addColorStop(.6,p[2]+'bb');gg.addColorStop(1,p[1]+'55');poly([[at-30,0],[at-19,-hh],[at+8,-hh-10],[at+27,0]],gg);for(let i=0;i<(low?5:14);i++){const y=-((t*16+i*17)%220),x=at+Math.sin(i*13)*35;ell(x,y,2.5,7,p[2]+'aa');}ring(at,0,48,9,p[2]);glow(at,-80,60,p[1]);}
  else if(fx==='icepillar'){for(let i=0;i<5;i++){const x=at+(i-2)*23,h=(i%2?88:140)*pulse;poly([[x-16,0],[x-9,-h*.7],[x+3,-h],[x+14,-h*.38],[x+20,0]],p[i%2?1:2]+'bb');stroke([[x+3,-h],[x+1,-5]],p[3]+'cc',1.4);}ring(at,-3,75,13,p[2]);sparks(at,-70,14,85,p[2]+'aa');}
  else if(fx==='pillar'){const h=190*pulse;poly([[at-24,0],[at-24,-h],[at+24,-h-10],[at+24,0]],p[0]);poly([[at-24,-h],[at+7,-h-20],[at+34,-h-8],[at+24,-h+8]],p[2]);poly([[at+24,0],[at+34,-8],[at+34,-h-8],[at+24,-h+8]],p[1]);for(let j=0;j<4;j++){const y=-25-j*38;stroke([[at-15,y],[at,y-12],[at+15,y],[at,y+12],[at-15,y]],p[2]+'cc',2);}ring(at,0,55,9,p[2]+'aa');}
  else if(fx==='meteor'){const fall=clamp(t/m.active),y=-285+fall*260;ctx.save();ctx.translate(at,y);ctx.rotate(.35);poly([[-48,-50],[5,-68],[64,-32],[54,34],[-8,56],[-55,9]],p[0]);poly([[-48,-50],[5,-68],[64,-32],[6,-8]],p[2]);stroke([[-48,-50],[6,-8],[54,34]],p[1],6);stroke([[5,-68],[6,-8],[-8,56]],p[3]+'aa',2);ctx.restore();for(let i=0;i<4;i++)stroke([[at+(i-2)*18,y-70],[at+(i-2)*13,y-150]],p[2]+'88',4);if(fall>.75){ring(at,-4,110*(fall-.75)*4,16,p[2]+'cc',4);sparks(at,-18,24,90,p[2]);}}
  else if(fx==='thunder'){if(pulse>0){for(let i=0;i<3;i++){const x=at+(i-1)*45;glow(x,-90,55,p[1]);bolt(x+12,-285,x,-5,p[1]+'dd',9*pulse,i);bolt(x+12,-285,x,-5,p[3]+'ee',2.5*pulse,i);ring(x,-5,28+pulse*17,7,p[2]+'aa');}sparks(at,-30,20,90,p[2]+'bb');}}
  else if(fx==='cannon'){const count=Math.floor((t-1)/(m.interval||18))%3,x=75+count*(end-90)/3;ring(x,-4,40,8,p[2]+'99');if(pulse>0){stroke([[x-85,-290],[x,0]],p[1]+'bb',16*pulse);stroke([[x-85,-290],[x,0]],p[3]+'dd',3*pulse);glow(x,-10,90*pulse,p[1]);ring(x,-6,65*pulse,12,p[2],3);sparks(x,-22,24,85*pulse,p[2]);}}
 }else if(['lightning','eye','fox','totem'].includes(fx)){
  if(fx==='lightning'){poly([[25,-147],[end,-124],[end,-104],[25,-94]],p[1]+'55');bolt(25,-120,end,-120,p[1],11);bolt(25,-120,end,-120,p[3],2.8);for(let i=0;i<5;i++)bolt(70+i*(end-80)/5,-120,90+i*(end-90)/5,-180+(i%2)*100,p[2]+'99',1.5,i);sparks(end-25,-120,16,45,p[2]);}
  if(fx==='eye'||fx==='totem'){const x=fx==='eye'?35:145,y=fx==='eye'?-235:-94;glow(x,y,55,p[1]);ctx.strokeStyle=p[2];ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x-38,y);ctx.quadraticCurveTo(x,y-25,x+38,y);ctx.quadraticCurveTo(x,y+25,x-38,y);ctx.stroke();diamond(x,y,10,p[3]);if(fx==='totem'){poly([[x-20,0],[x-12,-90],[x,-120],[x+12,-90],[x+20,0]],p[0]+'aa');poly([[x-29,-98],[x,-128],[x+29,-98],[x,-104]],p[2]+'cc');stroke([[x,-80],[x,-8]],p[1],4);ring(x,-4,32,7,p[2]+'99');}else bolt(30,-105,end,-105,p[2],4);}
  if(fx==='fox'){const x=28+clamp(t/Math.max(1,m.active))*Math.max(1,end-55);poly([[x-25,-101],[x-8,-118],[x-6,-137],[x+4,-122],[x+18,-137],[x+19,-116],[x+32,-104],[x+10,-97],[x-6,-85]],p[2]+'bb');stroke([[x-30,-103],[x-55,-121],[x-36,-137],[x-13,-125]],p[1],7);bolt(25,-110,x-20,-105,p[3]+'77',1.5);diamond(x+11,-113,2,p[3]);}
 }else if(['shotgun','sparks','bomb','bounce','ghost','butterfly'].includes(fx)){
  if(fx==='shotgun'){glow(35,-112,38,p[2]);for(let i=0;i<(low?5:13);i++){const y=-112+(i/(low?4:12)-.5)*110;stroke([[35,-112],[end-12,y]],p[2]+'88',1.3);diamond(end-15,y,4,p[3]+'c0');}poly([[25,-111],[50,-136],[64,-110],[50,-88]],p[3]+'cc');ring(45,-112,19,26,p[1]+'99',2);}
  if(fx==='sparks'){const k=Math.floor((t-1)/(m.interval||20)),u=(t-1)%(m.interval||20);for(let i=0;i<3;i++){const x=70+i*65;glow(x,-210,26,p[1]);blossom(x,-210,13,p[2]);if(u<10){stroke([[x,-210],[x+25,-65]],p[1],6*(1-u/12));stroke([[x,-210],[x+25,-65]],p[3]+'aa',1.5);sparks(x+25,-65,8,20,p[2]);}}}
  if(fx==='bomb'||fx==='bounce'){const b=M.hitboxes(m,f)[0];if(b){const x=b.x+b.w/2,y=-b.y-b.h/2,r=fx==='bounce'?22:12;glow(x,y,30,p[1]);ell(x,y,r,r,'#dc755b');ring(x,y,r,r,'#ffcf9c',2);poly([[x-7,y-9],[x-13,y-r-10],[x-2,y-r-6],[x+4,y-r+1]],'#f0d9b4');poly([[x+7,y-9],[x+13,y-r-10],[x+2,y-r-6],[x-4,y-r+1]],'#f0d9b4');ell(x-4,y-2,1.6,2,'#4b3031');ell(x+4,y-2,1.6,2,'#4b3031');for(let i=1;i<7;i++){const bt=t-i;if(bt<=0)continue;const prev=M.hitboxes(m,m.startup+bt)[0];if(prev)ell(prev.x+prev.w/2,-prev.y-prev.h/2,2,2,p[2]+'77');}if(t>m.flight-3){glow(x,-15,55,p[1]);ring(x,-4,45,8,p[2]);sparks(x,-18,20,48,p[2]);}}}
  if(fx==='ghost'){const a=clamp(t/m.active)*Math.PI,x=75+Math.sin(a)*85,y=-108+Math.cos(a)*22;glow(x,y,45,p[1]);ctx.fillStyle='#fff0d6d0';ctx.beginPath();ctx.moveTo(x-30,y+15);ctx.bezierCurveTo(x-53,y-45,x+38,y-55,x+43,y-3);ctx.quadraticCurveTo(x+23,y+28,x+6,y+19);ctx.quadraticCurveTo(x-2,y+36,x-11,y+16);ctx.closePath();ctx.fill();ell(x+5,y-12,3,7,'#be7c64');ell(x+21,y-13,3,7,'#be7c64');stroke([[x+8,y+1],[x+15,y+8],[x+23,y]],'#c47f66',2);sparks(x-35,y+10,10,28,p[2]+'bb');}
  if(fx==='butterfly'){stroke([[offset+22,-100],[end,-100]],p[1]+'aa',6);stroke([[offset+22,-100],[end,-100]],p[3],1.8);for(let i=0;i<(low?3:8);i++){const x=offset-i*16,y=-65+Math.sin(i*4+f*.2)*18;leaf(x-3,y,5,-.6,p[2]+'aa');leaf(x+3,y,5,.6,p[2]+'aa');}}
 }else if(['dual','wave','water','dash','plunge','arrow','thrust','slash','fireblade','afterimage','stiletto'].includes(fx)){
  if(fx==='arrow'){const b=M.hitboxes(m,f)[0];if(b){const x=b.x+b.w/2;stroke([[x-28,-110],[x+20,-110]],p[2],3);poly([[x+20,-110],[x+10,-116],[x+10,-104]],p[3]);for(let i=0;i<3;i++)stroke([[x-30-i*8,-114+i*4],[x-80-i*8,-114+i*4]],p[1]+'77',1);}}
  else if(fx==='plunge'){const impact=clamp(t/3);stroke([[35,-280],[35,-3]],p[2]+'66',24);stroke([[35,-280],[35,-3]],p[3],4);ring(35,-6,end*impact,17,p[2]+'bb',3);sparks(35,-35,22,end*.65,p[2]);}
  else if(fx==='dash'||fx==='thrust'){poly([[offset+20,-122],[end,-110],[offset+20,-98]],p[1]+'77');stroke([[offset+20,-110],[end,-110]],p[3]+'dd',2.5);for(let i=0;i<4;i++)stroke([[offset-50-i*15,-95+i*10],[offset+12,-105+i*10]],p[2]+'55',1);sparks(end-20,-110,8,18,p[2]);}
  else if(fx==='stiletto'){diamond(end-14,-116,14,p[2]);diamond(end-14,-116,6,p[3]);bolt(28,-116,end-20,-116,p[2]+'77',1.5);if(t>=2){stroke([[offset+10,-177],[end,-57]],p[1],12);stroke([[offset+10,-177],[end,-57]],p[3],2);}}
  else{const n=fx==='afterimage'?5:fx==='dual'?2:1;for(let j=0;j<n;j++){const dy=fx==='afterimage'?(j-2)*26:j*23,pts=[];for(let i=0;i<=28;i++){const q=i/28,angle=-1.7+q*2.9,r=(end-offset)*.5;pts.push([offset+r+Math.cos(angle)*r,-112+dy+Math.sin(angle)*49]);}stroke(pts,p[1]+'66',low?6:12);stroke(pts,p[2]+'cc',3.5);stroke(pts,p[3]+'cc',1);}
   if(fx==='wave'||fx==='water'){const x=end-25;for(let i=0;i<8;i++)ell(x+Math.sin(i)*16,-65-i*11,2,5,p[2]+'aa');}sparks(end-23,-100,low?5:16,30,p[2]+'bb');}
 }else{ctx.restore();return false;}
 ctx.restore();return true;
}
window.ProbeFX={draw,revision:3,deterministic:true,productionCombatChanged:false};
})();

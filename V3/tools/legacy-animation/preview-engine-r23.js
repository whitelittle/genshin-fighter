'use strict';
const $=id=>document.getElementById(id),cv=$('cv'),ctx=cv.getContext('2d');
const nahida=CHAR==='nahida',opponent=nahida?'raiden':'nahida',accent=nahida?'#c4ff9a':'#d3b1ff';
const actions=ACTION_DEFINITIONS;
const edit=(id,data)=>Object.assign(actions.find(a=>a.id===id),data);
edit('e',nahida?{name:'E · 所闻遍计 · 像素取景框',sheet:'skill',frames:[0,1,2,3,3],dur:[4,4,6,5,11],phase:['抬手','框成形','快速撞出','命中停顿与碎光','收势'],fx:'capture'}:{name:'E · 神变·恶曜开眼',sheet:'skill',frames:[0,1,2,3],dur:[6,12,24,18],phase:['聚雷','唤出雷眼','落雷命中','收势'],fx:'eye'});
edit('q',nahida?{name:'Q · 心景幻成 · 梦境领域',sheet:'skill',frames:[4,5,6,6,6,7],dur:[18,38,26,26,26,28],phase:['祈愿与插画','浮空展开神殿','草光 · 第一击','梦境 · 第二击','绽放 · 第三击','领域淡出'],fx:'q'}:{name:'Q · 梦想真说 · 三段演出',sheet:'qburst',frames:[0,1,2,3,2,3,2,3,0],dur:[18,38,12,10,25,10,25,14,32],phase:['命中进入演出','原插画切入','举刀蓄势','雷斩 · 第一击','再度蓄雷','雷斩 · 第二击','雷光汇聚','雷斩 · 第三击','收刀与恢复'],fx:'q'});
edit('throw',nahida?{name:'投技 · 兰那罗来帮忙',sheet:'skill',frames:[4,5,6,6,7],dur:[12,20,6,22,28],phase:['浮空呼唤','三只兰那罗飞入','合力撞击','对手旋转击飞','落地与起身'],fx:'aranara'}:{name:'投技 · 擒拿摔落',sheet:'throw',frames:[0,1,2,3],dur:[12,12,18,28],phase:['抓住对手','举起','雷光摔落','对手起身'],fx:'dust'});
if(nahida){edit('walk',{name:'前移 · 轻浮滑行',sheet:'move',frames:[1,2,1,2],dur:[12,12,12,12]});edit('back',{name:'后移 · 轻浮滑行',sheet:'move',frames:[2,1,2,1],dur:[12,12,12,12]});edit('idle',{name:'待机 · 轻浮呼吸'});edit('heavy',{name:'重攻击 · 草光绽放'});edit('dash',{name:'前冲 · 草光滑翔'});}
let atlas,images={},oppAtlas,oppImages={},portrait,aranara,a=actions.find(x=>x.id==='e'),time=0,playing=true,last=0,ready=false;
const total=()=>a.dur.reduce((x,y)=>x+y,0)+(a.finishIdle?12:0);
const clamp=(v,l=0,h=1)=>Math.max(l,Math.min(h,v)),ease=v=>1-(1-clamp(v))**3;
function phaseAt(t){let n=0;for(let i=0;i<a.dur.length;i++){n+=a.dur[i];if(t<n)return i;}return a.finishIdle?a.frames.length:a.frames.length-1;}
function startOf(p){return a.dur.slice(0,p).reduce((x,y)=>x+y,0);}
function localAt(p){return time-startOf(p);}
function sprite(bank,imgs,sheet,i,x,y,h=330,flip=false,c=ctx,rot=0){const s=bank[sheet],f=s?.frames[i];if(!f)return;const scale=h/s.height;c.save();c.translate(x,y);c.rotate(rot);if(flip)c.scale(-1,1);c.imageSmoothingEnabled=false;c.drawImage(imgs[sheet],f.x,f.y,f.w,f.h,-f.ax*scale,-f.ay*scale,f.w*scale,f.h*scale);c.restore();}
function previewMiddle(bank,sheet,i,j){const s=bank[sheet+'_between'];if(!s)return null;let k=s.next.findIndex((v,n)=>n===i&&v===j);if(k<0)k=s.next.findIndex((v,n)=>n===j&&v===i);if(k<0&&i===j)k=s.next.findIndex((v,n)=>n===i&&v===i);return k<0?null:[sheet+'_between',k];}
function pose(sheet,i,x,y,h=330,flip=false,c=ctx){
 if(c===ctx&&sheet===a.sheet){const p=phaseAt(time),span=a.dur[p],next=a.frames[p+1]??a.frames[0];if(i===a.frames[p]&&localAt(p)>=span-Math.min(3,Math.max(1,Math.floor(span*.35)))){const middle=previewMiddle(atlas,sheet,i,next);if(middle)[sheet,i]=middle;}}
 sprite(atlas,images,sheet,i,x,y,h,flip,c);}

function foe(sheet,i,x,y,h=340,rot=0){sprite(oppAtlas,oppImages,sheet,i,x,y,h,true,ctx,rot);}
function effect(i,x,y,w,alpha=1,ground=false){const f=atlas.effects.frames[i];ctx.save();ctx.globalAlpha=alpha;ctx.imageSmoothingEnabled=false;const h=w*f.h/f.w;ctx.drawImage(images.effects,f.x,f.y,f.w,f.h,x-w/2,ground?y-h:y-h/2,w,h);ctx.restore();}
function shadow(x,y,w=115,alpha=.22){ctx.fillStyle=`rgba(0,0,0,${alpha})`;ctx.beginPath();ctx.ellipse(x,y,w/2,10,0,0,Math.PI*2);ctx.fill();}
function line(x1,y1,x2,y2,col,width=2,alpha=1){ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle=col;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();ctx.restore();}
function ring(x,y,r,col,alpha=1,width=3){ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle=col;ctx.lineWidth=width;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.stroke();ctx.restore();}
function capture(p,x,ground){
 const steps=[0,.10,.26,.48,.74,1],k=time<8?0:steps[Math.max(0,Math.min(5,Math.floor(time-8)))],hit=p>=3,age=hit?localAt(3):0;
 const index=hit?(age<1?4:age<3?5:age<5?6:7):(time<6?0:time<8?1:time<10?2:3),cx=hit?810:x+140+260*k,cy=ground-175;
 const f=atlas.viewfinder.frames[index],alpha=time<4?0:hit?clamp(1-age/8):1;
 ctx.save();ctx.globalAlpha=alpha;ctx.imageSmoothingEnabled=false;ctx.drawImage(images.viewfinder,f.x,f.y,f.w,f.h,cx-190,cy-190,380,380);ctx.restore();}
function hitPhase(p){return a.id==='q'&&(nahida?[2,3,4]:[3,5,7]).includes(p);}
function backdrop(p){if(a.id!=='q'||!$('fx').checked)return;const fade=p===a.frames.length-1?1-localAt(p)/a.dur[p]:1;
 ctx.save();ctx.globalAlpha=fade;ctx.fillStyle=nahida?'#061e1a':'#0b041e';ctx.fillRect(0,0,1200,650);
 const glow=ctx.createRadialGradient(620,300,30,620,300,580);glow.addColorStop(0,nahida?'#316b49':'#603699');glow.addColorStop(1,nahida?'#061e1a':'#0b041e');ctx.fillStyle=glow;ctx.fillRect(0,0,1200,650);
 if(nahida){for(let i=0;i<20;i++){const px=(i*173)%1200,py=(i*127-time*.6+650)%650;ctx.fillStyle=i%2?'#dafaad':'#81dbaa';ctx.globalAlpha=.35+.15*Math.sin(time*.07+i);ctx.fillRect(px,py,3+i%3,3+i%3);}}
 else{const index=p<2?0:hitPhase(p)?2:p===a.frames.length-1?3:1;sprite(atlas,images,'burst_eye',index,620,265,450);for(let i=0;i<8;i++)line(i*160,0,i*160-150,650,'#a474de',3,.17);}
 ctx.restore();}
function cutin(p){if(a.id!=='q'||!$('fx').checked||time>=56)return;const alpha=clamp(time/6)*clamp((56-time)/10),x=-80+ease(time/16)*250;ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle=nahida?'rgba(20,58,36,.85)':'rgba(27,8,50,.85)';ctx.fillRect(0,110,1200,215);ctx.imageSmoothingEnabled=false;ctx.drawImage(portrait,x,130,310,310);ctx.fillStyle=accent;ctx.font='bold 42px system-ui';ctx.fillText(nahida?'心景幻成':'梦想真说',595,235);ctx.fillStyle='#fff0cf';ctx.font='22px system-ui';ctx.fillText(nahida?'纳西妲':'雷电将军',600,278);ctx.restore();}
function helpers(p,x,ground){if(a.id!=='throw'||!nahida||!$('fx').checked||p===0)return;
 for(let i=0;i<3;i++){const delayed=time-12-i*3,k=clamp(delayed/20);let px=210+ease(k)*600,py=ground-160-(i-1)*72-70*Math.sin(k*Math.PI);let frame=delayed<8?0:delayed<19?1:2,alpha=1;
 if(p>=3){const out=clamp((time-38)/28);px=810+out*300;py-=out*200;frame=3;alpha=1-out;}
 if(delayed<0)continue;const f=atlas.aranara.frames[i*4+frame];ctx.save();ctx.globalAlpha=alpha;ctx.drawImage(images.aranara,f.x,f.y,f.w,f.h,px-48,py-48,96,96*f.h/f.w);ctx.restore();
 if(k>.1&&k<1)line(px-70,py,px-25,py,accent,2,.35);
 }
 if(p===2){effect(3,810,ground-165,240);ring(810,ground-165,50+localAt(p)*12,'#f2ffca',1-localAt(p)/6,6);}}
function render(){if(!ready)return;const p=phaseAt(time),ground=550,x=410,u=localAt(p)/a.dur[Math.min(p,a.dur.length-1)];ctx.clearRect(0,0,1200,650);
 ctx.fillStyle=nahida?'#12221e':'#171324';ctx.fillRect(0,0,1200,650);backdrop(p);line(35,ground,1165,ground,nahida?'#5d9972':'#77628d',1,.5);
 const impact=(a.id==='e'&&p===3&&u<.35)||(hitPhase(p)&&localAt(p)<5)||(a.id==='throw'&&p===2&&localAt(p)<5),shake=impact?Math.sin(time*11)*7:0;ctx.save();ctx.translate(shake,impact?Math.cos(time*8)*3:0);
 let hover=0,px=x;if(nahida&&['idle','walk','back','e','q','throw','light1','light2','light3','heavy','dash','al','ah'].includes(a.id)){hover=(a.id==='q'?65:a.id==='e'?38:25)+Math.sin(time*.1)*5;if(a.id==='e'&&p===4)hover*=1-u;}
 if(a.id==='walk'||a.id==='back')px+=Math.sin(time/total()*Math.PI*2)*90*(a.id==='back'?-1:1);
 if(a.id==='jump')hover=160*Math.sin(clamp(time/total())*Math.PI);if(a.air)hover+=100;
 shadow(px,ground,115-hover*.25);
 if($('body').checked){if(p>=a.frames.length)pose('basic',0,px,ground-hover);else pose(a.sheet,a.frames[p],px,ground-hover,nahida?330:365);
  let ex=810,ey=ground,rot=0,sheet='basic',frame=0;
  if(a.id==='throw'){
   if(nahida){if(p===2){sheet='hurt';frame=0;}if(p===3){sheet='victim';frame=3;ex+=u*235;ey-=Math.sin(u*Math.PI)*150;rot=-u*.7;}if(p===4){sheet='hurt';frame=u<.45?3:u<.8?4:5;ex+=235;}}
   else{if(p<2){sheet='victim';frame=p;ex=px+120;ey-=p===1?u*140:0;}else if(p===2){sheet='victim';frame=3;ex=px+120+u*250;ey-=100*(1-u);rot=-u*.7;}else{sheet='hurt';frame=u<.45?3:u<.8?4:5;ex=px+370;}}
  }else if(a.id==='q'&&p>=2){sheet='victim';frame=3;ey=ground-100-Math.sin(time*.1)*20;if(p===a.frames.length-1){ex+=u*210;ey=ground-100*(1-u);sheet=u>.6?'hurt':'victim';frame=u>.85?5:u>.6?3:3;}}
  else if(a.id==='e'&&p>=3){sheet=p===3?'hurt':'basic';frame=0;ex+=p===3?u*20:20;}
  else if(['light1','light2','light3','heavy','al','ah','cl','ch'].includes(a.id)&&p===2){sheet='hurt';frame=0;}
  if(!['victim','hurt','getup','win','lose'].includes(a.id)){shadow(ex,ground,110);foe(sheet,frame,ex,ey,nahida?365:330,rot);}
 }
 if($('fx').checked){
  if(a.fx==='capture')capture(p,px,ground);
  if(a.fx==='eye'&&p>=1){effect(4,px+40,ground-390,130);if(p===2){const zz=clamp(u);effect(6,810,ground-180,200,1-zz);}}
  if(a.id==='q'&&p>=2){if(nahida){effect(9,px,ground,650,.85,true);if(hitPhase(p)){const fade=clamp(1-localAt(p)/17);effect(10,810,ground-180,270+u*200,fade);ring(810,ground-180,65+u*160,'#e9ffc5',fade,4);}}
   else if(hitPhase(p)){const fade=1-u;effect(9,px+235,ground-185,630,fade);effect(10,810,ground-180,360,fade);}
  }
  if((a.fx==='thrust'||a.fx==='sweep')&&p===2){effect(a.fx==='thrust'?0:1,px+210,ground-190-hover,260);effect(3,810,ground-190,95);}
  if(a.fx==='block'&&p===2)effect(2,px+95,ground-220,90);if(a.fx==='hit'&&p===0)effect(3,px+20,ground-220,100);
  if(!nahida&&a.id==='throw'&&p===2)effect(3,px+230,ground-160,170);
  helpers(p,px,ground);
  if(impact){ctx.fillStyle=nahida?'rgba(238,255,200,.13)':'rgba(240,217,255,.16)';ctx.fillRect(0,0,1200,650);}
 }
 ctx.restore();cutin(p);
 $('phase').textContent=a.phase?.[p]||`姿势 ${p+1}`;$('clock').textContent=`${Math.floor(time)+1} / ${total()} 帧 · ${(time/60).toFixed(2)} 秒`;$('scrub').value=Math.floor(time);
 document.querySelectorAll('.frame').forEach((b,i)=>b.setAttribute('aria-pressed',String(i===p)));
}
function choose(id){a=actions.find(x=>x.id===id);if(!a)throw Error('未知动作');time=0;$('name').textContent=a.name;$('scrub').max=total()-1;$('pair').textContent=a.id==='throw'?(nahida?'兰那罗协同 · 对手击飞与起身':'双方抓取、摔落与起身'):a.id==='q'?'原插画 · 背景切换 · 三段命中':a.id==='e'&&nahida?'举手取景 · 扫描 · 收框':'';
 $('note').textContent=nahida?'纳西妲重做预览：浮空、取景扫描、梦境领域与兰那罗投技。本页展示动作演出，尚未替换对战中的草神动作。':'雷电将军动作预览：E/Q、完整攻击、防御、投技与被投。大招按当前对战版展示三段演出。';
 document.querySelectorAll('.action').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===id)));$('timeline').replaceChildren();
 [...a.frames,...(a.finishIdle?[-1]:[])].forEach((f,i)=>{const b=document.createElement('button');b.className='frame';b.setAttribute('aria-label',a.phase?.[i]||`第${i+1}个姿势`);const c=document.createElement('canvas');c.width=240;c.height=190;const t=document.createElement('span');t.textContent=`${i+1} · ${a.phase?.[i]||'姿势'}`;b.append(c,t);pose(f===-1?'basic':a.sheet,f===-1?0:f,100,175,145,false,c.getContext('2d'));b.onclick=()=>{playing=false;time=startOf(i);sync();render();};$('timeline').append(b);});render();}
function sync(){$('play').textContent=playing?'暂停':'播放';}
$('play').onclick=()=>{if(time>=total()-1)time=0;playing=!playing;sync();};$('restart').onclick=()=>{time=0;playing=true;sync();};$('prev').onclick=()=>{playing=false;time=Math.max(0,Math.floor(time)-1);sync();render();};$('next').onclick=()=>{playing=false;time=Math.min(total()-1,Math.floor(time)+1);sync();render();};$('scrub').oninput=()=>{playing=false;time=Number($('scrub').value);sync();render();};['body','fx'].forEach(id=>$(id).onchange=render);
document.addEventListener('keydown',e=>{if(/INPUT|SELECT/.test(e.target.tagName))return;if(e.code==='Space'){e.preventDefault();$('play').click();}if(e.code==='ArrowRight'){$('next').click();e.preventDefault();}if(e.code==='ArrowLeft'){$('prev').click();e.preventDefault();}});
function load(url){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('素材载入失败：'+url));im.src=url;});}
async function bank(char){const base='/actions/'+char+'/';const r=await fetch(base+'atlas.json?v=r28');if(!r.ok)throw Error('素材清单载入失败');const data=await r.json();const imgs={};await Promise.all(Object.entries(data).map(async([k,v])=>imgs[k]=await load(base+v.url+'?v=r28')));return [data,imgs];}
async function init(){try{[[atlas,images],[oppAtlas,oppImages],portrait]=await Promise.all([bank(CHAR),bank(opponent),load('/actions/'+CHAR+'/assets/original-portrait.png?v=r28')]);
 for(const act of actions){if(act.group){const h=document.createElement('div');h.className='group';h.textContent=act.group;$('actions').append(h);}const b=document.createElement('button');b.className='action';b.dataset.id=act.id;b.textContent=act.name;b.setAttribute('aria-pressed','false');b.onclick=()=>choose(act.id);$('actions').append(b);}ready=true;$('loading').hidden=true;['play','restart','prev','next'].forEach(id=>$(id).disabled=false);if(matchMedia('(prefers-reduced-motion: reduce)').matches)playing=false;choose('e');sync();requestAnimationFrame(tick);
 }catch(e){$('loading').hidden=true;$('error').style.display='block';$('error').textContent=e.message;}}
function tick(now){if(last&&playing){time+=Math.min(now-last,100)*.06*Number($('speed').value);if(time>=total()){if($('loop').checked)time%=total();else{time=total()-1;playing=false;sync();}}}last=now;render();requestAnimationFrame(tick);}
window.ACTION_PREVIEW={actions,get ready(){return ready;},choose,seek(t){time=clamp(t,0,total()-1);playing=false;sync();render();},get state(){return {character:CHAR,action:a.id,time,playing,phase:phaseAt(time),duration:total()};}};init();

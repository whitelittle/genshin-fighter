// Candidate only: flight and movement input are independent of attack animation.
let airEntryTick=12,previewMoveX=0,moveHeld=new Set();
const jumpTicks=38,jumpPeak=160;
function flightRate(){return jumpTicks/bank['跳跃'].durations.reduce((a,b)=>a+b,0)}
function jumpHeight(t){return jumpPeak*Math.sin(Math.PI*Math.max(0,Math.min(1,t/jumpTicks)))}
const priorChoose=choose;
choose=async function(name){if(name==='空轻'||name==='空重')airEntryTick=selected==='跳跃'?time/total*jumpTicks:['空轻','空重'].includes(selected)?Math.min(jumpTicks,airEntryTick+time*flightRate()):12;return priorChoose(name)};
const priorStageRoot=stageRoot;
stageRoot=function(){if(selected==='空轻'||selected==='空重')return[410+previewMoveX,550-jumpHeight(airEntryTick+time*flightRate())];if(selected==='跳跃')return[410+previewMoveX,550-jumpHeight(time/total*jumpTicks)];return priorStageRoot()};
window.addEventListener('keydown',e=>{if(['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;if(['ArrowLeft','ArrowRight','a','d','A','D'].includes(e.key)){moveHeld.add(e.key.toLowerCase());e.preventDefault()}});
window.addEventListener('keyup',e=>moveHeld.delete(e.key.toLowerCase()));
window.addEventListener('blur',()=>moveHeld.clear());
const priorTick=tick;
tick=function(now){if(last&&playing&&['跳跃','空轻','空重'].includes(selected)){const dt=Math.min(100,now-last)*.06*+$('speed').value;previewMoveX=Math.max(-250,Math.min(250,previewMoveX+4*dt*((moveHeld.has('arrowright')||moveHeld.has('d')?1:0)-(moveHeld.has('arrowleft')||moveHeld.has('a')?1:0))))}priorTick(now)};
function airHelperState(x,y){
 const cd=bank['空重'].combatDesign,active=time>=cd.startup&&time<cd.startup+cd.active,index=active?2:time<cd.startup?1:3;
 const mouths=[[390,250],[410,249],[393,278],[390,250]],src=helperBank.chevalmarin.sourceFrames[index],q=mouths[index];
 const offset=[(q[0]-src.anchor[0])*src.scale,(q[1]-src.anchor[1])*src.scale],root=[x+120,y-140-offset[1]];
 return{index,root,mouth:[root[0]+offset[0],y-140],active};
}
const priorHelpers=drawHelpers;
drawHelpers=function(x,y){if(selected!=='空重')return priorHelpers(x,y);if(!$('companions').checked)return;const h=airHelperState(x,y);helperSprite('chevalmarin',h.index,...h.root,0)};
const priorEffects=drawEffects;
drawEffects=function(x,y){
 if(selected!=='空重')return priorEffects(x,y);if(!$('fx').checked)return;
 const h=airHelperState(x,y);if(!h.active)return;
 const e=bank[selected].effects,list=$('material').value==='fit'?e.fitFrames:e.sourceFrames,age=time-bank[selected].combatDesign.startup,i=Math.min(list.length-1,Math.floor(age/bank[selected].combatDesign.active*list.length)),f=list[i],im=effectImages[i];if(!im)return;
 const angle=Math.atan2(330-h.mouth[1],660-h.mouth[0]);
 ctx.save();ctx.translate(...h.mouth);ctx.rotate(angle);ctx.imageSmoothingEnabled=false;ctx.drawImage(im,-f.anchor[0]*f.scale,-f.anchor[1]*f.scale,im.naturalWidth*f.scale,im.naturalHeight*f.scale);ctx.restore();
};

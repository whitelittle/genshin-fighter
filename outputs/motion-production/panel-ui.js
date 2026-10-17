(()=>{'use strict';
const panels=[...document.querySelectorAll('.floating-panel')];let top=30;
function clamp(panel){const r=panel.getBoundingClientRect();panel.style.left=Math.max(8,Math.min(r.left,innerWidth-r.width-8))+'px';panel.style.top=Math.max(8,Math.min(r.top,innerHeight-r.height-8))+'px';}
function close(panel){panel.hidden=true;const opener=document.querySelector(`[data-open-panel="${panel.id}"]`);opener.setAttribute('aria-expanded','false');opener.focus();}
for(const opener of document.querySelectorAll('[data-open-panel]'))opener.addEventListener('click',()=>{const panel=document.getElementById(opener.dataset.openPanel);if(!panel.hidden){close(panel);return;}panel.hidden=false;panel.style.zIndex=++top;clamp(panel);opener.setAttribute('aria-expanded','true');panel.querySelector('input,.panel-heading').focus();});
for(const panel of panels){
 panel.querySelector('[data-close-panel]').addEventListener('click',()=>close(panel));
 panel.addEventListener('pointerdown',()=>panel.style.zIndex=++top);
 const heading=panel.querySelector('.panel-heading');let drag=null;
 heading.addEventListener('pointerdown',e=>{if(e.button!==0||e.target.closest('button'))return;const r=panel.getBoundingClientRect();drag={x:e.clientX,y:e.clientY,left:r.left,top:r.top};heading.setPointerCapture(e.pointerId);e.preventDefault();});
 heading.addEventListener('pointermove',e=>{if(!drag)return;panel.style.left=drag.left+e.clientX-drag.x+'px';panel.style.top=drag.top+e.clientY-drag.y+'px';clamp(panel);});
 for(const name of ['pointerup','pointercancel','lostpointercapture'])heading.addEventListener(name,()=>drag=null);
 heading.addEventListener('keydown',e=>{const delta={ArrowLeft:[-16,0],ArrowRight:[16,0],ArrowUp:[0,-16],ArrowDown:[0,16]}[e.key];if(!delta||e.target!==heading)return;e.preventDefault();const r=panel.getBoundingClientRect();panel.style.left=r.left+delta[0]+'px';panel.style.top=r.top+delta[1]+'px';clamp(panel);});
}
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;const panel=panels.filter(p=>!p.hidden).sort((a,b)=>+b.style.zIndex-+a.style.zIndex)[0];if(panel){e.preventDefault();close(panel);}});
addEventListener('resize',()=>panels.filter(p=>!p.hidden).forEach(clamp));
document.getElementById('roleSearch').addEventListener('input',e=>{let count=0;for(const button of document.getElementById('roles').children){button.hidden=!button.textContent.toLowerCase().includes(e.target.value.trim().toLowerCase());if(!button.hidden)count++;}document.getElementById('roleSearchEmpty').hidden=count!==0;});
})();

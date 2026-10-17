'use strict';
const n$=id=>document.getElementById(id),nc=n$('compare'),nx=nc.getContext('2d');
let nr,nb={},ni=0,np=true,nt=0,na=0,nm;
const niLoad=src=>new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>reject(Error('素材加载失败：'+src));i.src=src;});
function attackOptions(){const facing=n$('mirror').checked?-1:1,type=n$('contact').value;return{facing,target:{x:(type==='miss'?270:type==='behind'?-150:150)*facing,guard:type==='block',invulnerable:type==='invulnerable',downed:type==='downed'}};}
function resetAttack(){nm=Light1Model.create(attackOptions());}
function nDraw(){
 if(!nr)return;const key=n$('group').value,g=nr.groups[key],isAttack=key==='light1';if(isAttack)ni=Light1Model.pose(nm);
 const p=g.poses[ni],light=n$('light').checked;nx.fillStyle=light?'#eee6dc':'#161519';nx.fillRect(0,0,1500,480);nx.font='20px sans-serif';nx.textAlign='center';
 for(const [col,mode]of ['source','initial','optimized'].entries()){
  const root=230+500*col,floor=385;nx.fillStyle=light?'#292522':'#e8dacf';nx.fillText(['源图','初拟合','优化拟合'][col],250+500*col,42);
  nx.strokeStyle=light?'#a99b8d':'#635046';nx.beginPath();nx.moveTo(col*500+12,floor);nx.lineTo(col*500+488,floor);nx.stroke();
  if(isAttack){const t=Light1Model.targetBox(nm);nx.fillStyle=nm.hits?'#6b815d':nm.blocked?'#79613d':'#4c5059';nx.fillRect(root+t.x0,floor-t.y1,t.x1-t.x0,t.y1-t.y0);if(nm.tick>=14&&nm.tick<=16){const b=Light1Model.attackBox(nm);nx.strokeStyle='#f1ba62';nx.strokeRect(root+b.x0,floor-b.y1,b.x1-b.x0,b.y1-b.y0);}}
  const rect=mode==='source'?p.sourceRect:p.atlasRect,anchor=mode==='source'?p.sourceAnchor:p.anchor,scale=mode==='source'?g.displayScale:4;
  nx.save();nx.translate(root,floor);if(n$('mirror').checked)nx.scale(-1,1);nx.imageSmoothingEnabled=false;nx.drawImage(nb[key][mode],...rect,-anchor[0]*scale,-anchor[1]*scale,rect[2]*scale,rect[3]*scale);nx.restore();nx.fillStyle='#e57862';nx.fillRect(root-3,floor-3,6,6);
 }
 n$('frame').textContent=`${ni+1} / ${g.poses.length} 姿`;n$('seek').value=ni;n$('play').textContent=np?'暂停':'播放';
 const attackInfo=isAttack?` · 动作帧 ${nm.tick}/36 · ${nm.hits} 次命中 / ${nm.blocked} 次防御 · 停顿 ${nm.stop}`:'';
 n$('metrics').textContent=`当前初拟合 ${p.initialRectangles} / 优化 ${p.optimizedRectangles} 图元${attackInfo} · 独立候选，未接入正式战斗。`;
}
function nLoop(now){if(np&&nr){na+=Math.min(now-nt,100);const attack=n$('group').value==='light1',dt=attack?1000/60*5/Number(n$('speed').value):1000/Number(n$('speed').value);while(na>=dt&&np){if(attack){Light1Model.step(nm);if(nm.ended)np=false;}else ni=(ni+1)%nr.groups[n$('group').value].poses.length;na-=dt;}nDraw();}nt=now;requestAnimationFrame(nLoop);}
n$('group').onchange=()=>{ni=0;na=0;resetAttack();n$('seek').max=nr.groups[n$('group').value].poses.length-1;nDraw();};
n$('play').onclick=()=>{if(n$('group').value==='light1'&&nm.ended)resetAttack();np=!np;na=0;nDraw();};
n$('step').onclick=()=>{np=false;if(n$('group').value==='light1')Light1Model.step(nm);else ni=(ni+1)%nr.groups[n$('group').value].poses.length;nDraw();};
n$('seek').oninput=()=>{np=false;ni=Number(n$('seek').value);if(n$('group').value==='light1')nm=Light1Model.seek(attackOptions(),[0,10,14,17][ni]);nDraw();};
n$('light').onchange=nDraw;n$('mirror').onchange=()=>{resetAttack();nDraw();};n$('contact').onchange=()=>{np=false;resetAttack();nDraw();};
fetch('assets/neutral-rig-v6.json').then(r=>{if(!r.ok)throw Error('锚点数据未能加载');return r.json();}).then(async r=>{nr=r;await Promise.all(Object.entries(r.groups).map(async([key,g])=>{nb[key]={};await Promise.all(['source','initial','optimized'].map(async mode=>{nb[key][mode]=await niLoad('assets/'+g[mode]);}));}));resetAttack();nDraw();requestAnimationFrame(nLoop);}).catch(e=>{np=false;n$('metrics').textContent=e.message;});

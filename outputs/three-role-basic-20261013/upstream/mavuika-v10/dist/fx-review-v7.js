'use strict';
const f$=id=>document.getElementById(id),fc=f$('fxstage'),fg=fc.getContext('2d');let fb,fidle,ff,ft,fi={},fsim,frunning=false,flast=0,facc=0;
const fimg=src=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(Error('素材未能加载：'+src));image.src=src;});
const fjson=url=>fetch(url).then(r=>{if(!r.ok)throw Error('数据未能加载：'+url);return r.json();});
function foptions(){const face=f$('fxmirror').checked?-1:1,type=f$('fxoutcome').value;return{facing:face,target:{x:(type==='miss'?270:type==='behind'?-150:150)*face,guard:type==='block',invulnerable:type==='invulnerable'}};}
function freset(){fsim=Light1Model.create(foptions());facc=0;fdraw();}
function bitmap(image,rect,anchor,scale,x,y,facing=1,alpha=1,rotation=0){fg.save();fg.translate(x,-y);fg.scale(facing,1);fg.rotate(rotation*Math.PI/180);fg.globalAlpha=alpha;fg.imageSmoothingEnabled=false;fg.drawImage(image,...rect,-anchor[0]*scale,-anchor[1]*scale,rect[2]*scale,rect[3]*scale);fg.restore();}
function fdraw(){if(!fb)return;const s=fsim,light=f$('fxlight').checked,mode=f$('fxmaterial').value,layers=f$('fxlayers').value,receiver=Light1FX.receiver(s),effects=Light1FX.sample(s),pose=Light1FX.pose(s),g=pose<0?fidle:fb,p=g.poses[pose<0?0:pose];
 fg.fillStyle=light?'#eee6dc':'#17191e';fg.fillRect(0,0,1100,560);fg.strokeStyle=light?'#b4a592':'#675444';fg.beginPath();fg.moveTo(35,465);fg.lineTo(1065,465);fg.stroke();
 fg.save();fg.translate(s.facing===1?410:690,465);fg.scale(1.25,1.25);
 if(layers!=='fx'){
  const target=ft.poses[receiver.pose];bitmap(fi.target,target.rect,target.anchor,target.scale,receiver.x-target.offsetX*s.facing,receiver.y,-s.facing);
  if(receiver.flash&&layers==='all')bitmap(fi.flash,target.rect,target.anchor,target.scale,receiver.x-target.offsetX*s.facing,receiver.y,-s.facing,receiver.flash);
  bitmap(fi[pose<0?'idle-'+mode:mode],mode==='source'?p.sourceRect:p.atlasRect,mode==='source'?p.sourceAnchor:p.anchor,mode==='source'?g.displayScale:4,s.x,s.y,s.facing);
 }
 if(layers!=='actors')for(const e of effects){const f=ff.frames[e.index],source=mode==='source';bitmap(fi[source?'fxsource':'fxfit'],source?f.sourceRect:f.rect,source?f.sourceAnchor:f.anchor,source?f.sourceScale:f.scale,e.x,e.y,e.facing,e.alpha,e.rotation);}
 if(f$('fxanchors').checked&&pose>=0){const marks=Light1FX.landmarks(s);fg.font='11px sans-serif';fg.fillStyle=light?'#5f2616':'#ffe1aa';for(const[k,p]of Object.entries(marks)){fg.fillRect(p.x-2,-p.y-2,4,4);fg.fillText(k,p.x+4,-p.y-4);}for(const e of s.events){fg.fillStyle='#78e0d7';fg.fillRect(e.contact.x-3,-e.contact.y-3,6,6);}}
 fg.restore();fc.style.filter=f$('fxmono').checked?'grayscale(1) contrast(1.25)':'none';f$('fxseek').value=s.tick;f$('fxplay').textContent=frunning?'暂停':'播放';
 const counts=effects.reduce((sum,e)=>sum+ff.frames[e.index].rectangles,0);f$('fxreadout').textContent=`动作帧 ${s.tick}/36 · ${s.hits} 次命中 / ${s.blocked} 次防御 · 停顿 ${s.stop} · 当前特效编码 ${counts} 图元（非真机负载）`;
}
function floop(now){if(frunning){facc+=Math.min(100,now-flast)*Number(f$('fxspeed').value);while(facc>=1000/60&&frunning){Light1Model.step(fsim);facc-=1000/60;if(fsim.ended)frunning=false;}fdraw();}flast=now;requestAnimationFrame(floop);}
f$('fxplay').onclick=()=>{if(fsim.ended)freset();frunning=!frunning;fdraw();};f$('fxrestart').onclick=()=>{freset();frunning=true;fdraw();};f$('fxstep').onclick=()=>{frunning=false;Light1Model.step(fsim);fdraw();};f$('fxseek').oninput=()=>{frunning=false;fsim=Light1Model.seek(foptions(),Number(f$('fxseek').value));fdraw();};
for(const id of ['fxoutcome','fxmirror'])f$(id).onchange=()=>{frunning=false;freset();};for(const id of ['fxmaterial','fxlayers','fxlight','fxmono','fxanchors'])f$(id).onchange=fdraw;
Promise.all([fjson('assets/neutral-rig-v6.json'),fjson('assets/light1-fx-rig-v7.json'),fjson('assets/v3-target-rig-v7.json')]).then(async([body,fx,target])=>{fb=body.groups.light1;fidle=body.groups.idle;ff=fx;ft=target;const urls={source:fb.source,initial:fb.initial,optimized:fb.optimized,'idle-source':fidle.source,'idle-initial':fidle.initial,'idle-optimized':fidle.optimized,fxsource:fx.source,fxfit:fx.fit,target:target.file,flash:'v3-target-flash-v7.png'};await Promise.all(Object.entries(urls).map(async([key,file])=>{fi[key]=await fimg('assets/'+file);}));for(const id of ['fxplay','fxrestart','fxstep','fxseek'])f$(id).disabled=false;freset();requestAnimationFrame(floop);}).catch(e=>{frunning=false;f$('fxreadout').textContent=e.message;});

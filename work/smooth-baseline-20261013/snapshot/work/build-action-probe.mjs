import{readFileSync,writeFileSync,mkdirSync,existsSync,copyFileSync}from'node:fs';
import{createRequire}from'node:module';
import{designs}from'./action-probe-design.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json'),{createCanvas}=require('@napi-rs/canvas');
const out='outputs/action-probe';mkdirSync(out+'/poses',{recursive:true});mkdirSync(out+'/heads',{recursive:true});mkdirSync(out+'/portraits',{recursive:true});
const roster=JSON.parse(readFileSync('outputs/roster-v2/roster.json')),talents=JSON.parse(readFileSync('assets/roster-v2/talent-index.json'));
const roles=roster.map(([key,name],i)=>{
 const framesPath=existsSync(`assets/roster-v2/${key}-frames.json`)?`assets/roster-v2/${key}-frames.json`:`assets/${i<2?'vnext':'test-v1'}/${key}-frames.json`;
 const raw=JSON.parse(readFileSync(framesPath)),poses=[];const seen=new Map();
 for(const f of raw.frames){const signature=JSON.stringify(f.rows),pose=f.pose||'idle';let png=seen.get(signature);if(!png){png=`poses/${key}-${pose}.png`;const c=createCanvas(f.w,f.h),ctx=c.getContext('2d');for(const[x,y,w,h,r,g,b,a]of f.rows){ctx.fillStyle=`rgba(${r},${g},${b},${a/255})`;ctx.fillRect(x,y,w,h);}writeFileSync(out+'/'+png,c.toBuffer('image/png'));seen.set(signature,png);}poses.push({name:pose,url:png,w:f.w,h:f.h,anchor:f.anchor,scale:f.scale,rectangles:f.rows.length,alias:poses.some(p=>p.url===png)});}
 const icon=`assets/roster-v2/${key}-official-head.png`;let head=null;if(existsSync(icon)){head=`heads/${key}.png`;copyFileSync(icon,out+'/'+head);}
 const d=designs.find(d=>d.key===key),t=talents.find(t=>t.key===key);
 let portrait=null;if(['keqing','diluc'].includes(key)){const body=`assets/roster-v2/${key}-official-body.png`;if(existsSync(body)){portrait=`portraits/${key}.png`;copyFileSync(body,out+'/'+portrait);}}
 return{id:i+1,key,name,poses,head,portrait,design:d||null,originalSkills:key==='diluc'?{E:'逆焰之刃',Q:'黎明'}:t?.E&&t?.Q?{E:t.E,Q:t.Q}:null,sourceFrames:framesPath};
});
const recordsPath='assets/action-probe/references/video-records.json';const references=existsSync(recordsPath)?JSON.parse(readFileSync(recordsPath)):[];
const data={version:'20261003-action-probe-2',fps:60,bodyHeight:232,roles,references,researchRoles:designs.length,productionCombatChanged:false};
writeFileSync(out+'/data.js','window.PROBE_DATA='+JSON.stringify(data)+';');writeFileSync(out+'/designs.json',JSON.stringify(designs,null,2));
for(const f of['index.html','probe.js','model.js','motion-study.js','effects-v2.js','style.css'])copyFileSync('work/action-probe/'+f,out+'/'+f);
writeFileSync(out+'/build.json',JSON.stringify({roles:roles.length,researched:designs.length,poseImages:roles.reduce((a,r)=>a+new Set(r.poses.map(p=>p.url)).size,0),productionCombatChanged:false,deviceVerified:false},null,2));
console.log('ACTION_PROBE_BUILT',roles.length,designs.length);

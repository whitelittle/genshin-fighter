import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createRequire} from 'node:module';
import {sample,colorProcess,fit} from 'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const {createCanvas,loadImage}=require('@napi-rs/canvas');
const manifest=JSON.parse(readFileSync('assets/vnext/pose-manifest.json'));
const sets={};let report=[];
for(const role of ['keqing','diluc'])sets[role]=JSON.parse(readFileSync(`assets/demo/${role}-light-frames.json`));
for(const a of manifest){
 const img=await loadImage(a.path),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);
 const standing=a.role==='keqing'?96:103,unit=standing/a.bodyHeight,w=Math.max(1,Math.round(img.width*unit)),h=Math.max(1,Math.round(img.height*unit));
 const raw=sample(ctx.getImageData(0,0,img.width,img.height).data,img.width,img.height,w,h,'average',220);
 const data=colorProcess(raw,new Uint8Array(w*h),{colors:24,tolerance:5}).data,result=fit(data,w,h);
 if(!result.exact)throw Error('inexact '+a.pose);
 const f={role:a.role,pose:a.pose,w,h,profile:'light',scale:(a.role==='keqing'?224:240)/standing,anchor:[a.anchor[0]*w/img.width,a.anchor[1]*h/img.height],rows:result.rows};
 sets[a.role].frames.push(f);const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(data);pctx.putImageData(id,0,0);writeFileSync(`assets/vnext/${a.role}-${a.pose}.png`,pc.toBuffer('image/png'));
 report.push({role:a.role,pose:a.pose,grid:[w,h],rows:f.rows.length,exact:result.exact});
}
const portraits={};
for(const role of ['keqing','diluc']){
 const img=await loadImage(`assets/vnext/${role}-portrait-source.png`),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);
 const w=32,h=36,raw=sample(ctx.getImageData(0,0,img.width,img.height).data,img.width,img.height,w,h,'average',220);
 const data=colorProcess(raw,new Uint8Array(w*h),{colors:24,tolerance:5}).data,r=fit(data,w,h);
 portraits[role]={w,h,scale:1.6,anchor:[w/2,h/2],rows:r.rows};
 const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(data);pctx.putImageData(id,0,0);writeFileSync(`assets/vnext/${role}-portrait.png`,pc.toBuffer('image/png'));
 const set=sets[role];set.pool=Math.max(...set.frames.map(f=>f.rows.length));writeFileSync(`assets/vnext/${role}-frames.json`,JSON.stringify(set));
}
const phoenix=[];
const fx=await loadImage('assets/vnext/phoenix-source.png');
for(let i=0;i<2;i++){
 const sw=Math.floor(fx.width/2),c=createCanvas(sw,fx.height),ctx=c.getContext('2d');ctx.drawImage(fx,i*sw,0,sw,fx.height,0,0,sw,fx.height);
 const w=64,h=40,raw=sample(ctx.getImageData(0,0,sw,fx.height).data,sw,fx.height,w,h,'average',220),data=colorProcess(raw,new Uint8Array(w*h),{colors:12,tolerance:5}).data,r=fit(data,w,h);
 phoenix.push({w,h,scale:4,anchor:[w*.7,h*.65],rows:r.rows});
 const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(data);pctx.putImageData(id,0,0);writeFileSync(`assets/vnext/phoenix-${i+1}.png`,pc.toBuffer('image/png'));
}
const bg=await loadImage('assets/vnext/stages-source.png'),stages=[];
for(let i=0;i<3;i++){
 const sw=700,sh=Math.floor(bg.height/3),sx=[1200,1150,600][i],c=createCanvas(sw,sh),ctx=c.getContext('2d');ctx.drawImage(bg,sx,i*sh,sw,sh,0,0,sw,sh);
 const w=128,h=44,raw=sample(ctx.getImageData(0,0,sw,sh).data,sw,sh,w,h,'average',220),data=colorProcess(raw,new Uint8Array(w*h),{colors:24,tolerance:5}).data,r=fit(data,w,h);
 stages.push({w,h,scale:10,anchor:[64,44],rows:r.rows});
 const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(data);pctx.putImageData(id,0,0);writeFileSync(`assets/vnext/stage-${i+1}.png`,pc.toBuffer('image/png'));
}
writeFileSync('assets/vnext/stages.json',JSON.stringify(stages));
writeFileSync('assets/vnext/phoenix.json',JSON.stringify(phoenix));writeFileSync('assets/vnext/portraits.json',JSON.stringify(portraits));writeFileSync('assets/vnext/load-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify({pools:Object.fromEntries(Object.entries(sets).map(([k,v])=>[k,v.pool])),phoenixPool:Math.max(...phoenix.map(f=>f.rows.length)),stagePool:Math.max(...stages.map(f=>f.rows.length)),portraits:Object.fromEntries(Object.entries(portraits).map(([k,v])=>[k,v.rows.length]))}));

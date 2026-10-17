import{readFileSync,writeFileSync}from'node:fs';import{createRequire}from'node:module';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const req=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json'),{createCanvas,loadImage}=req('@napi-rs/canvas');
const out='outputs/group1-full-test',image=await loadImage(out+'/home-halfbody-v2.png'),frames=[];
for(let i=0;i<2;i++){const sw=Math.floor(image.width/2),sh=image.height,c=createCanvas(sw,sh),ctx=c.getContext('2d');ctx.drawImage(image,i*sw,0,sw,sh,0,0,sw,sh);const h=112,w=Math.round(sw*h/sh);const raw=sample(ctx.getImageData(0,0,sw,sh).data,sw,sh,w,h,'average',220),processed=colorProcess(raw,new Uint8Array(w*h),{colors:20,tolerance:4}).data,r=fit(processed,w,h);if(i===1)r.rows=r.rows.filter(row=>row[0]>=12);if(!r.exact)throw Error('portrait fit inexact');frames.push({w,h,scale:600/h,anchor:[w/2,h/2],rows:r.rows});const pc=createCanvas(w,h),pctx=pc.getContext('2d'),data=pctx.createImageData(w,h);data.data.set(processed);pctx.putImageData(data,0,0);writeFileSync(out+'/home-'+(i?'diluc':'keqing')+'-fit.png',pc.toBuffer('image/png'));}
writeFileSync(out+'/home-portraits.json',JSON.stringify(frames));console.log('HOME_PORTRAIT_FIT',frames.map(f=>({grid:[f.w,f.h],rectangles:f.rows.length})));


import {readFileSync,writeFileSync}from'node:fs';
import {createRequire}from'node:module';
import {sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const {createCanvas,loadImage}=require('@napi-rs/canvas');
const image=await loadImage('assets/vnext/paimon-loading-source.png'),frames=[];
for(let i=0;i<4;i++){
 const cw=Math.floor(image.width/2),ch=Math.floor(image.height/2),canvas=createCanvas(cw,ch),ctx=canvas.getContext('2d');ctx.drawImage(image,(i%2)*cw,Math.floor(i/2)*ch,cw,ch,0,0,cw,ch);
 const source=ctx.getImageData(0,0,cw,ch).data;let x0=cw,y0=ch,x1=0,y1=0;
 for(let y=0;y<ch;y++)for(let x=0;x<cw;x++)if(source[(y*cw+x)*4+3]>=220){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}
 const sw=x1-x0+1,sh=y1-y0+1,crop=ctx.getImageData(x0,y0,sw,sh).data,h=32,w=Math.round(sw/sh*h);
 const raw=sample(crop,sw,sh,w,h,'average',220),data=colorProcess(raw,new Uint8Array(w*h),{colors:10,tolerance:8}).data,result=fit(data,w,h);
 if(!result.exact)throw Error('Paimon fitting failed');frames.push({w,h,scale:1.65,anchor:[w/2,h/2],rows:result.rows});
 const preview=createCanvas(w,h),pc=preview.getContext('2d'),id=pc.createImageData(w,h);id.data.set(data);pc.putImageData(id,0,0);writeFileSync('assets/vnext/paimon-loading-'+(i+1)+'.png',preview.toBuffer('image/png'));
}
writeFileSync('assets/vnext/paimon-loading.json',JSON.stringify(frames));console.log(frames.map(f=>f.rows.length));

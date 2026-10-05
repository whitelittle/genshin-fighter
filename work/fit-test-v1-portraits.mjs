import{writeFileSync}from'node:fs';import{createRequire}from'node:module';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');const{createCanvas,loadImage}=require('@napi-rs/canvas');
// Face crops calibrated against head-reference.png (320x420 per first sheet cell).
const crops={kaeya:[125,65,95,90],jean:[80,52,135,115],klee:[75,75,180,160],lisa:[110,10,143,129],ganyu:[90,10,110,125],yanfei:[89,17,132,145],xiao:[140,78,94,89],hutao:[123,45,121,113],lawachurl:[145,25,175,195]};
for(const[key,[x,y,w,h]]of Object.entries(crops)){
 const im=await loadImage(`assets/test-v1/${key}-sheet.png`),c=createCanvas(24,28),ctx=c.getContext('2d');ctx.drawImage(im,x*im.width/1280,y*im.height/1260,w*im.width/1280,h*im.height/1260,0,0,24,28);
 const raw=sample(ctx.getImageData(0,0,24,28).data,24,28,24,28,'average',180),data=colorProcess(raw,new Uint8Array(24*28),{colors:18,tolerance:5}).data;
 writeFileSync(`assets/test-v1/${key}-portrait.json`,JSON.stringify({w:24,h:28,scale:2,anchor:[12,14],rows:fit(data,24,28).rows,sourceCrop320:crops[key]}));
}

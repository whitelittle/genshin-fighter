import {readFileSync,writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {sample,colorProcess,fit} from 'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
import {packFrame} from './v2-pack.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const {createCanvas,loadImage}=require('@napi-rs/canvas');
const out='outputs/windrise-pixel-experiment',source=await loadImage(out+'/source.png'),rawCanvas=createCanvas(source.width,source.height),rc=rawCanvas.getContext('2d');rc.drawImage(source,0,0);const sourceData=rc.getImageData(0,0,source.width,source.height).data;
const variants=[];let chosen;
for(const p of [{w:240,h:135,colors:24,tolerance:14},{w:224,h:126,colors:24,tolerance:12},{w:208,h:117,colors:24,tolerance:10},{w:192,h:108,colors:24,tolerance:8},{w:192,h:108,colors:20,tolerance:12},{w:176,h:99,colors:32,tolerance:3},{w:160,h:90,colors:32,tolerance:3},{w:160,h:90,colors:31,tolerance:3},{w:160,h:90,colors:30,tolerance:3},{w:192,h:108,colors:20,tolerance:12.1},{w:192,h:108,colors:20,tolerance:12.3},{w:192,h:108,colors:20,tolerance:12.5},{w:192,h:108,colors:20,tolerance:13},{w:192,h:108,colors:20,tolerance:14},{w:176,h:99,colors:24,tolerance:8},{w:160,h:90,colors:20,tolerance:10}]){
 const pixels=colorProcess(sample(sourceData,source.width,source.height,p.w,p.h,'nearest',220),new Uint8Array(p.w*p.h),p).data;
 let f=fit(pixels,p.w,p.h);if(f.rows.length>5000&&f.rows.length<=5300){const overlap=fit(pixels,p.w,p.h,'overlap');if(overlap.rows.length<=5000&&overlap.overdraw<=1.5)f=overlap;}variants.push({...p,rectangles:f.rows.length,actualColors:f.colors,fitMethod:f.method,overdraw:f.overdraw});console.log(p.w,p.colors,p.tolerance,f.rows.length,f.colors,f.method,f.overdraw);
 if(f.rows.length<=5000){chosen={p,pixels,f};break;}
}
assert(chosen,'No candidate fits the budget');const {p,pixels,f}=chosen;const canvas=createCanvas(p.w,p.h),ctx=canvas.getContext('2d');for(const r of f.rows){ctx.fillStyle=`rgba(${r[4]},${r[5]},${r[6]},${r[7]/255})`;ctx.fillRect(r[0],r[1],r[2],r[3]);}assert.deepEqual(ctx.getImageData(0,0,p.w,p.h).data,pixels);
const frame={w:p.w,h:p.h,scale:1600/p.w,anchor:[p.w/2,p.h/2],rows:f.rows},packed=packFrame(frame);writeFileSync(out+'/budget5000-rectangles.json',JSON.stringify([{x:0,y:0,...frame}]));writeFileSync(out+'/budget5000-grid.png',canvas.toBuffer('image/png'));
const full=createCanvas(1600,900),fc=full.getContext('2d');fc.imageSmoothingEnabled=false;fc.drawImage(canvas,0,0,1600,900);writeFileSync(out+'/budget5000-fitted.png',full.toBuffer('image/png'));const actor=await loadImage('outputs/fit-quality-preview/ayaka-medium.png');fc.drawImage(actor,800-actor.width/actor.height*226*.58,494,actor.width/actor.height*226,226);writeFileSync(out+'/budget5000-composite.png',full.toBuffer('image/png'));
const result={key:'budget5000',target:5000,...p,method:'nearest',fitMethod:f.method,overdraw:f.overdraw,rectangles:f.rows.length,approxControls:f.rows.length*2,compressedBytes:packed.compressedBytes,actualColors:f.colors,exactReconstruction:true,candidates:variants,includesCharacter:false,realDeviceVerified:false};writeFileSync(out+'/budget5000-report.json',JSON.stringify(result,null,2));
const report=JSON.parse(readFileSync(out+'/report.json'));report.presets=report.presets.filter(x=>x.key!=='budget5000');report.presets.push(result);writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
let html=readFileSync(out+'/index.html','utf8');if(!html.includes("key:'budget5000'")){html=html.replace("const options=[","const options=[{key:'budget5000',name:'5000图元预算档',n:"+f.rows.length+"},");html=html.replace('let selected=options[3];','let selected=options[0];');writeFileSync(out+'/index.html',html);}
html=html.replace(/key:'budget5000',name:'5000图元预算档',n:\d+/,"key:'budget5000',name:'5000图元预算档',n:"+f.rows.length);writeFileSync(out+'/index.html',html);
console.log(JSON.stringify(result));




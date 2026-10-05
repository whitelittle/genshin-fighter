import {mkdirSync,copyFileSync,writeFileSync,readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import {sample,colorProcess,fit} from 'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
import {packFrame} from './v2-pack.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const {createCanvas,loadImage}=require('@napi-rs/canvas');
const out='outputs/windrise-pixel-experiment';mkdirSync(out,{recursive:true});
copyFileSync('C:/Users/Cheng/.codex/generated_images/01a0f9d6-536d-7a82-aa51-cdee567758ac/exec-6574b2ce-2905-4b9b-9c66-c5ab4110d82c.png',out+'/source.png');
const report={status:'实际矩形拟合预览，未接入正式GIA，真机未测',source:'source.png',presets:[]};
for(const p of [{key:'240-average',w:240,h:135,colors:32,method:'average'},{key:'240-nearest',w:240,h:135,colors:32,method:'nearest'},{key:'320-nearest',w:320,h:180,colors:32,method:'nearest'},{key:'480-nearest',w:480,h:270,colors:32,method:'nearest'}]){
 const src=await loadImage(out+'/source.png'),c=createCanvas(src.width,src.height),ctx=c.getContext('2d');ctx.drawImage(src,0,0);
 const raw=sample(ctx.getImageData(0,0,c.width,c.height).data,c.width,c.height,p.w,p.h,p.method,220);
 const pixels=colorProcess(raw,new Uint8Array(p.w*p.h),{colors:p.colors,tolerance:3}).data;
 const canvas=createCanvas(p.w,p.h),draw=canvas.getContext('2d'),tiles=[];let rectangles=0,bytes=0;
 const nx=Math.ceil(p.w/240),ny=Math.ceil(p.h/180),tw=Math.ceil(p.w/nx),th=Math.ceil(p.h/ny);
 for(let y0=0;y0<p.h;y0+=th)for(let x0=0;x0<p.w;x0+=tw){const w=Math.min(tw,p.w-x0),h=Math.min(th,p.h-y0),data=new Uint8ClampedArray(w*h*4);for(let y=0;y<h;y++)data.set(pixels.subarray(((y+y0)*p.w+x0)*4,((y+y0)*p.w+x0+w)*4),y*w*4);
  const f=fit(data,w,h);assert(f.exact);const frame={w,h,scale:1600/p.w,anchor:[p.w/2-x0,p.h/2-y0],rows:f.rows};const pack=packFrame(frame);bytes+=pack.compressedBytes;rectangles+=f.rows.length;tiles.push({x:x0,y:y0,...frame});
  for(const r of f.rows){draw.fillStyle=`rgba(${r[4]},${r[5]},${r[6]},${r[7]/255})`;draw.fillRect(x0+r[0],y0+r[1],r[2],r[3]);}
 }
 const reconstructed=draw.getImageData(0,0,p.w,p.h).data;assert.deepEqual(reconstructed,pixels);
 writeFileSync(out+'/'+p.key+'-grid.png',canvas.toBuffer('image/png'));writeFileSync(out+'/'+p.key+'-rectangles.json',JSON.stringify(tiles));
 const full=createCanvas(1600,900),fc=full.getContext('2d');fc.imageSmoothingEnabled=false;fc.drawImage(canvas,0,0,1600,900);writeFileSync(out+'/'+p.key+'-fitted.png',full.toBuffer('image/png'));
 const ayaka=await loadImage('outputs/fit-quality-preview/ayaka-medium.png');fc.drawImage(ayaka,800-ayaka.width/ayaka.height*226*.58,720-226,ayaka.width/ayaka.height*226,226);writeFileSync(out+'/'+p.key+'-composite.png',full.toBuffer('image/png'));
 report.presets.push({...p,rectangles,approxControls:rectangles*2,compressedBytes:bytes,exactReconstruction:true});console.log(p.key,rectangles,bytes);
}
const old=JSON.parse(readFileSync('outputs/fit-quality-preview/quality-report.json'));report.oldComparison=old.presets.map(p=>({key:p.key,...p.scenes.find(x=>x.country==='mondstadt')}));
const a=report.presets[0],b=report.oldComparison.find(x=>x.key==='baseline');report.fairComparison={sameGrid:'240x135',samePalette:32,sameMethod:'average',sameTolerance:3,previousRectangles:b.rectangles,newRectangles:a.rectangles,reductionPercent:Number(((1-a.rectangles/b.rectangles)*100).toFixed(1))};
writeFileSync(out+'/report.json',JSON.stringify(report,null,2));

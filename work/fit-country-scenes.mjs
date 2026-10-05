import{readFileSync as read,writeFileSync as write,mkdirSync,copyFileSync}from'node:fs';
import{createRequire}from'node:module';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
import{packFrame}from'./v2-pack.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const{createCanvas,loadImage}=require('@napi-rs/canvas');
const out='assets/stages-country-v1';mkdirSync(out,{recursive:true});
const sources=JSON.parse(read('work/country-scene-sources.json'));const report=[];
for(const s of sources){
 copyFileSync(s.source,out+'/'+s.key+'-source.png');
 const img=await loadImage(s.source),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);
 const rgba=ctx.getImageData(0,0,img.width,img.height).data;
 for(const w of[192,240]){
  const h=Math.round(w*9/16),raw=sample(rgba,img.width,img.height,w,h,'average',220);
  const data=colorProcess(raw,new Uint8Array(w*h),{colors:32,tolerance:5}).data,result=fit(data,w,h);
  const f={w,h,scale:1600/w,anchor:[w/2,h/2],rows:result.rows};
  const preview=createCanvas(w,h),pc=preview.getContext('2d'),id=pc.createImageData(w,h);id.data.set(data);pc.putImageData(id,0,0);
  write(out+'/'+s.key+'-'+w+'.png',preview.toBuffer('image/png'));write(out+'/'+s.key+'-'+w+'.json',JSON.stringify(f));
  const packed=packFrame(f);report.push({key:s.key,w,h,rectangles:f.rows.length,colors:packed.palette.length,compressedBytes:packed.compressedBytes});
 }
 console.log(s.key,report.filter(r=>r.key===s.key));
}
write(out+'/sources.json',JSON.stringify(sources,null,2));write(out+'/fit-budget.json',JSON.stringify(report,null,2));

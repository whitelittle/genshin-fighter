import{readFileSync as read,writeFileSync as write,mkdirSync,copyFileSync}from'node:fs';import assert from'node:assert/strict';
import{createRequire}from'node:module';import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';import{packFrame}from'./v2-pack.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');const{createCanvas,loadImage}=require('@napi-rs/canvas');
const out='outputs/fit-quality-preview';mkdirSync(out,{recursive:true});
const sources=JSON.parse(read('work/repair-art-sources.json')),ayaka=sources.find(s=>s.key==='ayaka-ratio');copyFileSync(ayaka.source,out+'/ayaka-approved-master.png');
const ref=await loadImage(out+'/ayaka-approved-master.png'),original=createCanvas(ref.width,ref.height),oc=original.getContext('2d');oc.drawImage(ref,0,0);const rgba=oc.getImageData(0,0,ref.width,ref.height).data;
let l=ref.width,r=0,t=ref.height,b=0;for(let y=0;y<ref.height;y++)for(let x=0;x<ref.width;x++)if(rgba[(y*ref.width+x)*4+3]>=220){l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);}
const actorSource=createCanvas(r-l+7,b-t+7),ac=actorSource.getContext('2d');ac.drawImage(ref,l-3,t-3,r-l+7,b-t+7,0,0,r-l+7,b-t+7);
const actorRaw=ac.getImageData(0,0,actorSource.width,actorSource.height).data;const report=[];
for(const preset of[{key:'light',name:'轻量',sw:192,sh:108,colors:24,body:96},{key:'baseline',name:'当前精度对照',sw:240,sh:135,colors:32,body:96},{key:'balanced',name:'中低精度',sw:320,sh:180,colors:40,body:128},{key:'medium',name:'中精度',sw:480,sh:270,colors:48,body:144},{key:'high',name:'高精度',sw:640,sh:360,colors:64,body:192}]){
 const h=preset.body,w=Math.round(actorSource.width*h/actorSource.height),ar=sample(actorRaw,actorSource.width,actorSource.height,w,h,'average',220),ad=colorProcess(ar,new Uint8Array(w*h),{colors:Math.min(preset.colors,48),tolerance:3}).data,af=fit(ad,w,h);assert(af.exact);
 const actor=createCanvas(w,h),ap=actor.getContext('2d');for(const q of af.rows){ap.fillStyle=`rgba(${q[4]},${q[5]},${q[6]},${q[7]/255})`;ap.fillRect(q[0],q[1],q[2],q[3]);}write(out+'/ayaka-'+preset.key+'.png',actor.toBuffer('image/png'));
 const actorFrame={w,h,scale:226/h,anchor:[w*.58,h],rows:af.rows};write(out+'/ayaka-'+preset.key+'.json',JSON.stringify(actorFrame));const packedActor=packFrame(actorFrame);
 const sceneResults=[];
 for(const country of(process.env.FIT_COUNTRIES||'mondstadt,liyue,inazuma').split(',')){
  const img=await loadImage('assets/stages-country-v1/'+country+'-source.png'),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);
  const raw=sample(ctx.getImageData(0,0,img.width,img.height).data,img.width,img.height,preset.sw,preset.sh,'average',220),data=colorProcess(raw,new Uint8Array(preset.sw*preset.sh),{colors:preset.colors,tolerance:3}).data;
  const scene=createCanvas(preset.sw,preset.sh),sc=scene.getContext('2d'),tiles=[];let rectangles=0;
  // Each tile stays within the compact format's byte-coordinate range; no discarded overflow.
  const nx=Math.ceil(preset.sw/240),ny=Math.ceil(preset.sh/180),tw=Math.ceil(preset.sw/nx),th=Math.ceil(preset.sh/ny);
  for(let yy=0;yy<preset.sh;yy+=th)for(let xx=0;xx<preset.sw;xx+=tw){const cw=Math.min(tw,preset.sw-xx),ch=Math.min(th,preset.sh-yy),d=new Uint8ClampedArray(cw*ch*4);for(let y=0;y<ch;y++)d.set(data.subarray(((yy+y)*preset.sw+xx)*4,((yy+y)*preset.sw+xx+cw)*4),y*cw*4);
   const f=fit(d,cw,ch);assert(f.exact);rectangles+=f.rows.length;const frame={w:cw,h:ch,scale:1600/preset.sw,anchor:[preset.sw/2-xx,preset.sh/2-yy],rows:f.rows};const pf=packFrame(frame);tiles.push({...frame,compressedBytes:pf.compressedBytes});
   for(const q of f.rows){sc.fillStyle=`rgba(${q[4]},${q[5]},${q[6]},${q[7]/255})`;sc.fillRect(xx+q[0],yy+q[1],q[2],q[3]);}
  }
  write(out+'/'+country+'-'+preset.key+'-fitted.png',scene.toBuffer('image/png'));write(out+'/'+country+'-'+preset.key+'-tiles.json',JSON.stringify(tiles));
  const composite=createCanvas(1600,900),cc=composite.getContext('2d');cc.imageSmoothingEnabled=false;cc.drawImage(scene,0,0,1600,900);const height=226,aw=w*height/h;cc.drawImage(actor,800-aw*.58,685-height,aw,height);write(out+'/'+country+'-'+preset.key+'-composite.png',composite.toBuffer('image/png'));
  sceneResults.push({country,grid:[preset.sw,preset.sh],colors:preset.colors,rectangles,totalSceneAndActorImages:rectangles+af.rows.length,templateControlsApprox:(rectangles+af.rows.length)*2,compressedBytes:tiles.reduce((n,t)=>n+t.compressedBytes,0)});
 }
 report.push({key:preset.key,name:preset.name,character:{grid:[w,h],rectangles:af.rows.length,colors:packedActor.palette.length,shownHeight:226,compressedBytes:packedActor.compressedBytes},scenes:sceneResults});console.log(preset.key,af.rows.length,sceneResults.map(s=>s.rectangles));
}
write(out+'/quality-report.json',JSON.stringify({status:'actual fitted preview, reconstructed rectangle output; not yet switched into GIA',approvedAyakaMaster:true,displayCanvas:[1600,900],realDeviceVerified:false,presets:report},null,2));

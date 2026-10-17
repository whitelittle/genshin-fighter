import{readFileSync as read,writeFileSync as write,mkdirSync,copyFileSync}from'node:fs';import{createRequire}from'node:module';import assert from'node:assert/strict';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json'),{createCanvas,loadImage}=require('@napi-rs/canvas');
const root='outputs/motion-group1/kamisatoayaka-final';mkdirSync(root+'/frames',{recursive:true});mkdirSync(root+'/data',{recursive:true});
const template=structuredClone(JSON.parse(read('outputs/motion-production/manifest.json')).roles.find(r=>r.key==='kamisatoayaka'));assert(template);
template.name='神里绫华 · 比例与步态修复';template.variant='archive-final';template.height=226;template.frames=[];template.notes=['新比例母版全套动作接入；八帧近远腿步态，非整图平移','源板与拟合保留，真机待验'];
const generated='C:/Users/Cheng/.codex/generated_images/01a0f9d6-536d-7a82-aa51-cdee567758ac/';
const sources=[['basic',generated+'exec-b2f60570-210c-4d95-a5a7-46a8663f5575.png',4],['attack',generated+'exec-789f7cb3-a017-46cb-ab98-c75f8c6722b9.png',4],['connections',generated+'exec-d0f2fcaf-7e42-4e81-899c-f2cc7da2560a.png',4],['walk','assets/repair-art-v1/ayaka-walk-candidates/walk-v2.png',2]];
const frames=[],audit=[];
// This sheet has unequal row heights. Equal quarters cut boots and mix adjacent poses.
const basicRegions=[[0,0,300,367],[300,0,310,367],[610,0,320,367],[930,0,300,367],[0,367,300,336],[300,367,285,336],[585,367,315,336],[900,367,330,336],[0,703,290,275],[290,680,315,310],[605,675,325,325],[930,703,300,297],[0,978,285,300],[285,950,285,328],[560,990,420,288],[980,985,250,293]];
const attackRegions=[[0,0,310,330],[310,0,370,330],[650,0,290,335],[930,0,292,340],[0,330,430,305],[345,350,300,285],[630,318,280,322],[890,335,332,295],[0,650,370,290],[350,650,360,290],[670,600,270,345],[950,610,272,338],[0,925,345,362],[350,925,280,362],[690,925,280,362],[965,925,257,362]];
function cellMask(raw,width,x0,y0,x1,y1){
 const cw=x1-x0,ch=y1-y0,seen=new Uint8Array(cw*ch),parts=[];
 for(let y=0;y<ch;y++)for(let x=0;x<cw;x++){const start=y*cw+x;if(seen[start]||raw[((y+y0)*width+x+x0)*4+3]<220)continue;
  const queue=[start],points=[];seen[start]=1;let l=x,r=x,t=y,b=y;
  for(let at=0;at<queue.length;at++){const v=queue[at],vx=v%cw,vy=Math.floor(v/cw);points.push(v);l=Math.min(l,vx);r=Math.max(r,vx);t=Math.min(t,vy);b=Math.max(b,vy);
   for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const nx=vx+dx,ny=vy+dy;if(nx<0||nx>=cw||ny<0||ny>=ch)continue;const n=ny*cw+nx;if(!seen[n]&&raw[((ny+y0)*width+nx+x0)*4+3]>=220){seen[n]=1;queue.push(n);}}
  }parts.push({points,l,r,t,b});
 }parts.sort((a,b)=>b.points.length-a.points.length);assert(parts.length);const main=parts[0],keep=new Uint8Array(cw*ch);
 for(const part of parts){const gapX=Math.max(0,main.l-part.r,part.l-main.r),gapY=Math.max(0,main.t-part.b,part.t-main.b);if(part===main||(gapX<=10&&gapY<=10))for(const v of part.points)keep[v]=1;}
 return{keep,cw};
}
for(const[kind,path,rows]of sources){copyFileSync(path,root+'/'+kind+'-final.png');const image=await loadImage(path),c=createCanvas(image.width,image.height),ctx=c.getContext('2d');ctx.drawImage(image,0,0);const raw=ctx.getImageData(0,0,c.width,c.height).data,cw=c.width/4,ch=c.height/rows,boxes=[];
 for(let n=0;n<4*rows;n++){const region=kind==='basic'?basicRegions[n]:kind==='attack'?attackRegions[n]:null,x0=region?region[0]:Math.floor(n%4*cw),y0=region?region[1]:Math.floor(Math.floor(n/4)*ch),x1=region?region[0]+region[2]:Math.floor((n%4+1)*cw),y1=region?region[1]+region[3]:Math.floor((Math.floor(n/4)+1)*ch);let left=x1,top=y1,right=x0,bottom=y0;
  const mask=cellMask(raw,c.width,x0,y0,x1,y1);for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++)if(mask.keep[(y-y0)*mask.cw+x-x0]){left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}assert(right>left&&bottom>top,'empty cell');boxes.push({x:Math.max(x0,left-2),y:Math.max(y0,top-2),w:Math.min(x1,right+3)-Math.max(x0,left-2),h:Math.min(y1,bottom+3)-Math.max(y0,top-2),edge:left<=x0||right>=x1-1||top<=y0||bottom>=y1-1,mask,x0,y0});
 }
 const reference=kind==='basic'?boxes[0].h:kind==='attack'?boxes[15].h:kind==='connections'?boxes[0].h:Math.max(...boxes.map(b=>b.h));
 for(let n=0;n<boxes.length;n++){const b=boxes[n],crop=createCanvas(b.w,b.h),cx=crop.getContext('2d');cx.drawImage(image,b.x,b.y,b.w,b.h,0,0,b.w,b.h);const clean=cx.getImageData(0,0,b.w,b.h);for(let y=0;y<b.h;y++)for(let x=0;x<b.w;x++)if(!b.mask.keep[(y+b.y-b.y0)*b.mask.cw+x+b.x-b.x0])clean.data[(y*b.w+x)*4+3]=0;cx.putImageData(clean,0,0);const scale=96/reference,w=Math.max(1,Math.round(b.w*scale)),h=Math.max(1,Math.round(b.h*scale));
  const data=colorProcess(sample(cx.getImageData(0,0,b.w,b.h).data,b.w,b.h,w,h,'average',220),new Uint8Array(w*h),{colors:32,tolerance:4}).data,f=fit(data,w,h),png=createCanvas(w,h),pc=png.getContext('2d');for(const r of f.rows){pc.fillStyle=`rgba(${r[4]},${r[5]},${r[6]},${r[7]/255})`;pc.fillRect(r[0],r[1],r[2],r[3]);}
  const id=kind+n;let feet=[];for(let y=h-1;y>=Math.max(0,h-5);y--)for(let x=0;x<w;x++)if(data[(y*w+x)*4+3]>=220)feet.push(x);const anchor=[feet.length?feet.reduce((a,b)=>a+b,0)/feet.length:w/2,h];
  write(root+'/frames/kamisatoayaka-'+id+'.png',png.toBuffer('image/png'));frames.push({id,w,h,anchor,scale:226/96,rows:f.rows});template.frames.push({id,source:kind+'-final.png',sourceIndex:n,crop:[b.x,b.y,b.w,b.h],grid:[w,h],pixelAnchor:anchor,displayScale:226/96,png:'frames/kamisatoayaka-'+id+'.png',rectCount:f.rows.length,review:'integrated_candidate',edgeRisk:b.edge});audit.push({id,rectangles:f.rows.length,edgeRisk:b.edge,exact:f.exact});
 }
}
template.sequences.walk=Array.from({length:8},(_,n)=>['walk'+n,4]);template.pool=Math.max(...frames.map(f=>f.rows.length));write(root+'/manifest.json',JSON.stringify({status:'integrated_candidate',deviceVerified:false,roles:[template]},null,2));write(root+'/data/kamisatoayaka.json',JSON.stringify({role:'kamisatoayaka',frames,pool:template.pool}));write(root+'/fit-report.json',JSON.stringify({frames:audit,pool:template.pool,approvedMaster:true,deviceVerified:false,alphaThreshold:220},null,2));console.log('AYAKA_FINAL',frames.length,template.pool,'edge flags',audit.filter(f=>f.edgeRisk).map(f=>f.id));

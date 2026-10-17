import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {sample,colorProcess,fit} from 'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const {createCanvas,loadImage}=require('@napi-rs/canvas');
const profiles=JSON.parse(readFileSync('assets/quality-profiles.json'));
const sources={keqing:'assets/fighters/keqing/source/keqing-half-side-v1.png',diluc:'assets/fighters/diluc/source/diluc-wolfs-gravestone-v6-candidate.png'};
mkdirSync('assets/demo',{recursive:true});
const report=[];
for(const [role,path] of Object.entries(sources)){
 const img=await loadImage(path),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);
 const rgba=ctx.getImageData(0,0,img.width,img.height).data,hist=Array(256).fill(0);for(let i=3;i<rgba.length;i+=4)hist[rgba[i]]++;
 console.log(role,JSON.stringify({size:[img.width,img.height],alphaBins:hist.map((n,a)=>[a,n]).filter(x=>x[1]>1000)}));
 // Keep the source unchanged. Runtime sampling removes low-alpha halo, not a semantic cutout.
 const threshold=220;let minX=img.width,minY=img.height,maxX=0,maxY=0;
 for(let y=0;y<img.height;y++)for(let x=0;x<img.width;x++)if(rgba[(y*img.width+x)*4+3]>=threshold){minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);}
 if(minX>maxX)throw Error('No opaque subject '+role);
 const sw=maxX-minX+1,sh=maxY-minY+1,crop=new Uint8ClampedArray(sw*sh*4);
 for(let y=0;y<sh;y++)crop.set(rgba.slice(((y+minY)*img.width+minX)*4,((y+minY)*img.width+maxX+1)*4),y*sw*4);
 // Diluc body height spans almost the full canvas; weapon is allowed wider than body.
 const anchorX=role==='diluc'?570:img.width*.5;
 for(const profile of profiles.profiles){
  const h=profile.standingPixelHeight[role],w=Math.round(sw*h/sh),raw=sample(crop,sw,sh,w,h,'average',threshold),before=fit(raw,w,h);
  const data=colorProcess(raw,new Uint8Array(w*h),{colors:profile.opaqueColorsPerFighter,tolerance:5}).data,result=fit(data,w,h);
  const asset={role,profile:profile.id,w,h,scale:profiles.worldDisplayHeight[role]/h,anchor:[(anchorX-minX)*w/sw,h],rows:result.rows};
  writeFileSync(`assets/demo/${role}-${profile.id}.json`,JSON.stringify(asset));
  const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(data);pctx.putImageData(id,0,0);writeFileSync(`assets/demo/${role}-${profile.id}.png`,pc.toBuffer('image/png'));
  report.push({role,profile:profile.id,source:path,sourceSize:[img.width,img.height],crop:[minX,minY,sw,sh],threshold,grid:[w,h],colorsBefore:before.colors,colors:result.colors,rectangles:result.rows.length,exact:result.exact,overdraw:result.overdraw,worldHeight:profiles.worldDisplayHeight[role]});
 }
}
// Four-pose sheets are hand indexed after visual inspection. Keep complete figures.
const poses={
 keqing:[['windup',530,0,494,740,790,720,620],['slash',0,800,560,700,270,1465,607],['rising',550,750,474,786,785,1510,547]],
 diluc:[['windup',900,0,636,530,1150,522,440],['slash',0,530,905,494,330,992,440],['rising',900,480,636,544,1150,1005,410]]
};
for(const role of Object.keys(poses)){
 const path=`assets/fighters/${role}/source/${role}-demo-actions-v1.png`,img=await loadImage(path),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);const rgba=ctx.getImageData(0,0,img.width,img.height).data;
 for(const profile of profiles.profiles){
  const frames=[JSON.parse(readFileSync(`assets/demo/${role}-${profile.id}.json`))];
  for(const [name,x,y,sw,sh,anchorX,foot,bodyHeight] of poses[role]){
   const crop=new Uint8ClampedArray(sw*sh*4);for(let yy=0;yy<sh;yy++)crop.set(rgba.slice(((y+yy)*img.width+x)*4,((y+yy)*img.width+x+sw)*4),yy*sw*4);
   const unit=profile.standingPixelHeight[role]/bodyHeight,h=Math.round(sh*unit),w=Math.round(sw*unit);let raw=sample(crop,sw,sh,w,h,'average',220);
   // Adjacent-sheet fragments are disconnected. Retain the main complete character component.
   const seen=new Uint8Array(w*h),components=[];for(let i=0;i<w*h;i++)if(raw[i*4+3]&&!seen[i]){const q=[i];seen[i]=1;for(let k=0;k<q.length;k++){const j=q[k],xx=j%w,yy=Math.floor(j/w);for(const n of [xx?j-1:-1,xx<w-1?j+1:-1,yy?j-w:-1,yy<h-1?j+w:-1])if(n>=0&&!seen[n]&&raw[n*4+3]){seen[n]=1;q.push(n);}}components.push(q);}
   components.sort((a,b)=>b.length-a.length);for(const q of components.slice(1))for(const j of q)raw.fill(0,j*4,j*4+4);
   const data=colorProcess(raw,new Uint8Array(w*h),{colors:profile.opaqueColorsPerFighter,tolerance:5}).data,result=fit(data,w,h);
   const asset={role,pose:name,profile:profile.id,w,h,scale:profiles.worldDisplayHeight[role]/profile.standingPixelHeight[role],anchor:[(anchorX-x)*w/sw,(foot-y)*h/sh],rows:result.rows};frames.push(asset);
   const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(data);pctx.putImageData(id,0,0);writeFileSync(`assets/demo/${role}-${profile.id}-${name}.png`,pc.toBuffer('image/png'));
   report.push({role,pose:name,profile:profile.id,source:path,crop:[x,y,sw,sh],anchorSource:[anchorX,foot],bodyHeightSource:bodyHeight,grid:[w,h],colors:result.colors,rectangles:result.rows.length,exact:result.exact,overdraw:result.overdraw});
  }
  writeFileSync(`assets/demo/${role}-${profile.id}-frames.json`,JSON.stringify({role,frames,pool:Math.max(...frames.map(f=>f.rows.length))}));
 }
}
writeFileSync('assets/demo/load-report.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report.map(({role,profile,grid,colors,rectangles})=>({role,profile,grid,colors,rectangles}))));

import{readFileSync,writeFileSync,existsSync}from'node:fs';import{createRequire}from'node:module';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');const{createCanvas,loadImage}=require('@napi-rs/canvas');
const names=['idle','walk1','walk2','crouch','guard','crouchGuard','hurt','down','jump','slash','special','qRelease'];const report=[];
for(const key of ['kaeya','jean','klee','lisa','ganyu','yanfei','xiao','hutao','lawachurl']){
 if(!existsSync(`assets/test-v1/${key}-sheet.png`))continue;
 const image=await loadImage(`assets/test-v1/${key}-sheet.png`),sw=Math.floor(image.width/4),sh=Math.floor(image.height/3);let body=0;const frames=[];
 for(let i=0;i<12;i++){
  const c=createCanvas(sw,sh),ctx=c.getContext('2d');ctx.drawImage(image,(i%4)*sw,Math.floor(i/4)*sh,sw,sh,0,0,sw,sh);const rgba=ctx.getImageData(0,0,sw,sh).data;
  let x0=sw,y0=sh,x1=0,y1=0;for(let y=0;y<sh;y++)for(let x=0;x<sw;x++)if(rgba[(y*sw+x)*4+3]>=220){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}
  if(x0>x1)throw Error('empty cell '+key+' '+i);if(!i)body=y1-y0+1;
  const height=key==='klee'?66:key==='lawachurl'?104:84,world=key==='klee'?178:key==='lawachurl'?280:232;
  const factor=height/body,w=Math.max(1,Math.round((x1-x0+1)*factor)),h=Math.max(1,Math.round((y1-y0+1)*factor));
  const crop=createCanvas(x1-x0+1,y1-y0+1),cc=crop.getContext('2d');cc.drawImage(c,x0,y0,crop.width,crop.height,0,0,crop.width,crop.height);
  const raw=sample(cc.getImageData(0,0,crop.width,crop.height).data,crop.width,crop.height,w,h,'average',220),data=colorProcess(raw,new Uint8Array(w*h),{colors:18,tolerance:8}).data;
  const fitted=fit(data,w,h);if(!fitted.exact)throw Error('inexact');const f={pose:names[i],w,h,scale:world/height,anchor:[w/2,h-1],rows:fitted.rows};frames.push(f);
  const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(data);pctx.putImageData(id,0,0);writeFileSync(`assets/test-v1/${key}-${names[i]}.png`,pc.toBuffer('image/png'));
  if(!i){const ph=Math.round(crop.height*.25),pw=crop.width,px=createCanvas(pw,ph),pctx=px.getContext('2d');pctx.drawImage(crop,0,0,pw,ph,0,0,pw,ph);const w=20,h=22;const raw=sample(pctx.getImageData(0,0,pw,ph).data,pw,ph,w,h,'average',220),d=colorProcess(raw,new Uint8Array(w*h),{colors:14,tolerance:8}).data;writeFileSync(`assets/test-v1/${key}-portrait.json`,JSON.stringify({w,h,scale:2.5,anchor:[w/2,h/2],rows:fit(d,w,h).rows}));}
 }
 const aliases={idle2:'idle',airHurt:'hurt',getup:'crouch',windup:'guard',low:'slash',rising:'slash',eThrow:'special',qCharge:'guard'};
 for(const[pose,target]of Object.entries(aliases))frames.push({...frames.find(f=>f.pose===target),pose});
 const pool=Math.max(...frames.map(f=>f.rows.length));writeFileSync(`assets/test-v1/${key}-frames.json`,JSON.stringify({role:key,frames,pool}));report.push({role:key,uniquePoses:12,aliases:Object.keys(aliases),pool,deviceVerified:false});
}
writeFileSync('assets/test-v1/fit-report.json',JSON.stringify(report,null,2));console.log(report.map(r=>({role:r.role,pool:r.pool})));
await import('./fit-test-v1-portraits.mjs');


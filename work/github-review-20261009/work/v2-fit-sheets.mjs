import{readFileSync,writeFileSync,existsSync}from'node:fs';import{createRequire}from'node:module';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json'),{createCanvas,loadImage}=require('@napi-rs/canvas');
const roster=JSON.parse(readFileSync('assets/roster-v2/roster.json')).filter(r=>r[0]!=='ronova'),names=['idle','walk1','walk2','crouch','guard','crouchGuard','hurt','down','jump','slash','special','qRelease'],report=[];
for(const[key,name]of roster){const path=`assets/roster-v2/${key}-sheet.png`;if(!existsSync(path))continue;const im=await loadImage(path),sw=Math.floor(im.width/4),sh=Math.floor(im.height/3),frames=[];let body=0;
 for(let i=0;i<12;i++){const c=createCanvas(sw,sh),ctx=c.getContext('2d');ctx.drawImage(im,(i%4)*sw,Math.floor(i/4)*sh,sw,sh,0,0,sw,sh);const rgba=ctx.getImageData(0,0,sw,sh).data;let x0=sw,y0=sh,x1=0,y1=0;
  for(let y=0;y<sh;y++)for(let x=0;x<sw;x++)if(rgba[(y*sw+x)*4+3]>=180){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}
  if(x0>x1)throw Error('empty pose '+key+' '+i);if(!i)body=y1-y0+1;
  const child=['nahida','kachina'].includes(key),height=key==='lawachurl'?128:child?88:108,world=key==='lawachurl'?295:child?180:232;
  const factor=Math.min(height/body,250/(x1-x0+1),250/(y1-y0+1)),w=Math.max(1,Math.round((x1-x0+1)*factor)),h=Math.max(1,Math.round((y1-y0+1)*factor));
  const crop=createCanvas(x1-x0+1,y1-y0+1),cc=crop.getContext('2d');cc.drawImage(c,x0,y0,crop.width,crop.height,0,0,crop.width,crop.height);
  const raw=sample(cc.getImageData(0,0,crop.width,crop.height).data,crop.width,crop.height,w,h,'nearest',160),data=colorProcess(raw,new Uint8Array(w*h),{colors:32,tolerance:3}).data,rows=fit(data,w,h).rows;
  frames.push({pose:names[i],w,h,scale:world/height,anchor:[w/2,h-1],rows});
  const p=createCanvas(w,h),pc=p.getContext('2d'),d=pc.createImageData(w,h);d.data.set(data);pc.putImageData(d,0,0);writeFileSync(`assets/roster-v2/${key}-${names[i]}.png`,p.toBuffer('image/png'));
 }
 for(const[pose,target]of Object.entries({idle2:'idle',airHurt:'hurt',getup:'crouch',windup:'guard',low:'slash',rising:'slash',eThrow:'special',qCharge:'guard'}))frames.push({...frames.find(f=>f.pose===target),pose});
 const pool=Math.max(...frames.map(f=>f.rows.length));writeFileSync(`assets/roster-v2/${key}-frames.json`,JSON.stringify({role:key,frames,pool}));report.push({key,name,uniquePoses:12,aliases:8,pool});console.log(key,pool);
}writeFileSync('assets/roster-v2/fit-report.json',JSON.stringify(report,null,2));

import{readFileSync as read,writeFileSync as write}from'node:fs';
import{createRequire}from'node:module';
import{sample,colorProcess}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
import{packFrame}from'./v2-pack.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');const{createCanvas,loadImage}=require('@napi-rs/canvas');
const out='assets/stages-country-v1',sources=JSON.parse(read(out+'/sources.json')),report=[];const W=480,H=270,budget=6000;
class Heap{q=[];push(v){let i=this.q.length;this.q.push(v);while(i){const p=(i-1)>>1;if(this.q[p].error>=v.error)break;this.q[i]=this.q[p];i=p;}this.q[i]=v;}pop(){const v=this.q[0],last=this.q.pop();if(this.q.length){let i=0;while(i*2+1<this.q.length){let c=i*2+1;if(c+1<this.q.length&&this.q[c+1].error>this.q[c].error)c++;if(this.q[c].error<=last.error)break;this.q[i]=this.q[c];i=c;}this.q[i]=last;}return v;}}
for(const s of sources){
 const img=await loadImage(out+'/'+s.key+'-source.png'),c=createCanvas(img.width,img.height),ctx=c.getContext('2d');ctx.drawImage(img,0,0);
 const raw=sample(ctx.getImageData(0,0,img.width,img.height).data,img.width,img.height,W,H,'average',220);
 const data=colorProcess(raw,new Uint8Array(W*H),{colors:32,tolerance:5}).data,palette=[];const seen=new Set();
 for(let i=0;i<data.length;i+=4){const key=data[i]*65536+data[i+1]*256+data[i+2];if(!seen.has(key)){seen.add(key);palette.push([data[i],data[i+1],data[i+2]]);}}
 const stride=W+1,tables=Array.from({length:6},()=>new Float64Array(stride*(H+1)));
 for(let y=1;y<=H;y++)for(let x=1;x<=W;x++){const p=((y-1)*W+x-1)*4,i=y*stride+x;for(let k=0;k<6;k++){const v=data[p+k%3],z=k<3?v:v*v;tables[k][i]=z+tables[k][i-1]+tables[k][i-stride]-tables[k][i-stride-1];}}
 const sum=(t,x,y,w,h)=>t[(y+h)*stride+x+w]-t[y*stride+x+w]-t[(y+h)*stride+x]+t[y*stride+x];
 const make=(x,y,w,h,tile)=>{const n=w*h,avg=tables.slice(0,3).map(t=>sum(t,x,y,w,h)/n);let error=0;for(let k=0;k<3;k++)error+=Math.max(0,sum(tables[k+3],x,y,w,h)-avg[k]*avg[k]*n);return{x,y,w,h,tile,avg,error:(w===1&&h===1)?-1:error};};
 const heap=new Heap();for(let t=0;t<4;t++)heap.push(make(t%2*240,Math.floor(t/2)*135,240,135,t));
 while(heap.q.length<budget&&heap.q[0].error>0){const r=heap.pop();const vertical=r.w>=r.h;if(vertical){const a=r.w>>1;heap.push(make(r.x,r.y,a,r.h,r.tile));heap.push(make(r.x+a,r.y,r.w-a,r.h,r.tile));}else{const a=r.h>>1;heap.push(make(r.x,r.y,r.w,a,r.tile));heap.push(make(r.x,r.y+a,r.w,r.h-a,r.tile));}}
 const rows=Array.from({length:4},()=>[]),pv=createCanvas(W,H),pc=pv.getContext('2d');
 for(const r of heap.q){let color=palette[0],best=Infinity;for(const p of palette){let d=0;for(let k=0;k<3;k++)d+=(p[k]-r.avg[k])**2;if(d<best){best=d;color=p;}}const tx=r.tile%2*240,ty=Math.floor(r.tile/2)*135;rows[r.tile].push([r.x-tx,r.y-ty,r.w,r.h,...color,255]);pc.fillStyle=`rgb(${color})`;pc.fillRect(r.x,r.y,r.w,r.h);}
 const tiles=rows.map((r,i)=>({w:240,h:135,scale:1600/W,anchor:[W/2-i%2*240,H/2-Math.floor(i/2)*135],rows:r.sort((a,b)=>a[1]-b[1]||a[0]-b[0])}));
 write(out+'/'+s.key+'-adaptive.png',pv.toBuffer('image/png'));write(out+'/'+s.key+'-adaptive.json',JSON.stringify(tiles));
 report.push({key:s.key,master:[img.width,img.height],workingGrid:[W,H],rectangles:tiles.reduce((n,t)=>n+t.rows.length,0),tiles:tiles.map(t=>({rectangles:t.rows.length,...Object.fromEntries(Object.entries(packFrame(t)).filter(([k])=>['compressedBytes','rawBytes'].includes(k)))}))});console.log(s.key,report.at(-1).rectangles);
}
write(out+'/adaptive-budget.json',JSON.stringify({method:'error-priority multi-resolution rectangles; lossy design candidate, original masters preserved',budgetPerCurrentStage:budget,report},null,2));

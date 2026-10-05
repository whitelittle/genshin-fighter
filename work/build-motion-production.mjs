import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{createRequire}from'node:module';
import{gzipSync}from'node:zlib';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
import{designs}from'./action-probe-design.mjs';
const req=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json'),{createCanvas,loadImage}=req('@napi-rs/canvas');
const root=process.argv[2]||'outputs/motion-production',source=JSON.parse(readFileSync(root+'/source-manifest.json','utf8')),cache=new Map(),report=[];
mkdirSync(root+'/frames',{recursive:true});mkdirSync(root+'/data',{recursive:true});
const sequences={idle:[['basic0',24],['basic1',24]],walk:[['basic2',8],['basic3',8],['basic4',8],['basic3',8]],crouch:[['basic5',36]],guard:[['basic6',36]],crouchGuard:[['basic7',36]],jump:[['basic8',6],['basic9',14],['basic10',14],['basic11',6]],hurt:[['basic12',20]],airHurt:[['basic13',24]],down:[['basic14',36]],getup:[['basic15',16],['basic5',8],['basic0',12]],A:[['attack0',8],['attack1',3],['attack2',14]],lowA:[['attack3',8],['attack4',3],['attack5',14]],airA:[['attack6',8],['attack7',6],['basic10',10],['basic11',6]],E:[['attack8',14],['attack9',4],['attack10',24]],Q:[['attack11',22],['attack12',6],['attack13',36]],win:[['attack14',18],['attack15',48]]};
for(const role of source.roles){
 const design=structuredClone(role.design||designs.find(r=>r.key===role.key));if(!design)throw Error('Missing explicit design for '+role.key);design.moves.Q.active=5;design.moves.Q.hitCount=1;if(role.key==='nahida'){design.moves.Q.damage=30;design.moves.Q.support=false;design.moves.Q.effectDuration=0;design.moves.Q.notes='智慧殿堂意象用于命中后短演出；30伤害仅为探针候选。';}role.design=design;role.sequences=structuredClone(sequences);
 for(const action of['A','E','Q']){const m=design.moves[action];role.sequences[action].forEach((s,i)=>s[1]=[m.startup,m.active,m.recovery][i]);}
 for(const action of['A','E']){const m=design.moves[action],split=(n,k)=>Array.from({length:k},(_,i)=>Math.floor(n/k)+(i<n%k?1:0));const holds=[...split(m.startup,3),...split(m.active,2),...split(m.recovery,3)];role.sequences[action]=holds.map((n,i)=>['connections'+(i+(action==='E'?8:0)),n]).filter(s=>s[1]>0);}
 if(role.key==='diluc')role.sequences.E.at(-1)[0]='basic0';
 const data=[];
 for(const f of role.frames){
  if(!cache.has(f.source))cache.set(f.source,await loadImage(root+'/'+f.source));const img=cache.get(f.source),[x,y,sw,sh]=f.crop,c=createCanvas(sw,sh),ctx=c.getContext('2d');ctx.drawImage(img,x,y,sw,sh,0,0,sw,sh);
  const pixelUnit=f.unit*96/role.height,w=Math.max(1,Math.round(sw*pixelUnit)),h=Math.max(1,Math.round(sh*pixelUnit));
  const raw=sample(ctx.getImageData(0,0,sw,sh).data,sw,sh,w,h,'average',220),processed=colorProcess(raw,new Uint8Array(w*h),{colors:32,tolerance:4}).data,r=fit(processed,w,h);if(!r.exact)throw Error('inexact '+role.key+f.id);
  const pc=createCanvas(w,h),pctx=pc.getContext('2d'),id=pctx.createImageData(w,h);id.data.set(processed);pctx.putImageData(id,0,0);f.png=`frames/${role.key}-${f.id}.png`;writeFileSync(root+'/'+f.png,pc.toBuffer('image/png'));
  f.grid=[w,h];f.displayScale=role.height/96;f.pixelAnchor=[f.anchor[0]*w/sw,f.anchor[1]*h/sh];f.rectCount=r.rows.length;
  data.push({id:f.id,w,h,anchor:f.pixelAnchor,scale:f.displayScale,rows:r.rows});report.push({role:role.key,id:f.id,grid:[w,h],rects:r.rows.length,source:f.source,edgeRisk:f.edgeRisk,exact:r.exact});
 }
 const json=JSON.stringify({role:role.key,frames:data,pool:Math.max(...data.map(f=>f.rows.length))});writeFileSync(root+`/data/${role.key}.json`,json);writeFileSync(root+`/data/${role.key}.json.gz`,gzipSync(json));
 role.pool=Math.max(...data.map(f=>f.rows.length));role.dataBytes=Buffer.byteLength(json);role.gzipBytes=gzipSync(json).length;
}
writeFileSync(root+'/manifest.json',JSON.stringify(source,null,2));writeFileSync(root+'/data.js','window.MOTION_PRODUCTION='+JSON.stringify(source)+';');writeFileSync(root+'/fit-report.json',JSON.stringify({profile:'96 body pixels, 32 colors, average sample, alpha threshold 220, disjoint exact rectangles',frames:report,pools:source.roles.map(r=>({key:r.key,pool:r.pool,dataBytes:r.dataBytes,gzipBytes:r.gzipBytes})),verified:'native fitting reconstruction only',deviceVerified:false,productionCombatChanged:false},null,2));
console.log('MOTION_FIT',report.length,source.roles.map(r=>[r.key,r.pool,r.gzipBytes]));

import{readFileSync,writeFileSync,existsSync}from'node:fs';import{createRequire}from'node:module';
import{colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json'),{createCanvas,loadImage}=require('@napi-rs/canvas');
const roster=JSON.parse(readFileSync('assets/roster-v2/roster.json')).filter(r=>r[0]!=='ronova'),heads=[],thumbs=[],report=[];
async function make(key,size){let path=`assets/roster-v2/${key}-official-head.png`;if(key==='lawachurl')path='assets/roster-v2/lawachurl-reference.webp';const im=await loadImage(path),c=createCanvas(size,size),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;
 let sx=0,sy=0,sw=im.width,sh=im.height;if(key==='lawachurl'){sx=65;sy=8;sw=370;sh=340;}
 // Contain the entire reference icon. No face-only crop; keep ears, hats, horns and hair.
 const scale=Math.min((size-2)/sw,(size-2)/sh),w=Math.round(sw*scale),h=Math.round(sh*scale);ctx.drawImage(im,sx,sy,sw,sh,Math.floor((size-w)/2),Math.floor((size-h)/2),w,h);
 const raw=ctx.getImageData(0,0,size,size).data;for(let i=0;i<raw.length;i+=4){if(raw[i+3]<80){raw[i]=raw[i+1]=raw[i+2]=raw[i+3]=0;}else raw[i+3]=255;}
 const data=colorProcess(raw,new Uint8Array(size*size),{colors:size===32?24:40,tolerance:2}).data,rows=fit(data,size,size).rows;const f={w:size,h:size,scale:size===32?2.2:2.5,anchor:[size/2,size/2],rows};
 const id=ctx.createImageData(size,size);id.data.set(data);ctx.putImageData(id,0,0);writeFileSync(`assets/roster-v2/${key}-face-${size}.png`,c.toBuffer('image/png'));return f;
}
for(const[key,name]of roster){heads.push(await make(key,48));thumbs.push(await make(key,32));report.push({key,name,headRows:heads.at(-1).rows.length,thumbnailRows:thumbs.at(-1).rows.length,fullIconContain:true});}
writeFileSync('assets/roster-v2/heads.json',JSON.stringify(heads));writeFileSync('assets/roster-v2/thumbs.json',JSON.stringify(thumbs));writeFileSync('assets/roster-v2/head-budgets.json',JSON.stringify(report,null,2));
const c=createCanvas(9*110,5*125),ctx=c.getContext('2d');ctx.fillStyle='#233043';ctx.fillRect(0,0,c.width,c.height);for(let i=0;i<roster.length;i++){let im=await loadImage(`assets/roster-v2/${roster[i][0]}-face-48.png`),x=i%9*110,y=Math.floor(i/9)*125;ctx.imageSmoothingEnabled=false;ctx.drawImage(im,x+7,y,96,96);ctx.fillStyle='white';ctx.font='12px Arial';ctx.fillText(roster[i][0],x+3,y+114);}writeFileSync('assets/roster-v2/heads-fitted-gallery.png',c.toBuffer('image/png'));console.log({maxHead:Math.max(...heads.map(f=>f.rows.length)),maxThumb:Math.max(...thumbs.map(f=>f.rows.length)),roster:roster.length});

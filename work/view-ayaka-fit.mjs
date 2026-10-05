import{createRequire}from'node:module';import{writeFileSync,readFileSync}from'node:fs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json'),{createCanvas,loadImage}=require('@napi-rs/canvas');
const c=createCanvas(1300,650),x=c.getContext('2d');x.fillStyle='#222c36';x.fillRect(0,0,c.width,c.height);x.imageSmoothingEnabled=false;
for(const[n,id]of ['basic0','basic1','attack11','attack13'].entries()){const img=await loadImage('outputs/motion-group1/kamisatoayaka-final/frames/kamisatoayaka-'+id+'.png');x.drawImage(img,n*325+30,55,img.width*5,img.height*5);x.fillStyle='white';x.font='18px sans-serif';x.fillText(id,n*325+30,30);}
writeFileSync('outputs/midphase-final/ayaka-idle-fit-inspection.png',c.toBuffer('image/png'));
const data=JSON.parse(readFileSync('outputs/motion-group1/kamisatoayaka-final/manifest.json')).roles[0];console.log(JSON.stringify(data.frames.slice(0,4).map(f=>({id:f.id,crop:f.crop,grid:f.grid,edge:f.edgeRisk})),null,2));

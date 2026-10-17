import fs from 'node:fs';
import{createRequire}from'node:module';
const require=createRequire('C:/Users/Cheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
const folder='outputs/seat-video-inspection';fs.mkdirSync(folder,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'D:/Program Files/Google/Chrome/Application/chrome.exe'});
try{
 const page=await browser.newPage({acceptDownloads:false});
 const b64=fs.readFileSync('C:/Users/Cheng/Downloads/SVID_20261004_185629_1.mp4').toString('base64');
 await page.setContent('<video id="v" muted preload="auto" src="data:video/mp4;base64,'+b64+'"></video>');
 const info=await page.evaluate(async()=>{const v=document.getElementById('v');await new Promise((resolve,reject)=>{if(v.readyState>=2)return resolve();v.addEventListener('loadeddata',resolve,{once:true});v.addEventListener('error',()=>reject(new Error('Video decode error')),{once:true});});return{duration:v.duration,width:v.videoWidth,height:v.videoHeight};});
 console.log(JSON.stringify(info));
 for(const [i,fraction]of [0,.2,.4,.6,.8,.98].entries()){
  const result=await page.evaluate(async time=>{const v=document.getElementById('v');if(Math.abs(v.currentTime-time)>.01){await new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=time;});}const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);return c.toDataURL('image/png').split(',')[1];},info.duration*fraction);
  fs.writeFileSync(folder+'/frame-'+i+'.png',Buffer.from(result,'base64'));
 }
 fs.writeFileSync(folder+'/metadata.json',JSON.stringify(info,null,2));
}finally{await browser.close();}

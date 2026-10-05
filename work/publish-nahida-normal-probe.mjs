import{readFileSync,writeFileSync}from'node:fs';
const base='outputs/motion-production',root=base+'/nahida-normal-v2',D=JSON.parse(readFileSync(root+'/manifest.json','utf8')),r=structuredClone(D.roles[0]);
r.visualKey='nahida';r.key='nahida-normal-v2';r.frames.forEach(f=>f.png='nahida-normal-v2/'+f.png);
writeFileSync(root+'/addon.js','window.NAHIDA_NORMAL='+JSON.stringify(r)+';window.MOTION_PRODUCTION.roles.push(window.NAHIDA_NORMAL);');
let page=readFileSync(base+'/index.html','utf8');if(!page.includes('nahida-normal-v2/addon.js'))page=page.replace('<script src="data.js"></script>','<script src="data.js"></script><script src="nahida-normal-v2/addon.js"></script>');page=page.replace('<h2>当前五位</h2>','<h2>角色 / 动作版本</h2>');writeFileSync(base+'/index.html',page);
writeFileSync(root+'/index.html','<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../index.html#nahida-normal-v2"><title>纳西妲正常比例动作版</title><a href="../index.html#nahida-normal-v2">查看完整新版本动作探针</a>');
console.log('NAHIDA_NORMAL_PROBE',r.frames.length,r.pool);

import{readFileSync as read,writeFileSync as write,existsSync}from'node:fs';import assert from'node:assert/strict';import{createHash}from'node:crypto';
import{exportGia,importGia,inspectGia,validateServerGiaCompatibility}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out=process.env.REPAIR_OUT||'outputs/test-repair-v1',stamp=process.argv[2];assert.match(stamp,/^\d{8}_\d{6}$/);
const save=JSON.parse(read(out+'/fighter.save.json')),v=JSON.parse(read(out+'/verification.json'));assert(v.threeDifferentSynchronizedStages&&v.onePlayerResultReturnSynchronizesBoth);
assert(JSON.parse(read(out+'/loading-verification.json')).canceledPrefetchReleased);assert(JSON.parse(read(out+'/mobile-verification.json')).results.length===2);
const label=process.env.DELIVERY_LABEL||(out.includes('midphase-final')?'19角色_9000背景_蓝红圆点':'碰撞加载场景修复');
const lua='gpt_'+stamp+'_'+label+'.lua';save.assets.scripts[0].path='lua/'+lua;save.assets.scripts[0].filename=lua;write(out+'/'+lua,save.assets.scripts[0].source);
const files=[];for(const kind of['server','client']){const title='gpt_'+stamp+'_'+(kind==='server'?'A_'+label:'B_通用图元模板'),project=save.assets[kind];project.root.name=title;project.meta.name=title;project.meta.giaFileName=title+'.gia';if(kind==='client')project.root.children[0].name=title;
 const exported=exportGia(project,{scripts:kind==='server'?save.assets.scripts:[]}),info=inspectGia(exported.buffer);assert.equal(info.assetType,kind==='server'?'server-control-template':'client-control-template');assert(importGia(exported.buffer));if(kind==='server')assert(validateServerGiaCompatibility(exported.buffer).valid);
 const filename=title+'.gia';assert(!existsSync(out+'/'+filename));write(out+'/'+filename,exported.buffer);files.push({kind,filename,bytes:exported.buffer.length,sha256:createHash('sha256').update(exported.buffer).digest('hex')});}
write(out+'/delivery.json',JSON.stringify({stamp,lua,scriptPath:'lua/'+lua,files,stageSeedRange:[1,210],deviceVerified:false},null,2));console.log(JSON.stringify(files));

import{readFileSync,writeFileSync,existsSync}from'node:fs';import assert from'node:assert/strict';import{createHash}from'node:crypto';
import{exportGia,importGia,inspectGia,validateServerGiaCompatibility}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/group1-full-test',stamp=process.argv[2];assert.match(stamp,/^\d{8}_\d{6}$/);
const save=JSON.parse(readFileSync(out+'/fighter.save.json','utf8')),integration=JSON.parse(readFileSync(out+'/motion-integration.json','utf8')),test=JSON.parse(readFileSync(out+'/verification.json','utf8'));
assert.equal(integration.upgraded.length,14,'All fourteen batch roles must be integrated, including the correct reused Lawachurl');assert(test.onePlayerResultReturnSynchronizesBoth);assert(test.threeRounds);
const luaName=`gpt_${stamp}_第一批完整测试.lua`;save.assets.scripts[0].path='lua/'+luaName;save.assets.scripts[0].filename=luaName;writeFileSync(out+'/'+luaName,save.assets.scripts[0].source);
const deliveries=[];
for(const kind of['server','client']){
 const title=`gpt_${stamp}_${kind==='server'?'A_第一批完整测试界面':'B_通用图元模板'}`,project=save.assets[kind];project.root.name=title;project.meta.name=title;project.meta.giaFileName=title+'.gia';
 if(kind==='client')project.root.children[0].name=title;
 const ex=exportGia(project,{scripts:kind==='server'?save.assets.scripts:[]}),info=inspectGia(ex.buffer);assert.equal(info.assetType,kind==='server'?'server-control-template':'client-control-template');assert(importGia(ex.buffer));
 if(kind==='server'){const v=validateServerGiaCompatibility(ex.buffer);assert(v.valid,JSON.stringify(v));}
 const filename=title+'.gia';assert(!existsSync(out+'/'+filename));writeFileSync(out+'/'+filename,ex.buffer);deliveries.push({kind,filename,bytes:ex.buffer.length,sha256:createHash('sha256').update(ex.buffer).digest('hex'),...info});
}
writeFileSync(out+'/delivery.json',JSON.stringify({stamp,lua:luaName,scriptPath:'lua/'+luaName,files:deliveries,deviceVerified:false},null,2));console.log(JSON.stringify(deliveries));

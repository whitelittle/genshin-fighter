import{readFileSync,writeFileSync,copyFileSync,mkdirSync}from'node:fs';import{resolve,dirname}from'node:path';import assert from'node:assert/strict';
import{exportGia,importGia,validateServerGiaCompatibility}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/test-v1',delivery=JSON.parse(readFileSync(out+'/delivery.json')),save=JSON.parse(readFileSync(out+'/fighter.save.json'));assert.match(delivery.name,/^gpt_\d{8}_\d{6}_A_/);
const exportDir=resolve('C:/Users/Cheng/AppData/LocalLow/miHoYo/原神/BeyondLocal/Beyond_Local_Export'),stamp=delivery.name.match(/^gpt_(\d{8}_\d{6})/)[1];
save.assets.server.root.name=delivery.name;save.assets.server.meta.name=delivery.name;save.assets.server.meta.giaFileName=delivery.name+'.gia';save.assets.scripts[0].path=delivery.path;save.assets.scripts[0].filename=delivery.path.split('/').pop();
const exported=exportGia(save.assets.server,{scripts:save.assets.scripts});assert.ok(validateServerGiaCompatibility(exported.buffer).valid);assert.ok(importGia(exported.buffer,delivery.name+'.gia').scripts.some(s=>s.path===delivery.path&&s.source.includes('retryFlow')));
const backup=out+'/delivered-before-flow-retry';mkdirSync(backup,{recursive:true});
for(const[name,data]of[[delivery.name+'.gia',exported.buffer],[`gpt_${stamp}_fighter_test_v1.lua`,save.assets.scripts[0].source]]){
 const target=resolve(exportDir,name);assert.equal(dirname(target),exportDir);copyFileSync(out+'/'+name,backup+'/'+name);writeFileSync(out+'/'+name,data);writeFileSync(target,data);
}
writeFileSync(out+'/delivery-verification.json',JSON.stringify({serverOnly:true,valid:true,scriptRoundTrip:true,bytes:exported.buffer.length,retryFlow:true,oldDeliveryBackedUp:true,deviceVerified:false},null,2));console.log('DELIVERY_UPDATED_WITH_BACKUP');

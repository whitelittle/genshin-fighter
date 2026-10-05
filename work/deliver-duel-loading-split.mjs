import{readFileSync,writeFileSync,existsSync}from'node:fs';import assert from'node:assert/strict';
import{exportGia,importGia,inspectGia}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const stamp=process.argv[2];assert.match(stamp,/^\d{8}_\d{6}$/);
const save=JSON.parse(readFileSync('outputs/duel-loading/fighter.save.json'));
const names={server:`gpt_${stamp}_A_黑屏加载界面`,client:`gpt_${stamp}_B_图元模板`};
const deliveries=[];
for(const asset of ['server','client']){
 const project=save.assets[asset];project.root.name=names[asset];project.meta.name=names[asset];project.meta.giaFileName=names[asset]+'.gia';
 if(asset==='client')project.root.children[0].name=names[asset];
 const ex=exportGia(project,{scripts:asset==='server'?save.assets.scripts:[]}),filename=names[asset]+'.gia';
 const info=inspectGia(ex.buffer);assert.equal(info.assetType,asset==='server'?'server-control-template':'client-control-template');assert.equal(info.templateCount,asset==='server'?0:1);
 const imported=importGia(ex.buffer);assert.ok(imported);
 const target='C:/Users/Cheng/AppData/LocalLow/miHoYo/原神/BeyondLocal/Beyond_Local_Export/'+filename;assert.ok(!existsSync(target));
 writeFileSync('outputs/duel-loading/'+filename,ex.buffer);writeFileSync(target,ex.buffer);assert.deepEqual(readFileSync(target),ex.buffer);
 deliveries.push({filename,target,bytes:ex.buffer.length,...info});
}
writeFileSync('outputs/duel-loading/latest-split-delivery.json',JSON.stringify(deliveries,null,2));console.log(JSON.stringify(deliveries));

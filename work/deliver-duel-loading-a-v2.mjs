import{readFileSync,writeFileSync,existsSync}from'node:fs';import assert from'node:assert/strict';
import{exportGia,validateServerGiaCompatibility}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const stamp=process.argv[2];assert.match(stamp,/^\d{8}_\d{6}$/);
const save=JSON.parse(readFileSync('outputs/duel-loading/fighter.save.json'));
const name=`gpt_${stamp}_A_黑屏启动修订_索引已填`,project=save.assets.server;
project.root.name=name;project.meta.name=name;project.meta.giaFileName=name+'.gia';
const script=save.assets.scripts[0];assert.ok(script.source.includes('local PIXEL_TEMPLATE_INDEX=1073741845'));
const ex=exportGia(project,{scripts:save.assets.scripts});assert.ok(validateServerGiaCompatibility(ex.buffer).valid);
const dir='C:/Users/Cheng/AppData/LocalLow/miHoYo/原神/BeyondLocal/Beyond_Local_Export/';
for(const[filename,data]of[[name+'.gia',ex.buffer],[`gpt_${stamp}_fighter_duel_loading_v2_索引1073741845.lua`,script.source]]){
 assert.ok(!existsSync(dir+filename));writeFileSync('outputs/duel-loading/'+filename,data);writeFileSync(dir+filename,data);console.log(dir+filename);
}

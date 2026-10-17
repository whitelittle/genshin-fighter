import{readFileSync,writeFileSync,existsSync}from'node:fs';import assert from'node:assert/strict';
import{exportGia,validateServerGiaCompatibility}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const[dir,stamp,label,path]=process.argv.slice(2);assert.match(stamp,/^\d{8}_\d{6}$/);
const save=JSON.parse(readFileSync(dir+'/fighter.save.json')),name=`gpt_${stamp}_${label}`,project=save.assets.server,script=save.assets.scripts[0];
project.root.name=name;project.meta.name=name;project.meta.giaFileName=name+'.gia';script.path='lua/'+path;script.filename=path;
const ex=exportGia(project,{scripts:save.assets.scripts});assert.ok(validateServerGiaCompatibility(ex.buffer).valid);
const targetDir='C:/Users/Cheng/AppData/LocalLow/miHoYo/原神/BeyondLocal/Beyond_Local_Export/';
for(const[filename,data]of[[name+'.gia',ex.buffer],[`gpt_${stamp}_${path}`,script.source]]){assert.ok(!existsSync(targetDir+filename));writeFileSync(dir+'/'+filename,data);writeFileSync(targetDir+filename,data);console.log(targetDir+filename);}
writeFileSync(dir+'/delivery.json',JSON.stringify({name,path:script.path,index:1073741845},null,2));

import fs from 'node:fs';
import {importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const p=process.env.LOCALAPPDATA+'Low/miHoYo/原神/BeyondLocal/Beyond_Local_Export/GF_DUAL_POOL_A.gia';
const b=fs.readFileSync(p),a=importGia(b);let names=[],mounts=[];function walk(n){names.push(n.name);if(n.scriptMappingIds?.length)mounts.push({name:n.name,ids:n.scriptMappingIds});(n.children||[]).forEach(walk)}walk(a.project.root);
console.log(JSON.stringify({bytes:b.length,root:a.project.root.name,counts:{img:names.filter(n=>/^GF_IMG_/.test(n)).length,txt:names.filter(n=>/^GF_TXT_/.test(n)).length,btn:names.filter(n=>/^GF_BTN_/.test(n)).length},mounts,scripts:a.scripts.map(s=>({guid:s.guid,path:s.path,bytes:Buffer.byteLength(s.source),head:s.source.slice(0,180)})),valid:validateServerGiaCompatibility(b).valid}));

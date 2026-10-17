import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {decode,encode} from '../../work/node-gia-wire.mjs';
// Export boundary only: keep the known working UI wire payload and replace the mounted Lua.
const args=process.argv.slice(2);const arg=k=>{const i=args.indexOf(k);assert(i>=0,'missing '+k);return args[i+1]};
const template=arg('--template'),codecPath=arg('--codec'),out=arg('--out'),name=arg('--name');
const codec=await import(pathToFileURL(codecPath).href);
const root=path.resolve(import.meta.dirname,'..');
const lua=fs.readFileSync(args.includes('--source')?arg('--source'):path.join(root,'dist/genshin_fighter.lua'),'utf8');
const build=JSON.parse(fs.readFileSync(args.includes('--build')?arg('--build'):path.join(root,'dist/build.json'),'utf8'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(sha(Buffer.from(lua)),build.sha256);
const original=fs.readFileSync(template);const imported=codec.importGia(original);
assert(codec.validateServerGiaCompatibility(original).valid);assert.equal(imported.scripts.length,1);
const old=Buffer.from(imported.scripts[0].source);let replacements=0;
function patchFields(fields,from,to){return fields.map(f=>{
 if(f.w!==2)return f;
 if(f.v.equals(from)){replacements++;return {...f,v:to}};
 try{const nested=decode(f.v);if(!encode(nested).equals(f.v))return f;
 const count=replacements;const updated=patchFields(nested,from,to);
 return replacements===count?f:{...f,v:encode(updated)};
 }catch{return f}
})}
function envelope(base,payload){const head=Buffer.from(base.subarray(0,20)),tail=base.subarray(base.length-4);head.writeUInt32BE(payload.length+20,0);head.writeUInt32BE(payload.length,16);return Buffer.concat([head,payload,tail])}
assert.equal(original.readUInt32BE(16),original.length-24);
const payload=encode(patchFields(decode(original.subarray(20,-4)),old,Buffer.from(lua)));assert.equal(replacements,1);
const a=envelope(original,payload);const validation=codec.validateServerGiaCompatibility(a);assert(validation.valid,JSON.stringify(validation.errors));
const actual=codec.importGia(a);assert.equal(actual.scripts[0].source,lua);
assert.deepEqual(actual.project,imported.project,'UI/mount changed');
replacements=0;const restored=envelope(a,encode(patchFields(decode(a.subarray(20,-4)),Buffer.from(lua),old)));
assert.equal(replacements,1);assert(restored.equals(original),'non-script GIA wire fields changed');
const scriptsOnly=codec.exportScriptGia(actual.scripts).buffer;
assert(codec.validateScriptGiaCompatibility(scriptsOnly).valid);
assert.equal(codec.importScriptGia(scriptsOnly).scripts[0].source,lua);
const b=fs.readFileSync(arg('--image-template'));
assert(codec.validateGiaCompatibility(b).valid);
assert.equal(sha(b),'87a53307c4a292e8252b8569070e12ace6380eacfe6ecee0b1f2e4b132474ef6','wrong B template');
let nodes=[];function walk(n){nodes.push(n);(n.children||[]).forEach(walk)}walk(actual.project.root);
const pool={img:nodes.filter(n=>/^GF_IMG_/.test(n.name)).length,txt:nodes.filter(n=>/^GF_TXT_/.test(n.name)).length,btn:nodes.filter(n=>/^GF_BTN_/.test(n.name)).length};
assert(pool.img>=256&&pool.txt>=96&&pool.btn>=24);
const mounts=nodes.filter(n=>(n.scriptMappingIds||[]).includes(actual.scripts[0].guid));assert.equal(mounts.length,1);assert.equal(mounts[0].name,'GF_HOST');
fs.mkdirSync(out,{recursive:true});
const files=[{kind:'mainUI',filename:name+'_A.gia',data:a},{kind:'luaOnly',filename:name+'_仅脚本.gia',data:scriptsOnly},{kind:'imageTemplate',filename:name+'_B图片模板.gia',data:b},{kind:'lua',filename:name+'.lua',data:Buffer.from(lua)}];
for(const f of files){const p=path.join(out,f.filename);assert(!fs.existsSync(p),'refuse overwriting '+f.filename);fs.writeFileSync(p,f.data);f.bytes=f.data.length;f.sha256=sha(f.data);delete f.data;}
const registry=lua.match(/__loaders\['gf_character_registry'\]\s*=\s*function\(\)([\s\S]*?)\},byKey=/);assert(registry,'roster metadata unavailable');
const roster=[...registry[1].matchAll(/\{key='([^']+)'/g)].map(m=>m[1]);assert(roster.length>=4);
const protocolVersion=Number(lua.match(/O\.VERSION\s*=\s*(\d+)/)?.[1]);assert(protocolVersion>0);
const report={name,roster,protocolVersion,scene:'intro',files,sourceSha256:build.sha256,
 templateSha256:sha(original),preservedUIWire:true,scriptMountedOnceOn:'GF_HOST',pools:pool,giaRoundTrip:true,imageTemplateByteIdentical:true,
 serverNodes:roster.length>=6?'single-character GFV2 preserved; independent GF3 team preparation and GF3Battle frames required':'existing GFV2; not GF10',nativeDeviceTested:false,externalDelivery:false};
fs.writeFileSync(path.join(out,'delivery.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({out,files,checks:{preservedUIWire:true,giaRoundTrip:true,pools:pool,mount:'GF_HOST'}}));

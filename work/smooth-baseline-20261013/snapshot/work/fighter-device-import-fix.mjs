import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const stamp=new Date().toLocaleString('sv-SE',{timeZone:'Asia/Hong_Kong'}).replace(/[-: ]/g,'');
const walk=(n,fn)=>{fn(n);for(const c of n.children||[])walk(c,fn);};
function deviceLua(source){
 const s=source.replace(/^\uFEFF/,'').replace(/\r\n?/g,'\n');let out='',i=0;
 while(i<s.length){
  if(s.slice(i,i+2)==='--'){while(i<s.length&&s[i]!=='\n')i++;continue;}
  if(s[i]==='"'||s[i]==="'"){const quote=s[i++];out+=quote;while(i<s.length){const ch=s[i++];if(ch==='\\'){out+=ch+s[i++];continue;}if(ch===quote){out+=ch;break;}if(ch.charCodeAt(0)>127)out+=[...Buffer.from(ch,'utf8')].map(b=>'\\'+String(b).padStart(3,'0')).join('');else out+=ch;}}
  else out+=s[i++];
 }
 assert.ok(!/[^\x09\x0a\x20-\x7e]/.test(out));return out;
}
for(const online of [false,true]){
 const mode=online?'online':'solo',out=`outputs/demo-${mode}-light-importfix`;mkdirSync(out,{recursive:true});
 const save=JSON.parse(readFileSync(`outputs/demo-${mode}-light/fighter.save.json`)),host=save.assets.server.root.children[0],script=save.assets.scripts[0];
 const oldGuids=[];walk(save.assets.server.root,n=>oldGuids.push(n.guid));
 save.assets.server.root.name=online?'FighterOnlineDemo_ImportFix':'FighterSoloDemo_ImportFix';
 host.active=true;host.visible=true;
 const diagnostic=structuredClone(host.children.find(n=>n.name==='Status'));diagnostic.id='fighter_boot_diagnostic';diagnostic.name='BootDiagnostic';diagnostic.children=[];diagnostic.text='界面已导入，等待 Lua 启动';diagnostic.fontSize=16;diagnostic.active=true;diagnostic.visible=true;diagnostic.raycastTarget=false;
 for(const t of Object.values(diagnostic.transformByPlatform)){t.offset={x:0,y:165};t.size={x:1100,y:28};}host.children.unshift(diagnostic);
 let guid=1073741850,count=0;const ids=new Set();
 const compact=n=>{assert.ok(!ids.has(n.id),'duplicate control id');ids.add(n.id);n.guid=guid++;count++;delete n.giaRelatedGuids;delete n.giaInfoIndex;delete n.scriptMappingIds;};
 walk(save.assets.server.root,compact);ids.clear();if(save.assets.client?.root)walk(save.assets.client.root,compact);
 script.guid=guid++;script.id=String(script.guid);script.controlId=host.id;script.controlAsset='';script.path=`lua/fighter_${mode}_importfix.lua`;
 const wrapper=`
local bootOK=false
local originalInit,originalStart,originalUpdate=OnInit,OnStart,OnUpdate
local function bootText(message)
 local control=script.object:FindChild('BootDiagnostic')
 if control then control.text=message;control:SetVisible(true)end
end
function OnInit()
 local ok,message=pcall(originalInit)
 bootOK=ok
 if ok then bootText('Lua 已初始化')else bootText('INIT ERROR: '..tostring(message));print('[fighter boot] INIT ERROR '..tostring(message))end
end
function OnStart()
 if not bootOK then return end
 local ok,message=pcall(originalStart)
 bootOK=ok
 if ok then bootText('Lua 已启动 · 格斗界面运行中')else bootText('START ERROR: '..tostring(message));print('[fighter boot] START ERROR '..tostring(message))end
end
function OnUpdate(dt)
 if not bootOK then return end
 local ok,message=pcall(originalUpdate,dt)
 if not ok then bootOK=false;bootText('UPDATE ERROR: '..tostring(message));print('[fighter boot] UPDATE ERROR '..tostring(message))end
end
`;
 const annotated=script.source+wrapper;writeFileSync(out+'/fighter-中文源稿.lua',annotated);script.source=deviceLua(annotated);
 save.meta.name=save.assets.server.root.name;save.assets.server.meta.name=save.meta.name;delete save.assets.server.meta.giaFilePath;
 save.assets.server.meta.giaFileName=save.meta.name+'.gia';save.assets.server.meta.giaFileId=save.assets.server.root.guid;
 writeFileSync(out+'/fighter.lua',script.source);writeFileSync(out+'/fighter.save.json',JSON.stringify(save));
 const ex=createStudio(save).exportData('gia-combined'),buffer=Buffer.from(ex.data,ex.encoding);assert.ok(validateServerGiaCompatibility(buffer).valid);
 const imported=importGia(buffer,'fighter-importfix.gia');assert.ok(imported.scripts.some(s=>s.source.includes('bootOK')));
 const filename=`gpt_${stamp.slice(0,8)}_${stamp.slice(8,12)}_原神格斗_${online?'双人':'单人'}_轻量_导入修订.gia`;writeFileSync(out+'/'+filename,buffer);
 const info={filename,originalGuidRange:[Math.min(...oldGuids),Math.max(...oldGuids)],newGuidRange:[1073741850,guid-1],controlCount:count,rootName:save.assets.server.root.name,serverContainerIndex:save.assets.server.root.guid,fighterRootIndex:host.guid,scriptMappingIndex:script.guid,scriptPath:script.path,scriptMount:host.name,dynamicTemplateIndexRequired:false,encoding:{ascii:true,bom:false,crlf:false},giaCompatible:true,simulatorVerified:false,deviceVerified:false,rootCause:'unconfirmed; user reports imported client hierarchy empty'};
 writeFileSync(out+'/build.json',JSON.stringify(info,null,2));console.log(JSON.stringify({out,...info}));
}

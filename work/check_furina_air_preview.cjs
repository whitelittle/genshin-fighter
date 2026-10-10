const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const helper=JSON.parse(fs.readFileSync('outputs/furina-design-20261010/helpers.json'));
const sandbox={console,Math,Set,helperBank:helper,bank:{'跳跃':{durations:[4,3,7,5,9,4]},'空重':{combatDesign:{startup:9,active:6}}},selected:'跳跃',time:16,total:32,last:0,playing:true,window:{addEventListener(){}},$:()=>({checked:true,value:1}),choose:async function(n){sandbox.selected=n;sandbox.time=0},stageRoot:()=>[410,550],tick:()=>{},drawHelpers:()=>{},drawEffects:()=>{},helperSprite:()=>{}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('work/furina_air_preview.js','utf8'),sandbox);
async function main(){
 await sandbox.choose('空重');assert.equal(sandbox.stageRoot()[1],390);
 for(let t=0;t<27;t++){sandbox.time=t;assert.equal(sandbox.stageRoot()[0],410);const h=sandbox.airHelperState(...sandbox.stageRoot());assert.equal(h.mouth[1],sandbox.stageRoot()[1]-140);assert.equal(h.active,t>=9&&t<15);assert.equal(h.index,t>=9&&t<15?2:t<9?1:3)}
 sandbox.selected='待机';sandbox.time=0;await sandbox.choose('空轻');assert(Math.abs(sandbox.stageRoot()[1]-416.053)<.01);
 vm.runInContext("moveHeld.add('arrowright');last=100",sandbox);sandbox.tick(116);assert(sandbox.stageRoot()[0]>410);
 console.log('PASS: inherited jump apex; no automatic X drift; input-only movement; shared mouth and emission stage; standalone entry height ~134');
}main().catch(e=>{console.error(e);process.exitCode=1});

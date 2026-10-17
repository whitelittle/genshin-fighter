const fs=require('fs'),vm=require('vm');const root=require('path').resolve(process.argv[2]||require('path').join(__dirname,'../dist/full-actions'));
let draws=0,seen=new Set();const ctx=new Proxy({drawImage(im){draws++;if(im._src)seen.add(im._src)}}, {get(o,k){return k in o?o[k]:(()=>{})},set(o,k,v){o[k]=v;return true}});
class Element{constructor(){this.children=[];this.value='';this.checked=false;this.type='';this.style={};this.dataset={};this.textContent='';}append(...x){this.children.push(...x)}replaceChildren(){this.children=[]}setAttribute(){}getContext(){return ctx}}
const els=new Map();const defaults={material:'fit',speed:'1',background:'#171625',qbranch:'hit',airphase:'apex'};
function get(id){if(!els.has(id)){const e=new Element();if(id in defaults)e.value=defaults[id];if(['body','fx','stageMove','opponent','boxes','loop','mirror'].includes(id)){e.type='checkbox';e.checked=!['boxes','mirror'].includes(id)}els.set(id,e)}return els.get(id)}
get('actionData').textContent=fs.readFileSync(root+'/actions.json','utf8');get('foeData').textContent=fs.readFileSync(root+'/foe-fitted.json','utf8');
class FakeImage{constructor(){this.naturalWidth=100;this.naturalHeight=100;}set src(file){if(!fs.existsSync(root+'/'+file))throw Error('Missing image '+file);this._src=file;queueMicrotask(()=>this.onload?.())}decode(){return Promise.resolve()}}
const sandbox={document:{getElementById:get,createElement:()=>new Element(),querySelectorAll:(s)=>get(s==='.frame'?'timeline':'actions').children.filter(e=>e.className===(s==='.frame'?'frame':'action'))},Image:FakeImage,localStorage:{getItem:()=>null,setItem(){}},requestAnimationFrame:()=>{},console,queueMicrotask};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(root+'/app.js','utf8'),sandbox);
(async()=>{for(let i=0;i<20;i++)await Promise.resolve();const actions=JSON.parse(get('actionData').textContent);let executions=0;for(const material of ['source','initial','fit']){get('material').value=material;for(const name of Object.keys(actions)){const branches=name==='Q · 天星'?['hit','whiff','block']:['hit'];for(const branch of branches){get('qbranch').value=branch;await vm.runInContext('choose('+JSON.stringify(name)+')',sandbox);const total=vm.runInContext('total',sandbox);seen=new Set();for(let t=0;t<total;t++){draws=0;vm.runInContext('time='+t+';render()',sandbox);if(draws<2)throw Error('Body/opponent missing '+material+' '+name+' '+branch+' '+t+' draws='+draws);executions++}const effectPaths=material==='source'?actions[name].effects?.sourceFrames:actions[name].effects?.fitFrames;if(effectPaths){const hits=effectPaths.filter(f=>seen.has(f.file)).length;const expected=name==='Q · 天星'&&branch!=='hit'?0:effectPaths.length;if(hits!==expected)throw Error('FX coverage mismatch '+name+' '+branch+' '+material+': '+hits+'/'+expected)}}}}let neutralChecks=0;
for(const material of ['source','initial','fit']){
 get('material').value=material;await vm.runInContext("choose('E · 地心')",sandbox);
 const e=actions['E · 地心'],idle=actions['待机'],list=material==='source'?idle.sourceFrames:material==='initial'?idle.initialFrames:idle.frames;
 const bodyList=material==='source'?e.sourceFrames:material==='initial'?e.initialFrames:e.frames;
 for(let t=0;t<94;t++){
  seen=new Set();vm.runInContext('time='+t+';render()',sandbox);
  if(t<36){if(!bodyList.some(f=>seen.has(f.file)))throw Error('E body missing before recovery '+material+' '+t)}
  else{
   const i=Math.floor(((t-36)%48)/24);
   if(!seen.has(list[i].file)||bodyList.some(f=>seen.has(f.file)))throw Error('E must return to correct idle material after tick36 '+material+' '+t);
   if(!get('phase').textContent.includes('待机'))throw Error('E tail label mismatch');
  }
  const effectList=material==='source'?e.effects.sourceFrames:e.effects.fitFrames;
  if(t>=14&&!effectList.some(f=>seen.has(f.file)))throw Error('Pillar disappeared during neutral tail '+material+' '+t);
  neutralChecks++;
 }
}
const html=fs.readFileSync(root+'/offline.html','utf8');
if(!html.includes('<script>'+fs.readFileSync(root+'/app.js','utf8')+'</script>'))throw Error('Offline viewer differs from app.js');
if(get('error').textContent)throw Error(get('error').textContent);console.log(JSON.stringify({materials:3,actions:25,QBranches:3,renderTicksExercised:executions,ENeutralTailChecks:neutralChecks,inlineScriptMatches:true,scope:'JavaScript control flow with fake canvas/image loader; not browser or visual acceptance'}))})().catch(e=>{console.error(e);process.exit(1)});

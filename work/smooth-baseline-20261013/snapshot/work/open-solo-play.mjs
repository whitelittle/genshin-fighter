const sessionId='genshin-fighter-demo-solo';
async function post(action,body){const response=await fetch('http://127.0.0.1:4192/editor/api/'+action,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({sessionId,...body})});const result=await response.json();if(!response.ok||!result.ok)throw Error(JSON.stringify(result));return result.value;}
await post('load-archive',{path:'outputs/demo-solo-light/fighter.save.json'});
const state=await post('play',{action:'start',args:{playerCount:1,viewPlayerIndex:1}});
console.log(JSON.stringify({url:'http://127.0.0.1:4192/editor/play#'+sessionId,running:state.running,playerCount:state.playerCount}));

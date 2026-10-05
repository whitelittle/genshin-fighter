import {g,defineSignal} from 'genshin-ts/runtime/core'

// 原神格斗 online relay (server graph, genshin-ts). Port of our 泡泡堂 relay
// (genshin-ugc stage-squid-game/campaign/graphs/paopao-relay.ts). The server never
// simulates the fight: both clients run the deterministic simulation and the rollback
// netcode in Lua (game/lua/gf_net.lua, gf_online.lua); this graph only identifies
// senders and relays packets.
// Identity: per-player random GF_NONCE; GF_SLOT 1..8 = smallest free slot among players on
// the field, re-derived every second so leavers free their slot.
// Packet: int list of length 24, [1] = -7201, [2] = nonce (gf_net.lua N.F).
// Relay: Level GF_IN_<slot> = packet as received. Level GF_SLOTS = [8, 8 x 0/1].
// Debug:  Level GF_DIAG = [1, receipts, lastSlot, rejected]
// Needs in the map: PlayerSelf int vars GF_NONCE, GF_SLOT; Level int-list vars GF_IN_1..8,
// GF_SLOTS, GF_DIAG; the signal family SQ_REC_STRIKE_V1 with one int-list parameter
// (genshin-ugc scripts/native_signal.py). The entity id below is a placeholder: use the
// stage / level entity of the target map.
const net=defineSignal('SQ_REC_STRIKE_V1',[['request','int_list']] as const)
g.server({id:1073741916,name:'GF_原神格斗_中转',variables:{
 receipts:0n,
 rejected:0n
}}).on('whenEntityIsCreated',(evt,f)=>{
 f.startTimer(evt.eventSourceEntity,'GF_TICK',true,[1])
}).on('whenTimerIsTriggered',(evt,f)=>{
 if(evt.timerName!=='GF_TICK')return
 const players=f.getListOfPlayerEntitiesOnTheField()
 for(const player of players){
  if(f.getCustomVariable(player,'GF_NONCE').asType('int')===0n){
   f.setCustomVariable(player,'GF_NONCE',f.getRandomInteger(100000n,2000000000n),false)
  }
 }
 // resolve duplicate slots (two players claiming the same one): the later keeps 0
 for(const player of players){
  const mine=f.getCustomVariable(player,'GF_SLOT').asType('int')
  if(mine!==0n){
   let owners=0n
   for(const other of players){
    if(f.getCustomVariable(other,'GF_SLOT').asType('int')===mine)owners+=1n
   }
   if(owners>1n)f.setCustomVariable(player,'GF_SLOT',0n,false)
  }
 }
 for(const player of players){
  if(f.getCustomVariable(player,'GF_SLOT').asType('int')===0n){
   let chosen=0n
   for(let k=1n;k<=8n;k+=1n){
    if(chosen===0n){
     let used=0n
     for(const other of players){
      if(f.getCustomVariable(other,'GF_SLOT').asType('int')===k)used=1n
     }
     if(used===0n)chosen=k
    }
   }
   if(chosen!==0n)f.setCustomVariable(player,'GF_SLOT',chosen,false)
  }
 }
 let s1=0n,s2=0n,s3=0n,s4=0n,s5=0n,s6=0n,s7=0n,s8=0n
 for(const player of players){
  const k=f.getCustomVariable(player,'GF_SLOT').asType('int')
  if(k===1n)s1=1n
  if(k===2n)s2=1n
  if(k===3n)s3=1n
  if(k===4n)s4=1n
  if(k===5n)s5=1n
  if(k===6n)s6=1n
  if(k===7n)s7=1n
  if(k===8n)s8=1n
 }
 f.setCustomVariable(evt.eventSourceEntity,'GF_SLOTS',[8n,s1,s2,s3,s4,s5,s6,s7,s8],false)
}).onSignal(net,(evt,f)=>{
 const request=evt.params.request
 if(request.length!==24 || request[0]!==-7201n)return
 const nonce=request[1]
 let slot=0n
 if(nonce!==0n){
  for(const player of f.getListOfPlayerEntitiesOnTheField()){
   if(slot===0n && f.getCustomVariable(player,'GF_NONCE').asType('int')===nonce){
    slot=f.getCustomVariable(player,'GF_SLOT').asType('int')
   }
  }
 }
 const stage=evt.eventSourceEntity
 if(slot===1n)f.setCustomVariable(stage,'GF_IN_1',request,false)
 if(slot===2n)f.setCustomVariable(stage,'GF_IN_2',request,false)
 if(slot===3n)f.setCustomVariable(stage,'GF_IN_3',request,false)
 if(slot===4n)f.setCustomVariable(stage,'GF_IN_4',request,false)
 if(slot===5n)f.setCustomVariable(stage,'GF_IN_5',request,false)
 if(slot===6n)f.setCustomVariable(stage,'GF_IN_6',request,false)
 if(slot===7n)f.setCustomVariable(stage,'GF_IN_7',request,false)
 if(slot===8n)f.setCustomVariable(stage,'GF_IN_8',request,false)
 const receipts=f.get('receipts')+1n
 f.set('receipts',receipts)
 let rejected=f.get('rejected')
 if(slot===0n)rejected=rejected+1n
 f.set('rejected',rejected)
 f.setCustomVariable(stage,'GF_DIAG',[1n,receipts,slot,rejected],false)
})

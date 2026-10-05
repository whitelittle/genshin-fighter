import{readFileSync,writeFileSync,mkdirSync,copyFileSync,existsSync}from'node:fs';
const root='outputs/motion-group1/lawachurl';mkdirSync(root,{recursive:true});mkdirSync(root+'/reused-source',{recursive:true});
const old=JSON.parse(readFileSync('assets/roster-v2/lawachurl-frames.json','utf8'));
const aliases={idle2:'idle',airHurt:'hurt',getup:'crouch',windup:'guard',low:'slash',rising:'slash',eThrow:'special',qCharge:'guard'};
const ids={basic:['idle','idle2','walk1','idle','walk2','crouch','guard','crouchGuard','crouch','jump','jump','crouch','hurt','airHurt','down','getup'],attack:['windup','slash','idle','crouch','low','crouch','jump','slash','guard','special','idle','qCharge','qRelease','idle','guard','idle'],connections:['windup','windup','windup','slash','slash','idle','idle','idle','eThrow','eThrow','eThrow','special','special','idle','idle','idle']};
const frames=[];
for(const[kind,list]of Object.entries(ids))for(const[slot,pose]of list.entries()){
 const f=old.frames.find(f=>f.pose===pose),primary=aliases[pose]||pose,source='reused-source/lawachurl-'+primary+'.png';if(!existsSync(root+'/'+source))copyFileSync('assets/roster-v2/lawachurl-'+primary+'.png',root+'/'+source);
 frames.push({id:kind+slot,source,crop:[0,0,f.w,f.h],anchor:f.anchor,unit:f.scale,review:'reused_correct_roster_v2',edgeRisk:false,reusedPose:pose});
}
const move=(name,startup,reach,damage)=>({name,startup,active:5,recovery:30,reach,damage,hitCount:1,height:'mid',hitstun:25,fx:'impact',effectExtent:reach+20});
const role={key:'lawachurl',name:'岩盔丘丘王 · 正确旧版复用',height:295,design:{key:'lawachurl',name:'岩盔丘丘王',moves:{A:move('岩臂挥击',20,155,12),E:move('冲击砸地',24,220,20),Q:move('重击震地',30,270,34)}},frames,notes:['复用roster-v2正确身份的12个独立关键姿势；48状态槽含重复映射，不是48张新动作。','暂无新绘制的8张连续连接帧；关键帧代用已明确记录。','像素负载重新按96身体像素拟合，原素材与旧版数据保留。'],uniqueSourceFrames:12,reusedStateSlots:48};
writeFileSync(root+'/source-manifest.json',JSON.stringify({version:'lawachurl-reuse',status:'reused_candidate',deviceVerified:false,roles:[role]},null,2));console.log('LAWACHURL_CORRECT_REUSE',12);

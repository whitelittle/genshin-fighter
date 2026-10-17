import{readFileSync as read,writeFileSync as write}from'node:fs';import assert from'node:assert/strict';
const out=process.env.REPAIR_OUT||'outputs/midphase-final',save=JSON.parse(read(out+'/base.save.json'));let s=save.assets.scripts[0].source;
function rep(a,b){assert(s.includes(a),'mechanics target missing '+a);s=s.replace(a,b);}
rep('b.face==-a.face and b.stun<=0 and not b.attack','b.face==-a.face and (b.stun<=0 or b.guardStun) and not b.attack');
rep('b.stun=blocked and 8 or s.stun;','b.stun=blocked and 8 or s.stun;b.guardStun=blocked;');
rep('if a.stun>0 then a.stun=a.stun-1 end','if a.stun>0 then a.stun=a.stun-1 end;if a.stun<=0 then a.guardStun=false end');
rep('elseif a.stun>0 then return ids.basic12','elseif a.stun>0 then return ids[a.guardStun and(a.crouch and\'basic7\'or\'basic6\')or\'basic12\']');
rep('group1Sequence(m.walk,tick%32)','group1Sequence(m.walk,math.floor(a.walk*5)%32)');
rep("local fields={'x'","local fields={'guardStun','x'");
rep('local boolFields={launched=true','local boolFields={guardStun=true,launched=true');
rep('if #values~=62 then','if #values~=10+2*(#fields+5) then');
rep('actors[i]:SetAnchoredPosition(a.x,-182+a.y);', 'actors[i]:SetAnchoredPosition(a.x,Collision.floorY()+a.y);');
rep("rootNode('Shadow'..i):SetAnchoredPosition(a.x,-184);", "rootNode('Shadow'..i):SetAnchoredPosition(a.x,Collision.floorY()-2);");
rep("node:SetAnchoredPosition((b[1]+b[3])/2,-182+(b[2]+b[4])/2)","node:SetAnchoredPosition((b[1]+b[3])/2,Collision.floorY()+(b[2]+b[4])/2)");
rep('function Collision.drawStage(fighting)',`function Collision.floorY()
 local frame=Collision.stageData[Collision.stageId(stage,round)];local cw,ch=game.GetUICanvasSize()
 return (frame.h*.5-frame.h*.81)*math.max(cw/frame.w,ch/frame.h)
end
function Collision.drawStage(fighting)`);
if(process.env.FINAL_HUD==='dots'){
 const begin=s.indexOf('function Collision.drawHUD(fighting)'),end=s.indexOf('function Collision.drawBoxes()',begin);assert(begin>0&&end>begin);
 s=s.slice(0,begin)+`function Collision.drawHUD(fighting)
 local host=rootNode('BattleTeamHUD');host:SetVisible(fighting)
 for p=1,2 do for n=1,3 do local name='BattleTeam'..p..n;local plate=host:FindChild(name..'Plate');local winner=Collision.results[n]
 local active=winner==nil and n==round;local loss=winner~=nil and winner~=0 and winner~=p
 local color=loss and 0xff555b65 or(p==1 and(active and 0xff8bcaff or 0xff438ce7)or(active and 0xffffa4a4 or 0xffe45565))
 for _,stripe in ipairs(plate:GetChildren())do stripe.imageColor=color end
 plate:SetLocalScale(active and 1.3 or 1,active and 1.3 or 1,1)
 host:FindChild(name..'Face'):SetVisible(false);host:FindChild(name..'Text'):SetVisible(false)
 end end
end
`+s.slice(end);
 function find(n,name){if(n.name===name)return n;for(const c of n.children||[]){const f=find(c,name);if(f)return f;}}
 const hud=find(save.assets.server.root,'BattleTeamHUD');let serial=0;
 for(let p=1;p<=2;p++)for(let n=1;n<=3;n++){
  const plate=find(hud,'BattleTeam'+p+n+'Plate'),proto=structuredClone(plate);plate.imageColor=0;plate.children=[];
  for(const t of Object.values(plate.transformByPlatform)){t.offset={x:(p===1?-598:598)+(n-2)*22,y:229};t.size={x:14,y:14};}
  for(let y=-6;y<=6;y+=2){const stripe=structuredClone(proto);stripe.children=[];stripe.name='DotStripe'+(++serial);stripe.id='final_dot_'+serial;stripe.guid=1076200000+serial;stripe.imageColor=p===1?0xff438ce7:0xffe45565;for(const t of Object.values(stripe.transformByPlatform)){t.offset={x:0,y};t.size={x:2*Math.sqrt(49-y*y),y:2};}plate.children.push(stripe);}
 }
 save._pixelJobs=save._pixelJobs.filter(j=>j.path[0]!=='BattleTeamHUD');
 const top=find(save.assets.server.root,'TopPanel');for(const t of Object.values(top.transformByPlatform)){t.offset={x:0,y:270};t.size={x:1400,y:220};}
 for(const[name,x,label]of[['ExitMatch',-140,'返回首页'],['CommandToggle',140,'指令表']]){
  const button=find(save.assets.server.root,name);button.kind='cursor';button.children=button.children.filter(c=>c.name===name+'Caption');
  for(const t of Object.values(button.transformByPlatform)){t.offset={x,y:345};t.size={x:100,y:32};}
  const caption=button.children[0];caption.text=label;caption.fontSize=16;caption.minimumFontSize=14;caption.adaptiveFontSize=false;
  for(const t of Object.values(caption.transformByPlatform)){t.offset={x:0,y:0};t.size={x:100,y:30};}
 }
}
save.assets.scripts[0].source=s;write(out+'/base.save.json',JSON.stringify(save));
write(out+'/mechanics-changes.json',JSON.stringify({continuousGuard:true,guardVisual:true,guardInRollbackSerialization:true,walkClock:'per fighter movement',damageBalanceChanged:false,allWalkArtRepaired:false},null,2));console.log('FINAL_MECHANICS_READY');

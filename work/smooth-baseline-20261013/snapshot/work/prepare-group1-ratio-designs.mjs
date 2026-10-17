import{readFileSync,writeFileSync}from'node:fs';
import{designs}from'./action-probe-design.mjs';
for(const[key,name,height]of[['klee','可莉',150],['yanfei','烟绯',210]]){
 const m=(name,startup,active,recovery,reach,damage,fx,notes)=>({name,startup,active,recovery,reach,damage,fx,notes,height:'mid',hitCount:1,blockstun:12,hitstun:20,effectExtent:reach+22});
 const yanfei={key,name,weapon:'catalyst',color:'#ef997d',identity:'火系法器施法手势与丹书印记；正常青年女性比例',evidence:'原作技能方向沿用docs/第一版角色改编与素材来源；下列距离与时长为新探针候选，不是已批准战斗平衡。',moves:{A:m('火漆制印 · 掌势',10,4,19,160,9,'fireball','前掌推出，重心跟进，弹体独立。'),E:m('丹书立约 · 印落',17,5,27,210,15,'seal','明确落掌施法；印记不烘焙入人物帧。'),Q:m('凭此结契 · 契印终击',27,5,35,260,32,'seal','本轮命中演出候选；不是原作持续增益完整状态。')}};
 const design=structuredClone(designs.find(d=>d.key===key)||(key==='yanfei'?yanfei:null));if(!design)throw Error('Missing explicit design '+key);
 design.moves.Q.hitCount=1;design.moves.Q.support=false;design.moves.Q.effectDuration=0;
 writeFileSync(`outputs/motion-group1/${key}/role-design.json`,JSON.stringify({key,name,height,design,notes:['第一批比例修订候选；基础/攻击/连接姿势各16张，普攻/E各8张连接。',key==='klee'?'正常儿童比例，原显示150；预览整体等比120%，不拉长身体，不改变碰撞体。':'青年女性正常头身比；不靠缩小整张图掩盖大头。','具体特效仍待讨论；未接入正式测试GIA或真机验收。']},null,2));
}
